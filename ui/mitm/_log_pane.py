# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/mitm/_log_pane.py — Dual MITM and Passive Event Logs
"""

import time
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QSplitter
)
import config

class MITMLogPane(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.log_splitter = QSplitter(Qt.Orientation.Vertical)

        # Top Log (MITM)
        top_log_container = QWidget()
        top_log_layout = QVBoxLayout(top_log_container)
        top_log_layout.setContentsMargins(0, 0, 0, 0)
        top_log_layout.setSpacing(8)

        log_hdr = QLabel("MITM EVENT LOG")
        log_hdr.setObjectName("section_header")
        top_log_layout.addWidget(log_hdr)

        self._log = QTextEdit()
        self._log.document().setMaximumBlockCount(1000)
        self._log.setObjectName("event_log")
        self._log.setReadOnly(True)
        self._log.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        top_log_layout.addWidget(self._log)

        self.log_splitter.addWidget(top_log_container)

        # Bottom Log (Passive)
        bottom_log_container = QWidget()
        bottom_log_layout = QVBoxLayout(bottom_log_container)
        bottom_log_layout.setContentsMargins(0, 0, 0, 0)
        bottom_log_layout.setSpacing(8)

        passive_hdr = QLabel("PASSIVE EVENT LOG")
        passive_hdr.setObjectName("section_header")
        bottom_log_layout.addWidget(passive_hdr)

        self._passive_log = QTextEdit()
        self._passive_log.document().setMaximumBlockCount(1000)
        self._passive_log.setObjectName("event_log")
        self._passive_log.setReadOnly(True)
        self._passive_log.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        bottom_log_layout.addWidget(self._passive_log)

        self.log_splitter.addWidget(bottom_log_container)
        
        layout.addWidget(self.log_splitter)

    def log_message(self, message: str, level: str = "INFO") -> None:
        colors = {
            "INFO": config.COLOR_TEXT_PRIMARY,
            "WARN": config.COLOR_ACCENT_ORANGE,
            "CRIT": config.COLOR_ACCENT_RED,
            "EXEC": config.COLOR_ACCENT_CYAN,
        }
        color = colors.get(level, config.COLOR_TEXT_PRIMARY)
        timestamp = time.strftime("%H:%M:%S")
        formatted = f'<span style="color: {config.COLOR_TEXT_DIM};">[{timestamp}]</span> <span style="color: {color};">[{level}]</span> <span style="color: {config.COLOR_TEXT_PRIMARY};">{message}</span>'
        self._log.append(formatted)

    def log_passive(self, message: str, level: str = "INFO") -> None:
        colors = {
            "INFO": config.COLOR_TEXT_PRIMARY,
            "WARN": config.COLOR_ACCENT_ORANGE,
            "CRIT": config.COLOR_ACCENT_RED,
            "EXEC": config.COLOR_ACCENT_GREEN,
            "DATA": config.COLOR_ACCENT_GREEN,
        }
        color = colors.get(level, config.COLOR_TEXT_PRIMARY)
        timestamp = time.strftime("%H:%M:%S")
        formatted = f'<span style="color: {config.COLOR_TEXT_DIM};">[{timestamp}]</span> <span style="color: {color};">[{level}]</span> <span style="color: {config.COLOR_TEXT_PRIMARY};">{message}</span>'
        self._passive_log.append(formatted)
        self._passive_log.verticalScrollBar().setValue(
            self._passive_log.verticalScrollBar().maximum()
        )
