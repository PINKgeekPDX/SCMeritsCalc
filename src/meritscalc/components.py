import tkinter as tk
import customtkinter as ctk

from .logic import MeritsCalculator
from .settings import SettingsManager
from .theme import (
    FONT_FAMILY_HEADER,
    FONT_FAMILY_PRIMARY,
    FONT_SIZE_SM,
    COLOR_WARNING,
    COLOR_ACCENT_PRIMARY,
)


class CalculatorSection(ctk.CTkFrame):
    def __init__(
        self,
        master,
        settings: SettingsManager,
        calc: MeritsCalculator,
        on_change,
    ):
        super().__init__(master)
        self.settings = settings
        self.calc = calc
        self.on_change = on_change

        # Prison sentence first (as in reference)
        time_frame = ctk.CTkFrame(self)
        time_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(
            time_frame,
            text="PRISON SENTENCE",
            font=(FONT_FAMILY_HEADER, 14),
            text_color=COLOR_ACCENT_PRIMARY,
        ).pack(pady=5)

        grid = ctk.CTkFrame(time_frame)
        grid.pack()
        ctk.CTkLabel(grid, text="HOURS").grid(row=0, column=0, sticky="s")
        ctk.CTkLabel(grid, text="MINUTES").grid(row=0, column=2, sticky="s")
        self.entry_h = ctk.CTkEntry(grid, width=80, placeholder_text="0")
        self.entry_h.grid(row=1, column=0, padx=5)
        ctk.CTkLabel(grid, text=":").grid(row=1, column=1)
        self.entry_m = ctk.CTkEntry(grid, width=80, placeholder_text="0")
        self.entry_m.grid(row=1, column=2, padx=5)

        # Merits next
        ctk.CTkLabel(
            self,
            text="MERITS",
            font=(FONT_FAMILY_HEADER, 14),
            text_color=COLOR_ACCENT_PRIMARY,
        ).pack(pady=5)
        self.entry_merits = ctk.CTkEntry(
            self, placeholder_text="0", font=(FONT_FAMILY_PRIMARY, 12)
        )
        self.entry_merits.pack(pady=5, padx=20, fill="x")
        self.entry_merits.bind("<KeyRelease>", self._merits_changed)

        # Fee display panel
        fee_box = ctk.CTkFrame(self)
        fee_box.pack(pady=8, padx=10, fill="x")
        self.fee_header = ctk.CTkLabel(
            fee_box,
            text=f"MERITS WITH {self.settings.get('fee_percent', 0.5)}% FEE",
            font=(FONT_FAMILY_HEADER, 14),
            text_color=COLOR_ACCENT_PRIMARY,
        )
        self.fee_header.pack(pady=5)
        self.entry_fee = ctk.CTkEntry(
            fee_box, placeholder_text="0", font=(FONT_FAMILY_PRIMARY, 12)
        )
        self.entry_fee.pack(pady=5, padx=20, fill="x")

        # Total sentence time display
        time_box = ctk.CTkFrame(self)
        time_box.pack(pady=8, padx=10, fill="x")
        ctk.CTkLabel(
            time_box,
            text="TOTAL SENTENCE TIME",
            font=(FONT_FAMILY_HEADER, 14),
            text_color=COLOR_ACCENT_PRIMARY,
        ).pack(pady=5)
        self.entry_time_str = ctk.CTkEntry(time_box, font=(FONT_FAMILY_PRIMARY, 12))
        self.entry_time_str.pack(pady=5, padx=20, fill="x")

        # aUEC value display
        auec_box = ctk.CTkFrame(self)
        auec_box.pack(pady=8, padx=10, fill="x")
        ctk.CTkLabel(
            auec_box,
            text="aUEC VALUE",
            font=(FONT_FAMILY_HEADER, 14),
            text_color=COLOR_ACCENT_PRIMARY,
        ).pack(pady=5)
        self.entry_auec = ctk.CTkEntry(auec_box, font=(FONT_FAMILY_PRIMARY, 12))
        self.entry_auec.pack(pady=5, padx=20, fill="x")

        self.entry_h.bind("<KeyRelease>", self._time_changed)
        self.entry_m.bind("<KeyRelease>", self._time_changed)

    def _get_float(self, entry):
        try:
            val = entry.get()
            return float(val) if val else 0.0
        except ValueError:
            return 0.0

    def _update_fee_label(self, merits):
        fee_pct = self.settings.get("fee_percent", 0.5)
        with_fee = self.calc.apply_fee(merits, fee_pct)
        self.fee_header.configure(text=f"MERITS WITH {fee_pct}% FEE")
        self.entry_fee.delete(0, "end")
        self.entry_fee.insert(0, f"{with_fee:,.0f}")

    def _merits_changed(self, _event=None):
        merits = self._get_float(self.entry_merits)
        h, m, s = self.calc.merits_to_time(merits)
        self.entry_h.delete(0, "end")
        self.entry_h.insert(0, str(h))
        self.entry_m.delete(0, "end")
        self.entry_m.insert(0, str(m))
        # summary values (time, aUEC) are displayed on the right column
        self._update_fee_label(merits)
        # update derived displays
        self.entry_time_str.delete(0, "end")
        self.entry_time_str.insert(0, f"{int(h):02d}:{int(m):02d}:{int(s):02d}")
        auec_val = self.calc.merits_to_auec(merits)
        self.entry_auec.delete(0, "end")
        self.entry_auec.insert(0, f"{auec_val:,.2f}")
        if self.on_change:
            self.on_change()

    def _time_changed(self, _event=None):
        h = self._get_float(self.entry_h)
        m = self._get_float(self.entry_m)
        merits = self.calc.time_to_merits(h, m, 0)
        self.entry_merits.delete(0, "end")
        self.entry_merits.insert(0, f"{merits:.0f}")
        # summary values (time, aUEC) are displayed on the right column
        self._update_fee_label(merits)
        # update derived displays
        self.entry_time_str.delete(0, "end")
        self.entry_time_str.insert(0, f"{int(h):02d}:{int(m):02d}:00")
        auec_val = self.calc.merits_to_auec(merits)
        self.entry_auec.delete(0, "end")
        self.entry_auec.insert(0, f"{auec_val:,.2f}")
        if self.on_change:
            self.on_change()

    def _auec_changed(self, _event=None):
        auec = self._get_float(self.entry_auec)
        merits = self.calc.auec_to_merits(auec)
        self.entry_merits.delete(0, "end")
        self.entry_merits.insert(0, f"{merits:.0f}")
        h, m, s = self.calc.merits_to_time(merits)
        self.entry_h.delete(0, "end")
        self.entry_h.insert(0, str(h))
        self.entry_m.delete(0, "end")
        self.entry_m.insert(0, str(m))
        # summary values (time, aUEC) are displayed on the right column
        self._update_fee_label(merits)
        if self.on_change:
            self.on_change()

    def get_merits_value(self):
        return self._get_float(self.entry_merits)


