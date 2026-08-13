# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/right_panel/_event_log.py — Live Event Log
"""

import time
import re
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListView,
    QStyledItemDelegate,
)
from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex, QSize, QRect
from PySide6.QtGui import QPainter, QColor, QTextDocument
import config

class LogModel(QAbstractListModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logs = [] # list of (timestamp, level, message)

    def rowCount(self, parent=QModelIndex()):
        return len(self.logs)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.UserRole:
            return self.logs[index.row()]
        return None

    def add_log(self, timestamp: str, level: str, message: str):
        self.beginInsertRows(QModelIndex(), len(self.logs), len(self.logs))
        self.logs.append((timestamp, level, message))
        self.endInsertRows()
        
    def clear(self):
        self.beginResetModel()
        self.logs.clear()
        self.endResetModel()

class LogDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ip_regex = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')

    def paint(self, painter: QPainter, option, index):
        log_data = index.data(Qt.ItemDataRole.UserRole)
        if not log_data:
            return
            
        timestamp, level, message = log_data
        
        painter.save()
        
        # Draw timestamp
        ts_rect = QRect(option.rect.left() + 10, option.rect.top(), 80, option.rect.height())
        painter.setPen(QColor(config.COLOR_TEXT_DIM))
        painter.drawText(ts_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, f"[{timestamp}]")
        
        # Draw badge
        badge_rect = QRect(ts_rect.right() + 5, option.rect.top() + 4, 60, option.rect.height() - 8)
        
        colors = {
            "INFO": config.COLOR_ACCENT_CYAN,
            "WARN": config.COLOR_ACCENT_ORANGE,
            "ALERT": config.COLOR_ACCENT_RED,
            "OK": config.COLOR_ACCENT_GREEN,
            "EXEC": "#FF00FF",
            "DEBUG": config.COLOR_TEXT_DIM,
        }
        bg_color_hex = colors.get(level, config.COLOR_TEXT_DIM)
        bg_color = QColor(bg_color_hex)
        
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(badge_rect, 4, 4)
        
        painter.setPen(QColor(config.COLOR_BG))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(9) # Smaller font for badge
        painter.setFont(font)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, level)
        
        # Draw message using QTextDocument for rich text syntax highlighting
        msg_rect = QRect(badge_rect.right() + 15, option.rect.top(), option.rect.width() - badge_rect.right() - 15, option.rect.height())
        font.setBold(False)
        font.setPointSize(10)
        
        doc = QTextDocument()
        doc.setDefaultFont(font)
        
        msg_html = message.replace("<", "&lt;").replace(">", "&gt;")
        msg_html = self.ip_regex.sub(f'<span style="color:{config.COLOR_ACCENT_CYAN}; font-weight:bold;">\\g<0></span>', msg_html)
        msg_html = msg_html.replace("S.P.E.C.T.R.E.", f'<span style="color:{config.COLOR_ACCENT_GREEN}; font-weight:bold;">S.P.E.C.T.R.E.</span>')
        
        doc.setHtml(f"<div style='color:{config.COLOR_TEXT_PRIMARY}; white-space:nowrap;'>{msg_html}</div>")
        
        painter.translate(msg_rect.left(), msg_rect.top() + (msg_rect.height() - doc.size().height()) / 2)
        doc.drawContents(painter)
        
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(0, 26)

class EventLog(QWidget):
    """High-performance structured logging interface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._view = QListView()
        self._model = LogModel()
        self._delegate = LogDelegate()
        
        self._view.setModel(self._model)
        self._view.setItemDelegate(self._delegate)
        self._view.setAlternatingRowColors(True)
        self._view.setSelectionMode(QListView.SelectionMode.NoSelection)
        self._view.setStyleSheet(f"""
            QListView {{
                background-color: {config.COLOR_BG};
                alternate-background-color: {config.COLOR_PANEL_BG};
                color: {config.COLOR_TEXT_PRIMARY};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                outline: 0;
                border: none;
            }}
            QListView::item {{
                border-bottom: 1px solid {config.COLOR_BORDER};
            }}
        """)
        
        layout.addWidget(self._view)

    def log(self, message: str, level: str = "INFO") -> None:
        timestamp = time.strftime("%H:%M:%S")
        self._model.add_log(timestamp, level, message)
        self._view.scrollToBottom()

    def clear(self) -> None:
        """Clear all log entries."""
        self._model.clear()

    def refresh_theme(self) -> None:
        """Refresh inline styles after a theme change."""
        self._view.setStyleSheet(f"""
            QListView {{
                background-color: {config.COLOR_BG};
                alternate-background-color: {config.COLOR_PANEL_BG};
                color: {config.COLOR_TEXT_PRIMARY};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                outline: 0;
                border: none;
            }}
            QListView::item {{
                border-bottom: 1px solid {config.COLOR_BORDER};
            }}
        """)
