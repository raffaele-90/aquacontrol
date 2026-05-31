import sys
import os
import stat
import subprocess
import socket
import json
import time
import threading
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QSystemTrayIcon, QMenu, QStyle,
                               QListWidget, QListWidgetItem, QStackedWidget,
                               QLabel, QPushButton, QComboBox, QLineEdit, QScrollArea,
                               QGroupBox, QCheckBox, QMessageBox, QFrame)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QAction, QIcon, QFont, QColor

# --- Importazioni Modulari ---
from config_manager import global_config, save_config, CONFIG_FILE
from i18n import T
from engine import AquaeroEngine
from osd_widget import AquaeroOSD
from ui_tabs import DashboardTabWidget, SecurityTabWidget, SettingsTabWidget, GuideTabWidget, OSDConfigTabWidget, HardwareTabWidget
from ui_widgets import ChannelControlWidget, ProcessMappingDialog, MeltdownDialog

IPC_SOCKET_PATH = "/tmp/openaquaero_osd.sock"

def get_dynamic_style(opacity_value):
    return f"""
    QMainWindow {{ background: transparent; }}

    #CentralWidget {{
        background-color: rgba(20, 20, 20, {opacity_value});
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 15);
    }}

    QWidget {{ color: #e0e0e0; font-family: system-ui, sans-serif; }}

    #SidebarContainer {{
        background-color: rgba(10, 10, 15, {min(255, opacity_value + 35)});
        border-right: 1px solid rgba(0, 229, 255, 30);
        border-top-left-radius: 12px;
        border-bottom-left-radius: 12px;
    }}

    QListWidget#Sidebar {{ background: transparent; border: none; outline: 0; }}
    QListWidget#Sidebar::item {{ padding: 12px 0px; margin: 2px 0px; }}

    QListWidget#Sidebar::item:selected {{
        background-color: rgba(0, 229, 255, 50);
        border-left: 4px solid #00e5ff;
        color: #ffffff;
    }}

    #InfoButton {{ background: transparent; border: none; color: #a6adc8; font-size: 24px; padding: 20px 0px; }}
    #InfoButton:hover {{ color: #00e5ff; }}

    QGroupBox {{
        border: 1px solid rgba(255, 255, 255, 20);
        border-radius: 8px;
        margin-top: 30px;
        background-color: rgba(45, 45, 45, {max(0, opacity_value - 50)});
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; left: 15px; padding: 0 5px; color: #00e5ff; font-size: 13px;
    }}

    QPushButton#ActionBtn {{
        background-color: #00e5ff !important; color: #11111b !important; font-size: 14px;
        font-weight: bold; border-radius: 6px; padding: 12px; border: none;
    }}
    QPushButton#ActionBtn:disabled {{ background-color: #313244 !important; color: #585b70 !important; }}

    QPushButton#SecurityBtn {{
        background-color: #ff3333 !important; color: #ffffff !important; font-size: 14px;
        font-weight: bold; border-radius: 6px; padding: 12px; border: none;
    }}
    QPushButton#SecurityBtn:disabled {{ background-color: #313244 !important; color: #585b70 !important; }}

    /* --- FIX: Separazione per compatibilità temi di sistema (es. KDE Plasma) --- */
    QLineEdit, QComboBox {{
        background-color: rgba(10, 10, 10, {min(255, opacity_value + 20)});
        border: 1px solid rgba(255, 255, 255, 20); border-radius: 4px; padding: 5px; color: #ffffff;
    }}

    QSpinBox, QDoubleSpinBox {{
        background-color: rgba(10, 10, 10, {min(255, opacity_value + 20)});
        color: #ffffff;
        border: none;
        padding: 0px;
    }}

    /* --- FIX: Scrollbar sottili a capsula --- */
    QScrollArea {{ border: none; background: transparent; }}
    QScrollArea QWidget {{ background: transparent; }}

    QScrollBar:vertical {{ background-color: rgba(30, 30, 46, 120); width: 8px; margin: 0px; border-radius: 4px; }}
    QScrollBar::handle:vertical {{ background-color: rgba(0, 229, 255, 180); min-height: 30px; border-radius: 4px; }}
    QScrollBar::handle:vertical:hover {{ background-color: #5cf0ff; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

    QScrollBar:horizontal {{ background-color: rgba(30, 30, 46, 120); height: 8px; margin: 0px; border-radius: 4px; }}
    QScrollBar::handle:horizontal {{ background-color: rgba(0, 229, 255, 180); min-width: 30px; border-radius: 4px; }}
    QScrollBar::handle:horizontal:hover {{ background-color: #5cf0ff; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}
    """

