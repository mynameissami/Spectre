# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/mitm/_config_pane.py — Network and Attack Configuration
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QLineEdit, QSlider
)
from ui.settings.widgets import ComboBox

class MITMConfigPane(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        config_content = QFrame()
        config_content.setObjectName("panel")
        config_layout = QVBoxLayout(config_content)
        config_layout.setContentsMargins(16, 16, 16, 16)
        config_layout.setSpacing(16)

        # Network Configuration
        net_title = QLabel("NETWORK CONFIGURATION")
        net_title.setObjectName("section_header")
        config_layout.addWidget(net_title)

        self._target_lbl = QLabel("TARGET IP:")
        self._target_lbl.setObjectName("status_key")
        config_layout.addWidget(self._target_lbl)

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("e.g., Target IP")
        config_layout.addWidget(self.target_input)

        self._gateway_lbl = QLabel("GATEWAY IP (Router):")
        self._gateway_lbl.setObjectName("status_key")
        config_layout.addWidget(self._gateway_lbl)

        self.gateway_input = QLineEdit()
        self.gateway_input.setPlaceholderText("e.g., Gateway IP")
        config_layout.addWidget(self.gateway_input)

        self._block_target_lbl = QLabel("BLOCK TARGET (IP/Domain):")
        self._block_target_lbl.setObjectName("status_key")
        self._block_target_lbl.setStyleSheet("color: #FFD700;")
        config_layout.addWidget(self._block_target_lbl)

        self.block_target_input = QLineEdit()
        self.block_target_input.setPlaceholderText("e.g., windowsupdate.com or Target IP")
        config_layout.addWidget(self.block_target_input)

        config_layout.addSpacing(8)

        # Attack Configuration
        vec_title = QLabel("ATTACK VECTORS")
        vec_title.setObjectName("section_header")
        config_layout.addWidget(vec_title)

        vec_lbl = QLabel("MITM VECTOR:")
        vec_lbl.setObjectName("status_key")
        config_layout.addWidget(vec_lbl)

        self.vector_combo = ComboBox()
        self.vector_combo.addItems([
            "ARP SPOOFING (Poisoning)",
            "DNS SPOOFING (Redirection)",
            "CREDENTIAL HARVESTER (Passive)",
            "HTTP INJECTOR (Visual)",
            "TCP RST INJECTOR (Precision Block)",
            "SESSION & JWT SNIFFER (Passive)",
        ])
        config_layout.addWidget(self.vector_combo)

        int_lbl = QLabel("PACKET RATE (PPS):")
        int_lbl.setObjectName("status_key")
        config_layout.addWidget(int_lbl)

        int_layout = QHBoxLayout()
        int_layout.setSpacing(10)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(1, 100)
        self.slider.setValue(50)
        self._slider_val = QLabel("50%")
        self._slider_val.setObjectName("status_value_alert")
        self._slider_val.setMinimumWidth(35)
        self.slider.valueChanged.connect(lambda v: self._slider_val.setText(f"{v}%"))
        int_layout.addWidget(self.slider)
        int_layout.addWidget(self._slider_val)
        config_layout.addLayout(int_layout)
        config_layout.addStretch()

        layout.addWidget(config_content)
