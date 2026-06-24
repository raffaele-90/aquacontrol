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
import subprocess
import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
                               QPushButton, QGroupBox, QFormLayout, QComboBox,
                               QRadioButton, QCheckBox, QDoubleSpinBox, QLineEdit,
                               QInputDialog, QFrame, QDialog, QListWidget, QSpinBox,
                               QMessageBox, QApplication, QButtonGroup)
from PySide6.QtCore import Qt, Signal, QPointF, QRectF, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QPolygonF, QBrush, QFont

from config_manager import global_config, save_config
from i18n import T

def format_temp(celsius_val):
    if celsius_val is None: return T("err_sensor")
    if global_config.get("use_fahrenheit", False):
        return f"{(celsius_val * 1.8) + 32:.1f} °F"
    return f"{celsius_val:.1f} °C"

class CurveVisualizer(QWidget):
    """Componente grafico per la renderizzazione della curva termica automatica polinomiale."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(160)
        self.t_min = 35; self.t_max = 45; self.p_min = 0; self.p_max = 100
        self.gamma = 1.0; self.current_temp = 0.0

    def update_curve(self, t_min, t_max, p_min, p_max, gamma, current_temp):
        self.t_min = t_min; self.t_max = t_max; self.p_min = p_min; self.p_max = p_max
        self.gamma = gamma; self.current_temp = current_temp
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width(); h = self.height()

        bg_color = QColor(35, 38, 41, 225) if self.isEnabled() else QColor(20, 22, 24, 225)
        painter.fillRect(0, 0, w, h, bg_color)

        margin_x = 35; margin_y = 25
        graph_w = w - (margin_x * 2); graph_h = h - (margin_y * 2)

        painter.setPen(QPen(QColor("#313244"), 1, Qt.SolidLine))
        painter.drawLine(margin_x, h - margin_y, w - margin_x, h - margin_y)
        painter.drawLine(margin_x, margin_y, margin_x, h - margin_y)

        vis_t_min = float(self.t_min)
        vis_t_max = float(self.t_max)
        if vis_t_max <= vis_t_min: vis_t_max = vis_t_min + 1.0

        vis_p_min = float(self.p_min)
        vis_p_max = float(self.p_max)
        if vis_p_max <= vis_p_min: vis_p_max = vis_p_min + 1.0

        polygon = QPolygonF()
        polygon.append(QPointF(margin_x, h - margin_y))

        for i in range(51):
            temp_step = vis_t_min + (i / 50.0) * (vis_t_max - vis_t_min)
            if temp_step <= self.t_min: pwm = self.p_min
            elif temp_step >= self.t_max: pwm = self.p_max
            else:
                if self.t_max == self.t_min: t_norm = 1.0
                else: t_norm = (temp_step - self.t_min) / (self.t_max - self.t_min)
                pwm = self.p_min + (self.p_max - self.p_min) * pow(t_norm, self.gamma)

            x = margin_x + ((temp_step - vis_t_min) / (vis_t_max - vis_t_min)) * graph_w
            p_norm = (pwm - vis_p_min) / (vis_p_max - vis_p_min)
            y = (h - margin_y) - (p_norm * graph_h)
            polygon.append(QPointF(x, y))

        polygon.append(QPointF(w - margin_x, h - margin_y))

        painter.setPen(Qt.NoPen)
        brush_color = QColor("#00e5ff") if self.isEnabled() else QColor("#45475a")
        brush_color.setAlpha(40)
        painter.setBrush(QBrush(brush_color))
        painter.drawPolygon(polygon)

        pen_color = QColor("#00e5ff") if self.isEnabled() else QColor("#555555")
        painter.setPen(QPen(pen_color, 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawPolyline(polygon.mid(1, 51))

        painter.setPen(QPen(QColor("#6c7086"), 1))
        font = painter.font(); font.setPointSize(8); font.setBold(False); painter.setFont(font)

        painter.drawText(5, h - margin_y + 4, f"{int(vis_p_min)}%")
        painter.drawText(5, margin_y + 4, f"{int(vis_p_max)}%")
        painter.drawText(margin_x - 15, h - 5, f"{int(vis_t_min)}°C")
        painter.drawText(w - margin_x - 20, h - 5, f"{int(vis_t_max)}°C")

        if self.isEnabled() and self.current_temp > 0.0:
            font.setPointSize(9); font.setBold(True); painter.setFont(font)

            if self.current_temp < vis_t_min:
                x_pos = margin_x
                painter.setPen(QPen(QColor("#a6adc8"), 2, Qt.DashLine))
                painter.drawLine(int(x_pos), margin_y, int(x_pos), h - margin_y)
                val_attuale = T("current_val").format(v=f"{self.current_temp:.1f}")
                painter.drawText(int(x_pos) + 8, margin_y + 12, f"< {int(vis_t_min)}°C {val_attuale}")

            elif self.current_temp > vis_t_max:
                x_pos = w - margin_x
                painter.setPen(QPen(QColor("#ff3333"), 2, Qt.DashLine))
                painter.drawLine(int(x_pos), margin_y, int(x_pos), h - margin_y)
                val_attuale = T("current_val").format(v=f"{self.current_temp:.1f}")
                text = f"> {int(vis_t_max)}°C {val_attuale}"
                tw = painter.fontMetrics().horizontalAdvance(text)
                painter.drawText(int(x_pos) - tw - 8, margin_y + 12, text)

            else:
                x_temp = margin_x + ((self.current_temp - vis_t_min) / (vis_t_max - vis_t_min)) * graph_w

                if self.t_max == self.t_min: t_norm = 1.0
                else: t_norm = (self.current_temp - self.t_min) / (self.t_max - self.t_min)
                pwm = self.p_min + (self.p_max - self.p_min) * pow(t_norm, self.gamma)

                p_norm = (pwm - vis_p_min) / (vis_p_max - vis_p_min)
                y_pwm = (h - margin_y) - (p_norm * graph_h)

                painter.setPen(QPen(QColor("#a6adc8"), 1, Qt.DashLine))
                painter.drawLine(margin_x, int(y_pwm), int(x_temp), int(y_pwm))
                painter.drawLine(int(x_temp), int(y_pwm), int(x_temp), h - margin_y)

                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor("#00e5ff")))
                painter.drawEllipse(QPointF(x_temp, y_pwm), 4, 4)

                tooltip_text = f"{self.current_temp:.1f}°C | {int(pwm)}%"
                font.setPointSize(9); font.setBold(True); painter.setFont(font)
                metrics = painter.fontMetrics()
                tw = metrics.horizontalAdvance(tooltip_text)
                th = metrics.height()

                tx = x_temp + 10
                ty = y_pwm - 10 - th

                if tx + tw + 10 > w:
                    tx = x_temp - tw - 10
                if ty < 5:
                    ty = y_pwm + 15

                painter.setPen(QPen(QColor("#45475a"), 1))
                painter.setBrush(QBrush(QColor("#1e1e2e")))
                painter.drawRoundedRect(QRectF(tx - 4, ty - 2, tw + 8, th + 4), 4, 4)

                painter.setPen(QColor("#cdd6f4"))
                painter.drawText(int(tx), int(ty + th - 3), tooltip_text)


class InteractiveCurveWidget(QWidget):
    """Componente grafico per la manipolazione interattiva a nodi (interpolazione lineare)."""
    curve_changed = Signal()
    node_selected = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(220)
        self.setMouseTracking(True)
        self.points = [[25.0, 20.0], [45.0, 40.0], [70.0, 100.0]]
        self.current_temp = 0.0
        self.current_pwm = 0.0
        self.MIN_T = 10.0; self.MAX_T = 100.0
        self.MIN_P = 0.0; self.MAX_P = 100.0
        self.margin_x = 40; self.margin_y = 25
        self.dragging_idx = -1; self.hover_idx = -1; self.selected_idx = -1

    def t_to_x(self, t):
        w = self.width() - (self.margin_x * 2)
        return self.margin_x + ((t - self.MIN_T) / (self.MAX_T - self.MIN_T)) * w

    def p_to_y(self, p):
        h = self.height() - (self.margin_y * 2)
        return (self.height() - self.margin_y) - ((p - self.MIN_P) / (self.MAX_P - self.MIN_P)) * h

    def x_to_t(self, x):
        w = self.width() - (self.margin_x * 2)
        val = self.MIN_T + ((x - self.margin_x) / w) * (self.MAX_T - self.MIN_T)
        return max(self.MIN_T, min(self.MAX_T, val))

    def y_to_p(self, y):
        h = self.height() - (self.margin_y * 2)
        val = self.MIN_P + (((self.height() - self.margin_y) - y) / h) * (self.MAX_P - self.MIN_P)
        return max(self.MIN_P, min(self.MAX_P, val))

    def mousePressEvent(self, event):
        if not self.isEnabled(): return
        pos = event.position()
        for i, (t, p) in enumerate(self.points):
            x = self.t_to_x(t); y = self.p_to_y(p)
            if (pos.x() - x)**2 + (pos.y() - y)**2 < 100:
                if event.button() == Qt.LeftButton:
                    self.dragging_idx = i; self.selected_idx = i
                    self.node_selected.emit(t, p)
                elif event.button() == Qt.RightButton and len(self.points) > 2:
                    self.points.pop(i); self.selected_idx = -1
                    self.curve_changed.emit()
                self.update()
                return
        if event.button() == Qt.LeftButton:
            self.selected_idx = -1
            self.update()

    def mouseMoveEvent(self, event):
        if not self.isEnabled(): return
        pos = event.position()
        hovered = -1
        for i, (t, p) in enumerate(self.points):
            x = self.t_to_x(t); y = self.p_to_y(p)
            if (pos.x() - x)**2 + (pos.y() - y)**2 < 100:
                hovered = i
                break

        if hovered != self.hover_idx:
            self.hover_idx = hovered
            self.update()

        if self.dragging_idx >= 0:
            raw_t = self.x_to_t(pos.x()); raw_p = self.y_to_p(pos.y())
            new_t = round(raw_t * 2) / 2.0; new_p = round(raw_p * 2) / 2.0

            min_t_bound = self.MIN_T if self.dragging_idx == 0 else self.points[self.dragging_idx-1][0] + 0.1
            max_t_bound = self.MAX_T if self.dragging_idx == len(self.points)-1 else self.points[self.dragging_idx+1][0] - 0.1
            safe_t = max(min_t_bound, min(max_t_bound, new_t))
            safe_p = max(self.MIN_P, min(self.MAX_P, new_p))

            self.points[self.dragging_idx] = [safe_t, safe_p]
            self.node_selected.emit(safe_t, safe_p)
            self.curve_changed.emit()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging_idx = -1
            self.update()

    def mouseDoubleClickEvent(self, event):
        if not self.isEnabled(): return
        if event.button() == Qt.LeftButton and len(self.points) < 20:
            new_t = round(self.x_to_t(event.position().x()) * 2) / 2.0
            new_p = round(self.y_to_p(event.position().y()) * 2) / 2.0
            self.points.append([new_t, new_p])
            self.points.sort(key=lambda p: p[0])
            self.curve_changed.emit()
            self.update()

    def update_selected_node_from_spinbox(self, new_t, new_p):
        if self.selected_idx < 0: return None, None
        min_t_bound = self.MIN_T if self.selected_idx == 0 else self.points[self.selected_idx-1][0] + 0.1
        max_t_bound = self.MAX_T if self.selected_idx == len(self.points)-1 else self.points[self.selected_idx+1][0] - 0.1
        safe_t = max(min_t_bound, min(max_t_bound, new_t))
        safe_p = max(self.MIN_P, min(self.MAX_P, new_p))
        self.points[self.selected_idx] = [safe_t, safe_p]
        self.curve_changed.emit()
        self.update()
        return safe_t, safe_p

    def update_telemetry(self, temp, pwm):
        self.current_temp = temp
        self.current_pwm = pwm
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width(); h = self.height()

        bg_color = QColor(35, 38, 41, 225) if self.isEnabled() else QColor(20, 22, 24, 225)
        painter.fillRect(0, 0, w, h, bg_color)

        graph_w = w - (self.margin_x * 2); graph_h = h - (self.margin_y * 2)

        painter.setPen(QPen(QColor("#313244"), 1, Qt.SolidLine))
        painter.drawLine(self.margin_x, h - self.margin_y, w - self.margin_x, h - self.margin_y)
        painter.drawLine(self.margin_x, self.margin_y, self.margin_x, h - self.margin_y)

        painter.setPen(QPen(QColor("#6c7086"), 1))
        font = painter.font(); font.setPointSize(8); painter.setFont(font)
        painter.drawText(5, h - self.margin_y + 4, f"{int(self.MIN_P)}%")
        painter.drawText(5, self.margin_y + 4, f"{int(self.MAX_P)}%")
        painter.drawText(self.margin_x - 10, h - 5, f"{int(self.MIN_T)}°C")
        painter.drawText(w - self.margin_x - 10, h - 5, f"{int(self.MAX_T)}°C")

        if self.points:
            polygon = QPolygonF()
            polygon.append(QPointF(self.t_to_x(self.points[0][0]), h - self.margin_y))
            for t, p in self.points:
                polygon.append(QPointF(self.t_to_x(t), self.p_to_y(p)))
            polygon.append(QPointF(self.t_to_x(self.points[-1][0]), h - self.margin_y))

            brush_color = QColor("#00e5ff") if self.isEnabled() else QColor("#45475a")
            brush_color.setAlpha(30)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(brush_color))
            painter.drawPolygon(polygon)

        pen_color = QColor("#00e5ff") if self.isEnabled() else QColor("#555555")
        painter.setPen(QPen(pen_color, 2))
        painter.setBrush(Qt.NoBrush)

        for i in range(len(self.points) - 1):
            x1, y1 = self.t_to_x(self.points[i][0]), self.p_to_y(self.points[i][1])
            x2, y2 = self.t_to_x(self.points[i+1][0]), self.p_to_y(self.points[i+1][1])
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        if self.isEnabled() and self.current_temp > 0.0:
            font.setPointSize(9); font.setBold(True); painter.setFont(font)

            if self.current_temp < self.MIN_T:
                x_pos = self.margin_x
                painter.setPen(QPen(QColor("#a6adc8"), 2, Qt.DashLine))
                painter.drawLine(int(x_pos), self.margin_y, int(x_pos), h - self.margin_y)
                val_attuale = T("current_val").format(v=f"{self.current_temp:.1f}")
                painter.drawText(int(x_pos) + 8, self.margin_y + 12, f"< {int(self.MIN_T)}°C {val_attuale}")

            elif self.current_temp > self.MAX_T:
                x_pos = w - self.margin_x
                painter.setPen(QPen(QColor("#ff3333"), 2, Qt.DashLine))
                painter.drawLine(int(x_pos), self.margin_y, int(x_pos), h - self.margin_y)
                val_attuale = T("current_val").format(v=f"{self.current_temp:.1f}")
                text = f"> {int(self.MAX_T)}°C {val_attuale}"
                tw = painter.fontMetrics().horizontalAdvance(text)
                painter.drawText(int(x_pos) - tw - 8, self.margin_y + 12, text)

            else:
                curr_x = int(self.t_to_x(self.current_temp))
                curr_y = int(self.p_to_y(self.current_pwm))

                painter.setPen(QPen(QColor("#a6adc8"), 1, Qt.DashLine))
                painter.drawLine(self.margin_x, curr_y, curr_x, curr_y)
                painter.drawLine(curr_x, curr_y, curr_x, h - self.margin_y)

                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor("#00e5ff")))
                painter.drawEllipse(QPointF(curr_x, curr_y), 4, 4)

                tooltip_text = f"{self.current_temp:.1f}°C | {int(self.current_pwm)}%"
                font.setPointSize(9); font.setBold(True); painter.setFont(font)
                metrics = painter.fontMetrics()
                tw = metrics.horizontalAdvance(tooltip_text)
                th = metrics.height()

                tx = curr_x + 10
                ty = curr_y - 10 - th

                if tx + tw + 10 > w:
                    tx = curr_x - tw - 10
                if ty < 5:
                    ty = curr_y + 15

                painter.setPen(QPen(QColor("#00e5ff"), 1))
                painter.setBrush(QBrush(QColor("#1e1e2e")))
                painter.drawRoundedRect(QRectF(tx - 4, ty - 2, tw + 8, th + 4), 4, 4)

                painter.setPen(QColor("#00e5ff"))
                painter.drawText(int(tx), int(ty + th - 3), tooltip_text)

        if self.isEnabled():
            font.setBold(False); painter.setFont(font)
            for i, (t, p) in enumerate(self.points):
                x = self.t_to_x(t); y = self.p_to_y(p)
                is_active = (i == self.dragging_idx or i == self.hover_idx or i == self.selected_idx)

                node_color = QColor("#ffffff") if is_active else QColor("#00e5ff")
                r = 6 if is_active else 4

                painter.setPen(QPen(QColor("#1e1e2e"), 1))
                painter.setBrush(QBrush(node_color))
                painter.drawEllipse(QPointF(x, y), r, r)

                if is_active:
                    tooltip_text = f"{t}°C | {p}%"
                    font.setPointSize(9); painter.setFont(font)
                    metrics = painter.fontMetrics()
                    tw = metrics.horizontalAdvance(tooltip_text)
                    th = metrics.height()
                    tx = max(5, min(x - tw/2, w - tw - 5))
                    ty = y - r - th - 5

                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(QColor("#00e5ff")))
                    painter.drawRoundedRect(QRectF(tx - 4, ty - 2, tw + 8, th + 4), 3, 3)

                    painter.setPen(QPen(QColor("#11111b")))
                    painter.drawText(int(tx), int(ty + th - 3), tooltip_text)

class ChannelControlWidget(QGroupBox):
    """Componente UI per il controllo logico e visivo del singolo canale hardware"""
    def __init__(self, channel_id, engine, parent=None):
        super().__init__("", parent)
        self.channel_id = channel_id
        self.engine = engine
        self.last_known_temp = 0.0
        self.temp_history = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title_layout = QHBoxLayout()
        lbl_ch = QLabel(f"{T('channel')} {self.channel_id} |")
        lbl_ch.setStyleSheet("font-size: 18px; color: #a6adc8;")

        self.edit_name = QLineEdit()
        self.edit_name.setStyleSheet("font-size: 18px; border: none; background: transparent; color: #00e5ff; font-weight: bold;")

        saved_name = global_config["channels_names"].get(str(self.channel_id), T("unnamed_hw"))
        self.edit_name.setText(saved_name)
        self.edit_name.editingFinished.connect(self.save_channel_name)

        title_layout.addWidget(lbl_ch); title_layout.addWidget(self.edit_name)
        main_layout.addLayout(title_layout)

        line = QWidget(); line.setFixedHeight(1); line.setStyleSheet("background-color: #444;")
        main_layout.addWidget(line)

        top_layout = QHBoxLayout()
        status_layout = QVBoxLayout()

        self.lbl_temp = QLabel("Temp: --")
        self.lbl_temp.setStyleSheet("color: #cdd6f4; font-size: 15px; font-weight: bold;")
        self.lbl_pwm = QLabel("Power: -- %")
        self.lbl_pwm.setStyleSheet("color: #a6adc8; font-size: 15px;")
        self.lbl_rpm = QLabel("Speed: -- RPM")
        self.lbl_rpm.setStyleSheet("color: #a6adc8; font-size: 15px;")

        self.lbl_volt = QLabel("Volt: -- V")
        self.lbl_volt.setStyleSheet("color: #f9e2af; font-size: 15px; font-weight: bold;")

        status_layout.addWidget(self.lbl_temp)
        status_layout.addWidget(self.lbl_pwm)
        status_layout.addWidget(self.lbl_rpm)
        status_layout.addWidget(self.lbl_volt)

        top_layout.addLayout(status_layout)
        top_layout.addSpacing(20) # Aggiunge un po' di respiro tra i dati e i controlli

        setup_layout = QFormLayout()

        sensor_box = QHBoxLayout()
        self.combo_sensors = QComboBox()
        self.btn_rename_sensor = QPushButton("✎")
        self.btn_rename_sensor.setFixedWidth(35)
        self.btn_rename_sensor.clicked.connect(self.rename_current_sensor)
        sensor_box.addWidget(self.combo_sensors)
        sensor_box.addWidget(self.btn_rename_sensor)

        self.chk_delta = QCheckBox(T("delta_mode"))
        self.chk_delta.setStyleSheet("font-size: 13px; font-weight: normal;")

        self.lbl_delta_help = QLabel(f" {T('delta_hint')} ")
        self.lbl_delta_help.setStyleSheet("color: #6c7086; font-size: 12px; font-style: italic;")
        self.lbl_delta_help.setEnabled(False)

        self.combo_delta_cold = QComboBox()
        self.combo_delta_cold.setEnabled(False)

        self.chk_delta.toggled.connect(self.combo_delta_cold.setEnabled)
        self.chk_delta.toggled.connect(self.lbl_delta_help.setEnabled)

        sensor_box.addWidget(QLabel("  "))
        sensor_box.addWidget(self.chk_delta)
        sensor_box.addWidget(self.lbl_delta_help)
        sensor_box.addWidget(self.combo_delta_cold)
        sensor_box.addStretch()

        self.refresh_sensors()
        setup_layout.addRow(T("sensor"), sensor_box)

        hyst_layout = QHBoxLayout()
        self.chk_hysteresis = QCheckBox(T("hysteresis"))
        self.chk_hysteresis.setStyleSheet("font-size: 13px; font-weight: normal;")

        self.spin_hysteresis = QDoubleSpinBox()
        self.spin_hysteresis.setDecimals(0)
        self.spin_hysteresis.setRange(2, 60)
        self.spin_hysteresis.setValue(5)
        self.spin_hysteresis.setSuffix(" sec")
        self.spin_hysteresis.setEnabled(False)

        self.chk_hysteresis.toggled.connect(self.spin_hysteresis.setEnabled)
        self.chk_hysteresis.toggled.connect(lambda: self.temp_history.clear())

        hyst_layout.addWidget(self.chk_hysteresis)
        hyst_layout.addWidget(self.spin_hysteresis)

        hyst_layout.addWidget(QLabel("    |    " + T("mode")))
        self.radio_auto = QRadioButton(T("mode_auto"))
        self.radio_manual = QRadioButton(T("mode_manual"))
        self.radio_pid = QRadioButton(T("pid_mode"))
        self.radio_fixed = QRadioButton(T("fixed"))
        self.radio_auto.setChecked(True)

        hyst_layout.addWidget(self.radio_auto)
        hyst_layout.addWidget(self.radio_manual)
        hyst_layout.addWidget(self.radio_pid)
        hyst_layout.addWidget(self.radio_fixed)
        hyst_layout.addStretch()

        self.radio_auto.toggled.connect(self.update_ui_mode)
        self.radio_manual.toggled.connect(self.update_ui_mode)
        self.radio_pid.toggled.connect(self.update_ui_mode)
        self.radio_fixed.toggled.connect(self.update_ui_mode)

        setup_layout.addRow("", hyst_layout)

        top_layout.addLayout(setup_layout)
        main_layout.addLayout(top_layout)

        # ----------------- BOX AUTO -----------------
        self.box_auto = QWidget()
        auto_layout = QVBoxLayout(self.box_auto)
        auto_layout.setContentsMargins(0, 0, 0, 0)

        self.graph_auto = CurveVisualizer()
        self.graph_auto.setMinimumHeight(280)
        auto_layout.addWidget(self.graph_auto)

        self.btn_toggle_auto = QPushButton()
        self.btn_toggle_auto.setStyleSheet("text-align: left; background: transparent; border: none; color: #00e5ff; font-weight: bold; padding: 5px 0; font-size: 14px;")
        self.btn_toggle_auto.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_auto.clicked.connect(self.toggle_auto_controls)
        auto_layout.addWidget(self.btn_toggle_auto)

        self.container_auto_controls = QWidget()
        slider_layout = QFormLayout(self.container_auto_controls)
        slider_layout.setContentsMargins(0, 5, 0, 0)

        self.slider_t_min = self.create_slider(10, 100, 35); self.val_t_min = QLabel("35 °C")
        self.slider_t_max = self.create_slider(10, 100, 45); self.val_t_max = QLabel("45 °C")
        self.slider_p_min = self.create_slider(0, 100, 0); self.val_p_min = QLabel("0 %")
        self.slider_p_max = self.create_slider(0, 100, 100); self.val_p_max = QLabel("100 %")
        self.slider_gamma = QSlider(Qt.Horizontal); self.slider_gamma.setRange(1, 30); self.slider_gamma.setValue(10)
        self.val_gamma = QLabel("1.0")

        self.slider_t_min.valueChanged.connect(lambda v: (self.val_t_min.setText(f"{v} °C"), self.update_graph_auto(), self.update_auto_toggle_text()))
        self.slider_t_max.valueChanged.connect(lambda v: (self.val_t_max.setText(f"{v} °C"), self.update_graph_auto(), self.update_auto_toggle_text()))
        self.slider_p_min.valueChanged.connect(lambda v: (self.val_p_min.setText(f"{v} %"), self.update_graph_auto(), self.update_auto_toggle_text()))
        self.slider_p_max.valueChanged.connect(lambda v: (self.val_p_max.setText(f"{v} %"), self.update_graph_auto(), self.update_auto_toggle_text()))
        self.slider_gamma.valueChanged.connect(lambda v: (self.val_gamma.setText(f"{v/10.0}"), self.update_graph_auto()))

        slider_layout.addRow(QLabel(T("t_min")), self.make_row(self.slider_t_min, self.val_t_min))
        slider_layout.addRow(QLabel(T("t_max")), self.make_row(self.slider_t_max, self.val_t_max))
        slider_layout.addRow(QLabel(T("p_min")), self.make_row(self.slider_p_min, self.val_p_min))
        slider_layout.addRow(QLabel(T("p_max")), self.make_row(self.slider_p_max, self.val_p_max))
        slider_layout.addRow(QLabel(T("gamma")), self.make_row(self.slider_gamma, self.val_gamma))

        auto_layout.addWidget(self.container_auto_controls)
        self.container_auto_controls.hide()
        self.update_auto_toggle_text()

        main_layout.addWidget(self.box_auto)

        # ----------------- BOX MANUAL -----------------
        self.box_manual = QWidget()
        manual_layout = QVBoxLayout(self.box_manual)
        manual_layout.setContentsMargins(0, 0, 0, 0)

        self.graph_manual = InteractiveCurveWidget()
        self.graph_manual.setMinimumHeight(280)
        manual_layout.addWidget(self.graph_manual)

        lbl_tip = QLabel(T("curve_tip"))
        lbl_tip.setStyleSheet("color: #6c7086; font-size: 11px;")
        lbl_tip.setAlignment(Qt.AlignCenter)
        manual_layout.addWidget(lbl_tip)

        self.btn_toggle_manual = QPushButton()
        self.btn_toggle_manual.setStyleSheet("text-align: left; background: transparent; border: none; color: #00e5ff; font-weight: bold; padding: 5px 0; font-size: 14px;")
        self.btn_toggle_manual.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_manual.clicked.connect(self.toggle_manual_controls)
        manual_layout.addWidget(self.btn_toggle_manual)

        self.container_manual_controls = QWidget()
        manual_controls_layout = QVBoxLayout(self.container_manual_controls)
        manual_controls_layout.setContentsMargins(0, 5, 0, 0)

        scale_layout = QHBoxLayout()
        lbl_scale = QLabel(T("manual_range"))
        lbl_scale.setStyleSheet("color: #a6adc8; font-size: 12px; font-weight: bold;")
        self.spin_scale_min = QSpinBox()
        self.spin_scale_min.setRange(0, 150)
        self.spin_scale_min.setValue(10)
        self.spin_scale_min.setSuffix(" °C")
        self.spin_scale_max = QSpinBox()
        self.spin_scale_max.setRange(10, 200)
        self.spin_scale_max.setValue(100)
        self.spin_scale_max.setSuffix(" °C")

        scale_layout.addWidget(lbl_scale)
        scale_layout.addWidget(self.spin_scale_min)
        scale_layout.addWidget(QLabel(" - "))
        scale_layout.addWidget(self.spin_scale_max)
        scale_layout.addStretch()

        self.spin_scale_min.valueChanged.connect(lambda v: (self.on_manual_scale_changed(), self.update_manual_toggle_text()))
        self.spin_scale_max.valueChanged.connect(lambda v: (self.on_manual_scale_changed(), self.update_manual_toggle_text()))

        manual_controls_layout.addLayout(scale_layout)

        self.box_node_edit = QWidget()
        node_layout = QHBoxLayout(self.box_node_edit)
        node_layout.setContentsMargins(0, 10, 0, 0)
        lbl_node_edit = QLabel(T("manual_node"))
        lbl_node_edit.setStyleSheet("color: #00e5ff;")

        self.spin_temp = QDoubleSpinBox()
        self.spin_temp.setRange(10.0, 100.0)
        self.spin_temp.setDecimals(1)
        self.spin_temp.setSingleStep(0.1)
        self.spin_temp.setSuffix(" °C")

        self.spin_pwm = QDoubleSpinBox()
        self.spin_pwm.setRange(0.0, 100.0)
        self.spin_pwm.setDecimals(1)
        self.spin_pwm.setSingleStep(0.1)
        self.spin_pwm.setSuffix(" %")

        node_layout.addWidget(lbl_node_edit)
        node_layout.addWidget(self.spin_temp)
        node_layout.addWidget(self.spin_pwm)
        node_layout.addStretch()

        manual_controls_layout.addWidget(self.box_node_edit)

        manual_layout.addWidget(self.container_manual_controls)
        self.container_manual_controls.hide()
        self.update_manual_toggle_text()

        self.graph_manual.node_selected.connect(self.on_node_selected)
        self.spin_temp.valueChanged.connect(self.on_spinbox_changed)
        self.spin_pwm.valueChanged.connect(self.on_spinbox_changed)
        main_layout.addWidget(self.box_manual)

        # ----------------- BOX PID -----------------
        self.box_pid = QWidget()
        pid_main_layout = QVBoxLayout(self.box_pid)
        pid_main_layout.setContentsMargins(0, 15, 0, 10)

        # Riga 1: Target Temp
        target_layout = QHBoxLayout()
        lbl_pid = QLabel(T("pid_target"))
        lbl_pid.setStyleSheet("color: #00e5ff; font-weight: bold; font-size: 15px;")

        self.spin_pid_target = QDoubleSpinBox()
        self.spin_pid_target.setRange(20.0, 80.0)
        self.spin_pid_target.setDecimals(1)
        self.spin_pid_target.setSingleStep(0.5)
        self.spin_pid_target.setValue(35.0)
        self.spin_pid_target.setSuffix(" °C")

        target_layout.addWidget(lbl_pid)
        target_layout.addWidget(self.spin_pid_target)
        target_layout.addStretch()
        pid_main_layout.addLayout(target_layout)

        # Riga 2: Preset Mode
        preset_layout = QHBoxLayout()
        lbl_preset = QLabel(T("pid_preset"))
        lbl_preset.setStyleSheet("color: #a6adc8; font-size: 13px; font-weight: bold;")

        self.pid_mode_group = QButtonGroup(self.box_pid)
        self.radio_pid_slow = QRadioButton(T("pid_slow"))
        self.radio_pid_normal = QRadioButton(T("pid_normal"))
        self.radio_pid_fast = QRadioButton(T("pid_fast"))
        self.radio_pid_custom = QRadioButton(T("pid_manual"))
        self.radio_pid_normal.setChecked(True)

        self.pid_mode_group.addButton(self.radio_pid_slow)
        self.pid_mode_group.addButton(self.radio_pid_normal)
        self.pid_mode_group.addButton(self.radio_pid_fast)
        self.pid_mode_group.addButton(self.radio_pid_custom)

        preset_layout.addWidget(lbl_preset)
        preset_layout.addWidget(self.radio_pid_slow)
        preset_layout.addWidget(self.radio_pid_normal)
        preset_layout.addWidget(self.radio_pid_fast)
        preset_layout.addWidget(self.radio_pid_custom)
        preset_layout.addStretch()
        pid_main_layout.addLayout(preset_layout)

        # Riga 3: Parametri Custom (Nascosti di default)
        self.box_pid_custom = QWidget()
        custom_pid_layout = QHBoxLayout(self.box_pid_custom)
        custom_pid_layout.setContentsMargins(0, 5, 0, 0)

        self.spin_pid_kp = QDoubleSpinBox()
        self.spin_pid_kp.setPrefix(f"{T('pid_prop')} ")
        self.spin_pid_kp.setDecimals(1) # <--- Modificato (es. 5.0)
        self.spin_pid_kp.setRange(0.0, 100.0)
        self.spin_pid_kp.setSingleStep(0.5)

        self.spin_pid_ki = QDoubleSpinBox()
        self.spin_pid_ki.setPrefix(f"{T('pid_int')} ")
        self.spin_pid_ki.setDecimals(2) # <--- Modificato (es. 0.08)
        self.spin_pid_ki.setRange(0.0, 100.0)
        self.spin_pid_ki.setSingleStep(0.01)

        self.spin_pid_kd = QDoubleSpinBox()
        self.spin_pid_kd.setPrefix(f"{T('pid_der')} ")
        self.spin_pid_kd.setDecimals(1) # <--- Modificato (es. 0.3)
        self.spin_pid_kd.setRange(0.0, 100.0)
        self.spin_pid_kd.setSingleStep(0.1)

        custom_pid_layout.addWidget(self.spin_pid_kp)
        custom_pid_layout.addWidget(self.spin_pid_ki)
        custom_pid_layout.addWidget(self.spin_pid_kd)
        custom_pid_layout.addStretch()

        self.box_pid_custom.hide()
        pid_main_layout.addWidget(self.box_pid_custom)

        self.radio_pid_custom.toggled.connect(self.box_pid_custom.setVisible)
        main_layout.addWidget(self.box_pid)

        # ----------------- BOX FIXED -----------------
        self.box_fixed = QWidget()
        fixed_layout = QHBoxLayout(self.box_fixed)
        fixed_layout.setContentsMargins(0, 5, 0, 0)
        lbl_p_fixed = QLabel(T("p_fixed"))
        lbl_p_fixed.setFixedWidth(100)

        self.slider_p_fixed = QSlider(Qt.Horizontal)
        self.slider_p_fixed.setRange(0, 100)
        self.slider_p_fixed.setValue(100)
        self.val_p_fixed = QLabel("100 %")
        self.val_p_fixed.setFixedWidth(45)
        self.slider_p_fixed.valueChanged.connect(lambda v: self.val_p_fixed.setText(f"{v} %"))

        fixed_layout.addWidget(lbl_p_fixed)
        fixed_layout.addWidget(self.slider_p_fixed)
        fixed_layout.addWidget(self.val_p_fixed)
        main_layout.addWidget(self.box_fixed)

        self.update_graph_auto()
        self.update_ui_mode()

    def toggle_auto_controls(self):
        is_visible = self.container_auto_controls.isVisible()
        self.container_auto_controls.setVisible(not is_visible)
        self.update_auto_toggle_text()

    def update_auto_toggle_text(self):
        if self.container_auto_controls.isVisible():
            self.btn_toggle_auto.setText(T("hide_curve_params"))
        else:
            t_m = self.slider_t_min.value()
            t_M = self.slider_t_max.value()
            p_m = self.slider_p_min.value()
            p_M = self.slider_p_max.value()
            self.btn_toggle_auto.setText(T("show_curve_params").format(tm=t_m, tM=t_M, pm=p_m, pM=p_M))

    def toggle_manual_controls(self):
        is_visible = self.container_manual_controls.isVisible()
        self.container_manual_controls.setVisible(not is_visible)
        self.update_manual_toggle_text()

    def update_manual_toggle_text(self):
        if self.container_manual_controls.isVisible():
            self.btn_toggle_manual.setText(T("hide_graph_ctrls"))
        else:
            min_x = self.spin_scale_min.value()
            max_x = self.spin_scale_max.value()
            self.btn_toggle_manual.setText(T("show_graph_ctrls").format(min=min_x, max=max_x))

    def on_manual_scale_changed(self):
        min_v = self.spin_scale_min.value()
        max_v = self.spin_scale_max.value()
        if min_v >= max_v: return
        self.graph_manual.MIN_T = min_v
        self.graph_manual.MAX_T = max_v
        self.graph_manual.update()

    def create_slider(self, min_v, max_v, def_v):
        s = QSlider(Qt.Horizontal)
        s.setRange(min_v, max_v)
        s.setValue(def_v)
        return s

    def make_row(self, widget, label):
        container = QWidget()
        l = QHBoxLayout(container)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(widget)
        l.addWidget(label)
        label.setFixedWidth(55)
        return container

    def on_node_selected(self, temp, pwm):
        if not self.container_manual_controls.isVisible():
            self.toggle_manual_controls()
        self.box_node_edit.show()
        self.spin_temp.blockSignals(True)
        self.spin_pwm.blockSignals(True)
        self.spin_temp.setValue(temp)
        self.spin_pwm.setValue(pwm)
        self.spin_temp.blockSignals(False)
        self.spin_pwm.blockSignals(False)

    def on_spinbox_changed(self):
        new_t = self.spin_temp.value()
        new_p = self.spin_pwm.value()
        safe_t, safe_p = self.graph_manual.update_selected_node_from_spinbox(new_t, new_p)
        if safe_t is not None and safe_p is not None:
            self.spin_temp.blockSignals(True)
            self.spin_temp.setValue(safe_t)
            self.spin_temp.blockSignals(False)

    def update_ui_mode(self):
        mode = "fixed"
        if self.radio_auto.isChecked(): mode = "auto"
        elif self.radio_manual.isChecked(): mode = "manual"
        elif self.radio_pid.isChecked(): mode = "pid"

        self.box_auto.setVisible(mode == "auto")
        self.box_manual.setVisible(mode == "manual")
        self.box_pid.setVisible(mode == "pid")
        self.box_fixed.setVisible(mode == "fixed")
        if mode != "manual":
            self.box_node_edit.hide()
            self.graph_manual.selected_idx = -1

    def update_graph_auto(self):
        self.graph_auto.update_curve(
            self.slider_t_min.value(), self.slider_t_max.value(),
            self.slider_p_min.value(), self.slider_p_max.value(),
            self.slider_gamma.value() / 10.0, self.last_known_temp
        )

    def save_channel_name(self):
        global_config["channels_names"][str(self.channel_id)] = self.edit_name.text()
        save_config(global_config)

    def rename_current_sensor(self):
        s_id = self.combo_sensors.currentData()
        if not s_id: return
        current_name = self.combo_sensors.currentText()
        new_name, ok = QInputDialog.getText(self, T("dialog_ren_title"), T("dialog_ren_msg"), QLineEdit.Normal, current_name)
        if ok and new_name.strip():
            global_config["sensors"][s_id] = new_name.strip()
            save_config(global_config)
            self.refresh_sensors()

    def refresh_sensors(self):
        current_selection = self.combo_sensors.currentData()
        current_cold = self.combo_delta_cold.currentData()
        self.combo_sensors.clear()
        self.combo_delta_cold.clear()
        for s_id, hardware_label in self.engine.get_available_sensors().items():
            display_name = global_config["sensors"].get(s_id, hardware_label)
            self.combo_sensors.addItem(display_name, s_id)
            self.combo_delta_cold.addItem(display_name, s_id)
        if current_selection:
            index = self.combo_sensors.findData(current_selection)
            if index >= 0: self.combo_sensors.setCurrentIndex(index)
        if current_cold:
            index = self.combo_delta_cold.findData(current_cold)
            if index >= 0: self.combo_delta_cold.setCurrentIndex(index)

    def process_telemetry(self, temps_dict, rpms_dict, volts_dict, is_controlling):
        sensor_id = self.combo_sensors.currentData()
        cold_sensor_id = self.combo_delta_cold.currentData()
        raw_temp = temps_dict.get(sensor_id)

        if self.chk_delta.isChecked() and cold_sensor_id:
            cold_temp = temps_dict.get(cold_sensor_id)
            working_temp = self.engine.calculate_virtual_delta(raw_temp, cold_temp)
            display_str = f"Delta T: {working_temp:.1f} °C" if working_temp is not None else f"Delta T: {T('err_sensor')}"
        else:
            working_temp = raw_temp
            display_str = f"Temp: {format_temp(working_temp)}"

        rpm = rpms_dict.get(self.channel_id, 0)
        self.lbl_rpm.setText(f"Speed: {rpm} RPM")

        volt = volts_dict.get(self.channel_id, 0.0)
        self.lbl_volt.setText(f"Volt: {volt:.2f} V")

        if working_temp is not None:
            if self.chk_hysteresis.isChecked():
                max_samples = int(self.spin_hysteresis.value())
                self.temp_history.append(working_temp)
                if len(self.temp_history) > max_samples:
                    self.temp_history.pop(0)
                working_temp = sum(self.temp_history) / len(self.temp_history)
            else:
                self.temp_history.clear()

        if working_temp is not None:
            self.last_known_temp = working_temp
            self.lbl_temp.setText(display_str)
        else:
            self.lbl_temp.setText(f"Temp: {T('err_sensor')}")

        # --- INIZIO NUOVA LOGICA DI MAPPATURA ---
        logical_percent = None

        if self.radio_fixed.isChecked():
            logical_percent = float(self.slider_p_fixed.value())
        else:
            if working_temp is not None:
                if self.radio_pid.isChecked():
                    target = self.spin_pid_target.value()

                    pid_mode = "Normal"
                    if self.radio_pid_slow.isChecked(): pid_mode = "Slow"
                    elif self.radio_pid_fast.isChecked(): pid_mode = "Fast"
                    elif self.radio_pid_custom.isChecked(): pid_mode = "Custom"

                    kp = self.spin_pid_kp.value()
                    ki = self.spin_pid_ki.value()
                    kd = self.spin_pid_kd.value()

                    # Chiamata pulita: calcola solo la logica da 0 a 100
                    logical_percent = self.engine.calculate_pwm_pid(
                        self.channel_id, working_temp, target,
                        pid_mode, kp, ki, kd
                    )
                elif self.radio_auto.isChecked():
                    logical_percent = self.engine.calculate_pwm_auto(
                        working_temp, self.slider_t_min.value(), self.slider_t_max.value(),
                        self.slider_p_min.value(), self.slider_p_max.value(), self.slider_gamma.value() / 10.0
                    )
                elif self.radio_manual.isChecked():
                    logical_percent = self.engine.calculate_pwm_manual(working_temp, self.graph_manual.points)

        # Mappatura Hardware (Potenza Minima)
        if logical_percent is not None:
            hw_config = global_config.get("hardware_channels", {}).get(str(self.channel_id), {})
            min_power = hw_config.get("min_power", 0)

            # Converte il valore logico in fisico tramite il motore
            pwm_val_byte, hardware_percent = self.engine.apply_hardware_limits(
                self.channel_id, logical_percent, min_power
            )

            self.lbl_pwm.setText(f"Power: {int(hardware_percent)} %")

            if working_temp is not None:
                self.graph_auto.update_curve(self.slider_t_min.value(), self.slider_t_max.value(), self.slider_p_min.value(), self.slider_p_max.value(), self.slider_gamma.value() / 10.0, working_temp)
                self.graph_manual.update_telemetry(working_temp, hardware_percent)

            if is_controlling:
                return pwm_val_byte

        return None

    def get_state(self):
        mode = "fixed"
        if self.radio_auto.isChecked(): mode = "auto"
        elif self.radio_manual.isChecked(): mode = "manual"
        elif self.radio_pid.isChecked(): mode = "pid"
        return {
            "sensor": self.combo_sensors.currentData(),
            "delta_en": self.chk_delta.isChecked(),
            "delta_cold": self.combo_delta_cold.currentData(),
            "mode": mode,
            "hyst_en": self.chk_hysteresis.isChecked(),
            "hyst_sec": int(self.spin_hysteresis.value()),
            "t_min": self.slider_t_min.value(),
            "t_max": self.slider_t_max.value(),
            "p_min": self.slider_p_min.value(),
            "p_max": self.slider_p_max.value(),
            "gamma": self.slider_gamma.value(),
            "points": self.graph_manual.points,
            "p_fixed": self.slider_p_fixed.value(),
            "pid_target": self.spin_pid_target.value(),
            "m_scale_min": self.spin_scale_min.value(),
            "m_scale_max": self.spin_scale_max.value(),
            "pid_mode": "Slow" if self.radio_pid_slow.isChecked() else "Fast" if self.radio_pid_fast.isChecked() else "Custom" if self.radio_pid_custom.isChecked() else "Normal",
            "pid_kp": self.spin_pid_kp.value(),
            "pid_ki": self.spin_pid_ki.value(),
            "pid_kd": self.spin_pid_kd.value()
        }

    def set_state(self, state_dict):
        if not state_dict: return
        s_id = state_dict.get("sensor")
        if s_id:
            index = self.combo_sensors.findData(s_id)
            if index >= 0: self.combo_sensors.setCurrentIndex(index)

        cold_id = state_dict.get("delta_cold")
        if cold_id:
            index = self.combo_delta_cold.findData(cold_id)
            if index >= 0: self.combo_delta_cold.setCurrentIndex(index)

        mode = state_dict.get("mode", "auto")
        if mode == "fixed": self.radio_fixed.setChecked(True)
        elif mode == "manual": self.radio_manual.setChecked(True)
        elif mode == "pid": self.radio_pid.setChecked(True)
        else: self.radio_auto.setChecked(True)

        self.chk_delta.setChecked(state_dict.get("delta_en", False))
        self.chk_hysteresis.setChecked(state_dict.get("hyst_en", False))
        self.spin_hysteresis.setValue(state_dict.get("hyst_sec", 5))

        self.slider_p_fixed.setValue(state_dict.get("p_fixed", 100))
        self.spin_pid_target.setValue(state_dict.get("pid_target", 35.0))

        pmode = state_dict.get("pid_mode", "Normal")
        if pmode == "Slow": self.radio_pid_slow.setChecked(True)
        elif pmode == "Fast": self.radio_pid_fast.setChecked(True)
        elif pmode == "Custom": self.radio_pid_custom.setChecked(True)
        else: self.radio_pid_normal.setChecked(True)

        self.spin_pid_kp.setValue(state_dict.get("pid_kp", 0.0))
        self.spin_pid_ki.setValue(state_dict.get("pid_ki", 0.0))
        self.spin_pid_kd.setValue(state_dict.get("pid_kd", 0.0))

        self.slider_t_min.setValue(state_dict.get("t_min", 35))
        self.slider_t_max.setValue(state_dict.get("t_max", 45))
        self.slider_p_min.setValue(state_dict.get("p_min", 0))
        self.slider_p_max.setValue(state_dict.get("p_max", 100))
        self.slider_gamma.setValue(state_dict.get("gamma", 10))

        m_scale_min = state_dict.get("m_scale_min", 10)
        m_scale_max = state_dict.get("m_scale_max", 100)
        self.spin_scale_min.blockSignals(True)
        self.spin_scale_max.blockSignals(True)
        self.spin_scale_min.setValue(m_scale_min)
        self.spin_scale_max.setValue(m_scale_max)
        self.spin_scale_min.blockSignals(False)
        self.spin_scale_max.blockSignals(False)
        self.graph_manual.MIN_T = m_scale_min
        self.graph_manual.MAX_T = m_scale_max

        if "points" in state_dict:
            self.graph_manual.points = [list(p) for p in state_dict["points"]]
        else:
            self.graph_manual.points = [[25.0, 20.0], [45.0, 40.0], [70.0, 100.0]]

        self.graph_manual.selected_idx = -1
        self.box_node_edit.hide()
        self.graph_auto.update()
        self.graph_manual.update()
        self.update_ui_mode()

        self.update_auto_toggle_text()
        self.update_manual_toggle_text()
        self.temp_history.clear()


class ProcessMappingDialog(QDialog):
    """Componente per l'interfaccia di assegnazione tra processi del sistema operativo e profili termici."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T("proc_title"))
        self.resize(450, 300)
        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.refresh_list()
        layout.addWidget(self.list_widget)

        add_layout = QHBoxLayout()
        self.txt_process = QLineEdit()
        self.txt_process.setPlaceholderText(T("proc_ph"))

        self.combo_profiles = QComboBox()
        self.combo_profiles.addItems(global_config.get("profiles", {}).keys())

        self.btn_add = QPushButton(T("btn_add"))
        self.btn_add.clicked.connect(self.add_mapping)

        add_layout.addWidget(self.txt_process, stretch=2)
        add_layout.addWidget(QLabel(" ➡️ "))
        add_layout.addWidget(self.combo_profiles, stretch=1)
        add_layout.addWidget(self.btn_add)
        layout.addLayout(add_layout)

        self.btn_remove = QPushButton(T("btn_remove"))
        self.btn_remove.setStyleSheet("background-color: #ff3333; color: #ffffff;")
        self.btn_remove.clicked.connect(self.remove_mapping)
        layout.addWidget(self.btn_remove)

    def refresh_list(self):
        self.list_widget.clear()
        process_map = global_config.get("process_profiles", {})
        for proc, prof in process_map.items():
            self.list_widget.addItem(f"{proc} ➡️ {prof}")

    def add_mapping(self):
        proc = self.txt_process.text().strip()
        prof = self.combo_profiles.currentText()
        if proc and prof:
            if "process_profiles" not in global_config:
                global_config["process_profiles"] = {}
            global_config["process_profiles"][proc] = prof
            save_config(global_config)
            self.txt_process.clear()
            self.refresh_list()

    def remove_mapping(self):
        selected = self.list_widget.currentItem()
        if selected:
            text = selected.text()
            proc = text.split(" ➡️ ")[0]
            if proc in global_config.get("process_profiles", {}):
                del global_config["process_profiles"][proc]
                save_config(global_config)
                self.refresh_list()

