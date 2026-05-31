from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
                               QProgressBar, QFrame, QLayout, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QTimer

class AquaeroOSD(QWidget):
    """
    Floating desktop OSD widget.
    Implements drag-and-drop repositioning and dynamic telemetry updates.
    """
    position_changed = Signal(int, int)

    def __init__(self):
        super().__init__()
        self.scale = 1.0
        self.max_rows = 8
        self.bg_opacity = 220
        self.color_names = "#cdd6f4"
        self.color_values = "#00e5ff"
        self.color_badges = "#00e5ff"
        self.custom_font = None

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint |
                            Qt.Tool | Qt.BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._emit_position)

        self.layout = QVBoxLayout(self)
        # Manteniamo questo per forzare la contrazione della finestra su Wayland
        # quando si passa da uno scaling maggiore a uno minore
        self.layout.setSizeConstraint(QLayout.SetFixedSize)

        self.bg_widget = QFrame(self)
        self.bg_widget.setObjectName("osd_bg")
        self.bg_layout = QVBoxLayout(self.bg_widget)
        self.bg_layout.setSizeConstraint(QLayout.SetFixedSize)
        self.layout.addWidget(self.bg_widget)

        self.header_layout = QHBoxLayout()
        self.icon_lbl = QLabel("📊")
        self.title_lbl = QLabel("OPENAQUAERO OSD")
        self.title_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.header_layout.addWidget(self.icon_lbl)
        self.header_layout.addWidget(self.title_lbl)
        self.bg_layout.addLayout(self.header_layout)

        self.header_line = QFrame()
        self.header_line.setFrameShape(QFrame.HLine)
        self.bg_layout.addWidget(self.header_line)

        self.grid_layout = QGridLayout()
        # Allineamento globale della griglia
        self.grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.bg_layout.addLayout(self.grid_layout)

        self.sensor_ui = []
        self.apply_scaling()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.windowHandle():
                self.windowHandle().startSystemMove()
            event.accept()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.save_timer.start(500)

    def _emit_position(self):
        self.position_changed.emit(self.x(), self.y())

    def set_scale(self, new_scale):
        self.scale = new_scale
        self.apply_scaling()

    def set_customization(self, scale=None, opacity=None, c_names=None, c_values=None, c_badges=None, font=None, max_rows=None):
        if scale is not None: self.scale = scale
        if opacity is not None: self.bg_opacity = opacity
        if c_names is not None: self.color_names = c_names
        if c_values is not None: self.color_values = c_values
        if c_badges is not None: self.color_badges = c_badges
        if font is not None: self.custom_font = font
        if max_rows is not None: self.max_rows = max_rows

        self._force_rebuild = True
        self.apply_scaling()

    def apply_scaling(self):
        s = self.scale

        if self.custom_font:
            self.title_lbl.setFont(self.custom_font)

        self.layout.setContentsMargins(int(10*s), int(10*s), int(10*s), int(10*s))

        self.bg_widget.setStyleSheet(
            f"#osd_bg {{ background-color: rgba(17, 17, 27, {self.bg_opacity}); "
            f"border-radius: {int(8*s)}px; "
            f"border: {max(1, int(1*s))}px solid rgba(255, 255, 255, 30); }}"
        )
        self.bg_layout.setContentsMargins(int(15*s), int(12*s), int(15*s), int(12*s))
        self.bg_layout.setSpacing(int(8*s))

        self.icon_lbl.setStyleSheet(f"font-size: {int(14*s)}px; background: transparent; border: none;")
        self.title_lbl.setStyleSheet(
            f"color: {self.color_badges}; font-weight: 900; "
            f"font-size: {int(11*s)}px; letter-spacing: {int(1*s)}px; "
            f"background: transparent; border: none;"
        )
        self.header_line.setStyleSheet(
            f"background-color: rgba(255, 255, 255, 20); "
            f"border: none; max-height: {max(1, int(1*s))}px;"
        )

        # Spaziatura orizzontale (tra colonne) e verticale (tra righe)
        self.grid_layout.setHorizontalSpacing(int(12*s))
        self.grid_layout.setVerticalSpacing(int(6*s))

        # Forza un ricalcolo dell'interfaccia se i widget esistono già
        self._force_rebuild = True

    def update_data(self, hardware_data):
        s = self.scale

        if not hardware_data:
            self._clear_grid()
            return

        if not hasattr(self, 'sensor_ui') or len(self.sensor_ui) != len(hardware_data) or getattr(self, '_force_rebuild', False):
            self._force_rebuild = False
            self._clear_grid()
            self.sensor_ui = []

            for i, item in enumerate(hardware_data):
                row = i % self.max_rows
                # Se prevedi più colonne (es. affiancando due blocchi di sensori),
                # la logica base va gestita qui. Per ora assumiamo una griglia a sviluppo verticale.
                base_col = (i // self.max_rows) * 5

                # --- COL 0: BADGE ---
                # Usiamo il padding CSS per dare la forma, senza forzare la larghezza
                lbl_badge = QLabel()
                lbl_badge.setAlignment(Qt.AlignCenter)
                lbl_badge.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
                if self.custom_font: lbl_badge.setFont(self.custom_font)
                lbl_badge.setStyleSheet(
                    f"background-color: {self.color_badges}; color: #11111b; "
                    f"font-weight: 900; font-size: {int(10*s)}px; "
                    f"border-radius: {int(3*s)}px; "
                    f"padding: {int(3*s)}px {int(6*s)}px;"
                )
                self.grid_layout.addWidget(lbl_badge, row, base_col + 0)

                # --- COL 1: NOME ---
                lbl_name = QLabel()
                lbl_name.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                lbl_name.setMinimumWidth(int(80*s)) # Un minimo sindacale per non collassare
                if self.custom_font: lbl_name.setFont(self.custom_font)
                lbl_name.setStyleSheet(f"color: {self.color_names}; font-weight: 700; font-size: {int(12*s)}px;")
                self.grid_layout.addWidget(lbl_name, row, base_col + 1)

                # --- COL 2: VALORE PRINCIPALE ---
                lbl_val = QLabel()
                lbl_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                lbl_val.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
                self.grid_layout.addWidget(lbl_val, row, base_col + 2)

                # --- COL 3: RPM E VOLT IMPILATI ---
                rpm_volt_container = QWidget()
                rpm_volt_container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
                rpm_volt_layout = QVBoxLayout(rpm_volt_container)
                rpm_volt_layout.setContentsMargins(0, 0, 0, 0)
                rpm_volt_layout.setSpacing(0)

                lbl_rpm = QLabel()
                lbl_rpm.setAlignment(Qt.AlignRight | Qt.AlignBottom)
                lbl_volt = QLabel()
                lbl_volt.setAlignment(Qt.AlignRight | Qt.AlignTop)

                rpm_volt_layout.addWidget(lbl_rpm)
                rpm_volt_layout.addWidget(lbl_volt)
                self.grid_layout.addWidget(rpm_volt_container, row, base_col + 3)

                # --- COL 4: PROGRESS BAR ---
                prog_bar = QProgressBar()
                prog_bar.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
                prog_bar.setRange(0, 100)
                prog_bar.setTextVisible(True)
                prog_bar.setFormat("%p%")
                # L'altezza della barra la fissiamo, altrimenti rischia di occupare troppo spazio verticale
                prog_bar.setFixedHeight(int(16*s))
                prog_bar.setMinimumWidth(int(60*s))
                prog_bar.setStyleSheet(
                    f"QProgressBar {{ border: 1px solid #313244; border-radius: {int(3*s)}px; "
                    f"background-color: #181825; text-align: center; color: #cdd6f4; "
                    f"font-weight: 800; font-size: {int(10*s)}px; font-family: monospace; }} "
                    f"QProgressBar::chunk {{ background-color: {self.color_badges}; border-radius: {int(2*s)}px; }}"
                )

                spacer = QWidget()
                spacer.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)

                self.grid_layout.addWidget(prog_bar, row, base_col + 4)
                # Conserviamo lo spacer nel caso serva nascondere la barra
                self.grid_layout.addWidget(spacer, row, base_col + 4)

                self.sensor_ui.append({
                    'badge': lbl_badge,
                    'name': lbl_name,
                    'val': lbl_val,
                    'volt': lbl_volt,
                    'rpm': lbl_rpm,
                    'prog': prog_bar,
                    'spacer': spacer
                })

        # Aggiornamento effettivo dei dati
        for i, item in enumerate(hardware_data):
            ui = self.sensor_ui[i]

            name_text = item.get('name', '').upper()
            display_name = name_text.replace(" VOLTS", "")
            rpm = item.get('rpm')
            pwm = item.get('pwm')
            temp = item.get('temp')
            volt = item.get('volt')

            if "VOLT" in name_text: badge_txt = "VLT"
            elif rpm is not None: badge_txt = "FAN"
            elif pwm is not None: badge_txt = "PWR"
            elif temp is not None: badge_txt = "TMP"
            else: badge_txt = "SYS"

            ui['badge'].setText(badge_txt)
            ui['name'].setText(display_name)

            if temp is not None:
                unit = "V" if badge_txt == "VLT" else "°C"
                ui['val'].setText(f"{temp:.1f} {unit}")
                ui['val'].setStyleSheet(f"color: {self.color_values}; font-family: monospace; font-weight: 800; font-size: {int(13*s)}px;")
            else:
                ui['val'].setText("--")
                ui['val'].setStyleSheet(f"color: #45475a;")

            if volt is not None:
                ui['volt'].setText(f"{volt:.1f} V")
                ui['volt'].setStyleSheet(f"color: #f9e2af; font-family: monospace; font-weight: 800; font-size: {int(10*s)}px;")
                ui['volt'].show()
            else:
                ui['volt'].hide()

            if rpm is not None:
                ui['rpm'].setText(f"{rpm} RPM")
                ui['rpm'].setStyleSheet(f"color: #94e2d5; font-family: monospace; font-weight: 800; font-size: {int(10*s)}px;")
                ui['rpm'].show()
            else:
                ui['rpm'].hide()

            if pwm is not None:
                ui['prog'].show()
                ui['spacer'].hide()
                ui['prog'].setValue(int(pwm))
            else:
                ui['prog'].hide()
                ui['spacer'].show()

    def _clear_grid(self):
        """Pulisce in modo sicuro la griglia eliminando i widget."""
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
        self.sensor_ui = []

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
