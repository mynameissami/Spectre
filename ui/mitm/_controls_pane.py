# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/mitm/_controls_pane.py — Attack Module Controls and Passive Management
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
)
from ui.settings.widgets import ComboBox

class MITMControlsPane(QWidget):
    engage_module_requested = Signal(str)  # vector
    engage_passive_requested = Signal()
    terminate_all_requested = Signal()
    terminate_passive_selected = Signal(str) # module_id
    terminate_all_passive_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # ── Group 3: Console Actions ──
        actions_group = QFrame()
        actions_group.setObjectName("panel")
        actions_group_layout = QVBoxLayout(actions_group)
        actions_group_layout.setContentsMargins(12, 12, 12, 12)
        actions_group_layout.setSpacing(10)

        act_title = QLabel("MODULE CONTROLS")
        act_title.setObjectName("section_header")
        actions_group_layout.addWidget(act_title)

        # ARP Button
        self.arp_btn = QPushButton("ENGAGE ARP POISONING")
        self.arp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_btn_theme(self.arp_btn, "orange")
        self.arp_btn.clicked.connect(lambda: self.engage_module_requested.emit("ARP SPOOFING (Poisoning)"))
        actions_group_layout.addWidget(self.arp_btn)

        # DNS Button
        self.dns_btn = QPushButton("ENGAGE DNS SPOOFING")
        self.dns_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_btn_theme(self.dns_btn, "cyan")
        self.dns_btn.clicked.connect(lambda: self.engage_module_requested.emit("DNS SPOOFING (Redirection)"))
        actions_group_layout.addWidget(self.dns_btn)

        # Passive Attack Button
        self.passive_btn = QPushButton("ENGAGE PASSIVE ATTACK")
        self.passive_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_btn_theme(self.passive_btn, "green")
        self.passive_btn.clicked.connect(self.engage_passive_requested.emit)
        actions_group_layout.addWidget(self.passive_btn)

        # Terminate All Button
        self.stop_btn = QPushButton("TERMINATE ALL ATTACKS")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_btn_theme(self.stop_btn, "red")
        self.stop_btn.clicked.connect(self.terminate_all_requested.emit)
        actions_group_layout.addWidget(self.stop_btn)

        # ── Passive Module Management (NEW) ──
        passive_group = QFrame()
        passive_group.setObjectName("panel")
        passive_layout = QVBoxLayout(passive_group)
        passive_layout.setContentsMargins(12, 12, 12, 12)
        passive_layout.setSpacing(10)

        pass_title = QLabel("PASSIVE MODULE MANAGEMENT")
        pass_title.setObjectName("section_header")
        passive_layout.addWidget(pass_title)

        passive_row = QHBoxLayout()
        self.passive_dropdown = ComboBox()
        self.passive_dropdown.addItem("No Passive Modules Active")
        self.passive_dropdown.setEnabled(False)
        passive_row.addWidget(self.passive_dropdown, stretch=3)

        self.terminate_selected_passive_btn = QPushButton("TERMINATE SELECTED")
        self.terminate_selected_passive_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_btn_theme(self.terminate_selected_passive_btn, "orange")
        self.terminate_selected_passive_btn.setEnabled(False)
        self.terminate_selected_passive_btn.clicked.connect(self._on_terminate_selected_passive)
        passive_row.addWidget(self.terminate_selected_passive_btn, stretch=1)

        passive_layout.addLayout(passive_row)

        self.terminate_all_passive_btn = QPushButton("TERMINATE ALL PASSIVE MODULES")
        self.terminate_all_passive_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_btn_theme(self.terminate_all_passive_btn, "red")
        self.terminate_all_passive_btn.setEnabled(False)
        self.terminate_all_passive_btn.clicked.connect(self.terminate_all_passive_requested.emit)
        passive_layout.addWidget(self.terminate_all_passive_btn)

        layout.addWidget(passive_group)
        layout.addWidget(actions_group)

    def _set_btn_theme(self, btn: QPushButton, theme: str, active: str = "false") -> None:
        btn.setProperty("btnTheme", theme)
        btn.setProperty("btnActive", active)
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def _on_terminate_selected_passive(self) -> None:
        current_text = self.passive_dropdown.currentText()
        if current_text and current_text != "No Passive Modules Active":
            self.terminate_passive_selected.emit(current_text)

    def update_passive_dropdown(self, module_id: str, is_adding: bool) -> None:
        if is_adding:
            idx = self.passive_dropdown.findText("No Passive Modules Active")
            if idx >= 0:
                self.passive_dropdown.removeItem(idx)

            self.passive_dropdown.addItem(module_id)
            self.passive_dropdown.setCurrentText(module_id)
            self.passive_dropdown.setEnabled(True)
            self.terminate_selected_passive_btn.setEnabled(True)
            self.terminate_all_passive_btn.setEnabled(True)
        else:
            idx = self.passive_dropdown.findText(module_id)
            if idx >= 0:
                self.passive_dropdown.removeItem(idx)

            if self.passive_dropdown.count() == 0:
                self.passive_dropdown.addItem("No Passive Modules Active")
                self.passive_dropdown.setEnabled(False)
                self.terminate_selected_passive_btn.setEnabled(False)
                self.terminate_all_passive_btn.setEnabled(False)

    def reset_buttons(self) -> None:
        self.arp_btn.setText("ENGAGE ARP POISONING")
        self._set_btn_theme(self.arp_btn, "orange")
        self.dns_btn.setText("ENGAGE DNS SPOOFING")
        self._set_btn_theme(self.dns_btn, "cyan")
        self.passive_btn.setText("ENGAGE PASSIVE ATTACK")
        self._set_btn_theme(self.passive_btn, "green")
