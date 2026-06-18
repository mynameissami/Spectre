# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/mitm_panel.py — Man-in-the-Middle Operations Panel
"""

from __future__ import annotations
import time
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QFrame,
    QSlider,
    QTextEdit,
    QLineEdit,
    QScrollArea,
    QSplitter,
)
import config


class MITMPanel(QWidget):
    mitm_started = Signal(
        str, str, str, int, str
    )  # target_ip, gateway_ip, attack_type, intensity
    mitm_stopped = Signal()
    terminate_passive_selected = Signal(
        str
    )  # Emits the ID of the selected passive attack
    terminate_all_passive = Signal()
    payload_updated = Signal(str, str)  # payload_type, custom_script

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._active = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # ── Left Side: Controls ───────────────────────────────────────
        left_widget = QWidget()
        control_pane = QVBoxLayout(left_widget)
        control_pane.setSpacing(16)
        control_pane.setContentsMargins(0, 0, 0, 0)

        # Section Header
        hdr = QLabel("[ MAN-IN-THE-MIDDLE CONSOLE ]")
        hdr.setObjectName("section_header")
        hdr.setStyleSheet(
            f"color: {config.COLOR_ACCENT_RED}; border-bottom: 2px solid {config.COLOR_ACCENT_RED}; font-size: 13px; padding-bottom: 4px;"
        )
        control_pane.addWidget(hdr)

        combo_style = f"""
            QComboBox {{
                background-color: #08080C;
                border: 1px solid {config.COLOR_BORDER};
                padding: 6px;
                border-radius: 3px;
                color: {config.COLOR_TEXT_PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
        """

        input_style = f"background-color: #08080C; border: 1px solid {config.COLOR_BORDER}; padding: 6px; border-radius: 3px;"

        # Configuration Container
        config_content = QWidget()
        config_layout = QVBoxLayout(config_content)
        config_layout.setContentsMargins(16, 16, 16, 16)
        config_layout.setSpacing(12)

        # Network Configuration
        net_title = QLabel("--- NETWORK CONFIGURATION ---")
        net_title.setStyleSheet(
            f"color: {config.COLOR_ACCENT_CYAN}; font-weight: bold; font-size: 11px;"
        )
        config_layout.addWidget(net_title)

        self._target_lbl = QLabel("TARGET IP:")
        self._target_lbl.setObjectName("status_key")
        config_layout.addWidget(self._target_lbl)

        self._target_input = QLineEdit()
        self._target_input.setPlaceholderText("e.g., 192.168.1.100")
        self._target_input.setStyleSheet(input_style)
        config_layout.addWidget(self._target_input)

        self._gateway_lbl = QLabel("GATEWAY IP (Router):")
        self._gateway_lbl.setObjectName("status_key")
        config_layout.addWidget(self._gateway_lbl)

        self._gateway_input = QLineEdit()
        self._gateway_input.setPlaceholderText("e.g., 192.168.1.1")
        self._gateway_input.setStyleSheet(input_style)
        config_layout.addWidget(self._gateway_input)
        # ── NEW: Block Target Input ──
        self._block_target_lbl = QLabel("BLOCK TARGET (IP/Domain):")
        self._block_target_lbl.setObjectName("status_key")
        self._block_target_lbl.setStyleSheet(
            "color: #FFD700;"
        )  # Gold color to stand out
        config_layout.addWidget(self._block_target_lbl)

        self._block_target_input = QLineEdit()
        self._block_target_input.setPlaceholderText(
            "e.g., windowsupdate.com or 192.168.1.50"
        )
        self._block_target_input.setStyleSheet(input_style)
        config_layout.addWidget(self._block_target_input)

        config_layout.addSpacing(8)

        # Attack Configuration
        vec_title = QLabel("--- ATTACK CONFIGURATION ---")
        vec_title.setStyleSheet(
            f"color: {config.COLOR_ACCENT_ORANGE}; font-weight: bold; font-size: 11px;"
        )
        config_layout.addWidget(vec_title)

        vec_lbl = QLabel("MITM VECTOR:")
        vec_lbl.setObjectName("status_key")
        config_layout.addWidget(vec_lbl)

        self._vector_combo = QComboBox()
        self._vector_combo.addItems(
            [
                "ARP SPOOFING (Poisoning)",
                "DNS SPOOFING (Redirection)",
                "CREDENTIAL HARVESTER (Passive)",
                "HTTP INJECTOR (Visual)",
                "TCP RST INJECTOR (Precision Block)",
                "SESSION & JWT SNIFFER (Passive)",
            ]
        )
        self._vector_combo.setStyleSheet(combo_style)
        self._apply_combo_popup(self._vector_combo)
        config_layout.addWidget(self._vector_combo)

        int_lbl = QLabel("PACKET RATE (PPS):")
        int_lbl.setObjectName("status_key")
        config_layout.addWidget(int_lbl)

        int_layout = QHBoxLayout()
        int_layout.setSpacing(10)
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(1, 100)
        self._slider.setValue(50)
        self._slider_val = QLabel("50%")
        self._slider_val.setObjectName("status_value_alert")
        self._slider_val.setMinimumWidth(35)
        self._slider.valueChanged.connect(lambda v: self._slider_val.setText(f"{v}%"))
        int_layout.addWidget(self._slider)
        int_layout.addWidget(self._slider_val)
        config_layout.addLayout(int_layout)
        config_layout.addStretch()

        control_pane.addWidget(config_content)

        # ── Group 3: Console Actions ──
        actions_group = QFrame()
        actions_group.setObjectName("panel")
        actions_group_layout = QVBoxLayout(actions_group)
        actions_group_layout.setContentsMargins(12, 12, 12, 12)
        actions_group_layout.setSpacing(10)

        act_title = QLabel("[ MODULE CONTROLS ]")
        act_title.setStyleSheet(
            f"color: {config.COLOR_ACCENT_RED}; font-weight: bold; font-size: 11px; "
        )
        actions_group_layout.addWidget(act_title)

        # ARP Button
        self._arp_btn = QPushButton("ENGAGE ARP POISONING")
        self._arp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._arp_btn.setStyleSheet(
            f"color: {config.COLOR_ACCENT_ORANGE}; border-color: {config.COLOR_ACCENT_ORANGE}; padding: 8px 20px; font-size: 11px; "
        )
        self._arp_btn.clicked.connect(
            lambda: self._engage_module("ARP SPOOFING (Poisoning)")
        )
        actions_group_layout.addWidget(self._arp_btn)

        # DNS Button
        self._dns_btn = QPushButton("ENGAGE DNS SPOOFING")
        self._dns_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dns_btn.setStyleSheet(
            f"color: {config.COLOR_ACCENT_CYAN}; border-color: {config.COLOR_ACCENT_CYAN}; padding: 8px 20px; font-size: 11px; "
        )
        self._dns_btn.clicked.connect(
            lambda: self._engage_module("DNS SPOOFING (Redirection)")
        )
        actions_group_layout.addWidget(self._dns_btn)

        # Passive Attack Button
        self._passive_btn = QPushButton("ENGAGE PASSIVE ATTACK")
        self._passive_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._passive_btn.setStyleSheet(
            f"color: {config.COLOR_ACCENT_GREEN}; border-color: {config.COLOR_ACCENT_GREEN}; padding: 8px 20px; font-size: 11px; "
        )
        self._passive_btn.clicked.connect(self._engage_selected_passive)
        actions_group_layout.addWidget(self._passive_btn)

        # Terminate All Button
        self._stop_btn = QPushButton("TERMINATE ALL ATTACKS")
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stop_btn.setStyleSheet(
            f"color: {config.COLOR_ACCENT_RED}; border-color: {config.COLOR_ACCENT_RED}; padding: 8px 20px; font-size: 11px; "
        )
        self._stop_btn.clicked.connect(self._terminate_all)
        actions_group_layout.addWidget(self._stop_btn)
        # ── Passive Module Management (NEW) ──
        passive_group = QFrame()
        passive_group.setObjectName("panel")
        passive_layout = QVBoxLayout(passive_group)
        passive_layout.setContentsMargins(12, 12, 12, 12)
        passive_layout.setSpacing(10)

        pass_title = QLabel("[ PASSIVE MODULE MANAGEMENT ]")
        pass_title.setStyleSheet(
            f"color: {config.COLOR_ACCENT_GREEN}; font-weight: bold; font-size: 11px; "
        )
        passive_layout.addWidget(pass_title)

        # Dropdown and Terminate Selected Button (Side-by-Side)
        passive_row = QHBoxLayout()

        self._passive_dropdown = QComboBox()
        self._passive_dropdown.addItem("No Passive Modules Active")
        self._passive_dropdown.setStyleSheet(combo_style)
        self._passive_dropdown.setEnabled(False)  # Disabled until an attack starts
        passive_row.addWidget(self._passive_dropdown, stretch=3)

        self._terminate_selected_passive_btn = QPushButton("TERMINATE SELECTED")
        self._terminate_selected_passive_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self._terminate_selected_passive_btn.setStyleSheet(
            f"color: {config.COLOR_ACCENT_ORANGE}; border-color: {config.COLOR_ACCENT_ORANGE}; padding: 8px 10px; font-size: 10px; "
        )
        self._terminate_selected_passive_btn.setEnabled(False)
        self._terminate_selected_passive_btn.clicked.connect(
            self._on_terminate_selected_passive
        )
        passive_row.addWidget(self._terminate_selected_passive_btn, stretch=1)

        passive_layout.addLayout(passive_row)

        # Terminate All Passive Button
        self._terminate_all_passive_btn = QPushButton("TERMINATE ALL PASSIVE MODULES")
        self._terminate_all_passive_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._terminate_all_passive_btn.setStyleSheet(
            f"color: {config.COLOR_ACCENT_RED}; border-color: {config.COLOR_ACCENT_RED}; padding: 8px 20px; font-size: 11px; "
        )
        self._terminate_all_passive_btn.setEnabled(False)
        self._terminate_all_passive_btn.clicked.connect(self._on_terminate_all_passive)
        passive_layout.addWidget(self._terminate_all_passive_btn)

        control_pane.addWidget(passive_group)

        control_pane.addWidget(actions_group)
        control_pane.addStretch()

        self._left_container = QScrollArea()
        self._left_container.setWidgetResizable(True)
        self._left_container.setWidget(left_widget)
        self._left_container.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollArea > QWidget > QWidget {{ background: transparent; }}
            QScrollBar:vertical {{
                background: {config.COLOR_BG}; width: 8px; border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {config.COLOR_BORDER}; min-height: 30px; border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        # ── Right Side: Tactical Logs & Payload Config ─────────────────
        self._right_container = QWidget()
        right_main_layout = QHBoxLayout(self._right_container)
        right_main_layout.setContentsMargins(0, 0, 0, 0)
        right_main_layout.setSpacing(8)

        # Horizontal Splitter between logs and payload config
        main_h_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_h_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {config.COLOR_BORDER};
                width: 2px;
            }}
        """)

        # Logs Container (Left side of H-Splitter)
        logs_container = QWidget()
        log_pane = QVBoxLayout(logs_container)
        log_pane.setSpacing(8)
        log_pane.setContentsMargins(0, 0, 0, 0)

        log_splitter = QSplitter(Qt.Orientation.Vertical)
        log_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {config.COLOR_BORDER};
                height: 2px;
            }}
        """)

        # Top Log (MITM)
        top_log_container = QWidget()
        top_log_layout = QVBoxLayout(top_log_container)
        top_log_layout.setContentsMargins(0, 0, 0, 0)
        top_log_layout.setSpacing(8)

        log_hdr = QLabel("[ MITM EVENT LOG ]")
        log_hdr.setObjectName("section_header")
        log_hdr.setStyleSheet(
            f"color: {config.COLOR_ACCENT_RED}; border-bottom: 2px solid {config.COLOR_ACCENT_RED}; font-size: 13px; padding-bottom: 4px;"
        )
        top_log_layout.addWidget(log_hdr)

        self._log = QTextEdit()
        self._log.setObjectName("event_log")
        self._log.setReadOnly(True)
        self._log.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        top_log_layout.addWidget(self._log)

        log_splitter.addWidget(top_log_container)

        # Bottom Log (Passive)
        bottom_log_container = QWidget()
        bottom_log_layout = QVBoxLayout(bottom_log_container)
        bottom_log_layout.setContentsMargins(0, 0, 0, 0)
        bottom_log_layout.setSpacing(8)

        passive_hdr = QLabel("[ PASSIVE EVENT LOG ]")
        passive_hdr.setObjectName("section_header")
        passive_hdr.setStyleSheet(
            f"color: {config.COLOR_ACCENT_GREEN}; border-bottom: 2px solid {config.COLOR_ACCENT_GREEN}; font-size: 13px; padding-bottom: 4px;"
        )
        bottom_log_layout.addWidget(passive_hdr)

        self._passive_log = QTextEdit()
        self._passive_log.setObjectName("event_log")
        self._passive_log.setReadOnly(True)
        self._passive_log.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        bottom_log_layout.addWidget(self._passive_log)

        log_splitter.addWidget(bottom_log_container)

        log_pane.addWidget(log_splitter)
        main_h_splitter.addWidget(logs_container)

        # Payload Configuration Container (Right side of H-Splitter)
        self._payload_container = QWidget()
        payload_layout = QVBoxLayout(self._payload_container)
        payload_layout.setContentsMargins(16, 0, 0, 0)
        payload_layout.setSpacing(12)

        payload_hdr = QLabel("[ PAYLOAD CONFIGURATION ]")
        payload_hdr.setObjectName("section_header")
        payload_hdr.setStyleSheet(
            f"color: {config.COLOR_ACCENT_ORANGE}; border-bottom: 2px solid {config.COLOR_ACCENT_ORANGE}; font-size: 13px; padding-bottom: 4px;"
        )
        payload_layout.addWidget(payload_hdr)

        payload_lbl = QLabel("PAYLOAD TYPE:")
        payload_lbl.setObjectName("status_key")
        payload_layout.addWidget(payload_lbl)

        self._payload_dropdown = QComboBox()
        self._payload_dropdown.addItems(
            [
                "Black/Green Screen (Default)",
                "Simple Alert Box",
                "Page Redirect (to attacker IP)",
                "Custom Payload",
            ]
        )
        self._payload_dropdown.setStyleSheet(combo_style)
        self._apply_combo_popup(self._payload_dropdown)
        payload_layout.addWidget(self._payload_dropdown)

        script_lbl = QLabel("CUSTOM SCRIPT:")
        script_lbl.setObjectName("status_key")
        payload_layout.addWidget(script_lbl)

        self._payload_script_editor = QTextEdit()
        self._payload_script_editor.setPlaceholderText("Enter raw JavaScript here...")
        self._payload_script_editor.setMaximumHeight(200)
        self._payload_script_editor.setStyleSheet(
            f"background-color: #08080C; border: 1px solid {config.COLOR_BORDER}; padding: 6px; border-radius: 3px; font-family: monospace;"
        )
        payload_layout.addWidget(self._payload_script_editor)

        self._inject_btn = QPushButton("INJECT PAYLOAD")
        self._inject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._inject_btn.setStyleSheet(
            f"color: {config.COLOR_ACCENT_ORANGE}; border-color: {config.COLOR_ACCENT_ORANGE}; padding: 8px 20px; font-size: 11px; font-weight: bold;"
        )
        self._inject_btn.clicked.connect(self._on_inject_payload)
        payload_layout.addWidget(self._inject_btn)

        payload_layout.addStretch()

        main_h_splitter.addWidget(self._payload_container)

        # Hide by default
        self._payload_container.hide()

        # Set initial stretch factors (Logs 70%, Payload 30% when visible)
        main_h_splitter.setStretchFactor(0, 7)
        main_h_splitter.setStretchFactor(1, 3)

        right_main_layout.addWidget(main_h_splitter)

        layout.addWidget(self._left_container, 4)
        layout.addWidget(self._right_container, 6)

        # Connect vector combo to toggle payload visibility
        self._vector_combo.currentTextChanged.connect(self._on_vector_changed)

        self.log_message("MITM Console Online. Requires root/sudo privileges.", "WARN")

    def _apply_combo_popup(self, combo: QComboBox) -> None:
        """Replace default combo popup with a QListView to eliminate native white border artifacts."""
        from PySide6.QtWidgets import QListView, QStyledItemDelegate
        from PySide6.QtCore import QSize

        class _RowDelegate(QStyledItemDelegate):
            """Force each row to a fixed height so items never overlap."""

            def sizeHint(self, option, index):
                hint = super().sizeHint(option, index)
                hint.setHeight(36)
                return hint

        popup = QListView()
        popup.setItemDelegate(_RowDelegate(popup))
        popup.setStyleSheet(f"""
            QListView {{
                background-color: #08080C;
                color: {config.COLOR_TEXT_PRIMARY};
                border: 1px solid {config.COLOR_BORDER};
                outline: none;
            }}
            QListView::item {{
                background-color: #08080C;
                color: {config.COLOR_TEXT_PRIMARY};
                padding: 4px 6px;
            }}
            QListView::item:selected {{
                background-color: {config.COLOR_BORDER};
            }}
        """)
        combo.setView(popup)

    def reset_passive_button(self) -> None:
        """Resets the passive attack button to its default state."""
        self._passive_btn.setText("ENGAGE PASSIVE ATTACK")
        self._passive_btn.setStyleSheet(
            f"color: {config.COLOR_ACCENT_GREEN}; border-color: {config.COLOR_ACCENT_GREEN}; padding: 8px 20px; font-size: 11px; "
        )

    def _engage_module(self, vector: str) -> None:
        target = self._target_input.text().strip()
        gateway = self._gateway_input.text().strip()
        intensity = self._slider.value()

        if not target or not gateway:
            self.log_message(
                "Cannot initiate: Target and Gateway IPs are required.", "CRIT"
            )
            return

        self.log_message(
            f"ENGAGING {vector} -> Target: {target} | Gateway: {gateway}", "EXEC"
        )
        block_target = self._block_target_input.text().strip()
        self.mitm_started.emit(target, gateway, vector, intensity, block_target)

        # Visual feedback
        if "ARP" in vector:
            self._arp_btn.setText("ARP POISONING ACTIVE")
            self._arp_btn.setStyleSheet(
                f"color: {config.COLOR_BG}; background-color: {config.COLOR_ACCENT_ORANGE}; border-color: {config.COLOR_ACCENT_ORANGE}; "
            )
        elif "DNS" in vector:
            self._dns_btn.setText("DNS SPOOFING ACTIVE")
            self._dns_btn.setStyleSheet(
                f"color: {config.COLOR_BG}; background-color: {config.COLOR_ACCENT_CYAN}; border-color: {config.COLOR_ACCENT_CYAN}; "
            )
        elif "PASSIVE" in vector.upper() or "CREDENTIAL" in vector.upper():
            self._passive_btn.setText("PASSIVE ATTACK ACTIVE")
            self._passive_btn.setStyleSheet(
                f"color: {config.COLOR_BG}; background-color: {config.COLOR_ACCENT_GREEN}; border-color: {config.COLOR_ACCENT_GREEN}; "
            )
        # ── FIX: Check RST/BLOCK *BEFORE* INJECT/HTTP ──
        elif "RST" in vector.upper() or "BLOCK" in vector.upper():
            self._passive_btn.setText("RST BLOCKER ACTIVE")
            self._passive_btn.setStyleSheet(
                f"color: {config.COLOR_BG}; background-color: #FFD700; border-color: #FFD700; "
            )  # Gold
        elif "INJECT" in vector.upper() or "HTTP" in vector.upper():
            self._passive_btn.setText("INJECTOR ACTIVE")
            self._passive_btn.setStyleSheet(
                f"color: {config.COLOR_BG}; background-color: #FF00FF; border-color: #FF00FF; "
            )  # Magenta
        elif "SESSION" in vector.upper() or "JWT" in vector.upper():
            self._passive_btn.setText("SESSION SNIFFER ACTIVE")
            self._passive_btn.setStyleSheet(
                f"color: {config.COLOR_BG}; background-color: #9D00FF; border-color: #9D00FF;"
            )  # Purple

    def _engage_selected_passive(self) -> None:
        vector = self._vector_combo.currentText()
        if (
            "HARVESTER" in vector
            or "INJECTOR" in vector
            or "PASSIVE" in vector
            or "RST" in vector
            or "BLOCK" in vector
            or "COOKIE" in vector
            or "SESSION" in vector
            or "JWT" in vector
        ):  # <--- UPDATED
            self._engage_module(vector)
        else:
            self.log_message(
                "Please select a Passive module from the dropdown.", "CRIT"
            )

    def _terminate_all(self) -> None:
        self.log_message("TERMINATING ALL MITM MODULES...", "WARN")
        self.log_passive("TERMINATING ALL PASSIVE MODULES...", "WARN")
        self.mitm_stopped.emit()

        # Reset buttons
        self._arp_btn.setText("ENGAGE ARP POISONING")
        self._arp_btn.setStyleSheet(
            f"color: {config.COLOR_ACCENT_ORANGE}; border-color: {config.COLOR_ACCENT_ORANGE}; padding: 8px 20px; font-size: 11px; "
        )
        self._dns_btn.setText("ENGAGE DNS SPOOFING")
        self._dns_btn.setStyleSheet(
            f"color: {config.COLOR_ACCENT_CYAN}; border-color: {config.COLOR_ACCENT_CYAN}; padding: 8px 20px; font-size: 11px; "
        )
        self._passive_btn.setText("ENGAGE PASSIVE ATTACK")
        self._passive_btn.setStyleSheet(
            f"color: {config.COLOR_ACCENT_GREEN}; border-color: {config.COLOR_ACCENT_GREEN}; padding: 8px 20px; font-size: 11px; "
        )

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

    def update_passive_dropdown(self, module_id: str, is_adding: bool) -> None:
        """Called by MainWindow to add/remove modules from the dropdown."""
        if is_adding:
            # Remove the placeholder if it exists
            idx = self._passive_dropdown.findText("No Passive Modules Active")
            if idx >= 0:
                self._passive_dropdown.removeItem(idx)

            self._passive_dropdown.addItem(module_id)
            self._passive_dropdown.setCurrentText(module_id)
            self._passive_dropdown.setEnabled(True)
            self._terminate_selected_passive_btn.setEnabled(True)
            self._terminate_all_passive_btn.setEnabled(True)
        else:
            idx = self._passive_dropdown.findText(module_id)
            if idx >= 0:
                self._passive_dropdown.removeItem(idx)

            # If empty, restore placeholder and disable buttons
            if self._passive_dropdown.count() == 0:
                self._passive_dropdown.addItem("No Passive Modules Active")
                self._passive_dropdown.setEnabled(False)
                self._terminate_selected_passive_btn.setEnabled(False)
                self._terminate_all_passive_btn.setEnabled(False)

    def _on_terminate_selected_passive(self) -> None:
        current_text = self._passive_dropdown.currentText()
        if current_text and current_text != "No Passive Modules Active":
            self.log_message(f"Terminating passive module: {current_text}", "WARN")
            self.terminate_passive_selected.emit(current_text)

    def _on_terminate_all_passive(self) -> None:
        self.log_message("Terminating ALL passive modules...", "WARN")
        self.terminate_all_passive.emit()

    def _on_vector_changed(self, text: str) -> None:
        if text == "HTTP INJECTOR (Visual)":
            self._payload_container.show()
        else:
            self._payload_container.hide()

    def _on_inject_payload(self) -> None:
        payload_type = self._payload_dropdown.currentText()
        custom_script = self._payload_script_editor.toPlainText()

        # Emit signal to update backend
        self.payload_updated.emit(payload_type, custom_script)
        self.log_message(f"Payload configuration updated: {payload_type}", "EXEC")
