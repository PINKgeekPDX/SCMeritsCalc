"""SCMC Qt UI module."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


from PyQt6.QtCore import (
    QEvent,
    QRect,
    Qt,
    QUrl,
    QThread,
    pyqtSignal,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
)
from PyQt6.QtGui import (
    QDesktopServices,
    QFont,
    QIcon,
    QPainter,
    QPixmap,
    QKeySequence,
    QShortcut,
    QGuiApplication,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QScrollArea,
    QSlider,
    QSystemTrayIcon,
    QTabWidget,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QGraphicsOpacityEffect,
)

from .updater import UpdateManager
from .settings import _app_data_dir
from .theme import (
    get_main_stylesheet,
    get_dialog_stylesheet,
    ANIM_DURATION_NORMAL,
)
from .widgets import (
    HoloInput,
    SciFiPanel,
    GlowLabel,
    AnimatedProgressBar,
    QuantumButton,
)

try:
    from PyQt6.QtWidgets import QKeySequenceEdit

    HAVE_KEYSEQ = True
except ImportError:
    HAVE_KEYSEQ = False

try:
    import pyperclip  # type: ignore
except ImportError:
    pyperclip = None


BASE_DIR = Path(__file__).resolve().parent.parent


def resource_path(rel: str) -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass) / rel
    return Path(__file__).resolve().parents[2] / rel


def get_app_icon() -> QIcon:
    ico = resource_path("assets/app-logo.ico")
    png = resource_path("assets/app-logo.png")
    if ico.exists():
        return QIcon(str(ico))
    if png.exists():
        return QIcon(str(png))
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.GlobalColor.cyan)
    p.drawEllipse(4, 4, 56, 56)
    p.end()
    return QIcon(pm)


class ClickableSciFiPanel(SciFiPanel):
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.on_double_click = None

    def mouseDoubleClickEvent(self, event):
        if self.on_double_click:
            self.on_double_click()
        super().mouseDoubleClickEvent(event)


class UpdateWorker(QThread):
    """Worker thread for update operations."""

    progress = pyqtSignal(float, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(
        self, manager: UpdateManager, mode: str, download_dir: Optional[Path] = None
    ):
        super().__init__()
        self.manager = manager
        self.mode = mode  # "check" or "download"
        self.download_dir = download_dir
        self._result = None

    def run(self):
        try:
            if self.mode == "check":
                self.progress.emit(0, "Checking for updates...")
                result = self.manager.check_for_updates()
                self.progress.emit(100, "Check complete")
                self.finished.emit(result)
            elif self.mode == "download":
                self.progress.emit(0, "Starting download...")

                def cb(pct, status):
                    self.progress.emit(pct, status)

                path = self.manager.download_update(self.download_dir, cb)
                self.finished.emit(path)
        except Exception as e:
            self.error.emit(str(e))


class UpdateDialog(QDialog):
    """Dialog for checking and downloading updates."""

    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Check for Updates")
        self.setFixedSize(340, 200)
        self.manager = UpdateManager()
        self.worker = None
        self.installer_path = None
        self._btn_policy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._init_ui()
        self._start_check()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(8, 8, 8, 8)

        # Status panel using SciFiPanel for consistency
        status_panel = SciFiPanel("UPDATE STATUS")
        status_layout = QVBoxLayout(status_panel)
        status_layout.setContentsMargins(6, 8, 6, 6)
        status_layout.setSpacing(2)

        # Status Header with glow effect
        self.lbl_status_header = GlowLabel(
            "Checking for Updates...", status_panel, glow_enabled=True
        )
        f = QFont()
        f.setPointSize(10)
        f.setBold(True)
        self.lbl_status_header.setFont(f)
        self.lbl_status_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.lbl_status_header)

        # Animated Progress Bar
        self.progress_bar = AnimatedProgressBar(status_panel)
        self.progress_bar.setRange(0, 0)  # Indeterminate initially
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(18)
        status_layout.addWidget(self.progress_bar)

        # Status Text
        self.lbl_status = QLabel("Connecting to release server...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("color: #a0d0ff; font-size: 9pt;")
        status_layout.addWidget(self.lbl_status)

        layout.addWidget(status_panel)

        # Error Box (Hidden) - wrapped in SciFiPanel
        error_panel = SciFiPanel("ERROR")
        error_layout = QVBoxLayout(error_panel)
        error_layout.setContentsMargins(6, 8, 6, 6)
        self.txt_error = QTextEdit()
        self.txt_error.setReadOnly(True)
        self.txt_error.setVisible(False)
        self.txt_error.setFixedHeight(60)
        error_layout.addWidget(self.txt_error)
        error_panel.setVisible(False)
        self._error_panel = error_panel
        layout.addWidget(error_panel)

        # Buttons with glow effects
        self.btn_box = QHBoxLayout()
        self.btn_box.setSpacing(3)
        self.btn_download = QuantumButton("Download", self)
        self.btn_install = QuantumButton("Download & Update", self)
        self.btn_close = QuantumButton("Cancel", self)

        for btn in (self.btn_download, self.btn_install, self.btn_close):
            btn.setMinimumHeight(26)
            btn.setSizePolicy(self._btn_policy)

        self.btn_download.setVisible(False)
        self.btn_install.setVisible(False)

        self.btn_download.clicked.connect(
            lambda: self._start_download(install_now=False)
        )
        self.btn_install.clicked.connect(lambda: self._start_download(install_now=True))
        self.btn_close.clicked.connect(self.close)

        self.btn_box.addWidget(self.btn_download)
        self.btn_box.addWidget(self.btn_install)
        self.btn_box.addWidget(self.btn_close)
        layout.addLayout(self.btn_box)

        # Apply futuristic theme
        self.setStyleSheet(get_dialog_stylesheet())

    def _start_check(self):
        self.worker = UpdateWorker(self.manager, "check")
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_check_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _start_download(self, install_now: bool):
        self.lbl_status_header.setText("Downloading Update...")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self._error_panel.setVisible(False)
        self.btn_download.setVisible(False)
        self.btn_install.setVisible(False)
        self.btn_close.setText("Cancel")

        # Use persistent directory
        dl_dir = _app_data_dir() / "updates"

        self.worker = UpdateWorker(self.manager, "download", dl_dir)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(
            lambda path: self._on_download_finished(path, install_now)
        )
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, pct, status):
        self.lbl_status.setText(status)
        self.lbl_status.setStyleSheet("color: #a0d0ff; font-size: 9pt;")
        if self.worker and self.worker.mode == "download":
            self.progress_bar.setValue(int(pct))

    def _on_check_finished(self, result):
        available, version_str, notes = result
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)

        if available:
            self.lbl_status_header.setText(f"Update Available: v{version_str}")
            self.lbl_status.setText("A new version is available!")
            self.lbl_status.setStyleSheet("color: #20ff80; font-size: 10pt;")
            self.btn_download.setVisible(True)
            self.btn_install.setVisible(True)
            self.btn_close.setText("Close")
        else:
            from .version import __version__

            self.lbl_status_header.setText("SCMC is up to date")
            self.lbl_status_header.setStyleSheet("color: #20ff80;")
            self.lbl_status.setStyleSheet("color: #20ff80; font-size: 9pt;")
            self.lbl_status.setText(f"Current: {__version__} | Latest: {version_str}")
            self.btn_close.setText("Close")

    def _on_download_finished(self, path, install_now):
        self.installer_path = path
        self.lbl_status.setText("Download Complete!")
        self.lbl_status.setStyleSheet("color: #20ff80; font-size: 9pt;")

        if install_now:
            self.lbl_status_header.setText("Installing...")
            try:
                self.manager.run_installer(path)
                QApplication.instance().quit()
            except Exception as e:
                self._on_error(f"Failed to launch installer: {e}")
        else:
            # Save for later
            if self.settings:
                self.settings.set("pending_update_path", str(path))
            self.lbl_status_header.setText("Ready to Install")
            self.lbl_status.setText(
                "Update downloaded. Will install on next app start."
            )
            self.btn_close.setText("Close")

    def _on_error(self, msg):
        self.lbl_status_header.setText("Error Occurred")
        self.lbl_status.setText("An error occurred during the operation.")
        self.progress_bar.setVisible(False)
        self._error_panel.setVisible(True)
        self.txt_error.setVisible(True)
        self.txt_error.setText(msg)
        self.btn_close.setText("Close")
        self.btn_download.setVisible(False)
        self.btn_install.setVisible(False)


class UpdateFoundDialog(QDialog):
    """Shown when an update is found during startup auto-check."""

    def __init__(
        self,
        parent,
        manager: UpdateManager,
        version_str: str,
        notes: str | None,
        settings,
    ):
        super().__init__(parent)
        self.manager = manager
        self.settings = settings
        self.version_str = version_str
        self.notes = notes or "No release notes provided."
        self.worker: UpdateWorker | None = None
        self.download_path: str | None = None
        self._btn_policy = QSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        self.setWindowTitle("Update Available")
        self.setFixedSize(360, 280)
        self._init_ui()
        self.setStyleSheet(get_dialog_stylesheet())

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header panel
        header_panel = SciFiPanel("UPDATE FOUND")
        header_layout = QVBoxLayout(header_panel)
        header_layout.setContentsMargins(6, 8, 6, 6)
        header_layout.setSpacing(2)

        header = GlowLabel(f"v{self.version_str}", header_panel, glow_enabled=True)
        f = QFont()
        f.setPointSize(11)
        f.setBold(True)
        header.setFont(f)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(header)

        layout.addWidget(header_panel)

        # Meta details - more compact
        try:
            _, size_bytes, _ = self.manager.get_installer_meta()
        except Exception:
            _, size_bytes, _ = (None, None, None)

        size_str = "Unknown"
        if isinstance(size_bytes, int) and size_bytes > 0:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

        meta_box = SciFiPanel("DETAILS")
        meta_layout = QVBoxLayout(meta_box)
        meta_layout.setContentsMargins(6, 8, 6, 6)
        meta_layout.setSpacing(2)

        version_lbl = QLabel(f"Version: {self.version_str}")
        version_lbl.setStyleSheet("color: #a0d0ff; font-size: 9pt;")
        meta_layout.addWidget(version_lbl)

        size_lbl = QLabel(f"Size: {size_str}")
        size_lbl.setStyleSheet("color: #a0d0ff; font-size: 9pt;")
        meta_layout.addWidget(size_lbl)

        self.lbl_status = QLabel("Select an option below.")
        self.lbl_status.setStyleSheet(
            "color: #a0d0ff; font-size: 8pt; font-style: italic;"
        )
        meta_layout.addWidget(self.lbl_status)
        layout.addWidget(meta_box)

        # Notes - more compact with scroll if needed
        notes_box = SciFiPanel("RELEASE NOTES")
        notes_layout = QVBoxLayout(notes_box)
        notes_layout.setContentsMargins(6, 8, 6, 6)
        notes_layout.setSpacing(2)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFixedHeight(60)
        scroll_area.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )

        notes_label = QLabel(self.notes.strip())
        notes_label.setWordWrap(True)
        notes_label.setStyleSheet("color: #b8d4ff; font-size: 8pt; padding: 2px;")
        notes_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(notes_label)
        notes_layout.addWidget(scroll_area)
        layout.addWidget(notes_box)

        # Buttons - more compact
        btn_row = QHBoxLayout()
        btn_row.setSpacing(3)
        self.btn_now = QuantumButton("Update Now", self)
        self.btn_later = QuantumButton("Update Later", self)
        self.btn_ignore = QuantumButton("Ignore", self)
        for b in (self.btn_now, self.btn_later, self.btn_ignore):
            b.setMinimumHeight(26)
            b.setSizePolicy(self._btn_policy)
        self.btn_now.clicked.connect(
            lambda: self._start_download(install_now=True, next_exit=False)
        )
        self.btn_later.clicked.connect(
            lambda: self._start_download(install_now=False, next_exit=True)
        )
        self.btn_ignore.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_now)
        btn_row.addWidget(self.btn_later)
        btn_row.addWidget(self.btn_ignore)
        layout.addLayout(btn_row)

        # Never update toggle - more compact
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(3)
        toggle_row.addStretch()
        self.chk_never = QCheckBox("Never Update")
        self.chk_never.setChecked(bool(self.settings.get("never_update", False)))
        self.chk_never.setStyleSheet("color: #a0d0ff; font-size: 8pt;")
        self.chk_never.toggled.connect(
            lambda v: self.settings.set("never_update", bool(v))
        )
        toggle_row.addWidget(self.chk_never)
        layout.addLayout(toggle_row)

    def _set_busy(self, busy: bool):
        for btn in (self.btn_now, self.btn_later, self.btn_ignore):
            btn.setEnabled(not busy)

    def _start_download(self, install_now: bool, next_exit: bool):
        if self.worker:
            return
        self._set_busy(True)
        self.lbl_status.setText("Downloading update...")
        self.lbl_status.setStyleSheet(
            "color: #a0d0ff; font-size: 9pt; font-style: italic;"
        )
        dl_dir = _app_data_dir() / "updates"
        self.worker = UpdateWorker(self.manager, "download", dl_dir)
        self.worker.progress.connect(
            lambda pct, status: (
                self.lbl_status.setText(status),
                self.lbl_status.setStyleSheet(
                    "color: #a0d0ff; font-size: 9pt; font-style: italic;"
                ),
            )
        )
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(
            lambda path: self._on_download_finished(path, install_now, next_exit)
        )
        self.worker.start()

    def _on_download_finished(self, path, install_now: bool, next_exit: bool):
        self.download_path = path
        if next_exit:
            if self.settings:
                self.settings.set("pending_update_path", str(path))
            self.lbl_status.setText("Update downloaded. Will install on next exit.")
            self.lbl_status.setStyleSheet("color: #20ff80; font-size: 9pt;")
            self._set_busy(False)
            return
        if install_now:
            try:
                self.lbl_status.setText("Launching installer...")
                self.lbl_status.setStyleSheet(
                    "color: #a0d0ff; font-size: 9pt; font-style: italic;"
                )
                self.manager.run_installer(path)
                app = QApplication.instance()
                if app is not None:
                    app.quit()
            except Exception as e:
                self._on_error(str(e))

    def _on_error(self, msg: str):
        self.lbl_status.setText(f"Error: {msg}")
        self.lbl_status.setStyleSheet("color: #ff4444; font-size: 9pt;")
        self._set_busy(False)


class QtMeritCalcApp(QMainWindow):
    """Application main window for Merits calculations and reporting."""

    def __init__(self, s, c):
        super().__init__()
        self.settings = s
        self.calculator = c
        self.seconds_per_merit = float(
            self.settings.get("rate_merits_seconds", 1.0) or 1.0
        )
        self._updating = False
        self.in_hours = None
        self.in_minutes = None
        self.in_merits = None
        self.out_merits_fee = None
        self.out_auec = None
        self.btn_copy = None
        self.btn_save = None
        self.chk_min_tray = None
        self.chk_on_top = None
        self.sld_transparency = None
        self.spin_rate = None
        self.spin_fee = None
        self.tbl_keys = None
        self.sld_dpi = None
        self.chk_auto_scale = None
        self.spin_font = None
        self.tray = None
        self._shortcuts = []
        self._startup_anim = None
        self._startup_effect = None
        self._auto_update_worker = None
        self.setWindowTitle("SCMC")
        # Initialize tab animation
        self._tab_animation = None
        self._dpi_scale_factor = self._compute_dpi_scale()

        # Fixed window size to avoid scaling artifacts, scaled by DPI
        g = self.settings.get_window_geometry()
        base_w, base_h = 392, 534
        scaled_w = int(round(base_w * self._dpi_scale_factor))
        scaled_h = int(round(base_h * self._dpi_scale_factor))
        self.setGeometry(QRect(g["x"], g["y"], scaled_w, scaled_h))
        self.setFixedSize(scaled_w, scaled_h)
        self._init_ui()
        self._init_tray()

        # Ensure geometry is saved on application quit (covers tray exit)
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(
                lambda: self.settings.set_window_geometry(
                    self.geometry().x(),
                    self.geometry().y(),
                    self.geometry().width(),
                    self.geometry().height(),
                )
            )
        # Ensure geometry is saved on application quit (covers tray exit)

        # Apply initial transparency
        if bool(self.settings.get("transparency_enabled", True)):
            self.setWindowOpacity(float(self.settings.get("window_transparency", 0.9)))
        # Soft fade-in on startup to reinforce holo feel
        QTimer.singleShot(10, self._animate_startup)

        # Store reference to observer for later restoration
        self._settings_observers = []

        # Initialize Toast Overlay
        self._init_toasts()

        # Apply global application styles (like tooltips)
        self._apply_global_styles()

        # React to settings changes instantly
        def _on_setting_changed(key, value):
            if key == "window_transparency":
                try:
                    self.setWindowOpacity(float(value))
                except Exception:
                    pass
            elif key == "always_on_top":
                try:
                    self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, bool(value))
                    self.show()
                except Exception:
                    pass
                try:
                    val = float(value)
                    if hasattr(self, "lbl_fee_header"):
                        self.lbl_fee_header.setText(f"MERITS WITH {val:.1f}% FEE (☼)")
                        self._calculate()
                except Exception:
                    pass

            self.show_toast("Settings Saved", 1500)

        self.settings.add_observer(_on_setting_changed)

        # Check for pending updates
        self._check_pending_update()
        # Silent update check at startup
        QTimer.singleShot(0, self._auto_check_updates_on_start)

    def _animate_startup(self):
        """Fade in the main window for a subtle holo effect."""
        if self._startup_anim:
            return
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(0.0)
        self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(350)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _cleanup():
            # Remove effect after animation to avoid stacking
            self.setGraphicsEffect(None)

        anim.finished.connect(_cleanup)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self._startup_anim = anim
        self._startup_effect = effect

    def _init_toasts(self):
        # Status-bar–based toast replacement
        self._toast = None

    def show_toast(self, message: str, duration: int = 2500):
        if hasattr(self, "status_label") and hasattr(self, "_status_effect"):
            self.status_label.setText(message)
            self._status_anim.stop()
            self._status_anim.setStartValue(self._status_effect.opacity())
            self._status_anim.setEndValue(1.0)
            self._status_anim.start()
            self._status_timer.start(duration)

    def _fade_out_status(self):
        if not hasattr(self, "_status_effect"):
            return
        self._status_anim.stop()
        self._status_anim.setStartValue(self._status_effect.opacity())
        self._status_anim.setEndValue(0.0)
        self._status_anim.start()

    def _apply_global_styles(self):
        """Apply global stylesheet enhancements like tooltips."""
        # Get existing stylesheet or start fresh
        app = QApplication.instance()
        current_style = app.styleSheet() if app else ""

        tooltip_style = """
        QToolTip {
            background-color: #0a1016;
            color: #a0d0ff;
            border: 1px solid #00a2cc;
            padding: 4px;
            border-radius: 4px;
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
        }
        """
        if tooltip_style not in current_style:
            if app:
                app.setStyleSheet(current_style + tooltip_style)

    def _check_pending_update(self):
        pending = self.settings.get("pending_update_path")
        if pending and Path(pending).exists():
            dlg = QDialog(self)
            dlg.setWindowTitle("Update Ready")
            dlg.setFixedSize(300, 140)

            layout = QVBoxLayout(dlg)
            layout.setSpacing(4)
            layout.setContentsMargins(8, 8, 8, 8)

            # Status panel
            status_panel = SciFiPanel("UPDATE READY")
            status_layout = QVBoxLayout(status_panel)
            status_layout.setContentsMargins(6, 8, 6, 6)
            status_layout.setSpacing(3)

            lbl = QLabel(
                "An update has been downloaded.\nWould you like to install it now?"
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #a0d0ff; font-size: 9pt;")
            lbl.setWordWrap(True)
            status_layout.addWidget(lbl)
            layout.addWidget(status_panel)

            # Buttons
            btn_row = QHBoxLayout()
            btn_row.setSpacing(3)
            btn_yes = QuantumButton("Yes", dlg)
            btn_no = QuantumButton("No", dlg)
            for btn in (btn_yes, btn_no):
                btn.setMinimumHeight(26)
                btn.setSizePolicy(
                    QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                )
            btn_row.addWidget(btn_yes)
            btn_row.addWidget(btn_no)
            layout.addLayout(btn_row)

            btn_yes.clicked.connect(dlg.accept)
            btn_no.clicked.connect(dlg.reject)

            # Apply futuristic theme
            dlg.setStyleSheet(get_dialog_stylesheet())

            if dlg.exec() == QDialog.DialogCode.Accepted:
                try:
                    # Clear setting so we don't loop if it fails silently or user cancels installer
                    self.settings.set("pending_update_path", "")
                    UpdateManager().run_installer(pending)
                    QApplication.instance().quit()
                except Exception as e:
                    print(f"Error launching installer: {e}")

    def _check_for_updates(self):
        dlg = UpdateDialog(self, self.settings)
        dlg.exec()

    def _auto_check_updates_on_start(self):
        """Silently check for updates at startup if enabled."""
        if bool(self.settings.get("never_update", False)):
            return
        if not bool(self.settings.get("auto_check_updates", True)):
            return
        pending = self.settings.get("pending_update_path")
        if pending and Path(pending).exists():
            return

        manager = UpdateManager()

        def _on_progress(_pct, _status):
            return

        def _on_error(_msg):
            return

        def _on_finished(result):
            available, version_str, notes = result
            if available:
                dlg = UpdateFoundDialog(
                    self, manager, version_str, notes, self.settings
                )
                dlg.exec()

        worker = UpdateWorker(manager, "check")
        worker.progress.connect(_on_progress)
        worker.error.connect(_on_error)
        worker.finished.connect(_on_finished)
        self._auto_update_worker = worker
        worker.start()

    def _init_ui(self):
        container = QWidget()
        self.setCentralWidget(container)
        v = QVBoxLayout(container)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(6)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._on_tab_changed)
        v.addWidget(self.tabs, 1)
        # Status bar lives under the tabs to surface toast messages
        self._init_status_bar(v)
        calc = QWidget()
        settings_tab = QWidget()
        help_tab = QWidget()
        about_tab = QWidget()
        self.tabs.addTab(calc, "CALCULATOR")
        self.tabs.addTab(settings_tab, "SETTINGS")
        self.tabs.addTab(help_tab, "HELP")
        self.tabs.addTab(about_tab, "ABOUT")
        calc_layout = QVBoxLayout(calc)
        # Tighter margins and spacing to reduce vertical gaps on the calculator tab
        calc_layout.setContentsMargins(8, 8, 8, 8)
        calc_layout.setSpacing(2)

        self._add_prison(calc_layout)
        self._add_merits(calc_layout)
        self._add_fee(calc_layout)
        self._add_auec(calc_layout)
        self._add_actions(calc_layout)

        self._build_settings_tab(settings_tab)
        self._build_help_tab_v2(help_tab)
        self._build_about_tab(about_tab)
        self._apply_styles()

    def _compute_dpi_scale(self) -> float:
        """Compute a DPI scale factor based on primary screen DPI."""
        try:
            screen = QGuiApplication.primaryScreen()
            dpi = screen.logicalDotsPerInch() if screen else 96.0
        except Exception:
            dpi = 96.0
        # Clamp to reasonable bounds
        return max(0.85, min(2.0, dpi / 96.0))

    def _init_status_bar(self, parent_layout: QVBoxLayout):
        """Create a bottom status bar for toast-style messages."""
        bar = QWidget(self)
        bar.setObjectName("statusBar")
        bar.setMinimumHeight(16)
        bar.setMaximumHeight(18)
        bar.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        )
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(6, 2, 6, 2)
        bar_layout.setSpacing(4)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        bar_layout.addWidget(self.status_label, 1)

        # Opacity effect for fade in/out
        effect = QGraphicsOpacityEffect(bar)
        effect.setOpacity(0.0)
        bar.setGraphicsEffect(effect)
        self._status_effect = effect

        # Animation + timer
        self._status_anim = QPropertyAnimation(effect, b"opacity", self)
        self._status_anim.setDuration(250)
        self._status_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._fade_out_status)

        # Style the bar to match the app chrome
        bar.setStyleSheet(
            """
            QWidget#statusBar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0c1117, stop:1 #0a0e13);
                border: 1px solid #0078a8;
                border-radius: 4px;
            }
            QLabel#statusLabel {
                color: #e8f5ff;
                font-weight: 600;
                padding-left: 2px;
            }
            """
        )

        parent_layout.addWidget(bar, 0)
        self.status_bar = bar

    def _label(self, text, size):
        lbl = QLabel(text)
        f = QFont()
        f.setPointSize(size)
        f.setBold(True)
        lbl.setFont(f)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    def _card(self, title):
        box = SciFiPanel(title)
        box.setSizePolicy(
            QSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
            )
        )
        lay = QVBoxLayout(box)
        lay.setSpacing(4)
        # Add margin to content for the cut corners of SciFiPanel
        lay.setContentsMargins(8, 8, 8, 8)

        return box, lay

    def _add_prison(self, parent):
        box, lay = self._card("PRISON SENTENCE")
        row = QHBoxLayout()
        row.setSpacing(2)

        self.in_hours = HoloInput("00")
        self.in_minutes = HoloInput("00")
        for field in (self.in_hours, self.in_minutes):
            field.setFixedHeight(32)
        self.in_hours.setAccessibleName("HoursInput")
        self.in_minutes.setAccessibleName("MinutesInput")
        self.in_hours.setToolTip("Enter hours")
        self.in_minutes.setToolTip("Enter minutes")

        policy_exp = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.in_hours.setSizePolicy(policy_exp)
        self.in_minutes.setSizePolicy(policy_exp)

        hcol = QVBoxLayout()
        hcol.setSpacing(1)

        hcol.addWidget(self._label("HOURS", 8))
        hcol.addWidget(self.in_hours)
        mcol = QVBoxLayout()
        mcol.setSpacing(1)

        mcol.addWidget(self._label("MINUTES", 8))
        mcol.addWidget(self.in_minutes)
        row.addLayout(hcol, 1)
        row.addLayout(mcol, 1)
        lay.addLayout(row)
        parent.addWidget(box)
        self.in_hours.textEdited.connect(self._on_time_edited)
        self.in_minutes.textEdited.connect(self._on_time_edited)
        self.in_hours.textChanged.connect(self._calculate)
        self.in_minutes.textChanged.connect(self._calculate)

    def _add_merits(self, parent):
        box, lay = self._card("MERITS")
        row = QHBoxLayout()
        self.in_merits = HoloInput("")
        self.in_merits.setFixedHeight(32)
        self.in_merits.setAccessibleName("MeritsInput")
        self.in_merits.setToolTip("Enter merits or let them auto-calculate from time")
        self.in_merits.setProperty("mode", "auto")

        self.in_merits.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        )

        row.addWidget(self.in_merits, 1)
        lay.addLayout(row)
        self.in_merits.textEdited.connect(self._on_merits_edited)
        self.in_merits.textChanged.connect(self._calculate)
        parent.addWidget(box)

    def _add_fee(self, parent):
        box = ClickableSciFiPanel("MERITS WITH FEE")
        box.setSizePolicy(
            QSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
            )
        )
        box.on_double_click = self._copy_fee_val
        box.setToolTip(
            "Total merits needed when sending to another player,\n"
            "accounting for the in-game transfer fee."
        )
        lay = QVBoxLayout(box)
        lay.setContentsMargins(4, 8, 4, 4)
        lay.setSpacing(2)

        fee_pct = float(self.settings.get("fee_percent", 0.5))
        self.lbl_fee_header = self._label(f"MERITS WITH {fee_pct:.1f}% FEE (☼)", 9)
        lay.addWidget(self.lbl_fee_header)
        self.out_merits_fee = GlowLabel("☼ 0", box, glow_enabled=True)
        self.out_merits_fee.setAccessibleName("MeritsFeeOutput")
        f = QFont()
        f.setPointSize(14)
        f.setBold(True)
        self.out_merits_fee.setFont(f)
        self.out_merits_fee.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.out_merits_fee.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        )

        lay.addWidget(self.out_merits_fee)
        parent.addWidget(box)

    def _add_auec(self, parent):
        box = ClickableSciFiPanel("AUEC VALUE")
        box.setSizePolicy(
            QSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
            )
        )
        box.on_double_click = self._copy_auec_val
        lay = QVBoxLayout(box)
        lay.setContentsMargins(4, 8, 4, 4)
        lay.setSpacing(2)

        lay.addWidget(self._label("aUEC VALUE (¤)", 9))
        self.out_auec = GlowLabel("¤ 0", box, glow_enabled=True)
        self.out_auec.setAccessibleName("AUECOutput")
        f = QFont()
        f.setPointSize(14)
        f.setBold(True)
        self.out_auec.setFont(f)
        self.out_auec.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.out_auec.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        )

        lay.addWidget(self.out_auec)
        parent.addWidget(box)

    def _add_actions(self, parent):
        row = QHBoxLayout()
        row.setSpacing(4)

        self.btn_copy = QuantumButton("COPY REPORT")
        self.btn_save = QuantumButton("SAVE REPORT")
        self.btn_copy.setToolTip("Copy a formatted report to the clipboard")
        self.btn_save.setToolTip("Save a formatted report to a file")

        policy_btn = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_copy.setSizePolicy(policy_btn)
        self.btn_save.setSizePolicy(policy_btn)

        self.btn_copy.clicked.connect(self._copy_report)
        self.btn_save.clicked.connect(self._save_report_dialog)
        row.addWidget(self.btn_copy, 1)
        row.addWidget(self.btn_save, 1)
        parent.addLayout(row)

    def _apply_styles(self):
        """Apply the futuristic Star Citizen-inspired theme."""
        self.setStyleSheet(get_main_stylesheet())

    def _on_tab_changed(self, index):
        """Handle tab change with smooth animation."""
        if self._tab_animation:
            try:
                self._tab_animation.stop()
            except RuntimeError:
                # Animation already cleaned up
                pass
            self._tab_animation = None

        # Clear any lingering effects to prevent visual stacking
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if w:
                w.setGraphicsEffect(None)

        # Get current tab widget
        current_widget = self.tabs.widget(index)
        if current_widget:
            effect = QGraphicsOpacityEffect(current_widget)
            effect.setOpacity(0.0)
            current_widget.setGraphicsEffect(effect)

            anim = QPropertyAnimation(effect, b"opacity", self)
            anim.setDuration(ANIM_DURATION_NORMAL)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)

            def _cleanup():
                current_widget.setGraphicsEffect(None)
                self._tab_animation = None

            anim.finished.connect(_cleanup)
            anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
            self._tab_animation = anim

    def _refresh_styles(self):
        self.in_merits.style().unpolish(self.in_merits)
        self.in_merits.style().polish(self.in_merits)

    def _on_time_edited(self):
        if self._updating:
            return
        h = int("".join(filter(str.isdigit, self.in_hours.text())) or "0")
        m = int("".join(filter(str.isdigit, self.in_minutes.text())) or "0")
        h = max(0, min(99, h))
        m = max(0, min(59, m))
        rate_seconds = max(0.0001, float(self.seconds_per_merit))
        merits = int((h * 3600 + m * 60) / rate_seconds)
        self._updating = True
        self.in_hours.setText(f"{h:02d}")
        self.in_minutes.setText(f"{m:02d}")
        self.in_merits.setText(str(merits))
        self.in_merits.setProperty("mode", "auto")
        self._refresh_styles()
        self._updating = False

    def _on_merits_edited(self):
        if self._updating:
            return
        txt = "".join(filter(str.isdigit, self.in_merits.text()))
        if txt == "":
            txt = "0"
        merits = int(txt)
        total_seconds = int(merits * max(0.0001, float(self.seconds_per_merit)))
        h = max(0, min(99, total_seconds // 3600))
        m = max(0, min(59, (total_seconds % 3600) // 60))
        self._updating = True
        self.in_merits.setText(str(merits))
        self.in_hours.setText(f"{h:02d}")
        self.in_minutes.setText(f"{m:02d}")
        self.in_merits.setProperty("mode", "manual")
        self._refresh_styles()
        self._updating = False

    def _calculate(self):
        if self._updating:
            return
        h = int("".join(filter(str.isdigit, self.in_hours.text())) or "0")
        m = int("".join(filter(str.isdigit, self.in_minutes.text())) or "0")
        h = max(0, min(99, h))
        m = max(0, min(59, m))
        merits_text = "".join(filter(str.isdigit, self.in_merits.text())) or "0"
        merits_val = int(merits_text)
        rate_seconds = max(0.0001, float(self.seconds_per_merit))
        base_seconds = h * 3600 + m * 60
        auto_merits = int(base_seconds / rate_seconds)
        if str(self.in_merits.property("mode")) == "auto":
            merits = auto_merits
            if merits_val and merits_val != auto_merits:
                merits = merits_val
        else:
            merits = merits_val
        auec_rate = float(self.settings.get("rate_merits_auec", 0.618) or 0.0)
        fee_rate = float(self.settings.get("fee_percent", 0.5) or 0.0)
        auec_value = merits * auec_rate
        fee_amount = merits * (fee_rate / 100.0)
        merits_fee = merits + fee_amount
        self.out_merits_fee.setText(f"☼ {merits_fee:,.0f}")
        self.out_auec.setText(f"¤ {auec_value:,.0f}")

    def _copy_fee_val(self):
        if pyperclip is None:
            return
        txt = self.out_merits_fee.text()
        val = txt.replace("☼", "").strip()
        pyperclip.copy(val)
        self.show_toast("Merits Copied")

    def _copy_auec_val(self):
        if pyperclip is None:
            return
        txt = self.out_auec.text()
        val = txt.replace("¤", "").strip()
        pyperclip.copy(val)
        self.show_toast("aUEC Value Copied")

    def _copy_report(self) -> None:
        if pyperclip is None:
            return
        text = (
            f"Prison Sentence: {self.in_hours.text()}h {self.in_minutes.text()}m\n"
            f"Merits Entered: ☼ {self.in_merits.text()}\n"
            f"Merits with Fee: {self.out_merits_fee.text()}\n"
            f"AUEC Value: {self.out_auec.text()}\n"
        )
        pyperclip.copy(text)
        self.show_toast("Report Copied to Clipboard")

    def _save_report_dialog(self):
        default_name = f"SCMC_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", default_name, "Text Files (*.txt)"
        )
        if path:
            self._save_report_to_path(Path(path))

    def _save_report_to_path(self, filepath: Path) -> None:
        text = (
            f"Prison Sentence: {self.in_hours.text()}h {self.in_minutes.text()}m\n"
            f"Merits Entered: ☼ {self.in_merits.text()}\n"
            f"Merits with Fee: {self.out_merits_fee.text()}\n"
            f"AUEC Value: {self.out_auec.text()}\n"
        )
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            self.show_toast(f"Report Saved to {filepath.name}")
        except OSError as e:
            print(f"Error saving report: {e}")

    def _init_tray(self):
        icon = get_app_icon()
        QApplication.instance().setWindowIcon(icon)
        self.setWindowIcon(icon)
        self.tray = QSystemTrayIcon(icon, self)
        menu = QMenu()
        act_show = menu.addAction("Show/Hide")
        act_copy = menu.addAction("Copy Report")
        act_save = menu.addAction("Save Report")
        act_settings = menu.addAction("Settings")
        menu.addSeparator()
        act_exit = menu.addAction("Exit")
        act_show.triggered.connect(self._toggle_visibility)
        act_copy.triggered.connect(self._copy_report)
        act_save.triggered.connect(self._save_report_dialog)
        act_settings.triggered.connect(
            lambda: self._show_from_tray(select_settings=True)
        )
        act_exit.triggered.connect(lambda: QApplication.instance().quit())
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("SCMC")
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _toggle_visibility(self):
        if self.isHidden():
            self._show_from_tray()
        else:
            self._hide_to_tray()

    def _hide_to_tray(self):
        self.hide()

    def _show_from_tray(self, select_settings: bool = False):
        self.show()
        self.raise_()
        self.activateWindow()
        if select_settings:
            try:
                self.tabs.setCurrentIndex(1)
            except Exception:
                pass

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isHidden():
                self._show_from_tray()
            else:
                self._hide_to_tray()

    def closeEvent(self, event) -> None:
        g = self.geometry()
        self.settings.set_window_geometry(g.x(), g.y(), g.width(), g.height())
        event.accept()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _build_settings_tab(self, tab: QWidget):
        """Futuristic settings layout tuned for readability and no overlap."""
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        content.setObjectName("settings_scroll_content")
        main = QVBoxLayout(content)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(12)

        # Helper for common spinbox styling
        def create_spinbox(value, suffix=None):
            sb = QDoubleSpinBox()
            sb.setRange(0.0, 100.0)
            sb.setSingleStep(0.1)
            sb.setDecimals(2)
            sb.setValue(value)
            sb.setStyleSheet(
                "QDoubleSpinBox {"
                "  color: #e8f5ff;"
                "  background: rgba(10, 20, 30, 0.55);"
                "  font-weight: 600;"
                "  selection-background-color: #00c2ff;"
                "  selection-color: #061018;"
                "  padding: 4px;"
                "  border: 1px solid rgba(0, 200, 255, 0.3);"
                "  border-radius: 4px;"
                "}"
                "QDoubleSpinBox:hover { border: 1px solid rgba(0, 200, 255, 0.6); }"
                "QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {"
                "  background: rgba(0, 200, 255, 0.2);"
                "  border: none;"
                "  width: 16px;"
                "}"
                "QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {"
                "  background: rgba(0, 200, 255, 0.4);"
                "}"
            )
            sb.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            sb.setFixedWidth(120)
            sb.setFixedHeight(30)
            if suffix:
                sb.setSuffix(f" {suffix}")
            return sb

        # --- Rates Section ---
        rates_box = SciFiPanel("CALCULATION RATES")
        rates_box.setSizePolicy(
            QSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
            )
        )
        rates_layout = QVBoxLayout(rates_box)
        rates_layout.setContentsMargins(12, 14, 12, 12)
        rates_layout.setSpacing(10)

        self.spin_rate = create_spinbox(
            float(self.settings.get("rate_merits_seconds", 1.0))
        )
        self.spin_rate.setRange(0.1, 10.0)

        self.spin_auec_pct = create_spinbox(
            float(self.settings.get("rate_merits_auec", 0.618)) * 100.0, "%"
        )
        self.spin_fee = create_spinbox(
            float(self.settings.get("fee_percent", 0.5)), "%"
        )

        def add_param_row(label_text, widget, tooltip=None):
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: #a0d0ff; font-weight: bold; font-size: 13px;")
            if tooltip:
                lbl.setToolTip(tooltip)
                widget.setToolTip(tooltip)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(widget)
            rates_layout.addLayout(row)

        add_param_row(
            "Prison Rate (sec/merit)", self.spin_rate, "Seconds reduced per merit"
        )
        add_param_row(
            "aUEC Conversion Rate", self.spin_auec_pct, "Value of merits in aUEC (%)"
        )
        add_param_row(
            "Transfer Fee", self.spin_fee, "In-game transfer fee deduction (%)"
        )

        main.addSpacing(8)
        main.addWidget(rates_box)

        # --- Visual Effects Section ---
        trans_box = SciFiPanel("VISUAL EFFECTS")
        trans_box.setSizePolicy(
            QSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
            )
        )
        trans_layout = QVBoxLayout(trans_box)
        trans_layout.setContentsMargins(12, 14, 12, 12)
        trans_layout.setSpacing(10)

        chk_trans_en = QCheckBox("Enable Transparency")
        chk_trans_en.setChecked(bool(self.settings.get("transparency_enabled", True)))
        trans_layout.addWidget(chk_trans_en)

        trans_row = QHBoxLayout()
        trans_label = QLabel("Window Opacity")
        trans_label.setStyleSheet("color: #a0d0ff; font-weight: bold; font-size: 13px;")

        self.sld_transparency = QSlider(Qt.Orientation.Horizontal)
        self.sld_transparency.setRange(30, 100)
        self.sld_transparency.setValue(
            int(self.settings.get("window_transparency", 0.9) * 100)
        )

        self.lbl_opacity_value = QLabel(f"{self.sld_transparency.value()}%")
        self.lbl_opacity_value.setFixedWidth(40)
        self.lbl_opacity_value.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.lbl_opacity_value.setStyleSheet("color: #00d9ff; font-weight: bold;")

        trans_row.addWidget(trans_label)
        trans_row.addWidget(self.sld_transparency)
        trans_row.addWidget(self.lbl_opacity_value)
        trans_layout.addLayout(trans_row)

        main.addSpacing(8)
        main.addWidget(trans_box)

        # --- Window Behavior Section ---
        behavior_box = SciFiPanel("WINDOW BEHAVIOR")
        behavior_box.setSizePolicy(
            QSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
            )
        )
        behavior_layout = QVBoxLayout(behavior_box)
        behavior_layout.setContentsMargins(12, 14, 12, 12)
        behavior_layout.setSpacing(10)

        self.chk_on_top = QCheckBox("Always on Top")
        self.chk_on_top.setChecked(bool(self.settings.get("always_on_top", False)))
        self.chk_min_tray = QCheckBox("Minimize to System Tray")
        self.chk_min_tray.setChecked(bool(self.settings.get("minimize_to_tray", False)))

        behavior_layout.addWidget(self.chk_on_top)
        behavior_layout.addWidget(self.chk_min_tray)

        main.addSpacing(8)
        main.addWidget(behavior_box)

        # --- Updates Section ---
        updates_box = SciFiPanel("UPDATES & MAINTENANCE")
        updates_box.setSizePolicy(
            QSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
            )
        )
        updates_layout = QVBoxLayout(updates_box)
        updates_layout.setContentsMargins(12, 14, 12, 12)
        updates_layout.setSpacing(10)

        self.chk_auto_update = QCheckBox("Check for updates on startup")
        self.chk_auto_update.setChecked(
            bool(self.settings.get("auto_check_updates", True))
        )
        self.chk_never_update = QCheckBox("Never check for updates")
        self.chk_never_update.setChecked(bool(self.settings.get("never_update", False)))

        updates_layout.addWidget(self.chk_auto_update)
        updates_layout.addWidget(self.chk_never_update)

        main.addSpacing(8)
        main.addWidget(updates_box)
        # Spread available vertical space across sections to avoid large blank areas
        for idx in range(main.count()):
            main.setStretch(idx, 1)

        # --- Signal Connections ---
        self.chk_on_top.toggled.connect(
            lambda v: (
                self.settings.set("always_on_top", bool(v)),
                self._apply_on_top(bool(v)),
            )
        )
        self.chk_min_tray.toggled.connect(
            lambda v: self.settings.set("minimize_to_tray", bool(v))
        )
        self.chk_auto_update.toggled.connect(
            lambda _: self._sync_update_checkboxes("auto")
        )
        self.chk_never_update.toggled.connect(
            lambda v: (
                self.settings.set("never_update", bool(v)),
                self._sync_update_checkboxes("never"),
            )
        )
        chk_trans_en.toggled.connect(
            lambda v: self.settings.set("transparency_enabled", bool(v))
        )
        self.sld_transparency.valueChanged.connect(self._on_opacity_changed)
        self.spin_rate.valueChanged.connect(self._on_rate_changed)
        self.spin_fee.valueChanged.connect(self._on_fee_changed)
        self.spin_auec_pct.valueChanged.connect(
            lambda v: self.settings.set("rate_merits_auec", float(v) / 100.0)
        )
        # Initial sync for update checkboxes
        self._sync_update_checkboxes(None)

        scroll.setWidget(content)
        # Match calculator tab background by letting the pane show through
        scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QWidget#settings_scroll_content {
                background: transparent;
            }
            """
        )
        outer.addWidget(scroll)
        self._settings_scroll = scroll

    def _apply_on_top(self, v: bool):
        f = self.windowFlags()
        if v:
            f |= Qt.WindowType.WindowStaysOnTopHint
        else:
            f &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(f)
        self.show()

    def _apply_transparency(self, value: int):
        op = max(0.0, min(1.0, value / 100.0))
        self.setWindowOpacity(op)
        self.settings.set("window_transparency", op)

    def _on_opacity_changed(self, value: int):
        self._apply_transparency(value)
        if hasattr(self, "lbl_opacity_value") and self.lbl_opacity_value:
            self.lbl_opacity_value.setText(f"{value}%")

    def _apply_opacity(self, v: int):
        self._apply_transparency(v)

    def _sync_update_checkboxes(self, source: str | None = None):
        """Ensure auto-update and never-update are mutually exclusive."""
        if not hasattr(self, "chk_auto_update") or not hasattr(
            self, "chk_never_update"
        ):
            return
        if getattr(self, "_syncing_updates", False):
            return
        self._syncing_updates = True

        auto = self.chk_auto_update.isChecked()
        never = self.chk_never_update.isChecked()

        # Enforce exclusivity based on the source toggle
        if source == "auto" and auto:
            self.chk_never_update.setChecked(False)
            never = False
        if source == "never" and never:
            self.chk_auto_update.setChecked(False)
            auto = False

        # Enable/disable counterparts
        if auto:
            self.chk_never_update.setEnabled(False)
            self.chk_auto_update.setEnabled(True)
        elif never:
            self.chk_auto_update.setEnabled(False)
            self.chk_never_update.setEnabled(True)
        else:
            # both unchecked -> both available
            self.chk_auto_update.setEnabled(True)
            self.chk_never_update.setEnabled(True)

        # Persist settings
        self.settings.set("auto_check_updates", bool(auto))
        self.settings.set("never_update", bool(never))

        self._syncing_updates = False

    def _on_never_update_toggled(self, v: bool):
        self.settings.set("never_update", bool(v))
        self._sync_update_checkboxes("never")

    def changeEvent(self, e):
        if e.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                if bool(self.settings.get("minimize_to_tray", False)):
                    self._hide_to_tray()
        super().changeEvent(e)

    def _on_rate_changed(self, v):
        try:
            new_rate = float(v)
            self.settings.set("rate_merits_seconds", new_rate)
            self.seconds_per_merit = new_rate
            self._calculate()
        except Exception:
            pass

    def _on_fee_changed(self, v):
        try:
            val = float(v)
            self.settings.set("fee_percent", val)
            if hasattr(self, "lbl_fee_header"):
                self.lbl_fee_header.setText(f"MERITS WITH {val:.1f}% FEE (☼)")
                self._calculate()
        except Exception:
            pass

    def _clear_inputs(self):
        self.in_hours.setText("00")
        self.in_minutes.setText("00")
        self.in_merits.setText("0")
        self._calculate()

    def _toggle_on_top_action(self):
        v = not self.chk_on_top.isChecked()
        self.chk_on_top.setChecked(v)

    def _toggle_transparency_action(self):
        en = self.settings.get("transparency_enabled", True)
        self.settings.set("transparency_enabled", not en)
        pass

    def _keybind_definitions(self):
        return {
            "save_report": ("Save Report", self._save_report_dialog),
            "copy_report": ("Copy Report", self._copy_report),
            "quit": ("Exit", lambda: QApplication.instance().quit()),
            "clear_inputs": ("Clear Inputs", self._clear_inputs),
            "minimize": ("Minimize", lambda: self.showMinimized()),
            "toggle_transparency": (
                "Toggle Transparency",
                self._toggle_transparency_action,
            ),
            "toggle_always_on_top": (
                "Toggle Always On Top",
                self._toggle_on_top_action,
            ),
            "toggle_visibility": ("Toggle Visibility", self._toggle_visibility),
            "open_settings": ("Open Settings", lambda: self.tabs.setCurrentIndex(1)),
        }

    def _register_shortcuts(self):
        # clear old shortcuts
        for sc in self._shortcuts:
            sc.setEnabled(False)
            sc.deleteLater()
        self._shortcuts.clear()

        shortcuts = self.settings.get("shortcuts", {})
        defs = self._keybind_definitions()

        for key_id, (name, callback) in defs.items():
            seq_str = shortcuts.get(key_id, "")
            if seq_str:
                sc = QShortcut(QKeySequence(seq_str), self)
                sc.setContext(Qt.ShortcutContext.WindowShortcut)
                sc.activated.connect(callback)
                self._shortcuts.append(sc)

    def _populate_keybinds(self) -> None:
        """Populate the shortcuts list with clean, organized rows."""
        pass

    def _edit_keybind(self, key_id: str):
        defs = self._keybind_definitions()
        name = defs.get(key_id, (key_id, None))[0]

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Bind: {name}")
        dlg.setStyleSheet(get_dialog_stylesheet())
        lay = QVBoxLayout(dlg)
        lay.setSpacing(16)
        lay.setContentsMargins(20, 20, 20, 20)

        # Add label
        lbl = QLabel(f"Press keys for: {name}")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lbl)

        if HAVE_KEYSEQ:
            ks_edit = QKeySequenceEdit(dlg)
            lay.addWidget(ks_edit)
        else:
            text_edit = QLineEdit(dlg)
            lay.addWidget(text_edit)
        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        lay.addWidget(bb)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if HAVE_KEYSEQ:
                seq = ks_edit.keySequence().toString()
            else:
                seq = text_edit.text()
            sc = self.settings.get("shortcuts", {}) or {}
            sc[key_id] = seq
            self.settings.set("shortcuts", sc)
            # shortcuts setting observer will trigger _register_shortcuts and table update

    def _reset_keybind(self, key_id: str):
        from .settings import DEFAULT_SETTINGS

        sc = self.settings.get("shortcuts", {}) or {}
        default_sc = DEFAULT_SETTINGS.get("shortcuts", {})
        if isinstance(default_sc, dict) and key_id in default_sc:
            sc[key_id] = default_sc[key_id]
            self.settings.set("shortcuts", sc)

    def _build_about_tab(self, tab: QWidget):
        v = QVBoxLayout(tab)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(16)

        about_box = SciFiPanel("ABOUT")
        about_box.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )
        about_lay = QVBoxLayout(about_box)
        about_lay.setContentsMargins(12, 16, 12, 12)
        about_lay.setSpacing(12)

        header = self._label("SCMC", 12)
        about_lay.addWidget(header)

        body = QLabel(
            "SCMC (Star Citizen Merit Calculator). Calculates merits, fees and aUEC."
        )
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)
        about_lay.addWidget(body)

        dev_body = QLabel("Developer: PINKgeekPDX")
        dev_body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev_body.setWordWrap(True)
        dev_body.setStyleSheet("color: #a0d0ff;")
        about_lay.addWidget(dev_body)

        img = QLabel()
        img.setFixedSize(150, 150)
        icon = get_app_icon()
        pm = icon.pixmap(150, 150)
        img.setPixmap(pm)
        img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_lay.addWidget(img, 0, Qt.AlignmentFlag.AlignCenter)

        # Button row/column layout with non-bold text
        btn_repo = QuantumButton("GitHub", tab)
        btn_issues = QuantumButton("Issues", tab)
        btn_updates = QuantumButton("Check for Updates", tab)
        btn_updates.setEnabled(False)
        btn_license = QuantumButton("Open Source License", tab)

        # De-emphasize bold for these buttons
        for btn in (btn_repo, btn_issues, btn_updates, btn_license):
            f = btn.font()
            f.setBold(False)
            btn.setFont(f)

        # Space below the image before buttons
        about_lay.addSpacing(6)

        # Group button rows and center them
        buttons_col = QVBoxLayout()
        buttons_col.setSpacing(8)

        # First row: GitHub, Issues
        row_top = QHBoxLayout()
        row_top.setSpacing(10)
        row_top.addStretch()
        row_top.addWidget(btn_repo)
        row_top.addWidget(btn_issues)
        row_top.addStretch()
        buttons_col.addLayout(row_top)

        # Second row: Check for updates
        row_mid = QHBoxLayout()
        row_mid.setSpacing(10)
        row_mid.addStretch()
        row_mid.addWidget(btn_updates)
        row_mid.addStretch()
        buttons_col.addLayout(row_mid)

        # Third row: License
        row_bottom = QHBoxLayout()
        row_bottom.setSpacing(10)
        row_bottom.addStretch()
        row_bottom.addWidget(btn_license)
        row_bottom.addStretch()
        buttons_col.addLayout(row_bottom)

        about_lay.addLayout(buttons_col)

        v.addWidget(about_box, 1)

        repo_url = "https://github.com/PINKgeekPDX/SCMeritsCalc"
        issues_url = "https://github.com/PINKgeekPDX/SCMeritsCalc/issues"
        btn_repo.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(repo_url)))
        btn_issues.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(issues_url)))

        btn_updates.clicked.connect(self._check_for_updates)
        btn_updates.setEnabled(True)

        def _show_license():
            dlg = QDialog(self)
            dlg.setWindowTitle("MIT License")
            dlg.setStyleSheet(get_dialog_stylesheet())
            lay = QVBoxLayout(dlg)
            lay.setSpacing(16)
            lay.setContentsMargins(20, 20, 20, 20)
            txt = QLabel(
                (
                    "Permission is hereby granted, free of charge, "
                    "to any person obtaining "
                    "a copy of this software and associated documentation files "
                    '(the "Software"), '
                    "to deal in the Software without restriction, including without "
                    "limitation "
                    "the rights to use, copy, modify, merge, publish, distribute, "
                    "sublicense, "
                    "and/or sell copies of the Software, and to permit persons to "
                    "whom the Software is furnished to do so, subject to the "
                    "following conditions."
                )
            )
            txt.setWordWrap(True)
            lay.addWidget(txt)
            bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            bb.rejected.connect(dlg.reject)
            bb.accepted.connect(dlg.accept)
            lay.addWidget(bb)
            dlg.exec()

        btn_license.clicked.connect(_show_license)

    def _build_help_tab(self, tab: QWidget):
        v = QVBoxLayout(tab)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Create scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(4, 4, 4, 4)
        scroll_layout.setSpacing(4)

        # Calculator Section
        # Calculator Section
        calc_box = SciFiPanel("CALCULATOR")
        calc_lay = QVBoxLayout(calc_box)
        calc_lay.setContentsMargins(12, 16, 12, 12)
        calc_lay.setSpacing(8)

        calc_text = QLabel(
            "<b>Prison Sentence:</b><br>"
            "Enter hours and minutes of your prison sentence. The calculator will "
            "automatically convert this to merits based on the rate configured in Settings.<br><br>"
            "<b>Merits:</b><br>"
            "Merits are calculated automatically from your prison sentence time. "
            "You can also manually enter merits if needed. When manually entered, "
            "the time will update accordingly.<br><br>"
            "<b>Merits with Fee:</b><br>"
            "This shows the total merits needed when sending to another player, "
            "accounting for the in-game transfer fee. Double-click this value to copy it.<br><br>"
            "<b>aUEC Value:</b><br>"
            "Displays the aUEC (in-game currency) equivalent of your merits. "
            "Double-click this value to copy it."
        )
        calc_text.setWordWrap(True)
        calc_text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        calc_lay.addWidget(calc_text)
        scroll_layout.addWidget(calc_box)

        # Actions Section
        # Actions Section
        actions_box = SciFiPanel("ACTIONS")
        actions_lay = QVBoxLayout(actions_box)
        actions_lay.setContentsMargins(12, 16, 12, 12)
        actions_lay.setSpacing(4)

        actions_text = QLabel(
            "<b>Copy Report:</b><br>"
            "Copies a formatted report containing all calculation results to "
            "your clipboard. The report includes prison sentence time, merits "
            "entered, merits with fee, and aUEC value.<br><br>"
            "<b>Save Report:</b><br>"
            "Saves the formatted report to a text file. You can choose the "
            "save location in the file dialog that appears."
        )
        actions_text.setWordWrap(True)
        actions_text.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        actions_lay.addWidget(actions_text)
        scroll_layout.addWidget(actions_box)

        # Settings Section
        # Settings Section
        settings_box = SciFiPanel("SETTINGS")
        settings_lay = QVBoxLayout(settings_box)
        settings_lay.setContentsMargins(12, 16, 12, 12)
        settings_lay.setSpacing(8)

        settings_text = QLabel(
            "<b>Behavior:</b><br>"
            "• <b>Always On Top:</b> Keeps the window above all other windows."
            "<br>"
            "• <b>Minimize to Tray:</b> Minimizing the window sends it to "
            "the system tray instead of the taskbar.<br><br>"
            "<b>Transparency:</b><br>"
            "• <b>Enable Transparency:</b> Toggles window transparency on/off.<br>"
            "• <b>Transparency Slider:</b> Adjusts window opacity from 30% to 100%.<br><br>"
            "<b>Rates:</b><br>"
            "• <b>Prison Rate:</b> Seconds per merit (default: 1.0). Used to "
            "convert time to merits.<br>"
            "• <b>aUEC Conversion:</b> Percentage rate for converting merits "
            "to aUEC (default: 61.8%).<br>"
            "• <b>Fee:</b> Transfer fee percentage (default: 0.5%). Used when "
            "calculating total merits for player-to-player transfers."
        )
        settings_text.setWordWrap(True)
        settings_text.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        settings_lay.addWidget(settings_text)
        scroll_layout.addWidget(settings_box)

        # System Tray Section
        tray_box = SciFiPanel("SYSTEM TRAY")
        tray_lay = QVBoxLayout(tray_box)
        tray_lay.setContentsMargins(12, 16, 12, 12)
        tray_lay.setSpacing(8)

        tray_text = QLabel(
            "The application runs in the system tray when minimized (if enabled). "
            "Right-click the tray icon to access:<br>"
            "• Show/Hide: Toggle window visibility<br>"
            "• Copy Report: Copy current calculation results<br>"
            "• Save Report: Save current calculation results<br>"
            "• Settings: Open the Settings tab<br>"
            "• Exit: Close the application<br><br>"
            "Double-click the tray icon to quickly show/hide the window."
        )
        tray_text.setWordWrap(True)
        tray_text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        tray_lay.addWidget(tray_text)
        scroll_layout.addWidget(tray_box)

        # Updates Section
        updates_box = SciFiPanel("UPDATES")
        updates_lay = QVBoxLayout(updates_box)
        updates_lay.setContentsMargins(12, 16, 12, 12)
        updates_lay.setSpacing(8)

        updates_text = QLabel(
            "The application can automatically check for updates.<br><br>"
            "<b>Checking for Updates:</b><br>"
            "Click 'Check for Updates' in the About tab."
            "<br><br>"
            "<b>Download Options:</b><br>"
            "• <b>Download:</b> Downloads the installer for later installation. "
            "You'll be prompted to install it the next time you start the app.<br>"
            "• <b>Download and Update:</b> Downloads and immediately launches "
            "the installer, then closes the current app session.<br><br>"
            "Updates are checked against the latest release. "
            "The installer is automatically downloaded and can be "
            "run to update the application."
        )
        updates_text.setWordWrap(True)
        updates_text.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        updates_lay.addWidget(updates_text)
        scroll_layout.addWidget(updates_box)

        # Tips Section
        tips_box = SciFiPanel("TIPS & TRICKS")
        tips_lay = QVBoxLayout(tips_box)
        tips_lay.setContentsMargins(4, 10, 4, 4)
        tips_lay.setSpacing(4)

        tips_text = QLabel(
            "• Double-click any output value (Merits with Fee or aUEC Value) "
            "to quickly copy it.<br>"
            "• Adjust transparency to make the window less intrusive while "
            "gaming.<br>"
            "• Enable 'Always On Top' to keep the calculator visible while "
            "using other applications.<br>"
        )
        tips_text.setWordWrap(True)
        tips_text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        tips_lay.addWidget(tips_text)
        scroll_layout.addWidget(tips_box)

        # Add stretch at bottom
        scroll_layout.addStretch()

        # Set scroll content and add to layout
        scroll_area.setWidget(scroll_content)
        v.addWidget(scroll_area)

        # Style the help content - match app theme
        # Don't override global styles, just ensure proper background
        scroll_content.setObjectName("scroll_content")
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                background-color: #101216;
                border: none;
            }
            QWidget#scroll_content {
                background-color: #101216;
            }
            """
        )

    def _build_help_tab_v2(self, tab: QWidget):
        v = QVBoxLayout(tab)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # Create scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_content = QWidget()
        scroll_content.setObjectName("scroll_content")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(16, 16, 16, 16)
        scroll_layout.setSpacing(16)

        # Calculator Section
        calc_box = SciFiPanel("CALCULATOR")
        calc_box.setSizePolicy(
            QSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
            )
        )
        calc_lay = QVBoxLayout(calc_box)
        calc_lay.setContentsMargins(12, 16, 12, 12)
        calc_lay.setSpacing(8)

        calc_text = QLabel(
            "<b>Prison Sentence:</b> Enter your time to auto-calculate merits.<br>"
            "<b>Merits:</b> Manually enter merits to reverse-calculate time.<br>"
            "<b>aUEC Value:</b> Shows the currency value of entered merits."
        )
        calc_text.setWordWrap(True)
        calc_text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        calc_lay.addWidget(calc_text)
        scroll_layout.addWidget(calc_box)

        # Actions Section
        actions_box = SciFiPanel("ACTIONS")
        actions_box.setSizePolicy(
            QSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
            )
        )
        actions_lay = QVBoxLayout(actions_box)
        actions_lay.setContentsMargins(12, 16, 12, 12)
        actions_lay.setSpacing(8)

        actions_text = QLabel(
            "<b>Double-Click:</b> Copy any value ending in (☼) or (¤).<br>"
            "<b>Copy Report:</b> Copies a full formatted report to clipboard.<br>"
            "<b>Save Report:</b> Saves the report to a text file."
        )
        actions_text.setWordWrap(True)
        actions_text.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        actions_lay.addWidget(actions_text)
        scroll_layout.addWidget(actions_box)

        # Spread available space across panels to avoid large empty areas
        for idx in range(scroll_layout.count()):
            scroll_layout.setStretch(idx, 1)

        scroll_area.setWidget(scroll_content)
        v.addWidget(scroll_area)

        # Style the scroll area to match app theme
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                background-color: #101216;
                border: none;
            }
            QWidget#scroll_content {
                background-color: #101216;
            }
            """
        )


def create_qt_app(settings, calculator):
    class _Runner:
        def __init__(self, s, c):
            self.s = s
            self.c = c

        def run(self):
            app = QApplication.instance() or QApplication([])
            app.setWindowIcon(get_app_icon())
            w = QtMeritCalcApp(self.s, self.c)
            w.show()
            app.exec()

    return _Runner(settings, calculator)
