# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/mitm/_payload_pane.py — HTTP Injection Payload Configuration
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton
)
import config
from ui.settings.widgets import ComboBox

class MITMPayloadPane(QWidget):
    payload_updated = Signal(str, str)  # payload_type, custom_script

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        payload_layout = QVBoxLayout(self)
        payload_layout.setContentsMargins(16, 0, 0, 0)
        payload_layout.setSpacing(12)

        payload_hdr = QLabel("PAYLOAD CONFIGURATION")
        payload_hdr.setObjectName("section_header")
        payload_hdr.setStyleSheet("margin-top: 4px;") # Align with left side
        payload_layout.addWidget(payload_hdr)

        payload_lbl = QLabel("PAYLOAD TYPE:")
        payload_lbl.setObjectName("status_key")
        payload_layout.addWidget(payload_lbl)

        self.payload_dropdown = ComboBox()
        self.payload_dropdown.addItems(
            [
                "Black/Green Screen (Default)",
                "Simple Alert Box",
                "Page Redirect (to attacker IP)",
                "Custom Payload",
            ]
        )
        payload_layout.addWidget(self.payload_dropdown)

        script_lbl = QLabel("CUSTOM SCRIPT:")
        script_lbl.setObjectName("status_key")
        payload_layout.addWidget(script_lbl)

        self.payload_script_editor = QTextEdit()
        self.payload_script_editor.setObjectName("payload_editor")
        self.payload_script_editor.setPlaceholderText("Enter raw JavaScript here...")
        self.payload_script_editor.setMinimumHeight(150)
        self.payload_script_editor.setMaximumHeight(250)
        
        # Apply a custom monospace dark theme just for this script editor
        self.payload_script_editor.setStyleSheet(f"""
            QTextEdit#payload_editor {{
                background-color: {config.COLOR_BG};
                color: {config.COLOR_ACCENT_CYAN};
                font-family: "Courier New", Consolas, monospace;
                font-size: 13px;
                border: 1px solid {config.COLOR_BORDER};
                border-left: 3px solid {config.COLOR_ACCENT_GREEN};
                border-radius: 4px;
                padding: 10px;
            }}
            QTextEdit#payload_editor:focus {{
                border: 1px solid {config.COLOR_ACCENT_CYAN};
                border-left: 3px solid {config.COLOR_ACCENT_CYAN};
                background-color: #08080C;
            }}
        """)
        payload_layout.addWidget(self.payload_script_editor)

        self.inject_btn = QPushButton("INJECT PAYLOAD")
        self.inject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_btn_theme(self.inject_btn, "orange")
        self.inject_btn.clicked.connect(self._on_inject_payload)
        payload_layout.addWidget(self.inject_btn)

        payload_layout.addStretch()

    def _set_btn_theme(self, btn: QPushButton, theme: str, active: str = "false") -> None:
        btn.setProperty("btnTheme", theme)
        btn.setProperty("btnActive", active)
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def _on_inject_payload(self) -> None:
        payload_type = self.payload_dropdown.currentText()
        custom_script = self.payload_script_editor.toPlainText()
        self.payload_updated.emit(payload_type, custom_script)
