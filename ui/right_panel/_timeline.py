# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/right_panel/_timeline.py — Attack Timeline Widget
"""

import time
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
import config

class TimelineWidget(QWidget):
    """Visual attack timeline with state correlation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._timeline = QTextEdit()
        self._timeline.setReadOnly(True)
        self._timeline.setStyleSheet(f"""
            background-color: {config.COLOR_BG};
            color: {config.COLOR_TEXT_PRIMARY};
            font-family: 'Consolas', monospace;
            font-size: 10pt;
        """)
        layout.addWidget(self._timeline)

    def add_event(self, event_type: str, message: str) -> None:
        colors = {
            "ALERT": config.COLOR_ACCENT_RED,
            "RECON": config.COLOR_ACCENT_ORANGE,
            "INFO": config.COLOR_ACCENT_CYAN,
        }
        color = colors.get(event_type, config.COLOR_TEXT_PRIMARY)
        timestamp = time.strftime("%H:%M:%S")

        html = (
            f'<span style="color:{config.COLOR_TEXT_DIM}">[{timestamp}]</span> '
            f'<span style="color:{color}; font-weight:bold">[{event_type}]</span> '
            f'<span style="color:{config.COLOR_TEXT_PRIMARY}">{message}</span><br>'
        )
        self._timeline.insertHtml(html)
        self._timeline.verticalScrollBar().setValue(
            self._timeline.verticalScrollBar().maximum()
        )

    def refresh_theme(self) -> None:
        """Refresh inline styles after a theme change."""
        self._timeline.setStyleSheet(f"""
            background-color: {config.COLOR_BG};
            color: {config.COLOR_TEXT_PRIMARY};
            font-family: 'Consolas', monospace;
            font-size: 10pt;
        """)
