# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/topology_map.py — Visual Network Topology Map
"""

from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsTextItem,
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter  # Added QPainter
import math


class TopologyMap(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene())

        # FIX: Use QPainter.RenderHint.Antialiasing instead of self.renderHint()
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.setStyleSheet("background-color: #08080C; border: 1px solid #1A1A2E;")
        self._nodes = {}

    def clear_map(self):
        self.scene().clear()
        self._nodes = {}

    def add_device(self, ip: str, os_name: str, is_gateway: bool = False):
        if ip in self._nodes:
            return

        # Color coding based on OS
        if is_gateway:
            color = QColor("#FFD700")  # Gold for Gateway
        elif "Windows" in os_name:
            color = QColor("#0078D7")
        elif "Linux" in os_name or "Android" in os_name:
            color = QColor("#00FF41")
        elif "Network" in os_name:
            color = QColor("#FF8C00")
        else:
            color = QColor("#888888")

        # Draw Node (Circle)
        size = 40 if is_gateway else 25
        node = QGraphicsEllipseItem(0, 0, size, size)
        node.setBrush(QBrush(color))
        node.setPen(QPen(Qt.white, 2))

        # Draw IP Label
        text = QGraphicsTextItem(ip)
        text.setDefaultTextColor(Qt.white)
        text.setFont(QFont("monospace", 8))

        # Positioning logic (Radial layout)
        if is_gateway:
            node.setPos(0, 0)  # Center
            text.setPos(-text.boundingRect().width() / 2, size + 5)
        else:
            count = len(self._nodes)
            angle = count * (math.pi / 4)  # 45 degree increments
            radius = 150
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            node.setPos(x, y)
            text.setPos(x - text.boundingRect().width() / 2, y + size + 5)

            # Draw Connection Line to Gateway (0,0)
            if "Gateway" in self._nodes:
                line = QGraphicsLineItem(0, 0, x + size / 2, y + size / 2)
                line.setPen(QPen(QColor("#1A1A2E"), 2))
                self.scene().addItem(line)

        self.scene().addItem(node)
        self.scene().addItem(text)
        self._nodes[ip] = node

        # Center the view
        self.setSceneRect(-250, -250, 500, 500)
