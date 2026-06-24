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
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QCursor

from config_manager import global_config, save_config
from i18n import T
from ui_widgets import format_temp, SparklineWidget, PWMFillBar
from guide_texts import get_guide_text

FLOW_PRESETS = {
    "User defined": {},
    "Digmesa 5.6 mm (53061)": {
        "Water": {"N/A": 256},
        "DP Ultra": {"N/A": 262}
    },
    "Digmesa 3.3 mm (53024)": {
        "Water": {"N/A": 509},
        "DP Ultra": {"N/A": 522}
    },
    "Aqua Computer high flow (53068)": {
        "Water": {"Inner diameter <= 7mm": 159, "Inner diameter > 7mm": 153},
        "DP Ultra": {"Inner diameter <= 7mm": 163, "Inner diameter > 7mm": 157}
    },
    "Aqua Computer high flow LT (53291)": {
        "Water": {"Inner diameter <= 7mm": 173, "Inner diameter > 7mm": 164},
        "DP Ultra": {"Inner diameter <= 7mm": 177, "Inner diameter > 7mm": 167}
    },
    "Aqua Computer high flow 2 (53292)": {
        "Water": {"Inner diameter <= 7mm": 148, "Inner diameter > 7mm": 144},
        "DP Ultra": {"Inner diameter <= 7mm": 151, "Inner diameter > 7mm": 147}
    }
}

