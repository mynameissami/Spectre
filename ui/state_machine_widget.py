# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/state_machine_widget.py — Minimalist Protocol State Machine
Clean, lightweight, and informative.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsTextItem,
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient
from PySide6.QtCore import Qt, QRectF, QPointF
import config


class StateBox(QGraphicsRectItem):
    def __init__(self, x, y, width, height, label, color, scene):
        rect = QRectF(0, 0, width, height)
        super().__init__(rect)
        self.setPos(x, y)
        self.base_color = QColor(color)

        # Simple Gradient
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, self.base_color.lighter(110))
        gradient.setColorAt(1, self.base_color.darker(110))

        self.setBrush(QBrush(gradient))
        self.setPen(QPen(self.base_color, 2))
        scene.addItem(self)

        # Label
        self.text = QGraphicsTextItem(label, self)
        self.text.setDefaultTextColor(QColor("#FFFFFF"))
        font = QFont("Consolas", 9, QFont.Bold)
        self.text.setFont(font)

        tw = self.text.boundingRect().width()
        th = self.text.boundingRect().height()
        self.text.setPos((width - tw) / 2, (height - th) / 2)

    def activate(self):
        self.setPen(QPen(self.base_color, 4))
        self.setBrush(QBrush(self.base_color.lighter(130)))

    def deactivate(self):
        gradient = QLinearGradient(0, 0, 0, self.rect().height())
        gradient.setColorAt(0, self.base_color.lighter(110))
        gradient.setColorAt(1, self.base_color.darker(110))
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(self.base_color, 2))


class StateMachineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_state = "INIT"
        self._states = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header = QLabel("◈ 802.11 CONNECTION STATE MACHINE")
        header.setStyleSheet(f"""
            color: {config.COLOR_ACCENT_CYAN};
            font-size: 13px;
            font-weight: bold;
            font-family: 'Consolas', monospace;
            padding: 5px;
        """)
        layout.addWidget(header)

        # Graphics View
        self._scene = QGraphicsScene()
        self._scene.setBackgroundBrush(QColor("#0A0A0A"))

        self._view = QGraphicsView(self._scene)
        self._view.setRenderHint(QPainter.Antialiasing)
        self._view.setBackgroundBrush(QColor("#0A0A0A"))
        self._view.setFrameShape(QGraphicsView.NoFrame)
        self._view.setFixedSize(700, 250)
        layout.addWidget(self._view, alignment=Qt.AlignCenter)

        # Info Panel (Adds context)
        self._info_panel = QLabel("System initialized. Waiting for 802.11 traffic...")
        self._info_panel.setStyleSheet(f"""
            background-color: #151520;
            border: 1px solid {config.COLOR_BORDER};
            border-radius: 4px;
            padding: 10px;
            color: {config.COLOR_TEXT_PRIMARY};
            font-family: 'Consolas', monospace;
            font-size: 11px;
        """)
        self._info_panel.setWordWrap(True)
        layout.addWidget(self._info_panel)

        self._init_states()

    def _init_states(self):
        # Minimalist coordinates
        states_config = {
            "INIT": (40, 100, "INIT (Unauthenticated)", "#00FF41"),
            "AUTH_PENDING": (240, 30, "AUTH PENDING", "#00D4FF"),
            "AUTHENTICATED": (440, 30, "AUTHENTICATED", "#00D4FF"),
            "ASSOC_PENDING": (240, 170, "ASSOC PENDING", "#00D4FF"),
            "ASSOCIATED": (440, 170, "ASSOCIATED (Data)", "#FFA500"),
        }

        for state_id, (x, y, label, color) in states_config.items():
            self._states[state_id] = StateBox(x, y, 170, 50, label, color, self._scene)

        # Simple Arrows
        arrows = [
            ("INIT", "AUTH_PENDING"),
            ("AUTH_PENDING", "AUTHENTICATED"),
            ("AUTHENTICATED", "ASSOC_PENDING"),
            ("ASSOC_PENDING", "ASSOCIATED"),
        ]

        for start, end in arrows:
            s = self._states[start].boundingRect().center() + self._states[start].pos()
            e = self._states[end].boundingRect().center() + self._states[end].pos()

            line = self._scene.addLine(s.x(), s.y(), e.x(), e.y())
            line.setPen(QPen(QColor("#5A5A6A"), 2, Qt.DashLine))

        self._scene.setSceneRect(0, 0, 650, 250)
        self._view.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)
        self._states["INIT"].activate()

    def transition_to(self, new_state: str, frame_info: str = ""):
        if new_state not in self._states:
            return

        if self._current_state in self._states:
            self._states[self._current_state].deactivate()

        self._states[new_state].activate()
        self._current_state = new_state

        # Update Info Panel with context
        descriptions = {
            "INIT": "Device is powered on but not connected. Vulnerable to discovery.",
            "AUTH_PENDING": "Device requesting authentication from AP. (Layer 2)",
            "AUTHENTICATED": "Identity verified. Preparing to associate.",
            "ASSOC_PENDING": "Device requesting to join the network map.",
            "ASSOCIATED": "Connection established. Data traffic flowing securely.",
        }

        color = self._states[new_state].base_color.name()
        self._info_panel.setText(
            f"<span style='color:{color}; font-weight:bold;'>[{new_state}]</span> {descriptions.get(new_state, '')}<br>"
            f"<span style='color:#888;'>Last Event: {frame_info}</span>"
        )

    def reset(self):
        for state_id, box in self._states.items():
            box.deactivate() if state_id != "INIT" else box.activate()
        self._current_state = "INIT"
        self._info_panel.setText("System reset. Waiting for traffic...")
