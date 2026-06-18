# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/attack_panel.py — Offensive Operations Panel (Layer 2/3 Integrated)
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
    QTabWidget,
    QScrollArea,
    QListView,
)
import config


class AttackPanel(QWidget):
    attack_engaged = Signal(str, str, int)  # target_string, vector, intensity
    attack_aborted = Signal()
    host_ap_toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._armed = False
        self._ap_active = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # ── Left Side: Controls ───────────────────────────────────────
        self._left_container = QWidget()
        control_pane = QVBoxLayout(self._left_container)
        control_pane.setSpacing(16)
        control_pane.setContentsMargins(0, 0, 0, 0)

        # Section Header
        hdr = QLabel("[ TACTICAL OFFENSIVE CONSOLE ]")
        hdr.setObjectName("section_header")
        hdr.setStyleSheet(
            f"color: {config.COLOR_ACCENT_RED}; border-bottom: 2px solid {config.COLOR_ACCENT_RED}; font-size: 13px; padding-bottom: 4px;"
        )
        control_pane.addWidget(hdr)

        # Tooltip styling (applied to entire panel)
        self.setStyleSheet(f"""
            QToolTip {{
                background-color: {config.COLOR_BG_PANEL};
                color: {config.COLOR_TEXT_PRIMARY};
                border: 1px solid {config.COLOR_BORDER};
                padding: 4px;
            }}
        """)

        # Tabs for grouping vectors
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {config.COLOR_BORDER}; background: {config.COLOR_BG_PANEL}; }}
            QTabBar::tab {{ background: {config.COLOR_BG}; color: {config.COLOR_TEXT_DIM}; padding: 8px 16px; border: 1px solid {config.COLOR_BORDER}; }}
            QTabBar::tab:selected {{ background: {config.COLOR_BG_PANEL}; color: {config.COLOR_TEXT_PRIMARY}; border-bottom-color: {config.COLOR_BG_PANEL}; }}
        """)

        scroll_style = f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollArea > QWidget > QWidget {{ background: transparent; }}
            QScrollBar:vertical {{
                background: {config.COLOR_BG}; width: 8px; border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {config.COLOR_BORDER}; min-height: 30px; border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """

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

        # ── TAB 1: 802.11 RF OPERATIONS ──
        rf_content = QWidget()
        rf_layout = QVBoxLayout(rf_content)
        rf_layout.setContentsMargins(16, 16, 16, 16)
        rf_layout.setSpacing(12)

        targ_title = QLabel("--- TARGET ACQUISITION ---")
        targ_title.setStyleSheet(
            f"color: {config.COLOR_ACCENT_CYAN}; font-weight: bold; font-size: 11px;"
        )
        rf_layout.addWidget(targ_title)

        targ_lbl = QLabel("ACQUIRED TARGET:")
        targ_lbl.setObjectName("status_key")
        rf_layout.addWidget(targ_lbl)

        self._target_combo = QComboBox()
        self._target_combo.addItem("NO TARGET ACQUIRED", userData=None)
        self._target_combo.setStyleSheet(combo_style)
        self._apply_combo_popup(self._target_combo)
        rf_layout.addWidget(self._target_combo)

        self._ssid_lbl = QLabel("FAKE SSID (Evil Twin Name):")
        self._ssid_lbl.setObjectName("status_key")
        self._ssid_lbl.setVisible(False)
        rf_layout.addWidget(self._ssid_lbl)

        self._ssid_input = QLineEdit()
        self._ssid_input.setPlaceholderText("Enter Fake SSID (e.g., Campus_Guest)")
        self._ssid_input.setStyleSheet(
            f"background-color: #08080C; border: 1px solid {config.COLOR_BORDER}; padding: 6px; border-radius: 3px;"
        )
        self._ssid_input.setVisible(False)
        rf_layout.addWidget(self._ssid_input)

        config_title = QLabel("--- ATTACK CONFIGURATION ---")
        config_title.setStyleSheet(
            f"color: {config.COLOR_ACCENT_ORANGE}; font-weight: bold; font-size: 11px;"
        )
        rf_layout.addWidget(config_title)

        vec_lbl = QLabel("ATTACK VECTOR:")
        vec_lbl.setObjectName("status_key")
        rf_layout.addWidget(vec_lbl)

        self._rf_vector_combo = QComboBox()
        self._rf_vector_combo.addItems(
            [
                "DEAUTHENTICATION FLOOD (Subtype 12)",
                "CAPTIVE PORTAL (Evil Twin)",
                "BEACON SPAM (SSID Obfuscation)",
                "PROBE REQUEST STORM",
                "AUTHENTICATION FLOOD (DoS)",
                "RTS/CTS RESERVATION ATTACK",
            ]
        )
        self._rf_vector_combo.setStyleSheet(combo_style)
        self._apply_combo_popup(self._rf_vector_combo)
        self._rf_vector_combo.currentTextChanged.connect(self._on_rf_vector_change)
        rf_layout.addWidget(self._rf_vector_combo)

        int_lbl = QLabel("INTENSITY / INJECTION RATE:")
        int_lbl.setObjectName("status_key")
        rf_layout.addWidget(int_lbl)

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
        rf_layout.addLayout(int_layout)
        rf_layout.addStretch()

        rf_scroll = QScrollArea()
        rf_scroll.setWidgetResizable(True)
        rf_scroll.setWidget(rf_content)
        rf_scroll.setStyleSheet(scroll_style)

        # ── TAB 2: L2/L3 NETWORK ATTACKS ──
        net_content = QWidget()
        net_layout = QVBoxLayout(net_content)
        net_layout.setContentsMargins(16, 16, 16, 16)
        net_layout.setSpacing(12)

        net_targ_title = QLabel("--- TARGET ACQUISITION ---")
        net_targ_title.setStyleSheet(
            f"color: {config.COLOR_ACCENT_CYAN}; font-weight: bold; font-size: 11px;"
        )
        net_layout.addWidget(net_targ_title)

        self._ip_lbl = QLabel("TARGET IP (Layer 2/3):")
        self._ip_lbl.setObjectName("status_key")
        net_layout.addWidget(self._ip_lbl)

        self._ip_input = QLineEdit()
        self._ip_input.setPlaceholderText("e.g., 192.168.1.1")
        self._ip_input.setStyleSheet(
            f"background-color: #08080C; border: 1px solid {config.COLOR_BORDER}; padding: 6px; border-radius: 3px;"
        )
        net_layout.addWidget(self._ip_input)

        net_config_title = QLabel("--- ATTACK CONFIGURATION ---")
        net_config_title.setStyleSheet(
            f"color: {config.COLOR_ACCENT_ORANGE}; font-weight: bold; font-size: 11px;"
        )
        net_layout.addWidget(net_config_title)

        net_vec_lbl = QLabel("ATTACK VECTOR:")
        net_vec_lbl.setObjectName("status_key")
        net_layout.addWidget(net_vec_lbl)

        self._net_vector_combo = QComboBox()
        self._net_vector_combo.addItems(
            [
                "ARP FLOOD (DoS / Device Crash) ",  # Renamed from Spoofing
                "DHCP STARVATION (DoS) ",
                "DNS FLOOD (DoS / Server Crash) ",  # Renamed from Spoofing
                "ICMP FLOOD (Ping Storm) ",  # NEW
            ]
        )
        self._net_vector_combo.setStyleSheet(combo_style)
        self._apply_combo_popup(self._net_vector_combo)
        net_layout.addWidget(self._net_vector_combo)
        net_layout.addStretch()

        net_scroll = QScrollArea()
        net_scroll.setWidgetResizable(True)
        net_scroll.setWidget(net_content)
        net_scroll.setStyleSheet(scroll_style)

        self._tabs.addTab(rf_scroll, "802.11 RF OPERATIONS")
        self._tabs.addTab(net_scroll, "L2/L3 NETWORK ATTACKS")
        control_pane.addWidget(self._tabs)

        # ── Group 3: Console Actions ──
        actions_group = QFrame()
        actions_group.setObjectName("panel")
        actions_group_layout = QVBoxLayout(actions_group)
        actions_group_layout.setContentsMargins(12, 12, 12, 12)
        actions_group_layout.setSpacing(10)

        act_title = QLabel("[ CONSOLE ACTIONS ]")
        act_title.setStyleSheet(
            f"color: {config.COLOR_ACCENT_RED}; font-weight: bold; font-size: 11px;"
        )
        actions_group_layout.addWidget(act_title)

        self._arm_btn = QPushButton("ARM SYSTEM")
        self._arm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._arm_btn.setStyleSheet(
            f"color: {config.COLOR_ACCENT_ORANGE}; border-color: {config.COLOR_ACCENT_ORANGE}; padding: 8px 20px; font-size: 11px;"
        )
        self._arm_btn.clicked.connect(self._toggle_arm)
        actions_group_layout.addWidget(self._arm_btn)

        self._engage_btn = QPushButton("ENGAGE TARGET")
        self._engage_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._engage_btn.setStyleSheet(
            f"color: {config.COLOR_TEXT_DIM}; border-color: {config.COLOR_TEXT_DIM}; padding: 8px 20px; font-size: 11px;"
        )
        self._engage_btn.setEnabled(False)
        self._engage_btn.clicked.connect(self._engage_target)
        actions_group_layout.addWidget(self._engage_btn)

        self._host_ap_btn = QPushButton("HOST DEMO AP (OFF)")
        self._host_ap_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._host_ap_btn.setStyleSheet(
            f"color: {config.COLOR_ACCENT_CYAN}; border-color: {config.COLOR_ACCENT_CYAN}; padding: 8px 20px; font-size: 11px;"
        )
        self._host_ap_btn.clicked.connect(self._toggle_host_ap)
        actions_group_layout.addWidget(self._host_ap_btn)

        control_pane.addWidget(actions_group)

        # ── Right Side: Tactical Log ──────────────────────────────────
        self._right_container = QWidget()
        log_pane = QVBoxLayout(self._right_container)
        log_pane.setSpacing(8)

        log_hdr = QLabel("[ TACTICAL EVENT LOG ]")
        log_hdr.setObjectName("section_header")
        log_hdr.setStyleSheet(
            f"color: {config.COLOR_ACCENT_RED}; border-bottom: 2px solid {config.COLOR_ACCENT_RED}; font-size: 13px; padding-bottom: 4px;"
        )
        log_pane.addWidget(log_hdr)

        self._log = QTextEdit()
        self._log.setObjectName("event_log")
        self._log.setReadOnly(True)
        self._log.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        log_pane.addWidget(self._log)

        layout.addWidget(self._left_container, stretch=4)
        layout.addWidget(self._right_container, stretch=6)

        self.log_message("Tactical Offensive Console Online.", "INFO")

    def _apply_combo_popup(self, combo: QComboBox) -> None:
        """Replace default combo popup with a QListView to eliminate native white border artifacts."""
        popup = QListView()
        popup.setStyleSheet(f"""
            QListView {{
                background-color: #08080C;
                color: {config.COLOR_TEXT_PRIMARY};
                border: 1px solid {config.COLOR_BORDER};
                outline: none;
                padding: 0px;
                margin: 0px;
            }}
            QListView::item {{
                background-color: #08080C;
                color: {config.COLOR_TEXT_PRIMARY};
                padding: 4px 6px;
                min-height: 22px;
            }}
            QListView::item:selected {{
                background-color: {config.COLOR_BORDER};
            }}
        """)
        combo.setView(popup)

    def _on_rf_vector_change(self, text: str) -> None:
        if "CAPTIVE" in text or "PORTAL" in text or "BEACON" in text:
            self._ssid_lbl.setVisible(True)
            self._ssid_input.setVisible(True)
            self._ssid_input.setFocus()
        else:
            self._ssid_lbl.setVisible(False)
            self._ssid_input.setVisible(False)

    def update_targets(self, targets: list[tuple[str, str]]) -> None:
        current_bssid = self._target_combo.currentData()
        self._target_combo.clear()
        if not targets:
            self._target_combo.addItem("NO TARGET ACQUIRED", userData=None)
        else:
            for display_name, bssid in targets:
                self._target_combo.addItem(display_name, userData=bssid)
        if current_bssid is not None:
            idx = self._target_combo.findData(current_bssid)
            if idx >= 0:
                self._target_combo.setCurrentIndex(idx)

    def log_message(self, message: str, level: str = "INFO", data: str = "") -> None:
        colors = {
            "INFO": config.COLOR_ACCENT_CYAN,
            "WARN": config.COLOR_ACCENT_ORANGE,
            "CRIT": config.COLOR_ACCENT_RED,
            "EXEC": "#FF00FF",
            "RX": "#00FF00",
            "TX": "#FFFF00",
        }
        color = colors.get(level, config.COLOR_TEXT_PRIMARY)
        timestamp = time.strftime("%H:%M:%S.%f")[:-3]
        line = (
            f'<span style="color:{config.COLOR_TEXT_DIM};">[{timestamp}]</span> '
            f'<span style="color:{color}; font-weight:bold;">[{level:4s}]</span> '
            f'<span style="color:{config.COLOR_TEXT_PRIMARY};">{message}</span>'
        )
        if data:
            line += f'<br>&nbsp;&nbsp;&nbsp;<span style="color:{config.COLOR_TEXT_DIM}; font-family:monospace;">{data}</span>'
        self._log.append(line)
        sb = self._log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _toggle_arm(self) -> None:
        self._armed = not self._armed
        if self._armed:
            self._arm_btn.setText("DISARM SYSTEM")
            self._arm_btn.setStyleSheet(
                f"color: {config.COLOR_ACCENT_GREEN}; border-color: {config.COLOR_ACCENT_GREEN};"
            )
            self._engage_btn.setEnabled(True)
            self._engage_btn.setStyleSheet(
                f"color: {config.COLOR_BG}; background-color: {config.COLOR_ACCENT_RED}; border-color: {config.COLOR_ACCENT_RED};"
            )
            self.log_message("System ARMED. Weapons free.", "WARN")
        else:
            self._arm_btn.setText("ARM SYSTEM")
            self._arm_btn.setStyleSheet(
                f"color: {config.COLOR_ACCENT_ORANGE}; border-color: {config.COLOR_ACCENT_ORANGE};"
            )
            self._engage_btn.setEnabled(False)
            self._engage_btn.setStyleSheet(
                f"color: {config.COLOR_TEXT_DIM}; border-color: {config.COLOR_TEXT_DIM}; background-color: transparent;"
            )
            self.log_message("System DISARMED. Safeties engaged.", "INFO")
            self.attack_aborted.emit()

    def _engage_target(self) -> None:
        intensity = self._slider.value()

        active_tab = self._tabs.currentIndex()
        if active_tab == 0:  # RF Tab
            vector = self._rf_vector_combo.currentText()
            if "CAPTIVE" in vector or "PORTAL" in vector or "BEACON" in vector:
                target_string = self._ssid_input.text().strip()
                if not target_string:
                    if "BEACON" in vector:
                        target_string = "FREE_PUBLIC_WIFI"
                    else:
                        self.log_message(
                            "Cannot engage: Fake SSID is required for Captive Portal.",
                            "CRIT",
                        )
                        return
                self.log_message(
                    f"ENGAGING FAKE AP / CAPTIVE PORTAL: '{target_string}'", "EXEC"
                )
            else:
                target_string = self._target_combo.currentData()
                if not target_string:
                    self.log_message("Cannot engage: Invalid target.", "CRIT")
                    return
                self.log_message(
                    f"ENGAGING TARGET: {self._target_combo.currentText()} [{target_string}]",
                    "EXEC",
                )

        else:  # L2/L3 Tab
            vector = self._net_vector_combo.currentText()
            target_string = self._ip_input.text().strip()
            if not target_string:
                self.log_message(
                    "Cannot engage: Target IP is required for L2/L3 attacks.", "CRIT"
                )
                return
            self.log_message(
                f"ENGAGING L2/L3 ATTACK: {vector} -> {target_string}", "EXEC"
            )

        self.log_message(f"VECTOR: {vector} @ {intensity}% intensity", "EXEC")
        self.attack_engaged.emit(target_string, vector, intensity)

    def _toggle_host_ap(self) -> None:
        self._ap_active = not self._ap_active
        if self._ap_active:
            self._host_ap_btn.setText("HOST DEMO AP (ON)")
            self._host_ap_btn.setStyleSheet(
                f"color: {config.COLOR_BG}; background-color: {config.COLOR_ACCENT_CYAN}; border-color: {config.COLOR_ACCENT_CYAN};"
            )
            self.host_ap_toggled.emit(True)
        else:
            self._host_ap_btn.setText("HOST DEMO AP (OFF)")
            self._host_ap_btn.setStyleSheet(
                f"color: {config.COLOR_ACCENT_CYAN}; border-color: {config.COLOR_ACCENT_CYAN}; background-color: transparent;"
            )
            self.host_ap_toggled.emit(False)