class DashboardTabWidget(QWidget):
    """Tab visuale informativo avanzato: Storico, Delta T e Carichi PWM. Layout Responsivo."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Header layout: Titolo, Selettore Profilo, Pulsante Ripristino
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignVCenter)

        lbl_title = QLabel(f"📊 {T('tab_dash')}")
        lbl_title.setStyleSheet("font-size: 24px; color: #00e5ff; font-weight: bold;")
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

        # ------------------------------
        # COSTRUZIONE SEZIONI DINAMICHE
        # ------------------------------

        # Sensori Virtuali
        self.lbl_virt = QLabel(f"✨ {T('dash_virt_sensors')}")
        self.lbl_virt.setStyleSheet("font-size: 16px; color: #cdd6f4; font-weight: bold; margin-top: 15px;")
        self.grp_virt = QWidget()
        self.lay_virt = QGridLayout(self.grp_virt)
        self.lay_virt.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.lbl_virt.hide()
        self.grp_virt.hide()

        # Sensori di Sistema
        self.lbl_sys = QLabel(f"💻 {T('dash_sys_sensors')}")
        self.lbl_sys.setStyleSheet("font-size: 16px; color: #cdd6f4; font-weight: bold; margin-top: 15px;")
        self.grp_sys = QWidget()
        self.lay_sys = QGridLayout(self.grp_sys)
        self.lay_sys.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Sensori di Flusso
        self.lbl_flow = QLabel(f"🌀 {T('hw_flow_sensors_title')}")
        self.lbl_flow.setStyleSheet("font-size: 16px; color: #00e5ff; font-weight: bold; margin-top: 15px;")
        self.grp_flow = QWidget()
        self.lay_flow = QGridLayout(self.grp_flow)
        self.lay_flow.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.lbl_flow.hide()
        self.grp_flow.hide()

        # Uscite 12V
        self.lbl_fans = QLabel(f"⚡ {T('dash_12v_out')}")
        self.lbl_fans.setStyleSheet("font-size: 16px; color: #f9e2af; font-weight: bold; margin-top: 15px;")
        self.grp_fans = QWidget()
        self.lay_fans = QGridLayout(self.grp_fans)
        self.lay_fans.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Sensori Aquaero
        self.lbl_aqua = QLabel(f"🌡️ {T('dash_aqua_sensors')}")
        self.lbl_aqua.setStyleSheet("font-size: 16px; color: #f38ba8; font-weight: bold; margin-top: 15px;")
        self.grp_aqua = QWidget()
        self.lay_aqua = QGridLayout(self.grp_aqua)
        self.lay_aqua.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.main_layout.addWidget(self.lbl_virt)
        self.main_layout.addWidget(self.grp_virt)
        self.main_layout.addWidget(self.lbl_sys)
        self.main_layout.addWidget(self.grp_sys)
        self.main_layout.addWidget(self.lbl_flow)
        self.main_layout.addWidget(self.grp_flow)
        self.main_layout.addWidget(self.lbl_fans)
        self.main_layout.addWidget(self.grp_fans)
        self.main_layout.addWidget(self.lbl_aqua)
        self.main_layout.addWidget(self.grp_aqua)
        self.main_layout.addStretch()

        layout.addWidget(scroll)

    def change_active_profile(self, profile_name):
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
        self._clear_layout(self.lay_flow)
        self._clear_layout(self.lay_fans)
        self._clear_layout(self.lay_aqua)

        # Calcolo Dinamico delle colonne in base alla larghezza della finestra
        # Considerando una card larga in media ~300px + i margini
        available_width = self.width()
        num_cols = max(1, available_width // 310)

        col_virt, row_virt = 0, 0
        col_sys, row_sys = 0, 0
        col_flow, row_flow = 0, 0
        col_fans, row_fans = 0, 0
        col_aqua, row_aqua = 0, 0

        hidden = global_config.get("hidden_sensors", [])
        histories = data.get("history", {})

        # 1. Sensori Virtuali (Delta T)
        virt_data = data.get('virtuals', {})
        if virt_data:
            self.lbl_virt.show()
            self.grp_virt.show()
            for v_id, val in virt_data.items():
                if v_id in hidden: continue
                name = global_config.get("sensors", {}).get(v_id, v_id)
                hist = histories.get(v_id, [])
                self._add_dash_card(self.lay_virt, name, format_temp(val), "🧮", row_virt, col_virt, v_id, history_data=hist)
                col_virt += 1
                if col_virt >= num_cols: col_virt = 0; row_virt += 1
        else:
            self.lbl_virt.hide()
            self.grp_virt.hide()

        # 2. Sistema
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
            if col_sys >= num_cols: col_sys = 0; row_sys += 1

        # 3. Sensori di Flusso
        flow_data = data.get('flows', {})
        flow_config = global_config.get("flow_sensors", {})

        has_active_flows = False
        for flow_id, val in flow_data.items():
            conf = flow_config.get(str(flow_id), {})
            if not conf.get("enabled", False):
                continue

            has_active_flows = True
            s_id = f"flow_rate_{flow_id}"

            if s_id in hidden: continue

            hist = histories.get(s_id, [])
            self._add_dash_card(self.lay_flow, T("hw_flow_sensor_num").format(i=flow_id), f"{val:.1f} L/h", "🌀", row_flow, col_flow, s_id, history_data=hist)

            col_flow += 1
            if col_flow >= num_cols: col_flow = 0; row_flow += 1

        self.lbl_flow.setVisible(has_active_flows)
        self.grp_flow.setVisible(has_active_flows)

        # 4. Uscite Hardware (12V)
        pwm_loads = data.get('pwm_loads', {})
        volts = data.get('volts', {})
        hw_config = global_config.get("hardware_channels", {})
        for ch_id, rpm in data.get('rpms', {}).items():
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
            if col_fans >= num_cols: col_fans = 0; row_fans += 1

        # 5. Aquaero (Temperature hardware)
        for s_id, temp in data.get('temps', {}).items():
            if s_id in hidden: continue
            name = global_config["sensors"].get(s_id, s_id)
            hist = histories.get(s_id, [])

            self._add_dash_card(self.lay_aqua, name, format_temp(temp), "🌡️", row_aqua, col_aqua, s_id, history_data=hist)

            col_aqua += 1
            if col_aqua >= num_cols: col_aqua = 0; row_aqua += 1

    def _add_dash_card(self, target_layout, title, value, icon, row, col, sensor_id, history_data=None, pwm_load=None, sub_value=None):
        card = QFrame()
        # Riquadro elastico: si adatta tra 260px e 450px
        card.setMinimumWidth(260)
        card.setMaximumWidth(450)
        card.setStyleSheet("QFrame { background-color: rgba(30, 30, 30, 160); border-radius: 8px; border: 1px solid #333333; }")

        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(12, 10, 12, 10)
        c_layout.setSpacing(6)

        # Riga Superiore: Icona, Titolo, X per nascondere
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)

        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 16px; background: transparent; border: none;")

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #a6adc8; font-size: 12px; font-weight: bold; background: transparent; border: none;")

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
        lbl_val.setStyleSheet("color: #00e5ff; font-size: 20px; font-weight: bold; background: transparent; border: none;")
        c_layout.addWidget(lbl_val)

        if sub_value:
            lbl_sub = QLabel(sub_value)
            lbl_sub.setStyleSheet("color: #f9e2af; font-size: 14px; font-weight: bold; background: transparent; border: none;")
            c_layout.addWidget(lbl_sub)

        # Storico grafico
        if history_data and len(history_data) > 1:
            sparkline = SparklineWidget()
            sparkline.update_data(history_data)
            c_layout.addWidget(sparkline)

        # Carico ventole
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
        lbl_title.setStyleSheet("font-size: 24px; color: #ff3333; font-weight: bold; margin-bottom: 10px;")
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

        # ---------------------------------------------------------
        # 1. TITOLO SEZIONE 12V
        # ---------------------------------------------------------
        lbl_12v = QLabel(f"⚡ {T('dash_12v_out')}")
        lbl_12v.setStyleSheet("font-size: 16px; color: #cdd6f4; font-weight: bold; margin-top: 5px; margin-bottom: 5px;")
        sec_layout.addWidget(lbl_12v)

        for i in range(1, 5):
            ch_name = global_config["channels_names"].get(str(i), f"{T('channel')} {i}")

            lbl_ch = QLabel(ch_name)
            lbl_ch.setStyleSheet("font-size: 14px; color: #a6adc8; font-weight: bold; margin-top: 10px;")
            sec_layout.addWidget(lbl_ch)

            group = QGroupBox()
            group.setStyleSheet("QGroupBox { margin-top: 5px; padding-top: 5px; }")
            glayout = QFormLayout(group)

            box_delay_alarm = QHBoxLayout()
            lbl_delay_alarm = QLabel(T("sec_delay_alarm"))
            spin_delay_alarm = QSpinBox()
            spin_delay_alarm.setRange(0, 60)
            spin_delay_alarm.setSuffix(" s")
            box_delay_alarm.addWidget(lbl_delay_alarm)
            box_delay_alarm.addWidget(spin_delay_alarm)
            box_delay_alarm.addStretch()
            glayout.addRow("", box_delay_alarm)

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
            spin_delay_alarm.valueChanged.connect(self.set_dirty)

            self.sec_channels[str(i)] = {
                "chk_rpm": chk_rpm, "spin_rpm": spin_rpm,
                "chk_temp": chk_temp, "spin_temp": spin_temp,
                "chk_power": chk_power, "spin_power": spin_power,
                "chk_volt": chk_volt, "spin_volt": spin_volt,
                "spin_delay_alarm": spin_delay_alarm
            }
            sec_layout.addWidget(group)

        # ---------------------------------------------------------
        # 2. TITOLO SEZIONE FLUSSI
        # ---------------------------------------------------------
        lbl_flow = QLabel(f"🌀 {T('hw_flow_sensors_title')}")
        lbl_flow.setStyleSheet("font-size: 16px; color: #cdd6f4; font-weight: bold; margin-top: 15px; margin-bottom: 5px;")
        sec_layout.addWidget(lbl_flow)

        self.sec_flows = {}
        for i in range(1, 3):
            lbl_fl = QLabel(T("hw_flow_sensor_num").format(i=i))
            lbl_fl.setStyleSheet("font-size: 14px; color: #a6adc8; font-weight: bold; margin-top: 10px;")
            sec_layout.addWidget(lbl_fl)

            group_flow = QGroupBox()
            group_flow.setStyleSheet("QGroupBox { margin-top: 5px; padding-top: 5px; }")
            flayout = QFormLayout(group_flow)

            box_delay_flow = QHBoxLayout()
            lbl_delay_flow = QLabel(T("sec_delay_alarm"))
            spin_delay_flow = QSpinBox()
            spin_delay_flow.setRange(0, 60)
            spin_delay_flow.setSuffix(" s")
            box_delay_flow.addWidget(lbl_delay_flow)
            box_delay_flow.addWidget(spin_delay_flow)
            box_delay_flow.addStretch()
            flayout.addRow("", box_delay_flow)

            box_flow_alarm = QHBoxLayout()
            chk_flow_alarm = QCheckBox(T("sec_flow_alarm"))
            spin_flow_alarm = QDoubleSpinBox()
            spin_flow_alarm.setRange(0.0, 500.0)
            spin_flow_alarm.setDecimals(1)
            spin_flow_alarm.setSuffix(" L/h")
            box_flow_alarm.addWidget(chk_flow_alarm)
            box_flow_alarm.addWidget(spin_flow_alarm)
            box_flow_alarm.addStretch()
            flayout.addRow("", box_flow_alarm)

            chk_flow_alarm.toggled.connect(self.set_dirty)
            spin_flow_alarm.valueChanged.connect(self.set_dirty)
            spin_delay_flow.valueChanged.connect(self.set_dirty)

            self.sec_flows[str(i)] = {
                "chk_flow": chk_flow_alarm,
                "spin_flow": spin_flow_alarm,
                "spin_delay_flow": spin_delay_flow
            }
            sec_layout.addWidget(group_flow)

        # ---------------------------------------------------------
        # 3. AZIONI GLOBALI
        # ---------------------------------------------------------
        lbl_global = QLabel(T("sec_global"))
        lbl_global.setStyleSheet("font-size: 16px; color: #ff3333; font-weight: bold; margin-top: 15px; margin-bottom: 5px;")
        layout.addWidget(lbl_global)

        action_group = QGroupBox()
        action_group.setStyleSheet("QGroupBox { margin-top: 5px; padding-top: 5px; }")
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
        sec_config = {"channels": {}, "flows": {}, "actions": {}}

        for ch_id, widgets in self.sec_channels.items():
            sec_config["channels"][ch_id] = {
                "rpm_en": widgets["chk_rpm"].isChecked(),
                "rpm_val": widgets["spin_rpm"].value(),
                "temp_en": widgets["chk_temp"].isChecked(),
                "temp_val": widgets["spin_temp"].value(),
                "power_en": widgets["chk_power"].isChecked(),
                "power_val": widgets["spin_power"].value(),
                "volt_en": widgets["chk_volt"].isChecked(),
                "volt_val": widgets["spin_volt"].value(),
                "delay_val": widgets["spin_delay_alarm"].value()
            }

        for f_id, widgets in self.sec_flows.items():
            sec_config["flows"][f_id] = {
                "flow_en": widgets["chk_flow"].isChecked(),
                "flow_val": widgets["spin_flow"].value(),
                "delay_val": widgets["spin_delay_flow"].value()
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

        self.btn_save_sec.setText(T("saved_success"))
        self.btn_save_sec.setStyleSheet("background-color: #00e676 !important; color: #11111b !important; font-weight: bold;")
        QTimer.singleShot(2000, self.reset_save_btn_sec)

    def reset_save_btn_sec(self):
        self.btn_save_sec.setText(T("sec_save"))
        self.btn_save_sec.setStyleSheet("")


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
            widgets["spin_delay_alarm"].blockSignals(True); widgets["spin_delay_alarm"].setValue(saved.get("delay_val", 3)); widgets["spin_delay_alarm"].blockSignals(False)
            widgets["chk_volt"].blockSignals(True); widgets["chk_volt"].setChecked(saved.get("volt_en", False)); widgets["chk_volt"].blockSignals(False)
            widgets["spin_volt"].blockSignals(True); widgets["spin_volt"].setValue(saved.get("volt_val", 0.0)); widgets["spin_volt"].blockSignals(False)

        flows_config = sec_config.get("flows", {})
        for f_id, widgets in self.sec_flows.items():
            saved_f = flows_config.get(f_id, {})
            widgets["chk_flow"].blockSignals(True); widgets["chk_flow"].setChecked(saved_f.get("flow_en", False)); widgets["chk_flow"].blockSignals(False)
            widgets["spin_flow"].blockSignals(True); widgets["spin_flow"].setValue(saved_f.get("flow_val", 40.0)); widgets["spin_flow"].blockSignals(False)
            widgets["spin_delay_flow"].blockSignals(True); widgets["spin_delay_flow"].setValue(saved_f.get("delay_val", 5)); widgets["spin_delay_flow"].blockSignals(False)

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
        lbl_title.setStyleSheet("font-size: 24px; color: #00e5ff; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_title)

        info_txt = QLabel(T("osd_info"))
        info_txt.setWordWrap(True)
        info_txt.setStyleSheet("color: #a6adc8; margin-bottom: 5px; font-size: 13px;")
        layout.addWidget(info_txt)

        global_group = QGroupBox()
        global_group.setStyleSheet("QGroupBox { margin-top: 5px; padding-top: 5px; }")
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

        lbl_aesthetic = QLabel(T("osd_aesthetic"))
        lbl_aesthetic.setStyleSheet("font-size: 16px; color: #cdd6f4; font-weight: bold; margin-top: 15px; margin-bottom: 5px;")
        layout.addWidget(lbl_aesthetic)

        aesthetic_group = QGroupBox()
        aesthetic_group.setStyleSheet("QGroupBox { margin-top: 5px; padding-top: 5px; }")
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

        lbl_sensors = QLabel(T("osd_sensors_group"))
        lbl_sensors.setStyleSheet("font-size: 16px; color: #cdd6f4; font-weight: bold; margin-top: 15px; margin-bottom: 5px;")
        layout.addWidget(lbl_sensors)

        sensors_group = QGroupBox()
        sensors_group.setStyleSheet("QGroupBox { margin-top: 5px; padding-top: 5px; }")
        s_layout = QVBoxLayout(sensors_group)
        s_layout.setContentsMargins(0, 5, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        scroll.setWidget(container)
        list_layout = QVBoxLayout(container)

        self.osd_items = {}

        # Canali 12V
        for i in range(1, 5):
            comp_id = f"ch_{i}"
            desc = f"Aquaero: {T('channel')} {i}"
            placeholder = f"{T('channel')} {i}"
            self._add_sensor_row(list_layout, comp_id, desc, placeholder)

        # Flussi aggiunti qui come richiesto!
        for i in range(1, 3):
            comp_id = f"flow_{i}"
            desc = f"Aquaero: {T('hw_flow_sensor_num').format(i=i)}"
            placeholder = T('hw_flow_sensor_num').format(i=i)
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
        real_opacity = int(opacity_percent * 2.55)
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

        self.btn_save.setText(T("saved_success"))
        self.btn_save.setStyleSheet("background-color: #00e676 !important; color: #11111b !important; font-weight: bold")
        QTimer.singleShot(2000, self.reset_save_btn)

    def reset_save_btn(self):
        self.btn_save.setText(T("osd_save"))
        self.btn_save.setStyleSheet("")

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
        lbl_title.setStyleSheet("font-size: 24px; color: #00e5ff; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_title)

        lbl_sys_pref = QLabel(T("set_sys_pref"))
        lbl_sys_pref.setStyleSheet("font-size: 16px; color: #cdd6f4; font-weight: bold; margin-top: 10px; margin-bottom: 5px;")
        layout.addWidget(lbl_sys_pref)

        # GRUPPO SISTEMA
        group_sys = QGroupBox()
        group_sys.setStyleSheet("QGroupBox { margin-top: 5px; padding-top: 5px; }")
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

        # Opacità Interfaccia
        sys_layout.addSpacing(15)
        opac_row = QHBoxLayout()
        lbl_opac = QLabel(T("ui_opacity"))
        lbl_opac.setStyleSheet("color: #00e5ff; font-weight: bold;")

        self.slider_window_opac = QSlider(Qt.Horizontal)
        self.slider_window_opac.setRange(0, 100) # Range Trasparenza Interfaccia
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
        lbl_title.setStyleSheet("font-size: 24px; color: #00e5ff; font-weight: bold; margin-bottom: 10px;")
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
                background-color: rgba(35, 38, 41, 225);
                border: 1px solid rgba(255, 255, 255, 20);
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
        self.main_window = main_window
        layout = QVBoxLayout(self)

        lbl_title = QLabel(f"🔌 {T('tab_hw_channels')}")
        lbl_title.setStyleSheet("font-size: 24px; color: #00e5ff; font-weight: bold; margin-bottom: 10px;")
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

        # --- TITOLO SEZIONE 12V ---
        lbl_12v = QLabel(f"⚡ {T('dash_12v_out')}")
        lbl_12v.setStyleSheet("font-size: 16px; color: #cdd6f4; font-weight: bold; margin-top: 5px; margin-bottom: 5px;")
        self.channels_layout.addWidget(lbl_12v)

        self.hw_widgets = {}

        for i in range(1, 5):
            ch_name = global_config["channels_names"].get(str(i), f"{T('channel')} {i}")

            group = QGroupBox()
            group.setStyleSheet("QGroupBox { margin-top: 5px; padding-top: 5px; }")

            glayout = QFormLayout(group)
            glayout.setContentsMargins(15, 10, 15, 15)
            glayout.setSpacing(15)

            # --- 0. Abilitazione Canale ---
            box_enable = QHBoxLayout()
            chk_enable = QCheckBox(ch_name)
            chk_enable.setStyleSheet("color: #00e5ff; font-weight: bold; font-size: 15px;")
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
            glayout.addRow(box_enable)
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

        # --- TITOLO SEZIONE FLUSSI ---
        lbl_flow = QLabel(f"🌀 {T('hw_flow_sensors_title')}")
        lbl_flow.setStyleSheet("font-size: 16px; color: #cdd6f4; font-weight: bold; margin-top: 15px; margin-bottom: 5px;")
        self.channels_layout.addWidget(lbl_flow)

        self.flow_widgets = {}
        for i in range(1, 3):
            group_flow = QGroupBox()
            group_flow.setStyleSheet("QGroupBox { margin-top: 5px; padding-top: 5px; }")

            flayout = QFormLayout(group_flow)
            flayout.setContentsMargins(15, 10, 15, 15)
            flayout.setSpacing(10)

            # Riga 1: Spunta abilitazione
            box_flow_en = QHBoxLayout()
            chk_flow_en = QCheckBox(T("hw_flow_sensor_num").format(i=i))
            chk_flow_en.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 15px;")
            box_flow_en.addWidget(chk_flow_en)
            box_flow_en.addStretch()

            # Variabili Interfaccia
            combo_type = QComboBox()
            combo_type.addItems(list(FLOW_PRESETS.keys()))
            combo_type.setEnabled(False)

            combo_fluid = QComboBox()
            combo_fluid.addItems(["Water", "DP Ultra"])
            combo_fluid.setEnabled(False)

            combo_fitting = QComboBox()
            combo_fitting.setEnabled(False)

            spin_calib = QSpinBox()
            spin_calib.setRange(1, 3000)
            spin_calib.setSuffix(" imp/l")
            spin_calib.setEnabled(False)

            def update_ui_logic(c_type=combo_type, c_fluid=combo_fluid, c_fit=combo_fitting, spin=spin_calib):
                sensor = c_type.currentText()
                if sensor == "User defined":
                    c_fluid.setEnabled(False)
                    c_fit.setEnabled(False)
                    spin.setEnabled(True)
                else:
                    spin.setEnabled(False)
                    c_fluid.setEnabled(True)
                    fluid = c_fluid.currentText()

                    fittings = list(FLOW_PRESETS[sensor].get(fluid, {}).keys())
                    if "N/A" in fittings or not fittings:
                        c_fit.setEnabled(False)
                        c_fit.blockSignals(True)
                        c_fit.clear()
                        c_fit.addItem("N/A")
                        c_fit.blockSignals(False)
                        val = FLOW_PRESETS[sensor][fluid].get("N/A", 150)
                    else:
                        c_fit.setEnabled(True)
                        current_fit = c_fit.currentText()
                        c_fit.blockSignals(True)
                        c_fit.clear()
                        c_fit.addItems(fittings)
                        if current_fit in fittings:
                            c_fit.setCurrentText(current_fit)
                        c_fit.blockSignals(False)
                        val = FLOW_PRESETS[sensor][fluid].get(c_fit.currentText(), 150)

                    spin.setValue(val)

            combo_type.currentTextChanged.connect(lambda text, t=combo_type: update_ui_logic(c_type=t))
            combo_fluid.currentTextChanged.connect(lambda text, t=combo_type: update_ui_logic(c_type=t))
            combo_fitting.currentTextChanged.connect(lambda text, t=combo_type: update_ui_logic(c_type=t))

            chk_flow_en.toggled.connect(combo_type.setEnabled)
            chk_flow_en.toggled.connect(lambda checked, t=combo_type: update_ui_logic(c_type=t) if checked else None)

            chk_flow_en.toggled.connect(self.set_dirty)
            combo_type.currentTextChanged.connect(self.set_dirty)
            combo_fluid.currentTextChanged.connect(self.set_dirty)
            combo_fitting.currentTextChanged.connect(self.set_dirty)
            spin_calib.valueChanged.connect(self.set_dirty)

            flayout.addRow(box_flow_en)
            flayout.addRow(T("hw_flow_type"), combo_type)
            flayout.addRow(T("hw_flow_fluid"), combo_fluid)
            flayout.addRow(T("hw_flow_fitting"), combo_fitting)
            flayout.addRow(T("hw_flow_calib"), spin_calib)

            self.flow_widgets[str(i)] = {
                "chk_enable": chk_flow_en,
                "combo_type": combo_type,
                "combo_fluid": combo_fluid,
                "combo_fitting": combo_fitting,
                "spin_calib": spin_calib,
                "update_logic": update_ui_logic
            }
            self.channels_layout.addWidget(group_flow)

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
                print(f"Errore USB HID 12V: {e}")

        global_config["hardware_channels"] = hw_config

        flow_config = global_config.get("flow_sensors", {})
        for flow_id, widgets in self.flow_widgets.items():
            calib_val = widgets["spin_calib"].value()
            flow_config[flow_id] = {
                "enabled": widgets["chk_enable"].isChecked(),
                "sensor_type": widgets["combo_type"].currentText(),
                "fluid": widgets["combo_fluid"].currentText(),
                "fitting": widgets["combo_fitting"].currentText(),
                "impulses": calib_val
            }
            try:
                if widgets["chk_enable"].isChecked() and hasattr(self.main_window, 'engine'):
                    self.main_window.engine.set_flow_calibration_hid(int(flow_id), calib_val)
            except Exception as e:
                print(f"Errore USB HID Flusso: {e}")

        global_config["flow_sensors"] = flow_config
        save_config(global_config)

        self.btn_save_hw.setEnabled(False)

        self.btn_save_hw.setText(T("saved_success"))
        self.btn_save_hw.setStyleSheet("background-color: #00e676 !important; color: #11111b !important; font-weight: bold;")
        QTimer.singleShot(2000, self.reset_save_btn_hw)

    def reset_save_btn_hw(self):
        self.btn_save_hw.setText(T("hw_save_btn"))
        self.btn_save_hw.setStyleSheet("")

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

        flow_config = global_config.get("flow_sensors", {})
        for flow_id, widgets in self.flow_widgets.items():
            saved_flow = flow_config.get(flow_id, {})

            en = saved_flow.get("enabled", False)
            widgets["chk_enable"].blockSignals(True)
            widgets["chk_enable"].setChecked(en)
            widgets["chk_enable"].blockSignals(False)

            s_type = saved_flow.get("sensor_type", "User defined")
            widgets["combo_type"].blockSignals(True)
            widgets["combo_type"].setCurrentText(s_type)
            widgets["combo_type"].blockSignals(False)

            fluid = saved_flow.get("fluid", "Water")
            widgets["combo_fluid"].blockSignals(True)
            widgets["combo_fluid"].setCurrentText(fluid)
            widgets["combo_fluid"].blockSignals(False)

            fit = saved_flow.get("fitting", "N/A")
            if fit != "N/A":
                widgets["combo_fitting"].blockSignals(True)
                widgets["combo_fitting"].addItem(fit)
                widgets["combo_fitting"].setCurrentText(fit)
                widgets["combo_fitting"].blockSignals(False)

            calib = saved_flow.get("impulses", 150)
            widgets["spin_calib"].blockSignals(True)
            widgets["spin_calib"].setValue(calib)
            widgets["spin_calib"].blockSignals(False)

            widgets["combo_type"].setEnabled(en)
            if en:
                widgets["update_logic"]()
