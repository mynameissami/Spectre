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
    QFrame,
    QSlider,
    QTextEdit,
    QLineEdit,
    QTabWidget,
    QScrollArea,
    QListView,
    QFormLayout,
)
import config
from ui.settings.widgets import LabelledSlider, ComboBox


class AttackPanel(QWidget):
    attack_engaged = Signal(str, str, int)  # target_string, vector, intensity
    attack_aborted = Signal()
    host_ap_toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._armed = False
        self._ap_active = False
        self._setup_ui()

    def _make_panel_group(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        grp = QFrame()
        grp.setObjectName("panel")
        lyt = QVBoxLayout(grp)
        lyt.setContentsMargins(16, 16, 16, 16)
        lyt.setSpacing(16)
        
        hdr = QLabel(title)
        hdr.setObjectName("section_header")
        lyt.addWidget(hdr)
        
        return grp, lyt

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # ── Left Side: Controls ───────────────────────────────────────
        self._left_container = QWidget()
        control_pane = QVBoxLayout(self._left_container)
        control_pane.setSpacing(16)
        control_pane.setContentsMargins(0, 0, 16, 0)

        # Section Header
        hdr = QLabel("TACTICAL OFFENSIVE CONSOLE")
        hdr.setObjectName("section_header")
        control_pane.addWidget(hdr)


        # Tabs for grouping vectors
        self._tabs = QTabWidget()

        # ── TAB 1: 802.11 RF OPERATIONS ──
        rf_content = QWidget()
        rf_layout = QVBoxLayout(rf_content)
        rf_layout.setContentsMargins(0, 8, 0, 8)
        rf_layout.setSpacing(16)

        targ_group, targ_glayout = self._make_panel_group("TARGET ACQUISITION")
        rf_layout.addWidget(targ_group)
        form = QFormLayout()
        targ_glayout.addLayout(form)

        self._target_combo = ComboBox()
        self._target_combo.setEditable(True)
        self._target_combo.lineEdit().setPlaceholderText("Enter MAC (e.g., 00:11:22...)")
        self._target_combo.addItems(["BROADCAST (FF:FF:FF:FF:FF:FF)", "Custom Target..."])
        form.addRow("TARGET BSSID / MAC:", self._target_combo)

        self._ssid_lbl = QLabel("FAKE SSID (Evil Twin Name):")
        self._ssid_lbl.setObjectName("status_key")
        self._ssid_lbl.setVisible(False)
        targ_glayout.addWidget(self._ssid_lbl)

        self._ssid_input = QLineEdit()
        self._ssid_input.setPlaceholderText("Enter Fake SSID (e.g., Campus_Guest)")
        self._ssid_input.setVisible(False)
        targ_glayout.addWidget(self._ssid_input)

        config_group, config_glayout = self._make_panel_group("ATTACK CONFIGURATION")
        rf_layout.addWidget(config_group)
        form = QFormLayout()
        config_glayout.addLayout(form)

        self._rf_vector_combo = ComboBox()
        self._rf_vector_combo.addItems([
            "[DEAUTH] IEEE 802.11 Deauthentication Broadcast",
            "[DEAUTH] Targeted Client Disconnect",
            "[JAM] CTS/RTS Flood (Channel Jamming)",
            "[BEACON] Evil Twin / Beacon Flood"
        ])
        form.addRow("ATTACK VECTOR:", self._rf_vector_combo)
        self._rf_vector_combo.currentTextChanged.connect(self._on_rf_vector_change)

        int_lbl = QLabel("INTENSITY / INJECTION RATE:")
        int_lbl.setObjectName("status_key")
        config_glayout.addWidget(int_lbl)

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
        config_glayout.addLayout(int_layout)
        rf_layout.addStretch()

        rf_scroll = QScrollArea()
        rf_scroll.setWidgetResizable(True)
        rf_scroll.setWidget(rf_content)

        # ── TAB 2: L2/L3 NETWORK ATTACKS ──
        net_content = QWidget()
        net_layout = QVBoxLayout(net_content)
        net_layout.setContentsMargins(0, 8, 0, 8)
        net_layout.setSpacing(16)

        net_targ_group, net_targ_glayout = self._make_panel_group("TARGET ACQUISITION")
        net_layout.addWidget(net_targ_group)

        self._ip_lbl = QLabel("TARGET IP (Layer 2/3):")
        self._ip_lbl.setObjectName("status_key")
        net_targ_glayout.addWidget(self._ip_lbl)

        self._ip_input = QLineEdit()
        self._ip_input.setPlaceholderText("e.g., Target IP")
        net_targ_glayout.addWidget(self._ip_input)

        net_config_group, net_config_glayout = self._make_panel_group("ATTACK CONFIGURATION")
        net_layout.addWidget(net_config_group)

        net_vec_lbl = QLabel("ATTACK VECTOR:")
        net_vec_lbl.setObjectName("status_key")
        net_config_glayout.addWidget(net_vec_lbl)

        self._net_vector_combo = ComboBox()
        self._net_vector_combo.addItems(
            [
                "ARP FLOOD (DoS / Device Crash) ",
                "DHCP STARVATION (DoS) ",
                "DNS FLOOD (DoS / Server Crash) ",
                "ICMP FLOOD (Ping Storm) ",
            ]
        )
        net_config_glayout.addWidget(self._net_vector_combo)
        net_layout.addStretch()

        net_scroll = QScrollArea()
        net_scroll.setWidgetResizable(True)
        net_scroll.setWidget(net_content)

        self._tabs.addTab(rf_scroll, "802.11 RF OPERATIONS")
        self._tabs.addTab(net_scroll, "L2/L3 NETWORK ATTACKS")
        control_pane.addWidget(self._tabs)

        # ── Group 3: Console Actions ──
        actions_group = QFrame()
        actions_group.setObjectName("panel")
        actions_group_layout = QVBoxLayout(actions_group)
        actions_group_layout.setContentsMargins(12, 12, 12, 12)
        actions_group_layout.setSpacing(10)

        act_title = QLabel("CONSOLE ACTIONS")
        act_title.setObjectName("section_header")
        actions_group_layout.addWidget(act_title)

        self._arm_btn = QPushButton("ARM SYSTEM")
        self._arm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_btn_theme(self._arm_btn, "orange")
        self._arm_btn.clicked.connect(self._toggle_arm)
        actions_group_layout.addWidget(self._arm_btn)

        self._engage_btn = QPushButton("ENGAGE TARGET")
        self._engage_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_btn_theme(self._engage_btn, "dim")
        self._engage_btn.setEnabled(False)
        self._engage_btn.clicked.connect(self._engage_target)
        actions_group_layout.addWidget(self._engage_btn)

        self._host_ap_btn = QPushButton("HOST DEMO AP (OFF)")
        self._host_ap_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_btn_theme(self._host_ap_btn, "cyan")
        self._host_ap_btn.clicked.connect(self._toggle_host_ap)
        actions_group_layout.addWidget(self._host_ap_btn)

        control_pane.addWidget(actions_group)

        # ── Right Side: Tactical Log ──────────────────────────────────
        self._right_container = QWidget()
        log_pane = QVBoxLayout(self._right_container)
        log_pane.setSpacing(8)
        log_pane.setContentsMargins(0, 0, 0, 0)

        log_hdr = QLabel("TACTICAL EVENT LOG")
        log_hdr.setObjectName("section_header")
        log_pane.addWidget(log_hdr)

        self._log = QTextEdit()
        self._log.setObjectName("event_log")
        self._log.setReadOnly(True)
        self._log.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        log_pane.addWidget(self._log)

        layout.addWidget(self._left_container, stretch=4)
        layout.addWidget(self._right_container, stretch=6)

        self.log_message("Tactical Offensive Console Online.", "INFO")

    def _set_btn_theme(self, btn: QPushButton, theme: str, active: str = "false") -> None:
        btn.setProperty("btnTheme", theme)
        btn.setProperty("btnActive", active)
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    def refresh_theme(self) -> None:
        """Refresh inline styles after a theme change."""
        pass

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
            self._set_btn_theme(self._arm_btn, "green")
            self._engage_btn.setEnabled(True)
            self._set_btn_theme(self._engage_btn, "red", "true")
            self.log_message("System ARMED. Weapons free.", "WARN")
        else:
            self._arm_btn.setText("ARM SYSTEM")
            self._set_btn_theme(self._arm_btn, "orange")
            self._engage_btn.setEnabled(False)
            self._set_btn_theme(self._engage_btn, "dim")
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
            self._set_btn_theme(self._host_ap_btn, "cyan", "true")
            self.host_ap_toggled.emit(True)
        else:
            self._host_ap_btn.setText("HOST DEMO AP (OFF)")
            self._set_btn_theme(self._host_ap_btn, "cyan")
            self.host_ap_toggled.emit(False)