class FeeSection(ctk.CTkFrame):
    def __init__(
        self,
        master,
        settings: SettingsManager,
        calc: MeritsCalculator,
        get_base_merits,
    ):
        super().__init__(master)
        self.settings = settings
        self.calc = calc
        self.get_base_merits = get_base_merits

        ctk.CTkLabel(self, text="FEES", font=(FONT_FAMILY_HEADER, 14)).pack(pady=5)

        grid = ctk.CTkFrame(self)
        grid.pack(pady=6, padx=10, fill="x")

        ctk.CTkLabel(grid, text="Base", font=(FONT_FAMILY_PRIMARY, FONT_SIZE_SM)).grid(
            row=0, column=0, sticky="w"
        )
        self.base_var = tk.DoubleVar(value=0.0)
        self.entry_base = ctk.CTkEntry(grid)
        self.entry_base.grid(row=0, column=1, sticky="we")

        ctk.CTkLabel(
            grid, text="Additional", font=(FONT_FAMILY_PRIMARY, FONT_SIZE_SM)
        ).grid(row=1, column=0, sticky="w")
        self.add_var = tk.DoubleVar(value=0.0)
        self.entry_add = ctk.CTkEntry(grid)
        self.entry_add.grid(row=1, column=1, sticky="we")

        ctk.CTkLabel(
            grid, text="Discount %", font=(FONT_FAMILY_PRIMARY, FONT_SIZE_SM)
        ).grid(row=2, column=0, sticky="w")
        self.discount_var = tk.DoubleVar(
            value=float(self.settings.get("discount_percent", 0.0))
        )
        self.entry_disc = ctk.CTkEntry(grid)
        self.entry_disc.grid(row=2, column=1, sticky="we")

        grid.grid_columnconfigure(1, weight=1)

        self.total_label = ctk.CTkLabel(
            self, text="Total: 0", font=(FONT_FAMILY_PRIMARY, 12)
        )
        self.total_label.pack(pady=10)

        btns = ctk.CTkFrame(self)
        btns.pack(pady=6, fill="x")
        apply_btn = ctk.CTkButton(btns, text="APPLY", command=self._recalc_total)
        reset_btn = ctk.CTkButton(
            btns,
            text="RESET",
            fg_color=COLOR_WARNING,
            command=self._reset_fee_fields,
        )
        apply_btn.pack(side="left", padx=6)
        reset_btn.pack(side="left", padx=6)

        self._populate_defaults()

    def _populate_defaults(self):
        try:
            base = self.get_base_merits() or 0.0
        except Exception:
            base = 0.0
        self.base_var.set(base)
        self.entry_base.delete(0, "end")
        self.entry_base.insert(0, f"{base:.0f}")
        self.entry_add.insert(0, "0")
        self.entry_disc.insert(
            0, f"{float(self.settings.get('discount_percent', 0.0))}"
        )

    def _get_float(self, entry):
        try:
            val = entry.get()
            return float(val) if val else 0.0
        except ValueError:
            return 0.0

    def _reset_fee_fields(self):
        self._populate_defaults()
        self.total_label.configure(text="Total: 0")

    def _recalc_total(self):
        base = self._get_float(self.entry_base)
        addl = self._get_float(self.entry_add)
        disc = self._get_float(self.entry_disc)
        fee_pct = self.settings.get("fee_percent", 0.5)
        total = self.calc.total_with_fee(base, fee_pct, addl, disc)
        self.total_label.configure(text=f"Total: {total:,.2f}")