class MeltdownDialog(QDialog):
    """Finestra popup modale di avviso critico attivata dal sistema Fail-Safe."""
    def __init__(self, messages, actions_sec, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(550, 300)

        self.cmd_en = actions_sec.get("cmd_en", False)
        self.cmd_val = actions_sec.get("cmd_val", "")
        self.countdown = 10

        layout = QVBoxLayout(self)

        bg = QFrame()
        bg.setStyleSheet("background-color: rgba(30, 30, 46, 250); border: 4px solid #ff3333; border-radius: 12px;")
        bg_layout = QVBoxLayout(bg)

        title = QLabel(T("alarm_critical_title"))
        title.setStyleSheet("color: #ff3333; font-size: 22px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        bg_layout.addWidget(title)

        msg_text = "\n".join(messages)
        lbl_msg = QLabel(msg_text)
        lbl_msg.setStyleSheet("color: #cdd6f4; font-size: 16px;")
        lbl_msg.setAlignment(Qt.AlignCenter)
        lbl_msg.setWordWrap(True)
        bg_layout.addWidget(lbl_msg)

        self.lbl_timer = QLabel("")
        self.lbl_timer.setStyleSheet("color: #00e5ff; font-size: 18px; font-weight: bold;")
        self.lbl_timer.setAlignment(Qt.AlignCenter)
        bg_layout.addWidget(self.lbl_timer)

        self.btn_action = QPushButton()
        self.btn_action.setStyleSheet("background-color: #ff3333; color: #ffffff; font-size: 18px; font-weight: bold; padding: 15px;")
        self.btn_action.clicked.connect(self.on_button_click)
        bg_layout.addWidget(self.btn_action)

        layout.addWidget(bg)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        if self.cmd_en and self.cmd_val:
            self.btn_action.setText(T("alarm_cancel_exec").format(s=self.countdown))
            self.lbl_timer.setText(T("alarm_exec_in").format(s=self.countdown))
            self.timer.start(1000)
        else:
            self.btn_action.setText(T("alarm_close_verify"))
            self.lbl_timer.hide()

        self.center_on_screen()

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def update_timer(self):
        self.countdown -= 1
        if self.countdown <= 0:
            self.timer.stop()
            self.execute_command()
        else:
            self.lbl_timer.setText(T("alarm_exec_in").format(s=self.countdown))
            self.btn_action.setText(T("alarm_cancel_exec").format(s=self.countdown))

    def execute_command(self):
        try:
            subprocess.Popen(self.cmd_val, shell=True)
        except Exception as e:
            print(f"Errore comando emergenza: {e}")
        self.accept()

    def on_button_click(self):
        self.timer.stop()
        self.accept()


class SparklineWidget(QWidget):
    """Mini-grafico a linea privo di griglie per mostrare il trend (storico) di un sensore."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(25) # Altezza piccolissima, perfetta per stare dentro una card
        self.data = []

    def update_data(self, data_list):
        self.data = data_list
        self.update()

    def paintEvent(self, event):
        if not self.data or len(self.data) < 2:
            return # Niente da disegnare se non c'è storico

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        min_val = min(self.data)
        max_val = max(self.data)

        # Se i valori sono tutti uguali (es. temperatura fissa), allarghiamo il range visivo
        # per far passare la linea al centro invece di appiattirla sul fondo
        if max_val - min_val < 0.1:
            min_val -= 1.0
            max_val += 1.0

        range_val = max_val - min_val

        polygon = QPolygonF()
        polygon.append(QPointF(0, h)) # Punto di origine in basso a sinistra per il riempimento

        step_x = w / (len(self.data) - 1)

        for i, val in enumerate(self.data):
            x = i * step_x
            # 2px di padding sopra e sotto per non tagliare la linea ai bordi
            y = h - ((val - min_val) / range_val) * (h - 4) - 2
            polygon.append(QPointF(x, y))

        polygon.append(QPointF(w, h)) # Punto finale in basso a destra per chiudere il riempimento

        # 1. Disegna lo sfondo sfumato/semi-trasparente
        brush_color = QColor("#00e5ff")
        brush_color.setAlpha(30) # Molto trasparente
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(brush_color))
        painter.drawPolygon(polygon)

        # 2. Disegna la linea vera e propria (escludendo i punti di origine sul fondo)
        painter.setPen(QPen(QColor("#00e5ff"), 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        painter.drawPolyline(polygon.mid(1, len(self.data)))


class PWMFillBar(QWidget):
    """Barra di riempimento ultra-sottile per indicare il carico percentuale (0-100%)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(4) # Ultra-sottile e non invasiva
        self.percent = 0

    def update_value(self, percent):
        self.percent = max(0, min(100, percent))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Sfondo della barra (vuoto)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#313244")))
        painter.drawRoundedRect(0, 0, w, h, 2, 2)

        # 2. Riempimento dinamico
        if self.percent > 0:
            fill_w = int((self.percent / 100.0) * w)

            # Cambia colore visivamente se la ventola sta lavorando molto
            if self.percent < 50:
                color = QColor("#00e5ff") # Turchese AquaControl
            elif self.percent < 80:
                color = QColor("#f9e2af") # Giallo/Ambra morbido
            else:
                color = QColor("#ff3333") # Rosso di allerta

            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(0, 0, fill_w, h, 2, 2)
