"""MeritsCalc Qt UI module."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QEvent, QRect, Qt, QUrl, QThread, pyqtSignal
from PyQt6.QtGui import (
    QDesktopServices,
    QFont,
    QIcon,
    QPainter,
    QPixmap,
    QKeySequence,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSystemTrayIcon,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QTextEdit,
)

from meritscalc.updater import UpdateManager
from meritscalc.settings import _app_data_dir

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


class ClickableGroupBox(QGroupBox):
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
        self.setFixedSize(500, 350)
        self.manager = UpdateManager()
        self.worker = None
        self.installer_path = None
        self._init_ui()
        self._start_check()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Status Header
        self.lbl_status_header = QLabel("Checking for Updates...")
        f = QFont()
        f.setPointSize(14)
        f.setBold(True)
        self.lbl_status_header.setFont(f)
        self.lbl_status_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status_header)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate initially
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # Status Text
        self.lbl_status = QLabel("Connecting to release server...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_status)

        # Error Box (Hidden)
        self.txt_error = QTextEdit()
        self.txt_error.setReadOnly(True)
        self.txt_error.setVisible(False)
        self.txt_error.setStyleSheet(
            "color: #ff5555; background: #1a1a1a; border: 1px solid #ff5555;"
        )
        layout.addWidget(self.txt_error)

        # Buttons
        self.btn_box = QHBoxLayout()
        self.btn_download = QPushButton("Download")
        self.btn_install = QPushButton("Download and Update")
        self.btn_close = QPushButton("Cancel")

        self.btn_download.setVisible(False)
        self.btn_install.setVisible(False)

        self.btn_download.clicked.connect(
            lambda: self._start_download(install_now=False)
        )
        self.btn_install.clicked.connect(lambda: self._start_download(install_now=True))
        self.btn_close.clicked.connect(self.close)

        self.btn_box.addStretch()
        self.btn_box.addWidget(self.btn_download)
        self.btn_box.addWidget(self.btn_install)
        self.btn_box.addWidget(self.btn_close)
        self.btn_box.addStretch()
        layout.addLayout(self.btn_box)

        # Style
        self.setStyleSheet(
            """
            QDialog { background-color: #101216; color: #e6e9ef; }
            QLabel { color: #e6e9ef; }
            QProgressBar {
                border: 1px solid #00d9ff;
                border-radius: 4px;
                text-align: center;
                background: #1f2228;
            }
            QProgressBar::chunk { background-color: #00d9ff; }
            QPushButton {
                background: #23262c;
                color: #e6f7ff;
                border: 1px solid #00d9ff;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background: #00a2cc; }
            QPushButton:pressed { background: #00d9ff; }
        """
        )

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
        if self.worker.mode == "download":
            self.progress_bar.setValue(int(pct))

    def _on_check_finished(self, result):
        available, version_str, notes = result
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)

        if available:
            self.lbl_status_header.setText(f"Update Available: v{version_str}")
            self.lbl_status.setText("A new version is available!")
            self.btn_download.setVisible(True)
            self.btn_install.setVisible(True)
            self.btn_close.setText("Close")
        else:
            from meritscalc.version import __version__

            self.lbl_status_header.setText("SC Merits Calc is up to date")
            self.lbl_status_header.setStyleSheet("color: #00ff00;")
            self.lbl_status.setStyleSheet("color: #00ff00;")
            self.lbl_status.setText(
                f"Current version: {__version__} | Newest Version: {version_str}"
            )
            self.btn_close.setText("Close")

    def _on_download_finished(self, path, install_now):
        self.installer_path = path
        self.lbl_status.setText("Download Complete!")

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
                "Update downloaded. You will be prompted next time you run the app."
            )
            self.btn_close.setText("Close")

    def _on_error(self, msg):
        self.lbl_status_header.setText("Error Occurred")
        self.lbl_status.setText("An error occurred during the operation.")
        self.progress_bar.setVisible(False)
        self.txt_error.setVisible(True)
        self.txt_error.setText(msg)
        self.btn_close.setText("Close")
        self.btn_download.setVisible(False)
        self.btn_install.setVisible(False)


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
        self.setWindowTitle("SC MERIT CALC")
        # Apply saved window geometry
        g = self.settings.get_window_geometry()
        self.setGeometry(QRect(g["x"], g["y"], g["width"], g["height"]))
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
        # Apply initial auto scaling if enabled
        if bool(self.settings.get("auto_scale_ui", True)):
            self._apply_auto_scale()

        # Apply initial transparency
        if bool(self.settings.get("transparency_enabled", True)):
            self.setWindowOpacity(float(self.settings.get("window_transparency", 0.9)))

        # React to settings changes instantly
        def _on_setting_changed(key, value):
            if key == "ui_scale":
                if hasattr(self, "spin_font") and self.spin_font:
                    self._apply_font_size(self.spin_font.value())
            elif key == "font_size":
                if hasattr(self, "spin_font") and self.spin_font:
                    self._apply_font_size(float(value))
            elif key == "window_transparency":
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
            elif key == "auto_scale_ui" and bool(value):
                self._apply_auto_scale()
            elif key == "shortcuts":
                self._register_shortcuts()
            elif key == "fee_percent":
                try:
                    val = float(value)
                    if hasattr(self, "lbl_fee_header"):
                        self.lbl_fee_header.setText(f"MERITS WITH {val:.1f}% FEE (☼)")
                        self._calculate()
                except Exception:
                    pass

        self.settings.add_observer(_on_setting_changed)
        self._register_shortcuts()

        # Check for pending updates
        self._check_pending_update()

    def _check_pending_update(self):
        pending = self.settings.get("pending_update_path")
        if pending and Path(pending).exists():
            dlg = QDialog(self)
            dlg.setWindowTitle("Update Ready")
            dlg.setFixedSize(400, 200)

            layout = QVBoxLayout(dlg)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)

            lbl = QLabel(
                "An update has been downloaded.\nWould you like to install it now?"
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            f = QFont()
            f.setPointSize(12)
            lbl.setFont(f)
            layout.addWidget(lbl)

            btns = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No
            )
            layout.addWidget(btns)

            btns.accepted.connect(dlg.accept)
            btns.rejected.connect(dlg.reject)

            # Style to match
            dlg.setStyleSheet(
                """
                QDialog { background-color: #101216; color: #e6e9ef; }
                QLabel { color: #e6e9ef; }
                QPushButton {
                    background: #23262c;
                    color: #e6f7ff;
                    border: 1px solid #00d9ff;
                    border-radius: 6px;
                    padding: 8px 16px;
                }
                QPushButton:hover { background: #00a2cc; }
            """
            )

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

    def _init_ui(self):
        container = QWidget()
        self.setCentralWidget(container)
        v = QVBoxLayout(container)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(12)
        self.tabs = QTabWidget()
        v.addWidget(self.tabs)
        calc = QWidget()
        settings_tab = QWidget()
        help_tab = QWidget()
        about_tab = QWidget()
        self.tabs.addTab(calc, "CALCULATOR")
        self.tabs.addTab(settings_tab, "SETTINGS")
        self.tabs.addTab(help_tab, "HELP")
        self.tabs.addTab(about_tab, "ABOUT")
        calc_layout = QVBoxLayout(calc)
        calc_layout.setContentsMargins(8, 8, 8, 8)
        calc_layout.setSpacing(12)
        self._add_prison(calc_layout)
        self._add_merits(calc_layout)
        self._add_fee(calc_layout)
        self._add_auec(calc_layout)
        self._add_actions(calc_layout)
        self._build_settings_tab(settings_tab)
        self._build_help_tab(help_tab)
        self._build_about_tab(about_tab)
        self._apply_styles()

    def _label(self, text, size):
        lbl = QLabel(text)
        f = QFont()
        f.setPointSize(size)
        f.setBold(True)
        lbl.setFont(f)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    def _card(self, title):
        box = QGroupBox(title)
        lay = QVBoxLayout(box)
        lay.setSpacing(8)
        return box, lay

    def _add_prison(self, parent):
        box, lay = self._card("PRISON SENTENCE")
        row = QHBoxLayout()
        row.setSpacing(12)
        self.in_hours = QLineEdit("00")
        self.in_minutes = QLineEdit("00")
        self.in_hours.setAccessibleName("HoursInput")
        self.in_minutes.setAccessibleName("MinutesInput")
        self.in_hours.setToolTip("Enter hours")
        self.in_minutes.setToolTip("Enter minutes")
        hcol = QVBoxLayout()
        hcol.addWidget(self._label("HOURS", 10))
        hcol.addWidget(self.in_hours)
        mcol = QVBoxLayout()
        mcol.addWidget(self._label("MINUTES", 10))
        mcol.addWidget(self.in_minutes)
        row.addLayout(hcol)
        row.addLayout(mcol)
        lay.addLayout(row)
        parent.addWidget(box)
        self.in_hours.textEdited.connect(self._on_time_edited)
        self.in_minutes.textEdited.connect(self._on_time_edited)
        self.in_hours.textChanged.connect(self._calculate)
        self.in_minutes.textChanged.connect(self._calculate)

    def _add_merits(self, parent):
        box, lay = self._card("MERITS")
        row = QHBoxLayout()
        self.in_merits = QLineEdit("")
        self.in_merits.setAccessibleName("MeritsInput")
        self.in_merits.setToolTip("Enter merits or let them auto-calculate from time")
        self.in_merits.setProperty("mode", "auto")
        row.addWidget(self.in_merits)
        lay.addLayout(row)
        self.in_merits.textEdited.connect(self._on_merits_edited)
        self.in_merits.textChanged.connect(self._calculate)
        parent.addWidget(box)

    def _add_fee(self, parent):
        box = ClickableGroupBox()
        box.on_double_click = self._copy_fee_val
        box.setToolTip(
            "Total merits needed when sending to another player,\n"
            "accounting for the in-game transfer fee."
        )
        lay = QVBoxLayout(box)
        fee_pct = float(self.settings.get("fee_percent", 0.5))
        self.lbl_fee_header = self._label(f"MERITS WITH {fee_pct:.1f}% FEE (☼)", 12)
        lay.addWidget(self.lbl_fee_header)
        self.out_merits_fee = self._label("☼ 0", 36)
        self.out_merits_fee.setAccessibleName("MeritsFeeOutput")
        lay.addWidget(self.out_merits_fee)
        parent.addWidget(box)

    def _add_auec(self, parent):
        box = ClickableGroupBox()
        box.on_double_click = self._copy_auec_val
        lay = QVBoxLayout(box)
        lay.addWidget(self._label("aUEC VALUE (¤)", 14))
        self.out_auec = self._label("¤ 0", 36)
        self.out_auec.setAccessibleName("AUECOutput")
        lay.addWidget(self.out_auec)
        parent.addWidget(box)

    def _add_actions(self, parent):
        row = QHBoxLayout()
        row.setSpacing(12)
        self.btn_copy = QPushButton("COPY REPORT")
        self.btn_save = QPushButton("SAVE REPORT")
        self.btn_copy.setToolTip("Copy a formatted report to the clipboard")
        self.btn_save.setToolTip("Save a formatted report to a file")
        self.btn_copy.clicked.connect(self._copy_report)
        self.btn_save.clicked.connect(self._save_report_dialog)
        row.addWidget(self.btn_copy)
        row.addWidget(self.btn_save)
        parent.addLayout(row)

    def _apply_styles(self):
        css = (
            "QMainWindow { background-color: #101216; }\n"
            "QTabWidget::pane { border: 1px solid #00d9ff; }\n"
            "QTabBar::tab { background: #0f1116; color: #8ea0b2; padding: 8px 24px;\n"
            "  border: 1px solid #00d9ff; border-bottom: none; margin: 2px; }\n"
            "QTabBar::tab:selected { background: #00d9ff; color: #0b0f14;\n"
            "  font-weight: bold; }\n"
            "QGroupBox { color: #8ea0b2; border: 1px solid #00d9ff; border-radius: 8px;\n"
            "  margin-top: 8px; }\n"
            "QGroupBox:title { subcontrol-origin: margin; subcontrol-position: top left;\n"
            "  padding: 0 6px; }\n"
            "QLineEdit { background: #1f2228; color: #e6e9ef; border: 1px solid #00d9ff;\n"
            "  border-radius: 6px; padding: 8px 12px; font-size: 24px; }\n"
            "QLineEdit[mode=auto] { border: 1px solid #00d9ff; }\n"
            "QLineEdit[mode=manual] { border: 1px solid #ffbb66; }\n"
            "QLabel { color: #e6e9ef; }\n"
            "QPushButton { background: #23262c; color: #e6f7ff; border: 1px solid #00d9ff;\n"
            "  border-radius: 8px; padding: 10px 18px; font-weight: bold; }\n"
            "QPushButton:hover { background: #00a2cc; border-color: #00a2cc; }\n"
            "QPushButton:pressed { background: #00d9ff; border-color: #00d9ff; }\n"
        )
        self.setStyleSheet(css)

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
        merits = int(h * 3600 + m * 60)
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
        total_seconds = int(merits * self.seconds_per_merit)
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
        if str(self.in_merits.property("mode")) == "auto":
            merits = int(h * 3600 + m * 60)
        else:
            merits = merits_val
        auec_rate = self.settings.get("rate_merits_auec", 0.618)
        fee_rate = self.settings.get("rate_fee_percent", 0.5)
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

    def _copy_auec_val(self):
        if pyperclip is None:
            return
        txt = self.out_auec.text()
        val = txt.replace("¤", "").strip()
        pyperclip.copy(val)

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

    def _save_report_dialog(self):
        default_name = (
            f"MeritsCalc_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
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
        self.tray.setToolTip("SC MERIT CALC")
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
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        dsp_box = QGroupBox("DISPLAY")
        dsp_lay = QGridLayout(dsp_box)
        self.sld_dpi = QSlider(Qt.Orientation.Horizontal)
        self.sld_dpi.setRange(50, 200)
        self.sld_dpi.setValue(int(float(self.settings.get("ui_scale", 100))))
        self.chk_auto_scale = QCheckBox("Auto scaling")
        self.chk_auto_scale.setChecked(bool(self.settings.get("auto_scale_ui", True)))
        self.spin_font = QDoubleSpinBox()
        self.spin_font.setRange(8, 48)
        self.spin_font.setValue(float(self.settings.get("font_size", 14)))
        spin_bias = QDoubleSpinBox()
        spin_bias.setRange(0.5, 1.5)
        spin_bias.setSingleStep(0.01)
        spin_bias.setValue(float(self.settings.get("auto_scale_bias", 0.80)))
        dsp_lay.addWidget(QLabel("DPI scale (%)"), 0, 0)
        dsp_lay.addWidget(self.sld_dpi, 0, 1)
        dsp_lay.addWidget(self.chk_auto_scale, 1, 0)
        dsp_lay.addWidget(QLabel("Base font size"), 2, 0)
        dsp_lay.addWidget(self.spin_font, 2, 1)
        dsp_lay.addWidget(QLabel("Auto scale bias"), 3, 0)
        dsp_lay.addWidget(spin_bias, 3, 1)
        layout.addWidget(dsp_box)
        beh_box = QGroupBox("BEHAVIOR")
        beh_lay = QGridLayout(beh_box)
        self.chk_on_top = QCheckBox("Always on top")
        self.chk_on_top.setChecked(bool(self.settings.get("always_on_top", False)))
        self.chk_min_tray = QCheckBox("Minimize to tray")
        self.chk_min_tray.setChecked(bool(self.settings.get("minimize_to_tray", False)))
        beh_lay.addWidget(self.chk_on_top, 0, 0)
        beh_lay.addWidget(self.chk_min_tray, 0, 1)
        layout.addWidget(beh_box)
        tran_box = QGroupBox("TRANSPARENCY")
        tran_lay = QGridLayout(tran_box)
        chk_trans_en = QCheckBox("Enable transparency")
        chk_trans_en.setChecked(bool(self.settings.get("transparency_enabled", True)))
        self.sld_transparency = QSlider(Qt.Orientation.Horizontal)
        self.sld_transparency.setRange(30, 100)  # Fixed range 0.3 to 1.0
        self.sld_transparency.setValue(
            int(self.settings.get("window_transparency", 0.9) * 100)
        )
        tran_lay.addWidget(chk_trans_en, 0, 0)
        tran_lay.addWidget(self.sld_transparency, 0, 1)
        layout.addWidget(tran_box)
        rate_box = QGroupBox("RATES")
        rate_lay = QGridLayout(rate_box)
        self.spin_rate = QDoubleSpinBox()
        self.spin_rate.setRange(0.1, 10.0)
        self.spin_rate.setValue(float(self.settings.get("rate_merits_seconds", 1.0)))
        self.spin_fee = QDoubleSpinBox()
        self.spin_fee.setRange(0.0, 100.0)
        self.spin_fee.setValue(float(self.settings.get("fee_percent", 0.5)))
        spin_auec_pct = QDoubleSpinBox()
        spin_auec_pct.setRange(0.0, 100.0)
        spin_auec_pct.setSingleStep(0.1)
        spin_auec_pct.setValue(
            float(self.settings.get("rate_merits_auec", 0.618)) * 100.0
        )
        rate_lay.addWidget(QLabel("Prison rate (sec/merit)"), 0, 0)
        rate_lay.addWidget(self.spin_rate, 0, 1)
        rate_lay.addWidget(QLabel("aUEC conversion (%)"), 1, 0)
        rate_lay.addWidget(spin_auec_pct, 1, 1)
        rate_lay.addWidget(QLabel("Fee (%)"), 2, 0)
        rate_lay.addWidget(self.spin_fee, 2, 1)
        layout.addWidget(rate_box)
        self.sld_dpi.sliderReleased.connect(
            lambda: self._apply_dpi_scale(self.sld_dpi.value())
        )
        self.chk_auto_scale.toggled.connect(self._on_auto_toggled)
        self.spin_font.valueChanged.connect(lambda v: self._apply_font_size(float(v)))

        # Initialize widget state
        is_auto = self.chk_auto_scale.isChecked()
        self.sld_dpi.setEnabled(not is_auto)
        self.spin_font.setEnabled(not is_auto)
        self.chk_on_top.toggled.connect(
            lambda v: (
                self.settings.set("always_on_top", bool(v)),
                self._apply_on_top(bool(v)),
            )
        )
        self.chk_min_tray.toggled.connect(
            lambda v: self.settings.set("minimize_to_tray", bool(v))
        )
        chk_trans_en.toggled.connect(
            lambda v: self.settings.set("transparency_enabled", bool(v))
        )
        self.sld_transparency.valueChanged.connect(
            lambda v: self._apply_transparency(int(v))
        )
        spin_bias.valueChanged.connect(
            lambda v: self.settings.set("auto_scale_bias", float(v))
        )
        self.spin_rate.valueChanged.connect(self._on_rate_changed)
        self.spin_fee.valueChanged.connect(self._on_fee_changed)
        spin_auec_pct.valueChanged.connect(
            lambda v: self.settings.set("rate_merits_auec", float(v) / 100.0)
        )
        self.tbl_keys = QTableWidget()
        self.tbl_keys.setColumnCount(3)
        self.tbl_keys.setHorizontalHeaderLabels(["Action", "Shortcut", ""])
        hdr = self.tbl_keys.horizontalHeader()
        if hdr is not None:
            hdr.setStretchLastSection(True)
        layout.addWidget(self.tbl_keys)
        self._populate_keybinds()

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

    def _apply_opacity(self, v: int):
        self._apply_transparency(v)

    def _apply_dpi_scale(self, val: int):
        self.settings.set("ui_scale", float(val))
        self._apply_font_size(self.spin_font.value())

    def _apply_auto_scale(self):
        bias = float(self.settings.get("auto_scale_bias", 0.80))
        app = QApplication.instance() or QApplication([])
        screen = app.primaryScreen()
        dpi = 96.0
        if screen is not None:
            try:
                dpi = float(screen.logicalDotsPerInch())
            except Exception:
                dpi = 96.0
        # Reduce the impact of DPI scaling to keep UI compact
        # Using a dampening factor of 0.75 on the DPI ratio
        dpi_ratio = dpi / 96.0
        dampened_ratio = 1.0 + (dpi_ratio - 1.0) * 0.75
        scale = max(0.6, min(2.0, dampened_ratio * bias))
        val = int(scale * 100)
        if self.sld_dpi is not None:
            self.sld_dpi.blockSignals(True)
            self.sld_dpi.setValue(val)
            self.sld_dpi.blockSignals(False)
        self.settings.set("ui_scale", float(val))
        self._apply_font_size(self.spin_font.value())

    def changeEvent(self, e):
        if e.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                if bool(self.settings.get("minimize_to_tray", False)):
                    self._hide_to_tray()
        super().changeEvent(e)

    def _apply_font_size(self, size: float):
        scale = float(self.settings.get("ui_scale", 100)) / 100.0
        f = self.font()
        f.setPointSize(int(size * scale))
        self.setFont(f)

    def _on_rate_changed(self, v):
        try:
            self.settings.set("rate_merits_seconds", float(v))
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

    def _on_auto_toggled(self, v: bool):
        self.settings.set("auto_scale_ui", bool(v))

        # Update widget enabled state
        if self.sld_dpi:
            self.sld_dpi.setEnabled(not v)
        if self.spin_font:
            self.spin_font.setEnabled(not v)

        if bool(v):
            self._apply_auto_scale()

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

        # Refresh table if it exists
        if self.tbl_keys:
            self._populate_keybinds()

    def _populate_keybinds(self) -> None:
        self.tbl_keys.setRowCount(0)
        shortcuts = self.settings.get("shortcuts", {}) or {}
        defs = self._keybind_definitions()

        # Sort by name for display
        sorted_items = sorted(defs.items(), key=lambda x: x[1][0])

        for key_id, (name, _) in sorted_items:
            row = self.tbl_keys.rowCount()
            self.tbl_keys.insertRow(row)
            self.tbl_keys.setItem(row, 0, QTableWidgetItem(name))
            self.tbl_keys.setItem(row, 1, QTableWidgetItem(shortcuts.get(key_id, "")))
            edit_btn = QPushButton("Edit")
            reset_btn = QPushButton("Reset")
            cell = QWidget()
            h = QHBoxLayout(cell)
            h.setContentsMargins(0, 0, 0, 0)
            h.addWidget(edit_btn)
            h.addWidget(reset_btn)
            self.tbl_keys.setCellWidget(row, 2, cell)
            edit_btn.clicked.connect(lambda _, k=key_id: self._edit_keybind(k))
            reset_btn.clicked.connect(lambda _, k=key_id: self._reset_keybind(k))

    def _edit_keybind(self, key_id: str):
        defs = self._keybind_definitions()
        name = defs.get(key_id, (key_id, None))[0]

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Bind: {name}")
        lay = QVBoxLayout(dlg)
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
        from meritscalc.settings import DEFAULT_SETTINGS

        sc = self.settings.get("shortcuts", {}) or {}
        default_sc = DEFAULT_SETTINGS.get("shortcuts", {})
        if isinstance(default_sc, dict) and key_id in default_sc:
            sc[key_id] = default_sc[key_id]
            self.settings.set("shortcuts", sc)

    def _build_about_tab(self, tab: QWidget):
        v = QVBoxLayout(tab)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(12)
        header = self._label("SC MERIT CALC", 18)
        v.addWidget(header)
        body = QLabel(
            "Merits calculator for Star Citizen. Calculates merits, fees and aUEC."
        )
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(body)
        dev_body = QLabel("Developer: PINKgeekPDX • Development date: 2025-12-03")
        dev_body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(dev_body)
        img = QLabel()
        img.setFixedSize(300, 300)
        icon = get_app_icon()
        pm = icon.pixmap(300, 300)
        img.setPixmap(pm)
        v.addWidget(img)
        row = QHBoxLayout()
        btn_repo = QPushButton("GitHub")
        btn_issues = QPushButton("Issues")
        btn_updates = QPushButton("Check for Updates")
        btn_updates.setEnabled(False)
        btn_license = QPushButton("Open Source License")
        row.addWidget(btn_repo)
        row.addWidget(btn_issues)
        row.addWidget(btn_updates)
        row.addWidget(btn_license)
        v.addLayout(row)
        repo_url = "https://github.com/PINKgeekPDX/SCMeritsCalc"
        issues_url = "https://github.com/PINKgeekPDX/SCMeritsCalc/issues"
        btn_repo.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(repo_url)))
        btn_issues.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(issues_url)))

        btn_updates.clicked.connect(self._check_for_updates)
        btn_updates.setEnabled(True)

        def _show_license():
            dlg = QDialog(self)
            dlg.setWindowTitle("MIT License")
            lay = QVBoxLayout(dlg)
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
        scroll_layout.setContentsMargins(12, 12, 12, 12)
        scroll_layout.setSpacing(15)

        # Calculator Section
        calc_box = QGroupBox("CALCULATOR")
        calc_lay = QVBoxLayout(calc_box)
        calc_lay.setSpacing(10)

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
        actions_box = QGroupBox("ACTIONS")
        actions_lay = QVBoxLayout(actions_box)
        actions_lay.setSpacing(10)

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

        # Keyboard Shortcuts Section
        shortcuts_box = QGroupBox("KEYBOARD SHORTCUTS")
        shortcuts_lay = QVBoxLayout(shortcuts_box)
        shortcuts_lay.setSpacing(10)

        shortcuts_text = QLabel(
            "<b>Copy Report:</b> Ctrl+C<br>"
            "<b>Save Report:</b> Ctrl+S<br>"
            "<b>Clear Inputs:</b> Ctrl+R<br>"
            "<b>Minimize:</b> Esc<br>"
            "<b>Toggle Transparency:</b> Ctrl+Shift+T<br>"
            "<b>Toggle Always On Top:</b> Ctrl+Shift+A<br>"
            "<b>Toggle Visibility:</b> Ctrl+M<br>"
            "<b>Open Settings:</b> Ctrl+O<br>"
            "<b>Exit:</b> Shift+Esc<br><br>"
            "All shortcuts can be customized in the Settings tab."
        )
        shortcuts_text.setWordWrap(True)
        shortcuts_text.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        shortcuts_lay.addWidget(shortcuts_text)
        scroll_layout.addWidget(shortcuts_box)

        # Settings Section
        settings_box = QGroupBox("SETTINGS")
        settings_lay = QVBoxLayout(settings_box)
        settings_lay.setSpacing(10)

        settings_text = QLabel(
            "<b>Display:</b><br>"
            "• <b>DPI Scale:</b> Manually adjust the UI scaling percentage "
            "(50-200%). Disabled when Auto Scaling is enabled.<br>"
            "• <b>Auto Scaling:</b> Automatically scales the UI based on your "
            "screen's DPI. When enabled, manual scale controls are disabled.<br>"
            "• <b>Base Font Size:</b> Sets the base font size for the application "
            "(8-48pt). Disabled when Auto Scaling is enabled.<br>"
            "• <b>Auto Scale Bias:</b> Adjusts how aggressive the auto-scaling "
            "is (0.5-1.5). Lower values make the UI more compact.<br><br>"
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
        tray_box = QGroupBox("SYSTEM TRAY")
        tray_lay = QVBoxLayout(tray_box)
        tray_lay.setSpacing(10)

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
        updates_box = QGroupBox("UPDATES")
        updates_lay = QVBoxLayout(updates_box)
        updates_lay.setSpacing(10)

        updates_text = QLabel(
            "The application can automatically check for updates from GitHub "
            "releases.<br><br>"
            "<b>Checking for Updates:</b><br>"
            "Click 'Check for Updates' in the About tab. The app will connect "
            "to GitHub and compare your current version with the latest release."
            "<br><br>"
            "<b>Download Options:</b><br>"
            "• <b>Download:</b> Downloads the installer for later installation. "
            "You'll be prompted to install it the next time you start the app.<br>"
            "• <b>Download and Update:</b> Downloads and immediately launches "
            "the installer, then closes the current app session.<br><br>"
            "Updates are checked against the latest release on the GitHub "
            "repository. The installer is automatically downloaded and can be "
            "run to update the application."
        )
        updates_text.setWordWrap(True)
        updates_text.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        updates_lay.addWidget(updates_text)
        scroll_layout.addWidget(updates_box)

        # Tips Section
        tips_box = QGroupBox("TIPS & TRICKS")
        tips_lay = QVBoxLayout(tips_box)
        tips_lay.setSpacing(10)

        tips_text = QLabel(
            "• Double-click any output value (Merits with Fee or aUEC Value) "
            "to quickly copy it.<br>"
            "• Use keyboard shortcuts for faster workflow - customize them "
            "in Settings.<br>"
            "• Adjust transparency to make the window less intrusive while "
            "gaming.<br>"
            "• Enable 'Always On Top' to keep the calculator visible while "
            "using other applications.<br>"
            "• The calculator automatically saves your window position and "
            "settings.<br>"
            "• All settings are saved automatically when changed - no need "
            "to click Save."
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