class SummarySection(ctk.CTkFrame):
    def __init__(self, master, calc: MeritsCalculator):
        super().__init__(master)
        self.calc = calc

        m_box = ctk.CTkFrame(self)
        m_box.pack(pady=8, padx=10, fill="x")
        ctk.CTkLabel(m_box, text="MERITS", font=(FONT_FAMILY_HEADER, 14)).pack(pady=5)
        self.entry_summary_merits = ctk.CTkEntry(m_box)
        self.entry_summary_merits.pack(pady=5, padx=20, fill="x")

        t_box = ctk.CTkFrame(self, fg_color="#2e7d32")
        t_box.pack(pady=8, padx=10, fill="x")
        ctk.CTkLabel(t_box, text="TIME", font=(FONT_FAMILY_HEADER, 14)).pack(pady=5)
        self.entry_summary_time = ctk.CTkEntry(t_box)
        self.entry_summary_time.pack(pady=5, padx=20, fill="x")

    def update(self, merits_value: float):
        h, m, s = self.calc.merits_to_time(merits_value)
        self.entry_summary_merits.delete(0, "end")
        self.entry_summary_merits.insert(0, f"{merits_value:.0f}")
        self.entry_summary_time.delete(0, "end")
        self.entry_summary_time.insert(0, f"{int(h):02d}:{int(m):02d}:{int(s):02d}")


