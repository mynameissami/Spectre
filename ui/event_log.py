# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/event_log.py — Live Scrolling Event Log
HTML-coloured, auto-scrolling, capped-line QTextEdit widget.
"""

from __future__ import annotations

import time
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit

import config


# Colour map for event severity
_LEVEL_COLORS = {
    "INFO":    config.COLOR_ACCENT_CYAN,
    "OK":      config.COLOR_ACCENT_GREEN,
    "WARN":    config.COLOR_ACCENT_ORANGE,
    "ALERT":   config.COLOR_ACCENT_RED,
    "RECON":   "#CC88FF",   # purple for recon events
    "DEBUG":   config.COLOR_TEXT_DIM,
}


class EventLog(QWidget):
    """
    Live-updating scrolling event log with HTML colour coding.

    Enforces a maximum line count (config.EVENT_LOG_MAX_LINES) to
    prevent unbounded memory growth.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._line_count = 0
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header row
        hdr = QHBoxLayout()
        hdr.setContentsMargins(8, 4, 8, 0)

        title = QLabel("◈  LIVE EVENT LOG")
        title.setObjectName("section_header")
        hdr.addWidget(title)
        hdr.addStretch()

        clear_btn = QPushButton("CLR")
        clear_btn.setFixedSize(40, 20)
        clear_btn.setStyleSheet(
            f"font-size:9px; border:1px solid {config.COLOR_TEXT_DIM};"
            f" color:{config.COLOR_TEXT_DIM}; background:transparent;"
            f" border-radius:2px; padding:0px;"
        )
        clear_btn.clicked.connect(self.clear)
        hdr.addWidget(clear_btn)
        layout.addLayout(hdr)

        # Text area
        self._text = QTextEdit()
        self._text.setObjectName("event_log")
        self._text.setReadOnly(True)
        self._text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self._text)

    # ─── Public API ────────────────────────────────────────────────────────────

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Append a new log entry.

        Args:
            message: Human-readable event description.
            level:   Severity key — INFO | OK | WARN | ALERT | RECON | DEBUG
        """
        color     = _LEVEL_COLORS.get(level.upper(), config.COLOR_TEXT_PRIMARY)
        timestamp = time.strftime("%H:%M:%S")
        dim       = config.COLOR_TEXT_DIM

        line = (
            f'<span style="color:{dim};">[{timestamp}]</span> '
            f'<span style="color:{color}; font-weight:bold;">[{level.upper():5s}]</span> '
            f'<span style="color:{config.COLOR_TEXT_PRIMARY};">{self._escape(message)}</span>'
        )

        # Enforce max lines
        if self._line_count >= config.EVENT_LOG_MAX_LINES:
            self._trim_oldest()

        self._text.append(line)
        self._line_count += 1

        # Auto-scroll to bottom
        sb = self._text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear(self) -> None:
        self._text.clear()
        self._line_count = 0

    # ─── Internals ─────────────────────────────────────────────────────────────

    def _trim_oldest(self) -> None:
        """Remove the oldest 50 lines from the document."""
        cursor = self._text.textCursor()
        from PySide6.QtGui import QTextCursor
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        trim = min(50, self._line_count)
        for _ in range(trim):
            cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        self._line_count -= trim

    @staticmethod
    def _escape(text: str) -> str:
        """Minimal HTML escaping to prevent injection into QTextEdit HTML."""
        return (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