class IPCServer(QThread):
    toggle_osd_signal = Signal()
    def __init__(self):
        super().__init__() # <--- Fermati qui. Non aggiungere altro sotto questa riga.
        self.running = True
        if os.path.exists(IPC_SOCKET_PATH):
            try: os.remove(IPC_SOCKET_PATH)
            except: pass
    def run(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            s.bind(IPC_SOCKET_PATH)
            s.listen(1)
            os.chmod(IPC_SOCKET_PATH, 0o666)
        except Exception as e:
            print(f"IPC Socket error: {e}")
            return
        while self.running:
            try:
                conn, _ = s.accept()
                data = conn.recv(1024)
                if b"toggle_osd" in data:
                    self.toggle_osd_signal.emit()
                conn.close()
            except: pass
    def stop(self):
        self.running = False
        try:
            dummy = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            dummy.connect(IPC_SOCKET_PATH)
            dummy.close()
        except: pass
        self.wait()

class HardwareWorker(QThread):
    telemetry_ready = Signal(dict)
    def __init__(self, engine):
        super().__init__() # <--- Fermati qui. Non aggiungere altro sotto questa riga.
        self.engine = engine
        self.running = True
        self.active_control = True
        self.pwm_commands = {}

    def run(self):
        while self.running:
            # 1. Raccoglie la telemetria completa (inclusi voltaggi, storico e pwm_loads)
            data = self.engine.get_dashboard_telemetry()

            # 2. Applica i comandi fisici alle ventole se il controllo è attivo
            if self.active_control:
                for ch_id, pwm_val in self.pwm_commands.items():
                    self.engine.set_fan_speed(ch_id, pwm_val)

            # 3. Spedisce l'intero pacchetto dati alla UI
            self.telemetry_ready.emit(data)
            time.sleep(1)
    def stop(self):
        self.running = False
        self.wait()


class OpenAquaeroUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.engine = AquaeroEngine()
        self.setWindowTitle(T("app_title"))
        self.resize(1000, 950)
        self.updating_combo = False
        self.alarm_triggered = False

        self.autostart_dir = os.path.expanduser("~/.config/autostart")
        self.desktop_file_path = os.path.join(self.autostart_dir, "openaquaero.desktop")

        self.ipc_server = IPCServer()
        self.ipc_server.toggle_osd_signal.connect(self.toggle_osd_from_hotkey)
        self.ipc_server.start()

        self.osd_window = AquaeroOSD()
        self.osd_window.position_changed.connect(self.save_osd_position)
        if global_config.get("osd_export", False):
            self.osd_window.show()
            QTimer.singleShot(100, self.restore_osd_position)

        self.setup_tray_icon()
        self.init_settings_vars()
        self.setup_ui()

        self.hw_thread = HardwareWorker(self.engine)
        self.hw_thread.telemetry_ready.connect(self.on_telemetry_received)
        self.hw_thread.start()
        self.is_controlling = True

        self.refresh_profile_list()
        self.combo_profiles.currentIndexChanged.connect(self.load_selected_profile)
        self.load_last_profile()

        self.active_auto_profile = None
        self.pre_auto_profile = None
        self.process_timer = QTimer(self)
        self.process_timer.timeout.connect(self.check_running_processes)
        self.process_timer.start(5000)

        self.dirty_timer = QTimer(self)
        self.dirty_timer.timeout.connect(self.check_dirty_state)
        self.dirty_timer.start(500)

    def init_settings_vars(self):
        self.chk_autostart = QCheckBox(T("autostart"))
        self.chk_autostart.setStyleSheet("font-size: 13px;")
        self.chk_autostart.setChecked(os.path.exists(self.desktop_file_path))

        self.chk_minimized = QCheckBox(T("start_min"))
        self.chk_minimized.setStyleSheet("font-size: 13px;")
        self.chk_minimized.setChecked(global_config.get("autostart_min", False))
        self.chk_minimized.setEnabled(self.chk_autostart.isChecked())

        self.chk_autostart.toggled.connect(self.on_autostart_toggled)
        self.chk_minimized.toggled.connect(self.toggle_autostart)

        self.chk_autoswitch = QCheckBox(T("autoswitch"))
        self.chk_autoswitch.setStyleSheet("font-size: 13px;")
        self.chk_autoswitch.setChecked(global_config.get("autoswitch_enabled", False))
        self.chk_autoswitch.toggled.connect(lambda v: self._save_simple_config("autoswitch_enabled", v))

        self.btn_autoswitch_settings = QPushButton("⚙️")
        self.btn_autoswitch_settings.setFixedWidth(40)
        self.btn_autoswitch_settings.clicked.connect(self.open_autoswitch_settings)

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("openaquaero", self.style().standardIcon(QStyle.SP_ComputerIcon)))
        self.tray_menu = QMenu()

        self.action_toggle_osd = QAction(T("tray_toggle_osd"), self)
        self.action_toggle_osd.triggered.connect(self.toggle_osd_from_tray)
        self.tray_menu.addAction(self.action_toggle_osd)
        self.tray_menu.addSeparator()

        show_action = QAction(T("tray_show"), self)
        show_action.triggered.connect(self.showNormal)
        self.tray_menu.addAction(show_action)

        self.tray_profiles_menu = QMenu(T("tray_change_profile"), self.tray_menu)
        self.tray_menu.addMenu(self.tray_profiles_menu)
        self.tray_menu.aboutToShow.connect(self.update_tray_profiles)
        self.tray_menu.addSeparator()

        quit_action = QAction(T("tray_quit"), self)
        quit_action.triggered.connect(self.force_quit)
        self.tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_click)

    def setup_ui(self):
        # Importazione necessaria per la gestione dello spazio
        from PySide6.QtWidgets import QSizePolicy

        # 1. Widget Centrale (Sfondo trasparente)
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        main_h_layout = QHBoxLayout(central_widget)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        # 2. SIDEBAR CONTAINER (La colonna scura a sinistra)
        sidebar_container = QWidget()
        sidebar_container.setObjectName("SidebarContainer")
        sidebar_container.setFixedWidth(75)
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # 3. LISTA ICONE (Sidebar)
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")

        # LOGICA ESPANSIONE: Diciamo alla lista di occupare tutto lo spazio verticale
        self.sidebar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sidebar.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar.setFrameShape(QFrame.NoFrame)

        # Icone originali
        icons = [("📊", T("tab_dash")),
                 ("🎛️", T("fan_tab_title")),
                 ("🔌", T("tab_hw_channels")),
                 ("\u2622\uFE0E", T("sidebar_sec")),
                 ("🖥️", T("sidebar_osd")),
                 ("⚙️", T("tab_settings")),
                 ("📖", T("tab_guide"))]

        for icon_txt, tooltip in icons:
            item = QListWidgetItem(icon_txt)
            item.setFont(QFont("Arial", 22))
            item.setTextAlignment(Qt.AlignCenter)
            item.setToolTip(tooltip)
            if tooltip == T("sidebar_sec"): item.setForeground(QColor("#ff3333"))
            self.sidebar.addItem(item)

        sidebar_layout.addWidget(self.sidebar)

        # 4. TASTO INFO (In fondo alla colonna scura)
        self.btn_info_sidebar = QPushButton("ℹ️")
        self.btn_info_sidebar.setObjectName("InfoButton")
        self.btn_info_sidebar.setCursor(Qt.PointingHandCursor)
        self.btn_info_sidebar.clicked.connect(self.show_about_dialog)
        sidebar_layout.addWidget(self.btn_info_sidebar)

        # 5. CONTENUTI (STACKED WIDGET)
        self.stack = QStackedWidget()

        # Inizializziamo ogni Tab con il suo NOME CORRETTO (self.xxx)
        self.dashboard_tab = DashboardTabWidget()
        self.stack.addWidget(self.dashboard_tab)

        self.fan_page = QWidget()
        fan_layout = QVBoxLayout(self.fan_page)
        fan_layout.setContentsMargins(15, 15, 15, 15)
        self.build_fan_control_ui(fan_layout)
        self.stack.addWidget(self.fan_page)

        self.hw_channels_tab = HardwareTabWidget(self)
        self.stack.addWidget(self.hw_channels_tab)

        self.security_tab = SecurityTabWidget()
        self.stack.addWidget(self.security_tab)

        self.osd_tab = OSDConfigTabWidget(self)
        self.stack.addWidget(self.osd_tab)

        self.settings_tab = SettingsTabWidget(self)
        self.stack.addWidget(self.settings_tab)

        self.guide_tab = GuideTabWidget()
        self.stack.addWidget(self.guide_tab)

        # 6. ASSEMBLAGGIO FINALE
        main_h_layout.addWidget(sidebar_container)
        main_h_layout.addWidget(self.stack)

        # Connessioni logiche
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

        # 7. APPLICAZIONE STILE E OPACITÀ
        initial_opacity = global_config.get("window_opacity", 180)
        self.setStyleSheet(get_dynamic_style(initial_opacity))

    def build_fan_control_ui(self, layout):
        lbl_main_title = QLabel(T("fan_tab_title"))
        lbl_main_title.setStyleSheet("font-size: 22px; color: #00e5ff; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(lbl_main_title)

        top_bar = QHBoxLayout()
        profile_group = QGroupBox(T("profile_group"))
        profile_layout = QHBoxLayout()
        self.combo_profiles = QComboBox()

        self.btn_save_current = QPushButton("💾")
        self.btn_save_current.setFixedWidth(40)
        self.btn_save_current.clicked.connect(self.save_current_profile)

        self.btn_delete_profile = QPushButton("✖")
        self.btn_delete_profile.setFixedWidth(40)
        self.btn_delete_profile.clicked.connect(self.delete_current_profile)

        self.txt_new_profile = QLineEdit()
        self.txt_new_profile.setPlaceholderText(T("placeholder"))
        self.btn_save_profile = QPushButton(T("save_btn"))
        self.btn_save_profile.setStyleSheet("background-color: #00e5ff; color: #11111b;")
        self.btn_save_profile.clicked.connect(self.save_new_profile)

        profile_layout.addWidget(self.combo_profiles)
        profile_layout.addWidget(self.btn_save_current)
        profile_layout.addWidget(self.btn_delete_profile)
        profile_layout.addWidget(QLabel("   |   "))
        profile_layout.addWidget(self.txt_new_profile)
        profile_layout.addWidget(self.btn_save_profile)
        profile_group.setLayout(profile_layout)
        top_bar.addWidget(profile_group)
        layout.addLayout(top_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        scroll.setWidget(container)
        self.channels_layout = QVBoxLayout(container)
        layout.addWidget(scroll)

        self.channels = []
        for i in range(1, 5):
            cw = ChannelControlWidget(i, self.engine)
            self.channels_layout.addWidget(cw)
            self.channels.append(cw)

        bottom_controls = QHBoxLayout()
        self.btn_master = QPushButton(T("suspend_btn"))
        self.btn_master.setCheckable(True)
        self.btn_master.setChecked(True)
        self.btn_master.setStyleSheet("background-color: #00e5ff; color: #11111b; border: none; padding: 12px; font-size: 15px; font-weight: bold; border-radius: 6px;")
        self.btn_master.toggled.connect(self.toggle_master)
        bottom_controls.addWidget(self.btn_master)
        layout.addLayout(bottom_controls)

    def on_telemetry_received(self, data):
        temps = data.get('temps', {})
        rpms = data.get('rpms', {})
        volts = data.get('volts', {}) # <--- AGGIUNTO: Estrazione sicura dei voltaggi
        sys_data = data.get('system', {})
        new_pwm_commands = {}
        osd_data = []

        self.dashboard_tab.update_telemetry(data)
        osd_conf = global_config.get("osd_config", {})
        # ... il resto della funzione scende invariato

        if getattr(self, 'chk_osd', None) and self.chk_osd.isChecked():
            for s_id, conf in osd_conf.items():
                if s_id.startswith("sys_") and conf.get("enabled"):
                    val = sys_data.get(s_id)
                    if val is not None:
                        custom_name = conf.get("custom_name")
                        default_name = self.engine.sys_sensors_meta.get(s_id, {}).get('label', s_id)
                        name = custom_name if custom_name else default_name
                        s_type = self.engine.sys_sensors_meta.get(s_id, {}).get('type', 'temp')
                        if s_type == 'load': osd_data.append({'name': name, 'pwm': int(val)})
                        else: osd_data.append({'name': name, 'temp': val})

        hw_config = global_config.get("hardware_channels", {})

        for ch in self.channels:
            ch_conf = hw_config.get(str(ch.channel_id), {})
            is_enabled = ch_conf.get("enabled", True)

            ch.setVisible(is_enabled)

            if not is_enabled:
                # Se è spento, forza a 0 il comando e salta i calcoli
                if self.is_controlling: new_pwm_commands[ch.channel_id] = 0
                continue

            pwm_val = ch.process_telemetry(temps, rpms, volts, self.is_controlling)
            if pwm_val is not None: new_pwm_commands[ch.channel_id] = pwm_val

            if getattr(self, 'chk_osd', None) and self.chk_osd.isChecked():

                ch_id = f"ch_{ch.channel_id}"
                ch_conf = osd_conf.get(ch_id, {"enabled": True, "custom_name": ""})
                if ch_conf.get("enabled", True):
                    sensor_id = ch.combo_sensors.currentData()
                    t = temps.get(sensor_id) if sensor_id else 0.0
                    if t is None: t = 0.0
                    r = rpms.get(ch.channel_id, 0)
                    p = int((pwm_val / 255.0) * 100) if pwm_val is not None else 0
                    ch_name = ch_conf.get("custom_name") or ch.edit_name.text()
                    osd_data.append({'name': ch_name, 'temp': t, 'rpm': r, 'pwm': p})

        if self.is_controlling:
            self.hw_thread.pwm_commands = new_pwm_commands

        if getattr(self, 'chk_osd', None) and self.chk_osd.isChecked() and osd_data:
            self.osd_window.update_data(osd_data)
            self.restore_osd_position()

        self.check_security_alarms(temps, rpms, new_pwm_commands)

    def check_security_alarms(self, temps, rpms, pwm_commands):
        sec_config = global_config.get("security", {})
        if not sec_config: return

        channels_sec = sec_config.get("channels", {})
        actions_sec = sec_config.get("actions", {})
        alarm_triggered_this_tick = False
        alarm_messages = []

        for ch in self.channels:
            ch_id_str = str(ch.channel_id)
            c_sec = channels_sec.get(ch_id_str, {})

            # Ottieni la potenza fisica (0-255) che stiamo inviando in questo istante
            current_pwm = pwm_commands.get(ch.channel_id, 0) if self.is_controlling else 0
            current_pwm_percent = int((current_pwm / 255.0) * 100)

            # FIX: Se il software ha deliberatamente spento la ventola (0%), bypassiamo gli allarmi di blocco di questo canale
            if self.is_controlling and current_pwm_percent == 0:
                continue

            if c_sec.get("rpm_en"):
                current_rpm = rpms.get(ch.channel_id, 0)
                if current_rpm <= c_sec.get("rpm_val", 0):
                    alarm_triggered_this_tick = True
                    alarm_messages.append(f"Canale {ch_id_str}: RPM critici ({current_rpm} RPM)")

            if c_sec.get("temp_en"):
                sensor_id = ch.combo_sensors.currentData()
                current_temp = temps.get(sensor_id)
                if current_temp is not None and current_temp >= c_sec.get("temp_val", 999):
                    alarm_triggered_this_tick = True
                    alarm_messages.append(f"Canale {ch_id_str}: Temperatura critica ({current_temp:.1f} °C)")

            if c_sec.get("power_en") and self.is_controlling:
                if current_pwm_percent <= c_sec.get("power_val", 0):
                    alarm_triggered_this_tick = True
                    alarm_messages.append(f"Canale {ch_id_str}: Crollo di Potenza ({current_pwm_percent}%)")

        if alarm_triggered_this_tick and not self.alarm_triggered:
            self.alarm_triggered = True
            if actions_sec.get("osd_en") and self.osd_window.isVisible():
                self.osd_window.bg_widget.setStyleSheet("background-color: rgba(200, 0, 0, 235); border-radius: 12px; border: 3px solid #ffffff;")
            if actions_sec.get("sound_en"):
                default_alarm = "/usr/share/sounds/freedesktop/stereo/suspend-error.oga"
                fallback_alarm = "/usr/share/sounds/freedesktop/stereo/dialog-error.oga"
                if os.path.exists(default_alarm): subprocess.Popen(["paplay", default_alarm])
                elif os.path.exists(fallback_alarm): subprocess.Popen(["paplay", fallback_alarm])
                else: subprocess.Popen(["paplay", "/usr/share/sounds/ocean/stereo/dialog-warning.oga"])

            self.tray_icon.showMessage("🚨 EMERGENZA LOOP 🚨", " | ".join(alarm_messages), QSystemTrayIcon.Critical, 5000)

            if not hasattr(self, 'meltdown_dialog') or not self.meltdown_dialog.isVisible():
                self.meltdown_dialog = MeltdownDialog(alarm_messages, actions_sec, None)
                self.meltdown_dialog.show()

            # --- Esecuzione Logica di Emergenza ---
            def execute_emergency_sequence():
                cmd_enabled = actions_sec.get("cmd_en")
                cmd_text = actions_sec.get("cmd_val", "").strip()
                shutdown_enabled = actions_sec.get("shutdown_en")
                delay_seconds = actions_sec.get("delay_val", 0)

                # Se l'utente ha impostato un comando personalizzato, lo lanciamo subito in background
                if cmd_enabled and cmd_text:
                    try:
                        subprocess.Popen(cmd_text, shell=True)
                    except Exception as e:
                        print(f"Errore comando personalizzato: {e}")

                # Se lo spegnimento è attivo, chiamiamo il motore passandogli anche il ritardo (delay_seconds)
                if shutdown_enabled:
                    trigger_reason = alarm_messages[0] if alarm_messages else "Unknown"

                    # NOTA: Ora passiamo 3 parametri. Il motore userà systemd per gestire il timer in modo sicuro
                    self.engine.trigger_emergency_shutdown(trigger_reason, 99.9, delay_seconds)

            emergency_thread = threading.Thread(target=execute_emergency_sequence)
            emergency_thread.daemon = True
            emergency_thread.start()

        elif not alarm_triggered_this_tick and self.alarm_triggered:
            self.alarm_triggered = False
            if self.osd_window.isVisible():
                self.osd_window.apply_scaling()

    def check_dirty_state(self):
        p_name = self.combo_profiles.currentText()
        if not p_name or p_name not in global_config["profiles"]: return
        if p_name == "Default":
            self.btn_delete_profile.setEnabled(False)
            self.btn_delete_profile.setStyleSheet("background-color: #313244; color: #585b70; font-size: 16px; padding: 5px;")
        else:
            self.btn_delete_profile.setEnabled(True)
            self.btn_delete_profile.setStyleSheet("background-color: #313244; color: #ff3333; font-size: 16px; font-weight: bold; padding: 5px;")

        saved_profile_data = global_config["profiles"][p_name]
        current_profile_data = {str(ch.channel_id): ch.get_state() for ch in self.channels}
        current_safe = json.loads(json.dumps(current_profile_data))
        is_dirty = (saved_profile_data != current_safe)

        self.btn_save_current.setEnabled(is_dirty)
        if is_dirty: self.btn_save_current.setStyleSheet("background-color: #00e5ff; color: #11111b; font-size: 16px; padding: 5px;")
        else: self.btn_save_current.setStyleSheet("background-color: #313244; color: #6c7086; font-size: 16px; padding: 5px;")

    def save_current_profile(self):
        p_name = self.combo_profiles.currentText()
        if not p_name: return
        global_config["profiles"][p_name] = {str(ch.channel_id): ch.get_state() for ch in self.channels}
        save_config(global_config)
        self.check_dirty_state()

    def delete_current_profile(self):
        p_name = self.combo_profiles.currentText()
        if p_name == "Default": return
        reply = QMessageBox.question(self, T("dialog_del_title"), T("dialog_del_msg").format(p=p_name), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del global_config["profiles"][p_name]
            global_config["last_profile"] = "Default"
            save_config(global_config)
            self.refresh_profile_list()
            self.updating_combo = True
            self.combo_profiles.setCurrentText("Default")
            self.updating_combo = False
            self.load_selected_profile()

    def refresh_profile_list(self):
        self.updating_combo = True
        self.combo_profiles.clear()
        self.combo_profiles.addItems(global_config["profiles"].keys())
        self.updating_combo = False

    def save_new_profile(self):
        p_name = self.txt_new_profile.text().strip()
        if not p_name: return
        if p_name == "Default":
            QMessageBox.warning(self, T("dialog_warn_title"), T("dialog_warn_default"))
            return
        global_config["profiles"][p_name] = {str(ch.channel_id): ch.get_state() for ch in self.channels}
        global_config["last_profile"] = p_name
        save_config(global_config)
        self.refresh_profile_list()
        self.updating_combo = True
        self.combo_profiles.setCurrentText(p_name)
        self.updating_combo = False
        self.txt_new_profile.clear()
        self.check_dirty_state()

    def load_selected_profile(self, index=None):
        if self.updating_combo: return
        p_name = self.combo_profiles.currentText()
        if p_name in global_config["profiles"]:
            profile_data = global_config["profiles"][p_name]
            for ch in self.channels:
                ch_data = profile_data.get(str(ch.channel_id))
                if ch_data: ch.set_state(ch_data)
            global_config["last_profile"] = p_name
            save_config(global_config)
            self.check_dirty_state()

    def load_last_profile(self):
        last_p = global_config.get("last_profile")
        if last_p and last_p in global_config["profiles"]:
            self.updating_combo = True
            self.combo_profiles.setCurrentText(last_p)
            self.updating_combo = False
            self.load_selected_profile()

    def change_osd_scale(self, text):
        val = float(text.replace("%", "")) / 100.0
        self._save_simple_config("osd_scale", val)
        self.osd_window.set_scale(val)
        QTimer.singleShot(50, self.restore_osd_position)

    def show_about_dialog(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(T("info_btn"))
        msg.setTextFormat(Qt.RichText)
        # Richiama l'HTML tradotto direttamente da i18n
        msg.setText(T("info_dialog_html"))
        msg.exec()

    def change_language(self, lang):
        if global_config.get("lang") != lang:
            global_config["lang"] = lang
            save_config(global_config)
            reply = QMessageBox.question(self, T("info_btn"), T("lang_prompt"), QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes: self.force_quit_and_restart()
            else: QMessageBox.information(self, "Language", T("lang_restart"))

    def force_quit_and_restart(self):
        self.ipc_server.stop()
        self.hw_thread.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def force_quit(self):
        self.ipc_server.stop()
        self.hw_thread.stop()
        QApplication.quit()

    def on_autostart_toggled(self, checked):
        self.chk_minimized.setEnabled(checked)
        self.toggle_autostart()

    def toggle_autostart(self, *args):
        enabled = self.chk_autostart.isChecked()
        minimized = self.chk_minimized.isChecked()
        global_config["autostart_min"] = minimized
        save_config(global_config)
        if enabled:
            os.makedirs(self.autostart_dir, exist_ok=True)
            exec_cmd = "/usr/bin/openaquaero --minimized" if minimized else "/usr/bin/openaquaero"
            with open(self.desktop_file_path, "w") as f:
                f.write(f"[Desktop Entry]\nType=Application\nExec={exec_cmd}\nHidden=false\nNoDisplay=false\nX-GNOME-Autostart-enabled=true\nName=OpenAquaero\nComment=Aquaero Thermal Control\nCategories=System;HardwareSettings;\n")
            os.chmod(self.desktop_file_path, os.stat(self.desktop_file_path).st_mode | stat.S_IEXEC)
        elif os.path.exists(self.desktop_file_path):
            os.remove(self.desktop_file_path)

    def toggle_master(self, checked):
        self.is_controlling = checked
        self.hw_thread.active_control = checked
        if checked:
            self.btn_master.setText(T("suspend_btn"))
            self.btn_master.setStyleSheet("background-color: #00e5ff; color: #11111b; border: none; padding: 12px; font-size: 15px; font-weight: bold; border-radius: 6px;")
        else:
            self.btn_master.setText(T("resume_btn"))
            self.btn_master.setStyleSheet("background-color: #ff3333; color: #ffffff; border: none; padding: 12px; font-size: 15px; font-weight: bold; border-radius: 6px;")

    def _save_simple_config(self, key, value):
        global_config[key] = value
        save_config(global_config)

    def open_autoswitch_settings(self):
        ProcessMappingDialog(self).exec()

    def update_tray_profiles(self):
        self.tray_profiles_menu.clear()
        for p_name in global_config.get("profiles", {}).keys():
            action = QAction(p_name, self)
            action.triggered.connect(lambda checked, p=p_name: self.load_profile_by_name(p))
            self.tray_profiles_menu.addAction(action)

    def load_profile_by_name(self, p_name):
        self.updating_combo = True
        index = self.combo_profiles.findText(p_name)
        if index >= 0:
            self.combo_profiles.setCurrentIndex(index)
            self.updating_combo = False
            self.load_selected_profile()
            self.tray_icon.showMessage("OpenAquaero", T("tray_prof_activated").format(p=p_name), QSystemTrayIcon.Information, 1500)
        else: self.updating_combo = False

    def check_running_processes(self):
        if not self.chk_autoswitch.isChecked(): return
        running_target, detected_proc = None, None
        for proc_name, prof_name in global_config.get("process_profiles", {}).items():
            try:
                if subprocess.run(["pgrep", "-f", proc_name], capture_output=True).returncode == 0:
                    running_target, detected_proc = prof_name, proc_name
                    break
            except: pass

        if running_target and self.active_auto_profile != running_target:
            if self.active_auto_profile is None: self.pre_auto_profile = self.combo_profiles.currentText()
            self.load_profile_by_name(running_target)
            self.active_auto_profile = running_target
            self.tray_icon.showMessage("Auto-Switch", T("tray_proc_detected").format(proc=detected_proc, prof=running_target), QSystemTrayIcon.Information, 2000)
        elif not running_target and self.active_auto_profile is not None:
            if self.pre_auto_profile: self.load_profile_by_name(self.pre_auto_profile)
            self.active_auto_profile = None
            self.tray_icon.showMessage("Auto-Switch", T("tray_proc_ended"), QSystemTrayIcon.Information, 2000)

    def toggle_osd_from_tray(self):
        self.chk_osd.setChecked(not self.chk_osd.isChecked())

    def toggle_osd(self, checked):
        self._save_simple_config("osd_export", checked)
        if checked:
            self.osd_window.show()
            self.restore_osd_position()
        else: self.osd_window.hide()

    def toggle_osd_from_hotkey(self):
        new_state = not global_config.get("osd_export", False)
        global_config["osd_export"] = new_state
        save_config(global_config)
        if hasattr(self, 'chk_osd'):
            self.chk_osd.blockSignals(True)
            self.chk_osd.setChecked(new_state)
            self.chk_osd.blockSignals(False)
        if new_state:
            self.osd_window.show()
            self.restore_osd_position()
        else: self.osd_window.hide()

    def save_osd_position(self, x, y):
        global_config.setdefault("osd_config", {})["pos_x"] = x
        global_config["osd_config"]["pos_y"] = y
        save_config(global_config)

    def restore_osd_position(self):
        pos_x = global_config.get("osd_config", {}).get("pos_x")
        pos_y = global_config.get("osd_config", {}).get("pos_y")
        screen = QApplication.primaryScreen().geometry()
        if pos_x is not None and pos_y is not None and 0 <= pos_x < screen.width() and 0 <= pos_y < screen.height():
            self.osd_window.move(pos_x, pos_y)
        else: self.osd_window.move(screen.width() - self.osd_window.width() - 20, 20)

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isHidden(): self.showNormal()
            else: self.hide()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage("OpenAquaero", T("tray_msg"), QSystemTrayIcon.Information, 2000)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # --- FIX ICONA E WAYLAND ---
    app.setWindowIcon(QIcon("openaquaero.png"))
    app.setDesktopFileName("openaquaero")

    # --- MODIFICA QUI ---
    # Recuperiamo il valore dell'opacità salvato nel file config.
    # Se non esiste, usiamo 180 (che è circa il 70% di opacità).
    initial_opacity = global_config.get("window_opacity", 180)
    app.setStyleSheet(get_dynamic_style(initial_opacity))
    # ---------------------

    win = OpenAquaeroUI()
    win.setWindowIcon(QIcon("openaquaero.png"))

    if "--minimized" not in sys.argv:
        win.show()
    sys.exit(app.exec())