class SettingsSection(ctk.CTkFrame):
    def __init__(self, master, settings: SettingsManager, on_apply):
        super().__init__(master)
        self.settings = settings
        self.on_apply = on_apply

        ctk.CTkLabel(self, text="CONVERSION RATES", font=(FONT_FAMILY_HEADER, 14)).pack(
            pady=5
        )

        row1 = ctk.CTkFrame(self)
        row1.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row1, text="1 Merit = X Seconds:").pack(side="left")
        self.set_rate_seconds = ctk.CTkEntry(row1, width=80)
        self.set_rate_seconds.pack(side="right")
        self.set_rate_seconds.insert(0, str(self.settings.get("rate_merits_seconds")))

        row2 = ctk.CTkFrame(self)
        row2.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row2, text="1 Merit = X aUEC:").pack(side="left")
        self.set_rate_auec = ctk.CTkEntry(row2, width=80)
        self.set_rate_auec.pack(side="right")
        self.set_rate_auec.insert(0, str(self.settings.get("rate_merits_auec")))

        row3 = ctk.CTkFrame(self)
        row3.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row3, text="Fee Percent (%):").pack(side="left")
        self.set_fee_percent = ctk.CTkEntry(row3, width=80)
        self.set_fee_percent.pack(side="right")
        self.set_fee_percent.insert(0, str(self.settings.get("fee_percent")))

        row4 = ctk.CTkFrame(self)
        row4.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row4, text="Discount Percent (%):").pack(side="left")
        self.set_discount_percent = ctk.CTkEntry(row4, width=80)
        self.set_discount_percent.pack(side="right")
        self.set_discount_percent.insert(
            0, str(self.settings.get("discount_percent", 0.0))
        )

        prefs = ctk.CTkFrame(self)
        prefs.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(prefs, text="PREFERENCES", font=(FONT_FAMILY_HEADER, 14)).pack(
            pady=5
        )

        self.var_tray = tk.BooleanVar(value=self.settings.get("minimize_to_tray"))
        ctk.CTkCheckBox(
            prefs,
            text="Minimize to Tray",
            variable=self.var_tray,
            command=self._apply,
        ).pack(pady=5, padx=20, anchor="w")

        self.var_autosave = tk.BooleanVar(value=self.settings.get("auto_save"))
        ctk.CTkCheckBox(
            prefs,
            text="Auto-Save Inputs",
            variable=self.var_autosave,
            command=self._apply,
        ).pack(pady=5, padx=20, anchor="w")

        ctk.CTkButton(self, text="APPLY RATES", command=self._apply).pack(pady=10)
        ctk.CTkButton(
            self,
            text="RESET DEFAULTS",
            fg_color=COLOR_WARNING,
            command=self._reset_defaults,
        ).pack(pady=10)

    def _apply(self):
        try:
            rate_sec = float(self.set_rate_seconds.get())
            rate_auec = float(self.set_rate_auec.get())
            fee_pct = float(self.set_fee_percent.get())
            disc_pct = float(self.set_discount_percent.get())
        except ValueError:
            tk.messagebox.showerror(
                "Error", "Invalid rate values. Please enter numbers."
            )
            return

        self.settings.set("rate_merits_seconds", rate_sec)
        self.settings.set("rate_merits_auec", rate_auec)
        self.settings.set("fee_percent", fee_pct)
        self.settings.set("discount_percent", disc_pct)
        self.settings.set("minimize_to_tray", self.var_tray.get())
        self.settings.set("auto_save", self.var_autosave.get())
        if self.on_apply:
            self.on_apply()

    def _reset_defaults(self):
        self.settings.reset_defaults()
        self.set_rate_seconds.delete(0, "end")
        self.set_rate_seconds.insert(0, str(self.settings.get("rate_merits_seconds")))
        self.set_rate_auec.delete(0, "end")
        self.set_rate_auec.insert(0, str(self.settings.get("rate_merits_auec")))
        self.set_fee_percent.delete(0, "end")
        self.set_fee_percent.insert(0, str(self.settings.get("fee_percent")))
        self.set_discount_percent.delete(0, "end")
        self.set_discount_percent.insert(
            0, str(self.settings.get("discount_percent", 0.0))
        )
        self.var_tray.set(self.settings.get("minimize_to_tray"))
        self.var_autosave.set(self.settings.get("auto_save"))
        self._apply()
