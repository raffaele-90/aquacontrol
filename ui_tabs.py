# AquaControl
# Copyright (C) 2026 Raffaele Schiavone
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
                               QScrollArea, QGridLayout, QFrame, QGroupBox,
                               QComboBox, QCheckBox, QPushButton, QFormLayout,
                               QSpinBox, QDoubleSpinBox, QLineEdit, QColorDialog, QFontDialog,
                               QMessageBox, QDialog, QDialogButtonBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QCursor

from config_manager import global_config, save_config
from i18n import T
from ui_widgets import format_temp, SparklineWidget, PWMFillBar
from guide_texts import get_guide_text

class DashboardTabWidget(QWidget):
    """Tab visuale informativo avanzato: Storico, Delta T e Carichi PWM."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Header layout: Titolo, Selettore Profilo, Pulsante Ripristino
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignVCenter)

        lbl_title = QLabel(f"📊 {T('tab_dash')}")
        lbl_title.setStyleSheet("font-size: 22px; color: #00e5ff; font-weight: bold;")
        header_layout.addWidget(lbl_title)

        header_layout.addSpacing(20)

        lbl_prof = QLabel(f"{T('dash_profile')}:")
        lbl_prof.setStyleSheet("color: #a6adc8; font-size: 13px; font-weight: bold;")
        header_layout.addWidget(lbl_prof)

        self.combo_profile = QComboBox()
        self.combo_profile.setCursor(QCursor(Qt.PointingHandCursor))
        self.combo_profile.setStyleSheet("""
            QComboBox { background-color: #313244; color: #cdd6f4; border-radius: 4px; padding: 4px 10px; font-weight: bold; }
            QComboBox::drop-down { border: none; }
        """)
        # Carica i profili (con un fallback se il dizionario non esiste)
        profiles = global_config.get("profiles", {"Default": {}})
        self.combo_profile.addItems(profiles.keys())
        active_prof = global_config.get("active_profile", "Default")
        if active_prof in profiles:
            self.combo_profile.setCurrentText(active_prof)
        self.combo_profile.currentTextChanged.connect(self.change_active_profile)
        header_layout.addWidget(self.combo_profile)

        header_layout.addStretch()

        self.btn_restore = QPushButton(f"👁\uFE0E {T('dash_manage_hidden')}")
        self.btn_restore.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_restore.setStyleSheet("""
            QPushButton { background-color: #313244; color: #cdd6f4; border-radius: 4px; padding: 4px 10px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: #45475a; }
        """)
        self.btn_restore.clicked.connect(self.show_restore_dialog)
        header_layout.addWidget(self.btn_restore)

        layout.addLayout(header_layout)
        layout.addSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        container = QWidget()
        scroll.setWidget(container)
        self.main_layout = QVBoxLayout(container)

        # Creazione dei Gruppi Logici
        self.grp_virt = QGroupBox(f"✨ {T('dash_virt_sensors')}")
        self.lay_virt = QGridLayout(self.grp_virt)
        self.grp_virt.hide() # Nascosto di default se non ci sono Delta T attivi

        self.grp_sys = QGroupBox(f"💻 {T('dash_sys_sensors')}")
        self.lay_sys = QGridLayout(self.grp_sys)

        self.grp_fans = QGroupBox(f"⚡ {T('dash_12v_out')}")
        self.lay_fans = QGridLayout(self.grp_fans)

        self.grp_aqua = QGroupBox(f"🌡️ {T('dash_aqua_sensors')}")
        self.lay_aqua = QGridLayout(self.grp_aqua)

        self.main_layout.addWidget(self.grp_virt)
        self.main_layout.addWidget(self.grp_sys)
        self.main_layout.addWidget(self.grp_fans)
        self.main_layout.addWidget(self.grp_aqua)
        self.main_layout.addStretch()

        layout.addWidget(scroll)

    def change_active_profile(self, profile_name):
        """Salva il cambio di profilo."""
        global_config["active_profile"] = profile_name
        save_config(global_config)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def update_telemetry(self, data):
        self._clear_layout(self.lay_virt)
        self._clear_layout(self.lay_sys)
        self._clear_layout(self.lay_fans)
        self._clear_layout(self.lay_aqua)

        col_virt, row_virt = 0, 0
        col_sys, row_sys = 0, 0
        col_fans, row_fans = 0, 0
        col_aqua, row_aqua = 0, 0

        hidden = global_config.get("hidden_sensors", [])
        histories = data.get("history", {})

        # Sensori Virtuali (Delta T)
        virt_data = data.get('virtuals', {})
        if virt_data:
            self.grp_virt.show()
            for v_id, val in virt_data.items():
                if v_id in hidden: continue
                name = global_config.get("sensors", {}).get(v_id, v_id)
                hist = histories.get(v_id, [])
                self._add_dash_card(self.lay_virt, name, format_temp(val), "🧮", row_virt, col_virt, v_id, history_data=hist)
                col_virt += 1
                if col_virt > 2: col_virt = 0; row_virt += 1
        else:
            self.grp_virt.hide()

        # Sistema (Fix Voltaggi)
        sys_data = data.get('system', {})
        for s_id, val in sys_data.items():
            if s_id in hidden: continue
            name = global_config["sensors"].get(s_id, s_id)
            hist = histories.get(s_id, [])

            if "load" in s_id.lower() or "busy" in s_id.lower():
                self._add_dash_card(self.lay_sys, name, f"{int(val)} %", "⚡", row_sys, col_sys, s_id, history_data=hist)
            elif "_in" in s_id.lower() or "volt" in s_id.lower():
                self._add_dash_card(self.lay_sys, name, f"{val:.2f} V", "🔌", row_sys, col_sys, s_id, history_data=hist)
            else:
                self._add_dash_card(self.lay_sys, name, format_temp(val), "🖥️", row_sys, col_sys, s_id, history_data=hist)

            col_sys += 1
            if col_sys > 2: col_sys = 0; row_sys += 1

        # Uscite Hardware
        pwm_loads = data.get('pwm_loads', {})
        volts = data.get('volts', {})
        hw_config = global_config.get("hardware_channels", {})
        for ch_id, rpm in data.get('rpms', {}).items():

            # --- FIX: Salta la card se il canale è disabilitato ---
            ch_conf = hw_config.get(str(ch_id), {})
            if not ch_conf.get("enabled", True): continue

            s_id = f"ch_rpm_{ch_id}"
            if s_id in hidden: continue
            ch_name = global_config["channels_names"].get(str(ch_id), f"{T('channel')} {ch_id}")
            hist = histories.get(s_id, [])
            pwm_load = pwm_loads.get(ch_id, 0)
            volt_val = volts.get(ch_id, 0.0)

            self._add_dash_card(self.lay_fans, ch_name, f"{rpm} RPM", "⚡", row_fans, col_fans, s_id, history_data=hist, pwm_load=pwm_load, sub_value=f"{volt_val:.2f} V")

            col_fans += 1
            if col_fans > 2: col_fans = 0; row_fans += 1

        # Aquaero (Temperature fisiche/liquido)
        for s_id, temp in data.get('temps', {}).items():
            if s_id in hidden: continue
            name = global_config["sensors"].get(s_id, s_id)
            hist = histories.get(s_id, [])

            self._add_dash_card(self.lay_aqua, name, format_temp(temp), "🌡️", row_aqua, col_aqua, s_id, history_data=hist)

            col_aqua += 1
            if col_aqua > 2: col_aqua = 0; row_aqua += 1

    def _add_dash_card(self, target_layout, title, value, icon, row, col, sensor_id, history_data=None, pwm_load=None, sub_value=None):
        card = QFrame()
        card.setMaximumWidth(300)
        # Sostituiamo il colore solido con un grigio vetro semi-trasparente
        card.setStyleSheet("QFrame { background-color: rgba(30, 30, 30, 160); border-radius: 8px; border: 1px solid #333333; }")

        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(10, 8, 10, 8)
        c_layout.setSpacing(4)

        # Riga Superiore: Icona, Titolo, X per nascondere
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)

        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 16px; background: transparent; border: none;")

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: bold; background: transparent; border: none;")

        btn_hide = QPushButton("✖")
        btn_hide.setFixedSize(16, 16)
        btn_hide.setCursor(QCursor(Qt.PointingHandCursor))
        btn_hide.setToolTip(T("dash_hide_tooltip"))
        btn_hide.setStyleSheet("""
            QPushButton { color: #6c7086; background: transparent; border: none; font-size: 10px; font-weight: bold; }
            QPushButton:hover { color: #f38ba8; }
        """)
        btn_hide.clicked.connect(lambda _, s=sensor_id: self.hide_sensor(s))

        top_layout.addWidget(lbl_icon)
        top_layout.addWidget(lbl_title)
        top_layout.addStretch()
        top_layout.addWidget(btn_hide)
        c_layout.addLayout(top_layout)

        # Valore centrale
        lbl_val = QLabel(value)
        lbl_val.setStyleSheet("color: #00e5ff; font-size: 18px; font-weight: bold; background: transparent; border: none;")
        c_layout.addWidget(lbl_val)

        if sub_value:
            lbl_sub = QLabel(sub_value)
            lbl_sub.setStyleSheet("color: #f9e2af; font-size: 13px; font-weight: bold; background: transparent; border: none;")
            c_layout.addWidget(lbl_sub)

        # Integrazione Sparkline (Storico grafico)
        if history_data and len(history_data) > 1:
            sparkline = SparklineWidget()
            sparkline.update_data(history_data)
            c_layout.addWidget(sparkline)

        # Integrazione Fill Bar (Carico ventole)
        if pwm_load is not None:
            fill_bar = PWMFillBar()
            fill_bar.update_value(pwm_load)
            c_layout.addWidget(fill_bar)

        target_layout.addWidget(card, row, col)

    def hide_sensor(self, sensor_id):
        hidden = global_config.get("hidden_sensors", [])
        if sensor_id not in hidden:
            hidden.append(sensor_id)
            global_config["hidden_sensors"] = hidden
            save_config(global_config)

    def show_restore_dialog(self):
        hidden = global_config.get("hidden_sensors", [])
        if not hidden:
            QMessageBox.information(self, "Info", T("dash_no_hidden"))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(T("dash_manage_hidden"))
        dialog.setMinimumWidth(300)
        dialog.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")

        layout = QVBoxLayout(dialog)
        lbl_info = QLabel(T("dash_restore_info"))
        lbl_info.setWordWrap(True)
        layout.addWidget(lbl_info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: 1px solid #313244; background-color: #11111b; border-radius: 4px;")
        container = QWidget()
        scroll.setWidget(container)
        list_layout = QVBoxLayout(container)

        checkboxes = {}
        for s_id in hidden:
            nice_name = global_config.get("sensors", {}).get(s_id, s_id)
            chk = QCheckBox(f"{nice_name} ({s_id})")
            chk.setStyleSheet("font-size: 13px;")
            list_layout.addWidget(chk)
            checkboxes[s_id] = chk

        list_layout.addStretch()
        layout.addWidget(scroll)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.setStyleSheet("QPushButton { background-color: #313244; color: #cdd6f4; padding: 5px; border-radius: 4px; } QPushButton:hover { background-color: #45475a; }")
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

        if dialog.exec() == QDialog.Accepted:
            sensors_to_restore = [s_id for s_id, chk in checkboxes.items() if chk.isChecked()]
            if sensors_to_restore:
                for s in sensors_to_restore:
                    hidden.remove(s)
                global_config["hidden_sensors"] = hidden
                save_config(global_config)


class SecurityTabWidget(QWidget):
    """Componente per l'interfaccia degli allarmi hardware di sistema (Fail-Safe)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        lbl_title = QLabel(f"\u2622\uFE0E {T('sec_title')}")
        lbl_title.setStyleSheet("font-size: 20px; color: #ff3333; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_title)

        info_txt = QLabel(T("sec_info"))
        info_txt.setWordWrap(True)
        info_txt.setStyleSheet("color: #a6adc8; margin-bottom: 15px; font-size: 13px;")
        layout.addWidget(info_txt)

        self.sec_channels = {}
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        scroll.setWidget(container)
        sec_layout = QVBoxLayout(container)
        layout.addWidget(scroll)

        for i in range(1, 5):
            ch_name = global_config["channels_names"].get(str(i), f"{T('channel')} {i}")
            group = QGroupBox(f"{ch_name}")
            glayout = QFormLayout(group)

            box_rpm = QHBoxLayout()
            chk_rpm = QCheckBox(T("sec_rpm"))
            spin_rpm = QSpinBox()
            spin_rpm.setRange(0, 5000)
            spin_rpm.setSuffix(" RPM")
            box_rpm.addWidget(chk_rpm)
            box_rpm.addWidget(spin_rpm)
            box_rpm.addStretch()
            glayout.addRow("", box_rpm)

            box_temp = QHBoxLayout()
            chk_temp = QCheckBox(T("sec_temp"))
            spin_temp = QSpinBox()
            spin_temp.setRange(20, 110)
            spin_temp.setSuffix(" °C")
            box_temp.addWidget(chk_temp)
            box_temp.addWidget(spin_temp)
            box_temp.addStretch()
            glayout.addRow("", box_temp)

            box_power = QHBoxLayout()
            chk_power = QCheckBox(T("sec_pwm"))
            spin_power = QSpinBox()
            spin_power.setRange(0, 100)
            spin_power.setSuffix(" %")
            box_power.addWidget(chk_power)
            box_power.addWidget(spin_power)
            box_power.addStretch()
            glayout.addRow("", box_power)

            # --- NUOVO: BOX VOLTAGGIO ---
            box_volt = QHBoxLayout()
            chk_volt = QCheckBox(T("sec_volt"))
            spin_volt = QDoubleSpinBox()
            spin_volt.setRange(0.0, 12.0)
            spin_volt.setSingleStep(0.1)
            spin_volt.setDecimals(1)
            spin_volt.setSuffix(" V")
            box_volt.addWidget(chk_volt)
            box_volt.addWidget(spin_volt)
            box_volt.addStretch()
            glayout.addRow("", box_volt)

            # Segnali
            chk_rpm.toggled.connect(self.set_dirty)
            spin_rpm.valueChanged.connect(self.set_dirty)
            chk_temp.toggled.connect(self.set_dirty)
            spin_temp.valueChanged.connect(self.set_dirty)
            chk_power.toggled.connect(self.set_dirty)
            spin_power.valueChanged.connect(self.set_dirty)
            chk_volt.toggled.connect(self.set_dirty)
            spin_volt.valueChanged.connect(self.set_dirty)

            # Aggiornato con chk_volt e spin_volt
            self.sec_channels[str(i)] = {
                "chk_rpm": chk_rpm, "spin_rpm": spin_rpm,
                "chk_temp": chk_temp, "spin_temp": spin_temp,
                "chk_power": chk_power, "spin_power": spin_power,
                "chk_volt": chk_volt, "spin_volt": spin_volt
            }
            sec_layout.addWidget(group)

        action_group = QGroupBox(T("sec_global"))
        alayout = QVBoxLayout(action_group)

        self.chk_sound = QCheckBox(T("sec_sound"))
        self.chk_osd_alert = QCheckBox(T("sec_osd_flash"))
        self.chk_osd_alert.setChecked(True)

        box_cmd = QHBoxLayout()
        self.chk_cmd = QCheckBox(T("sec_cmd_custom"))
        self.txt_cmd = QLineEdit()
        self.txt_cmd.setPlaceholderText("/home/user/allarme.sh")
        box_cmd.addWidget(self.chk_cmd)
        box_cmd.addWidget(self.txt_cmd)

        self.chk_shutdown = QCheckBox(T("sec_shutdown"))
        self.chk_shutdown.setStyleSheet("color: #ff3333; font-weight: bold;")

        self.box_delay = QHBoxLayout()
        self.lbl_delay = QLabel(T("sec_delay"))
        self.lbl_delay.setStyleSheet("color: #6c7086;")
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(0, 60)
        self.spin_delay.setSuffix(" sec")
        self.spin_delay.setEnabled(False)

        self.box_delay.addSpacing(25)
        self.box_delay.addWidget(self.lbl_delay)
        self.box_delay.addWidget(self.spin_delay)
        self.box_delay.addStretch()

        self.chk_sound.toggled.connect(self.set_dirty)
        self.chk_osd_alert.toggled.connect(self.set_dirty)
        self.chk_cmd.toggled.connect(self.set_dirty)
        self.chk_cmd.toggled.connect(self.update_delay_visibility)
        self.txt_cmd.textChanged.connect(self.set_dirty)
        self.txt_cmd.textChanged.connect(self.update_delay_visibility)
        self.chk_shutdown.toggled.connect(self.set_dirty)
        self.chk_shutdown.toggled.connect(self.update_delay_visibility)
        self.spin_delay.valueChanged.connect(self.set_dirty)

        alayout.addWidget(self.chk_sound)
        alayout.addWidget(self.chk_osd_alert)
        alayout.addLayout(box_cmd)
        alayout.addWidget(self.chk_shutdown)
        alayout.addLayout(self.box_delay)

        self.btn_save_sec = QPushButton(T("sec_save"))
        self.btn_save_sec.setObjectName("SecurityBtn")
        self.btn_save_sec.setEnabled(False)
        self.btn_save_sec.clicked.connect(self.save_security)
        alayout.addWidget(self.btn_save_sec)

        layout.addWidget(action_group)
        self.load_security()

    def update_delay_visibility(self):
        cmd_active = self.chk_cmd.isChecked() and bool(self.txt_cmd.text().strip())
        shutdown_active = self.chk_shutdown.isChecked()

        should_enable = cmd_active and shutdown_active

        self.spin_delay.setEnabled(should_enable)
        if should_enable:
            self.lbl_delay.setStyleSheet("color: #cdd6f4;")
        else:
            self.lbl_delay.setStyleSheet("color: #6c7086;")

    def set_dirty(self):
        self.btn_save_sec.setEnabled(True)

    def save_security(self):
        sec_config = {"channels": {}, "actions": {}}
        for ch_id, widgets in self.sec_channels.items():
            sec_config["channels"][ch_id] = {
                "rpm_en": widgets["chk_rpm"].isChecked(),
                "rpm_val": widgets["spin_rpm"].value(),
                "temp_en": widgets["chk_temp"].isChecked(),
                "temp_val": widgets["spin_temp"].value(),
                "power_en": widgets["chk_power"].isChecked(),
                "power_val": widgets["spin_power"].value(),
                "volt_en": widgets["chk_volt"].isChecked(),   # <--- NUOVO
                "volt_val": widgets["spin_volt"].value()      # <--- NUOVO
            }
        sec_config["actions"] = {
            "sound_en": self.chk_sound.isChecked(),
            "osd_en": self.chk_osd_alert.isChecked(),
            "cmd_en": self.chk_cmd.isChecked(),
            "cmd_val": self.txt_cmd.text(),
            "shutdown_en": self.chk_shutdown.isChecked(),
            "delay_val": self.spin_delay.value()
        }
        global_config["security"] = sec_config
        save_config(global_config)
        self.btn_save_sec.setEnabled(False)
        QMessageBox.information(self, T("sidebar_sec"), T("sec_saved_msg"))

    def load_security(self):
        sec_config = global_config.get("security", {})
        ch_config = sec_config.get("channels", {})
        for ch_id, widgets in self.sec_channels.items():
            saved = ch_config.get(ch_id, {})
            widgets["chk_rpm"].blockSignals(True); widgets["chk_rpm"].setChecked(saved.get("rpm_en", False)); widgets["chk_rpm"].blockSignals(False)
            widgets["spin_rpm"].blockSignals(True); widgets["spin_rpm"].setValue(saved.get("rpm_val", 500)); widgets["spin_rpm"].blockSignals(False)
            widgets["chk_temp"].blockSignals(True); widgets["chk_temp"].setChecked(saved.get("temp_en", False)); widgets["chk_temp"].blockSignals(False)
            widgets["spin_temp"].blockSignals(True); widgets["spin_temp"].setValue(saved.get("temp_val", 55)); widgets["spin_temp"].blockSignals(False)
            widgets["chk_power"].blockSignals(True); widgets["chk_power"].setChecked(saved.get("power_en", False)); widgets["chk_power"].blockSignals(False)
            widgets["spin_power"].blockSignals(True); widgets["spin_power"].setValue(saved.get("power_val", 20)); widgets["spin_power"].blockSignals(False)

            # --- NUOVO: Carica stato Volt ---
            widgets["chk_volt"].blockSignals(True); widgets["chk_volt"].setChecked(saved.get("volt_en", False)); widgets["chk_volt"].blockSignals(False)
            widgets["spin_volt"].blockSignals(True); widgets["spin_volt"].setValue(saved.get("volt_val", 0.0)); widgets["spin_volt"].blockSignals(False)

        actions = sec_config.get("actions", {})
        self.chk_sound.blockSignals(True); self.chk_sound.setChecked(actions.get("sound_en", False)); self.chk_sound.blockSignals(False)
        self.chk_osd_alert.blockSignals(True); self.chk_osd_alert.setChecked(actions.get("osd_en", True)); self.chk_osd_alert.blockSignals(False)
        self.chk_cmd.blockSignals(True); self.chk_cmd.setChecked(actions.get("cmd_en", False)); self.chk_cmd.blockSignals(False)
        self.txt_cmd.blockSignals(True); self.txt_cmd.setText(actions.get("cmd_val", "")); self.txt_cmd.blockSignals(False)

        self.chk_shutdown.blockSignals(True); self.chk_shutdown.setChecked(actions.get("shutdown_en", False)); self.chk_shutdown.blockSignals(False)
        self.spin_delay.blockSignals(True); self.spin_delay.setValue(actions.get("delay_val", 0)); self.spin_delay.blockSignals(False)

        self.update_delay_visibility()
        self.btn_save_sec.setEnabled(False)

class OSDConfigTabWidget(QWidget):
    """Componente per l'interfaccia di personalizzazione e configurazione dell'overlay OSD."""
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout(self)

        lbl_title = QLabel(f"🖥️ {T('osd_title')}")
        lbl_title.setStyleSheet("font-size: 20px; color: #00e5ff; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_title)

        info_txt = QLabel(T("osd_info"))
        info_txt.setWordWrap(True)
        info_txt.setStyleSheet("color: #a6adc8; margin-bottom: 5px; font-size: 13px;")
        layout.addWidget(info_txt)

        global_group = QGroupBox(T("osd_global"))
        g_layout = QHBoxLayout(global_group)

        self.main_window.chk_osd = QCheckBox(T("osd_show"))
        self.main_window.chk_osd.setStyleSheet("font-size: 13px; font-weight: bold; color: #00e5ff;")
        self.main_window.chk_osd.setChecked(global_config.get("osd_export", False))
        self.main_window.chk_osd.toggled.connect(self.main_window.toggle_osd)

        self.main_window.combo_osd_scale = QComboBox()
        self.main_window.combo_osd_scale.addItems(["50%", "75%", "100%", "125%", "150%", "200%"])
        self.main_window.combo_osd_scale.setFixedWidth(80)
        current_scale = global_config.get("osd_scale", 1.0)
        self.main_window.combo_osd_scale.setCurrentText(f"{int(current_scale * 100)}%")
        self.main_window.combo_osd_scale.currentTextChanged.connect(self.main_window.change_osd_scale)

        g_layout.addWidget(self.main_window.chk_osd)
        g_layout.addWidget(QLabel(T("osd_scale")))
        g_layout.addWidget(self.main_window.combo_osd_scale)
        g_layout.addStretch()
        layout.addWidget(global_group)

        aesthetic_group = QGroupBox(T("osd_aesthetic"))
        a_layout = QFormLayout(aesthetic_group)

        opacity_layout = QHBoxLayout()
        from PySide6.QtWidgets import QSlider
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setFixedWidth(180)
        self.lbl_opacity_val = QLabel()
        opacity_layout.addWidget(self.slider_opacity)
        opacity_layout.addWidget(self.lbl_opacity_val)
        opacity_layout.addStretch()
        self.slider_opacity.valueChanged.connect(self.update_aesthetic)

        self.spin_max_rows = QSpinBox()
        self.spin_max_rows.setRange(3, 15)
        self.spin_max_rows.setFixedWidth(60)
        self.spin_max_rows.valueChanged.connect(self.update_aesthetic)

        row_names = QHBoxLayout()
        self.btn_color_names = QPushButton(T("osd_btn_color"))
        self.lbl_preview_names = QLabel()
        self.lbl_preview_names.setFixedSize(24, 24)
        row_names.addWidget(self.btn_color_names)
        row_names.addWidget(self.lbl_preview_names)
        row_names.addStretch()

        row_values = QHBoxLayout()
        self.btn_color_values = QPushButton(T("osd_btn_color"))
        self.lbl_preview_values = QLabel()
        self.lbl_preview_values.setFixedSize(24, 24)
        row_values.addWidget(self.btn_color_values)
        row_values.addWidget(self.lbl_preview_values)
        row_values.addStretch()

        row_badges = QHBoxLayout()
        self.btn_color_badges = QPushButton(T("osd_btn_color"))
        self.lbl_preview_badges = QLabel()
        self.lbl_preview_badges.setFixedSize(24, 24)
        row_badges.addWidget(self.btn_color_badges)
        row_badges.addWidget(self.lbl_preview_badges)
        row_badges.addStretch()

        self.btn_color_names.clicked.connect(lambda: self.pick_color("c_names"))
        self.btn_color_values.clicked.connect(lambda: self.pick_color("c_values"))
        self.btn_color_badges.clicked.connect(lambda: self.pick_color("c_badges"))

        font_layout = QHBoxLayout()
        self.btn_font = QPushButton(T("osd_btn_font"))
        self.btn_font.clicked.connect(self.pick_font)
        self.lbl_current_font = QLabel(T("font_default"))
        self.lbl_current_font.setStyleSheet("color: #a6adc8; font-style: italic;")
        font_layout.addWidget(self.btn_font)
        font_layout.addWidget(self.lbl_current_font)
        font_layout.addStretch()

        a_layout.addRow(QLabel(T("osd_opacity")), opacity_layout)
        a_layout.addRow(QLabel(T("osd_max_rows")), self.spin_max_rows)
        a_layout.addRow(QLabel(T("osd_col_names")), row_names)
        a_layout.addRow(QLabel(T("osd_col_values")), row_values)
        a_layout.addRow(QLabel(T("osd_col_badges")), row_badges)
        a_layout.addRow(QLabel(T("osd_font_style")), font_layout)
        layout.addWidget(aesthetic_group)

        sensors_group = QGroupBox(T("osd_sensors_group"))
        s_layout = QVBoxLayout(sensors_group)
        s_layout.setContentsMargins(0, 5, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        scroll.setWidget(container)
        list_layout = QVBoxLayout(container)

        self.osd_items = {}

        for i in range(1, 5):
            comp_id = f"ch_{i}"
            desc = f"Aquaero: {T('channel')} {i}"
            placeholder = f"{T('channel')} {i}"
            self._add_sensor_row(list_layout, comp_id, desc, placeholder)

        sys_sensors = self.main_window.engine.get_available_system_sensors()
        for comp_id, label in sys_sensors.items():
            self._add_sensor_row(list_layout, comp_id, label, f"Es. {label}")

        s_layout.addWidget(scroll)

        self.btn_save = QPushButton(T("osd_save"))
        self.btn_save.setObjectName("ActionBtn")
        self.btn_save.setEnabled(False) # Spento di default
        self.btn_save.clicked.connect(self.save_osd_config)
        s_layout.addWidget(self.btn_save)

        layout.addWidget(sensors_group)
        self.load_osd_config()

    def _add_sensor_row(self, layout, comp_id, desc, placeholder):
        row = QHBoxLayout()
        chk = QCheckBox(desc)
        chk.setToolTip(comp_id)
        txt_name = QLineEdit()
        txt_name.setPlaceholderText(placeholder)

        chk.toggled.connect(self.set_dirty)
        txt_name.textChanged.connect(self.set_dirty)

        row.addWidget(chk, stretch=2)
        row.addWidget(txt_name, stretch=3)
        layout.addLayout(row)

        self.osd_items[comp_id] = {"chk": chk, "txt": txt_name}

    def set_dirty(self):
        self.btn_save.setEnabled(True)

    def update_aesthetic(self):
        self.set_dirty()
        opacity_percent = self.slider_opacity.value()
        real_opacity = int(opacity_percent * 2.55) # Conversione per il back-end
        max_rows = self.spin_max_rows.value()
        self.lbl_opacity_val.setText(f"{opacity_percent} %")
        self.main_window.osd_window.set_customization(opacity=real_opacity, max_rows=max_rows)

        conf = global_config.get("osd_config", {})
        conf["opacity"] = real_opacity
        conf["max_rows"] = max_rows
        global_config["osd_config"] = conf

    def pick_color(self, target):
        color = QColorDialog.getColor(Qt.white, self, T("select_color"))
        if color.isValid():
            self.set_dirty()
            hex_c = color.name()
            conf = global_config.get("osd_config", {})
            style_preview = f"background-color: {hex_c}; border: 1px solid #45475a; border-radius: 4px;"

            if target == "c_names":
                self.lbl_preview_names.setStyleSheet(style_preview)
                self.main_window.osd_window.set_customization(c_names=hex_c)
                conf["color_names"] = hex_c
            elif target == "c_values":
                self.lbl_preview_values.setStyleSheet(style_preview)
                self.main_window.osd_window.set_customization(c_values=hex_c)
                conf["color_values"] = hex_c
            elif target == "c_badges":
                self.lbl_preview_badges.setStyleSheet(style_preview)
                self.main_window.osd_window.set_customization(c_badges=hex_c)
                conf["color_badges"] = hex_c
            global_config["osd_config"] = conf

    def pick_font(self):
        current_font = self.main_window.osd_window.custom_font or QFont()
        ok, font = QFontDialog.getFont(current_font, self)
        if ok:
            self.set_dirty()
            self.main_window.osd_window.set_customization(font=font)
            self.lbl_current_font.setText(f"Font: {font.family()}")

            conf = global_config.get("osd_config", {})
            conf["font_family"] = font.family()
            conf["font_size"] = font.pointSize()
            conf["font_bold"] = font.bold()
            conf["font_italic"] = font.italic()
            global_config["osd_config"] = conf

    def save_osd_config(self):
        conf = global_config.get("osd_config", {})
        for comp_id, widgets in self.osd_items.items():
            conf[comp_id] = {
                "enabled": widgets["chk"].isChecked(),
                "custom_name": widgets["txt"].text().strip()
            }
        global_config["osd_config"] = conf
        save_config(global_config)
        self.btn_save.setEnabled(False)
        QMessageBox.information(self, "OSD", T("osd_saved_msg"))

    def load_osd_config(self):
        conf = global_config.get("osd_config", {})

        for comp_id, widgets in self.osd_items.items():
            saved = conf.get(comp_id, {})
            default_state = True if comp_id.startswith("ch_") else False
            widgets["chk"].blockSignals(True); widgets["chk"].setChecked(saved.get("enabled", default_state)); widgets["chk"].blockSignals(False)
            widgets["txt"].blockSignals(True); widgets["txt"].setText(saved.get("custom_name", "")); widgets["txt"].blockSignals(False)

        opacity = conf.get("opacity", 220)
        opacity_percent = int(opacity / 2.55)
        self.slider_opacity.blockSignals(True); self.slider_opacity.setValue(opacity_percent); self.slider_opacity.blockSignals(False)
        self.lbl_opacity_val.setText(f"{opacity_percent} %")

        max_rows = conf.get("max_rows", 8)
        self.spin_max_rows.blockSignals(True); self.spin_max_rows.setValue(max_rows); self.spin_max_rows.blockSignals(False)

        c_names = conf.get("color_names", "#cdd6f4")
        self.lbl_preview_names.setStyleSheet(f"background-color: {c_names}; border: 1px solid #45475a; border-radius: 4px;")

        c_values = conf.get("color_values", "#00e5ff")
        self.lbl_preview_values.setStyleSheet(f"background-color: {c_values}; border: 1px solid #45475a; border-radius: 4px;")

        c_badges = conf.get("color_badges", "#00e5ff")
        self.lbl_preview_badges.setStyleSheet(f"background-color: {c_badges}; border: 1px solid #45475a; border-radius: 4px;")

        font_family = conf.get("font_family")
        custom_font = None
        if font_family:
            self.lbl_current_font.setText(f"Font: {font_family}")
            custom_font = QFont(font_family)
            if "font_size" in conf: custom_font.setPointSize(conf["font_size"])
            if "font_bold" in conf: custom_font.setBold(conf["font_bold"])
            if "font_italic" in conf: custom_font.setItalic(conf["font_italic"])

        self.main_window.osd_window.set_customization(
            opacity=opacity, c_names=c_names, c_values=c_values,
            c_badges=c_badges, font=custom_font, max_rows=max_rows
        )

class SettingsTabWidget(QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        layout = QVBoxLayout(self)

        lbl_title = QLabel(f"⚙️ {T('tab_settings')}")
        lbl_title.setStyleSheet("font-size: 22px; color: #00e5ff; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_title)

        # GRUPPO SISTEMA
        group_sys = QGroupBox(T("set_sys_pref"))
        sys_layout = QVBoxLayout(group_sys)

        # Lingua
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel(T("set_lang")))
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["it", "en", "de", "fr", "es"])
        self.combo_lang.setCurrentText(global_config.get("lang", "it"))
        self.combo_lang.currentTextChanged.connect(self.main_window.change_language)
        lang_row.addWidget(self.combo_lang)
        lang_row.addStretch()
        sys_layout.addLayout(lang_row)

        # --- AGGIUNTA SLIDER OPACITÀ ---
        sys_layout.addSpacing(15)
        opac_row = QHBoxLayout()
        lbl_opac = QLabel(T("ui_opacity"))
        lbl_opac.setStyleSheet("color: #00e5ff; font-weight: bold;")

        self.slider_window_opac = QSlider(Qt.Horizontal)
        self.slider_window_opac.setRange(15, 100) # Minimo 15% per non far sparire la finestra
        saved_opac = global_config.get("window_opacity", 180)
        saved_opac_percent = int(saved_opac / 2.55) # Converte in percentuale
        self.slider_window_opac.setValue(saved_opac_percent)

        self.lbl_window_opac_val = QLabel(f"{saved_opac_percent} %")
        self.lbl_window_opac_val.setStyleSheet("color: #a6adc8; font-weight: bold;")

        self.slider_window_opac.valueChanged.connect(self.change_ui_opacity)

        opac_row.addWidget(lbl_opac)
        opac_row.addWidget(self.slider_window_opac)
        opac_row.addWidget(self.lbl_window_opac_val)
        sys_layout.addLayout(opac_row)

        # Checkbox varie
        self.chk_close_tray = QCheckBox(T("close_to_tray"))
        self.chk_close_tray.setChecked(global_config.get("close_to_tray", True))
        self.chk_close_tray.toggled.connect(self.toggle_close_tray)

        sys_layout.addWidget(self.main_window.chk_autostart)
        sys_layout.addWidget(self.main_window.chk_minimized)
        sys_layout.addWidget(self.chk_close_tray)

        layout.addWidget(group_sys)
        layout.addStretch()

    def toggle_units(self, checked):
        global_config["use_fahrenheit"] = checked
        save_config(global_config)

    def change_ui_opacity(self, value):
        self.lbl_window_opac_val.setText(f"{value} %")
        real_opacity = int(value * 2.55)

        global_config["window_opacity"] = real_opacity
        save_config(global_config)

        from main import get_dynamic_style
        self.main_window.setStyleSheet(get_dynamic_style(real_opacity))

    def toggle_close_tray(self, checked):
        global_config["close_to_tray"] = checked
        save_config(global_config)


class GuideTabWidget(QWidget):
    """Manuale tecnico integrato per le funzioni avanzate."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        lbl_title = QLabel(f"📖 {T('tab_guide')}")
        lbl_title.setStyleSheet("font-size: 22px; color: #00e5ff; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QLabel()
        content.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        content.setWordWrap(True)
        content.setTextFormat(Qt.RichText)

        content.setText(get_guide_text())

        content.setStyleSheet("""
            QLabel {
                background-color: rgba(30, 30, 30, 160);
                border: 1px solid #333333;
                border-radius: 8px;
                padding: 25px;
                font-size: 14px;
                line-height: 1.6;
                color: #e0e0e0;
            }
        """)
        scroll.setWidget(content)
        layout.addWidget(scroll)

class HardwareTabWidget(QWidget):
    """Tab per la configurazione fisica dei canali: Potenza Minima e Avvio Rapido."""
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window # <--- Memorizza il riferimento nativo
        layout = QVBoxLayout(self)

        lbl_title = QLabel(f"🔌 {T('tab_hw_channels')}")
        lbl_title.setStyleSheet("font-size: 22px; color: #00e5ff; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_title)

        info_txt = QLabel(T("hw_channels_info"))
        info_txt.setWordWrap(True)
        info_txt.setStyleSheet("color: #a6adc8; margin-bottom: 15px; font-size: 13px;")
        layout.addWidget(info_txt)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        container = QWidget()
        scroll.setWidget(container)
        self.channels_layout = QVBoxLayout(container)

        self.hw_widgets = {}

        for i in range(1, 5):
            ch_name = global_config["channels_names"].get(str(i), f"{T('channel')} {i}")
            group = QGroupBox(f"{ch_name}")
            group.setStyleSheet("QGroupBox { font-weight: bold; color: #cdd6f4; }")

            glayout = QFormLayout(group)
            glayout.setContentsMargins(15, 15, 15, 15)
            glayout.setSpacing(15)

            # --- 0. Abilitazione Canale ---
            box_enable = QHBoxLayout()
            chk_enable = QCheckBox(T("hw_enable_ch").format(ch=ch_name))
            chk_enable.setStyleSheet("color: #00e5ff; font-weight: bold; font-size: 14px;")
            box_enable.addWidget(chk_enable)
            box_enable.addStretch()

            # --- 1. Segnale di Controllo ---
            box_mode = QHBoxLayout()
            combo_dc_pwm = QComboBox()
            combo_dc_pwm.addItems(["PWM", "DC"])
            combo_dc_pwm.setFixedWidth(80)
            combo_dc_pwm.setCursor(Qt.PointingHandCursor)
            box_mode.addWidget(QLabel(T("hw_ctrl_mode")))
            box_mode.addWidget(combo_dc_pwm)
            box_mode.addStretch()

            # --- 2. Slider Potenza Minima ---
            box_min_power = QHBoxLayout()
            slider_min_power = QSlider(Qt.Horizontal)
            slider_min_power.setRange(0, 50)
            val_min_power = QLabel("0 %")
            val_min_power.setFixedWidth(40)
            val_min_power.setStyleSheet("font-weight: bold; color: #00e5ff;")
            slider_min_power.valueChanged.connect(lambda v, lbl=val_min_power: lbl.setText(f"{v} %"))
            box_min_power.addWidget(slider_min_power)
            box_min_power.addWidget(val_min_power)

            # --- 3. Start Boost ---
            box_boost = QHBoxLayout()
            chk_boost = QCheckBox(T("hw_start_boost"))
            chk_boost.setToolTip(T("hw_boost_tooltip"))
            chk_boost.setStyleSheet("font-size: 13px;")

            spin_boost_time = QDoubleSpinBox()
            spin_boost_time.setRange(0.1, 5.0)
            spin_boost_time.setSingleStep(0.1)
            spin_boost_time.setDecimals(1)
            spin_boost_time.setSuffix(" s")
            spin_boost_time.setEnabled(False)

            chk_boost.toggled.connect(spin_boost_time.setEnabled)
            box_boost.addWidget(chk_boost)
            box_boost.addSpacing(15)
            box_boost.addWidget(QLabel(T("hw_boost_time")))
            box_boost.addWidget(spin_boost_time)
            box_boost.addStretch()

            # Assemblaggio in ordine esatto
            glayout.addRow("", box_enable)
            glayout.addRow("", box_mode)
            glayout.addRow(T("hw_min_power"), box_min_power)
            glayout.addRow("", box_boost)

            # Segnali
            chk_enable.toggled.connect(self.set_dirty)
            combo_dc_pwm.currentTextChanged.connect(self.set_dirty)
            slider_min_power.valueChanged.connect(self.set_dirty)
            chk_boost.toggled.connect(self.set_dirty)
            spin_boost_time.valueChanged.connect(self.set_dirty)

            self.hw_widgets[str(i)] = {
                "chk_enable": chk_enable,
                "combo_dc_pwm": combo_dc_pwm,
                "slider_min_power": slider_min_power,
                "val_min_power": val_min_power,
                "chk_boost": chk_boost,
                "spin_boost_time": spin_boost_time
            }

            self.channels_layout.addWidget(group)

        self.channels_layout.addStretch()
        layout.addWidget(scroll)

        self.btn_save_hw = QPushButton(T("hw_save_btn"))
        self.btn_save_hw.setObjectName("ActionBtn")

        self.btn_save_hw.setEnabled(False)
        self.btn_save_hw.clicked.connect(self.save_hardware_config)
        layout.addWidget(self.btn_save_hw)

        self.load_hardware_config()

    def set_dirty(self):
        self.btn_save_hw.setEnabled(True)

    def save_hardware_config(self):
        hw_config = {}
        for ch_id, widgets in self.hw_widgets.items():
            selected_mode = widgets["combo_dc_pwm"].currentText()
            hw_config[ch_id] = {
                "enabled": widgets["chk_enable"].isChecked(),
                "ctrl_mode": selected_mode,
                "min_power": widgets["slider_min_power"].value(),
                "boost_en": widgets["chk_boost"].isChecked(),
                "boost_time": widgets["spin_boost_time"].value()
            }

            try:
                if hasattr(self.main_window, 'engine'):
                    self.main_window.engine.set_channel_mode_hid(int(ch_id), selected_mode)
            except Exception as e:
                print(f"Errore USB HID: {e}")

        global_config["hardware_channels"] = hw_config
        save_config(global_config)

        self.btn_save_hw.setEnabled(False)
        QMessageBox.information(self, T("tab_hw_channels"), T("hw_saved_msg"))

    def load_hardware_config(self):
        hw_config = global_config.get("hardware_channels", {})

        for ch_id, widgets in self.hw_widgets.items():
            saved = hw_config.get(ch_id, {})

            en = saved.get("enabled", True)
            widgets["chk_enable"].blockSignals(True)
            widgets["chk_enable"].setChecked(en)
            widgets["chk_enable"].blockSignals(False)

            mode = saved.get("ctrl_mode", "PWM")
            widgets["combo_dc_pwm"].blockSignals(True)
            widgets["combo_dc_pwm"].setCurrentText(mode)
            widgets["combo_dc_pwm"].blockSignals(False)

            val = saved.get("min_power", 0)
            widgets["slider_min_power"].blockSignals(True)
            widgets["slider_min_power"].setValue(val)
            widgets["slider_min_power"].blockSignals(False)
            widgets["val_min_power"].setText(f"{val} %")

            boost = saved.get("boost_en", False)
            widgets["chk_boost"].blockSignals(True)
            widgets["chk_boost"].setChecked(boost)
            widgets["chk_boost"].blockSignals(False)

            b_time = saved.get("boost_time", 1.0)
            widgets["spin_boost_time"].blockSignals(True)
            widgets["spin_boost_time"].setValue(b_time)
            widgets["spin_boost_time"].setEnabled(boost)
            widgets["spin_boost_time"].blockSignals(False)

