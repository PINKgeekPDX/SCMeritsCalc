"""MeritsCalc Qt UI module."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QEvent, QRect, Qt, QUrl
from PyQt6.QtGui import (
    QDesktopServices,
    QFont,
    QIcon,
    QPainter,
    QPixmap,
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
    QSlider,
    QSystemTrayIcon,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
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
        self.merits_mode = None
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

        # React to settings changes instantly
        def _on_setting_changed(key, value):
            if key == "ui_scale":
                self._apply_font_size(self.spin_font.value())
            elif key == "font_size":
                self._apply_font_size(float(value))
            elif key == "window_opacity":
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

        self.settings.add_observer(_on_setting_changed)

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
        about_tab = QWidget()
        self.tabs.addTab(calc, "CALCULATOR")
        self.tabs.addTab(settings_tab, "SETTINGS")
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
        self.merits_mode = QLabel("AUTO")
        self.merits_mode.setObjectName("MeritsMode")
        self.merits_mode.setProperty("mode", "auto")
        self.in_merits.setProperty("mode", "auto")
        row.addWidget(self.in_merits)
        row.addWidget(self.merits_mode)
        lay.addLayout(row)
        self.in_merits.textEdited.connect(self._on_merits_edited)
        self.in_merits.textChanged.connect(self._calculate)
        parent.addWidget(box)

    def _add_fee(self, parent):
        box = QGroupBox()
        lay = QVBoxLayout(box)
        lay.addWidget(self._label("MERITS WITH 0.5% FEE (☼)", 12))
        self.out_merits_fee = self._label("☼ 0", 36)
        self.out_merits_fee.setAccessibleName("MeritsFeeOutput")
        lay.addWidget(self.out_merits_fee)
        parent.addWidget(box)

    def _add_auec(self, parent):
        box = QGroupBox()
        lay = QVBoxLayout(box)
        lay.addWidget(self._label("AUEC VALUE (¤)", 14))
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
            "QLabel#MeritsMode[mode=auto] { color: #00d9ff; padding-left: 8px; }\n"
            "QLabel#MeritsMode[mode=manual] { color: #ffbb66; padding-left: 8px; }\n"
            "QPushButton { background: #23262c; color: #e6f7ff; border: 1px solid #00d9ff;\n"
            "  border-radius: 8px; padding: 10px 18px; font-weight: bold; }\n"
            "QPushButton:hover { background: #00a2cc; border-color: #00a2cc; }\n"
            "QPushButton:pressed { background: #00d9ff; border-color: #00d9ff; }\n"
        )
        self.setStyleSheet(css)

    def _refresh_styles(self):
        self.in_merits.style().unpolish(self.in_merits)
        self.in_merits.style().polish(self.in_merits)
        self.merits_mode.style().unpolish(self.merits_mode)
        self.merits_mode.style().polish(self.merits_mode)

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
        self.merits_mode.setProperty("mode", "auto")
        self.merits_mode.setText("AUTO")
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
        self.merits_mode.setProperty("mode", "manual")
        self.merits_mode.setText("MANUAL")
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
        dsp_lay.addWidget(QLabel("DPI scale (%)"), 0, 0)
        dsp_lay.addWidget(self.sld_dpi, 0, 1)
        dsp_lay.addWidget(self.chk_auto_scale, 1, 0)
        dsp_lay.addWidget(QLabel("Base font size"), 2, 0)
        dsp_lay.addWidget(self.spin_font, 2, 1)
        layout.addWidget(dsp_box)
        self.sld_transparency = QSlider(Qt.Orientation.Horizontal)
        self.sld_transparency.setRange(30, 100)
        self.sld_transparency.setValue(
            int(self.settings.get("transparency_default", 90) * 100)
        )
        self.sld_transparency.valueChanged.connect(
            lambda v: self._apply_opacity(int(v))
        )
        layout.addWidget(self.sld_transparency)
        self.spin_rate = QDoubleSpinBox()
        self.spin_rate.setRange(0.1, 10.0)
        self.spin_rate.setValue(float(self.settings.get("rate_merits_seconds", 1.0)))
        self.spin_rate.valueChanged.connect(self._on_rate_changed)
        layout.addWidget(self.spin_rate)
        self.spin_fee = QDoubleSpinBox()
        self.spin_fee.setRange(0.0, 100.0)
        self.spin_fee.setValue(float(self.settings.get("fee_percent", 0.5)))
        self.spin_fee.valueChanged.connect(self._on_fee_changed)
        layout.addWidget(self.spin_fee)
        self.sld_dpi.valueChanged.connect(lambda v: self._apply_dpi_scale(int(v)))
        self.chk_auto_scale.toggled.connect(self._on_auto_toggled)
        self.spin_font.valueChanged.connect(lambda v: self._apply_font_size(float(v)))
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
        self.settings.set("window_opacity", op)

    def _apply_dpi_scale(self, val: int):
        self.settings.set("ui_scale", float(val))
        self._apply_font_size(self.spin_font.value())

    def _apply_auto_scale(self):
        bias = float(self.settings.get("auto_scale_bias", 0.90))
        app = QApplication.instance() or QApplication([])
        screen = app.primaryScreen()
        dpi = 96.0
        if screen is not None:
            try:
                dpi = float(screen.logicalDotsPerInch())
            except Exception:
                dpi = 96.0
        scale = max(0.5, min(2.0, (dpi / 96.0) * bias))
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
            self.settings.set("fee_percent", float(v))
        except Exception:
            pass

    def _on_auto_toggled(self, v: bool):
        self.settings.set("auto_scale_ui", bool(v))
        if bool(v):
            self._apply_auto_scale()

    def _keybind_actions(self):
        return [
            ("Copy Report", self._copy_report),
            ("Save Report", self._save_report_dialog),
            ("Toggle Visibility", self._toggle_visibility),
            ("Open Settings", lambda: self.tabs.setCurrentIndex(1)),
            ("Exit", lambda: QApplication.instance().quit()),
        ]

    def _populate_keybinds(self) -> None:
        self.tbl_keys.setRowCount(0)
        shortcuts = self.settings.get("shortcuts", {}) or {}
        for name, _ in self._keybind_actions():
            row = self.tbl_keys.rowCount()
            self.tbl_keys.insertRow(row)
            self.tbl_keys.setItem(row, 0, QTableWidgetItem(name))
            self.tbl_keys.setItem(row, 1, QTableWidgetItem(shortcuts.get(name, "")))
            edit_btn = QPushButton("Edit")
            reset_btn = QPushButton("Reset")
            cell = QWidget()
            h = QHBoxLayout(cell)
            h.setContentsMargins(0, 0, 0, 0)
            h.addWidget(edit_btn)
            h.addWidget(reset_btn)
            self.tbl_keys.setCellWidget(row, 2, cell)
            edit_btn.clicked.connect(lambda _, n=name: self._edit_keybind(n))
            reset_btn.clicked.connect(lambda _, n=name: self._reset_keybind(n))

    def _edit_keybind(self, name: str):
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
            sc[name] = seq
            self.settings.set("shortcuts", sc)
            self._populate_keybinds()

    def _reset_keybind(self, name: str):
        sc = self.settings.get("shortcuts", {}) or {}
        if name in sc:
            del sc[name]
            self.settings.set("shortcuts", sc)
            self._populate_keybinds()

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
        btn_license = QPushButton("Open Source License")
        row.addWidget(btn_repo)
        row.addWidget(btn_issues)
        row.addWidget(btn_updates)
        row.addWidget(btn_license)
        v.addLayout(row)
        prog = QProgressBar()
        prog.setRange(0, 100)
        prog.setValue(0)
        v.addWidget(prog)
        btn_repo.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/"))
        )
        btn_issues.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/issues"))
        )

        def _fake_update():
            prog.setValue(100)

        btn_updates.clicked.connect(_fake_update)

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
