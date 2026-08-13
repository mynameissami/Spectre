# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/mitm/_panel.py — Man-in-the-Middle Operations Panel Orchestrator
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QSplitter
)
from PySide6.QtCore import Qt

from ui.mitm._config_pane import MITMConfigPane
from ui.mitm._controls_pane import MITMControlsPane
from ui.mitm._log_pane import MITMLogPane
from ui.mitm._payload_pane import MITMPayloadPane


class MITMPanel(QWidget):
    mitm_started = Signal(str, str, str, int, str)
    mitm_stopped = Signal()
    terminate_passive_selected = Signal(str)
    terminate_all_passive = Signal()
    payload_updated = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # ── Left Side: Config and Controls ───────────────────────────
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(16)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self._config_pane = MITMConfigPane()
        left_layout.addWidget(self._config_pane)

        self._controls_pane = MITMControlsPane()
        left_layout.addWidget(self._controls_pane)
        left_layout.addStretch()

        self._left_container = QScrollArea()
        self._left_container.setWidgetResizable(True)
        self._left_container.setWidget(left_widget)
        self._left_container.setStyleSheet("QScrollArea { background: transparent; border: none; } QScrollArea > QWidget { background: transparent; }")

        # ── Right Side: Logs and Payload ──────────────────────────────
        self._right_container = QWidget()
        right_layout = QHBoxLayout(self._right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        main_h_splitter = QSplitter(Qt.Orientation.Horizontal)

        self._log_pane = MITMLogPane()
        main_h_splitter.addWidget(self._log_pane)

        self._payload_pane = MITMPayloadPane()
        main_h_splitter.addWidget(self._payload_pane)
        self._payload_pane.hide()

        main_h_splitter.setStretchFactor(0, 7)
        main_h_splitter.setStretchFactor(1, 3)

        right_layout.addWidget(main_h_splitter)

        layout.addWidget(self._left_container, 4)
        layout.addWidget(self._right_container, 6)

        # ── Signals ──
        self._config_pane.vector_combo.currentTextChanged.connect(self._on_vector_changed)
        
        self._controls_pane.engage_module_requested.connect(self._engage_module)
        self._controls_pane.engage_passive_requested.connect(self._engage_selected_passive)
        self._controls_pane.terminate_all_requested.connect(self._terminate_all)
        self._controls_pane.terminate_passive_selected.connect(self.terminate_passive_selected.emit)
        self._controls_pane.terminate_all_passive_requested.connect(self.terminate_all_passive.emit)
        
        self._payload_pane.payload_updated.connect(self._on_inject_payload)

        self.log_message("MITM Console Online. Requires root/sudo privileges.", "WARN")

    def _on_vector_changed(self, text: str) -> None:
        if text == "HTTP INJECTOR (Visual)":
            self._payload_pane.show()
        else:
            self._payload_pane.hide()

    def refresh_theme(self) -> None:
        pass

    def reset_passive_button(self) -> None:
        self._controls_pane.passive_btn.setText("ENGAGE PASSIVE ATTACK")
        self._controls_pane._set_btn_theme(self._controls_pane.passive_btn, "green")

    def log_message(self, message: str, level: str = "INFO") -> None:
        self._log_pane.log_message(message, level)

    def log_passive(self, message: str, level: str = "INFO") -> None:
        self._log_pane.log_passive(message, level)

    def update_passive_dropdown(self, module_id: str, is_adding: bool) -> None:
        self._controls_pane.update_passive_dropdown(module_id, is_adding)

    def _engage_module(self, vector: str) -> None:
        target = self._config_pane.target_input.text().strip()
        gateway = self._config_pane.gateway_input.text().strip()
        intensity = self._config_pane.slider.value()

        if not target or not gateway:
            self.log_message("Cannot initiate: Target and Gateway IPs are required.", "CRIT")
            return

        self.log_message(f"ENGAGING {vector} -> Target: {target} | Gateway: {gateway}", "EXEC")
        block_target = self._config_pane.block_target_input.text().strip()
        self.mitm_started.emit(target, gateway, vector, intensity, block_target)

        # Visual feedback
        if "ARP" in vector:
            self._controls_pane.arp_btn.setText("ARP POISONING ACTIVE")
            self._controls_pane._set_btn_theme(self._controls_pane.arp_btn, "orange", "true")
        elif "DNS" in vector:
            self._controls_pane.dns_btn.setText("DNS SPOOFING ACTIVE")
            self._controls_pane._set_btn_theme(self._controls_pane.dns_btn, "cyan", "true")
        elif "PASSIVE" in vector.upper() or "CREDENTIAL" in vector.upper():
            self._controls_pane.passive_btn.setText("PASSIVE ATTACK ACTIVE")
            self._controls_pane._set_btn_theme(self._controls_pane.passive_btn, "green", "true")
        elif "RST" in vector.upper() or "BLOCK" in vector.upper():
            self._controls_pane.passive_btn.setText("RST BLOCKER ACTIVE")
            self._controls_pane._set_btn_theme(self._controls_pane.passive_btn, "gold", "true")
        elif "INJECT" in vector.upper() or "HTTP" in vector.upper():
            self._controls_pane.passive_btn.setText("INJECTOR ACTIVE")
            self._controls_pane._set_btn_theme(self._controls_pane.passive_btn, "magenta", "true")
        elif "SESSION" in vector.upper() or "JWT" in vector.upper():
            self._controls_pane.passive_btn.setText("SESSION SNIFFER ACTIVE")
            self._controls_pane._set_btn_theme(self._controls_pane.passive_btn, "purple", "true")

    def _engage_selected_passive(self) -> None:
        vector = self._config_pane.vector_combo.currentText()
        if any(kw in vector.upper() for kw in ["HARVESTER", "INJECTOR", "PASSIVE", "RST", "BLOCK", "COOKIE", "SESSION", "JWT"]):
            self._engage_module(vector)
        else:
            self.log_message("Please select a Passive module from the dropdown.", "CRIT")

    def _terminate_all(self) -> None:
        self.log_message("TERMINATING ALL MITM MODULES...", "WARN")
        self.log_passive("TERMINATING ALL PASSIVE MODULES...", "WARN")
        self.mitm_stopped.emit()
        self._controls_pane.reset_buttons()

    def _on_inject_payload(self, payload_type: str, custom_script: str) -> None:
        self.payload_updated.emit(payload_type, custom_script)
        self.log_message(f"Payload configuration updated: {payload_type}", "EXEC")
