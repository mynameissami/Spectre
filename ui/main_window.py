# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

from __future__ import annotations
from ui.mitm_panel import MITMPanel
from core.web_server import DynamicWebServer
from core.mitm_engine import MITMEngine
import time
from ui.doc_panel import DocPanel
from collections import deque
from typing import Optional
from core.network_scanner import NetworkScanner
from core.port_scanner import PortScanner
from ui.recon_panel import ReconPanel
import numpy as np
from PySide6.QtCore import Qt, QTimer, Slot, QPoint
from core.simulator import AttackSimulator
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QFrame,
    QTabWidget,
    QMenuBar,
    QMessageBox,
    QStackedWidget,
    QLabel,
    QMenu,
)
import config
from core.telemetry import TelemetryReceiver
from core.dsp import DSPEngine
from core.recon import ReconEngine, ReconEventType
from core.threat import ThreatMonitor, ThreatLevel
from core.ids_engine import IDSEngine
from core.pmkid_sim import PMKIDSimulator
from core.spectrum_analysis import SpectrumAnalyzer
from ui.banner import Banner
from ui.left_panel import LeftPanel
from ui.right_panel import RightPanel
from ui.attack_panel import AttackPanel


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(config.APP_TITLE)
        self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.setMinimumSize(config.WINDOW_MIN_W, config.WINDOW_MIN_H)

        self._dsp = DSPEngine()
        self._recon = ReconEngine()
        self._threat = ThreatMonitor()
        self._ids = IDSEngine()
        self._pmkid = PMKIDSimulator()
        self._spectrum = SpectrumAnalyzer()
        self._simulator = AttackSimulator()
        self._simulator.packet_generated.connect(self._on_packet)

        self._receiver: Optional[TelemetryReceiver] = None
        self._connected: bool = False
        self._current_port: str = ""
        self._pkt_timestamps: deque[float] = deque(maxlen=500)
        self._throughput_samples = deque(maxlen=100)
        self._packet_bytes_window = deque()
        self._last_throughput_calc = 0.0
        self._pending_raw: Optional[np.ndarray] = None
        self._pending_smooth: Optional[np.ndarray] = None
        self._data_dirty: bool = False
        self._last_ui_update = 0.0

        self._mitm_panel = MITMPanel()
        self._mitm_panel.payload_updated.connect(self._on_payload_updated)
        self._mitm_panel.mitm_started.connect(self._on_mitm_started)
        self._mitm_panel.mitm_stopped.connect(self._on_mitm_stopped)
        self._mitm_panel.terminate_passive_selected.connect(
            self._on_terminate_passive_selected
        )
        self._mitm_panel.terminate_all_passive.connect(self._on_terminate_all_passive)
        self._recon_panel = ReconPanel()
        self._recon_panel._scan_btn.clicked.connect(self._start_recon_scan)
        self._recon_panel.port_scan_requested.connect(self._start_port_scan)
        self._doc_panel = DocPanel()
        self._scanner_thread = None
        self._port_scanner_thread = None
        self._mitm_engines = {}
        self._passive_engines = {}
        self._harvester_active = False

        self._web_server = DynamicWebServer(port=80)
        self._web_server.start()

        self._build_ui()
        self._create_menus()

        self._timer = QTimer(self)
        self._timer.setInterval(config.PLOT_UPDATE_INTERVAL_MS)
        self._timer.timeout.connect(self._on_timer)

        self._log.log("S.P.E.C.T.R.E. Engine OS v1.0 initialised", "OK")

    def _create_menus(self) -> None:
        mb = self.menuBar()
        mb.setStyleSheet("""
            QMenuBar { background-color: #0A0A0F; border-bottom: 1px solid #1A1A2E; color: #E0E0E0; }
            QMenuBar::item { background-color: transparent; padding: 6px 12px; }
            QMenuBar::item:selected { background-color: #00FF41; color: #0A0A0A; }
            QMenu { background-color: #0A0A0F; border: 1px solid #1A1A2E; color: #E0E0E0; }
            QMenu::item { padding: 6px 24px 6px 36px; }
            QMenu::item:selected { background-color: #00FF41; color: #0A0A0A; }
            QMenu::indicator { width: 12px; height: 12px; left: 12px; border: 1px solid #00FF41; }
            QMenu::indicator:checked { background-color: #00FF41; }
            QMenu::indicator:unchecked { background-color: transparent; }
        """)

        # ── File Menu ──
        file_menu = mb.addMenu("&File")
        act_exit = QAction("E&xit", self)
        act_exit.setShortcut(QKeySequence.Quit)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # ── Edit Menu ──
        edit_menu = mb.addMenu("&Edit")
        act_clear_log = QAction("Clear Event Log", self)
        act_clear_log.triggered.connect(lambda: self._log.clear())
        edit_menu.addAction(act_clear_log)
        act_reset_dsp = QAction("Reset DSP History", self)
        act_reset_dsp.triggered.connect(lambda: self._dsp.reset())
        edit_menu.addAction(act_reset_dsp)

        # ── View Menu ──
        view_menu = mb.addMenu("&View")
        act_fullscreen = QAction("Toggle Full Screen", self)
        act_fullscreen.setShortcut(QKeySequence(Qt.Key.Key_F11))
        act_fullscreen.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(act_fullscreen)
        view_menu.addSeparator()

        for title, widget in self._available_tabs:
            tab_menu = view_menu.addMenu(f"Show {title.title()}")
            act_open = QAction("Open Panel", self)
            act_open.triggered.connect(
                lambda checked=False, w=widget, t=title: self._show_tab(w, t)
            )
            tab_menu.addAction(act_open)
            tab_menu.addSeparator()

            if title == "DEFENSIVE / ANALYTICS":
                left_widget = self._left
                right_widget = self._right
            elif title == "OFFENSIVE / ATTACK":
                left_widget = self._attack_panel._left_container
                right_widget = self._attack_panel._right_container
            elif title == "MAN-IN-THE-MIDDLE":
                left_widget = self._mitm_panel._left_container
                right_widget = self._mitm_panel._right_container
            elif title == "NETWORK RECON / INTEL":
                left_widget = self._recon_panel._left_container
                right_widget = self._recon_panel._right_container
            else:  # DOCUMENTATION / AI
                left_widget = self._doc_panel._left_container
                right_widget = self._doc_panel._right_container

            act_left = QAction("Show Left Panel", self)
            act_left.setCheckable(True)
            act_left.setChecked(not left_widget.isHidden())
            act_left.toggled.connect(left_widget.setVisible)
            tab_menu.addAction(act_left)

            act_right = QAction("Show Right Panel", self)
            act_right.setCheckable(True)
            act_right.setChecked(not right_widget.isHidden())
            act_right.toggled.connect(right_widget.setVisible)
            tab_menu.addAction(act_right)

            if title == "DEFENSIVE / ANALYTICS":
                rp_menu = tab_menu.addMenu("Right Panel Elements")
                for i in range(self._right._tabs.count()):
                    tab_text = self._right._tabs.tabText(i)
                    act_rp = QAction(tab_text.title(), self)
                    act_rp.setCheckable(True)
                    act_rp.setChecked(True)
                    act_rp.toggled.connect(
                        lambda checked, idx=i: self._right._tabs.setTabVisible(
                            idx, checked
                        )
                    )
                    rp_menu.addAction(act_rp)

                tab_menu.addSeparator()
                act_refresh = QAction("Refresh All Graphs", self)
                act_refresh.triggered.connect(self._refresh_all_graphs)
                tab_menu.addAction(act_refresh)

                act_payload = None
            elif title == "MAN-IN-THE-MIDDLE":
                rp_menu = None
                act_payload = QAction("Show HTTP Payload Config", self)
                act_payload.setCheckable(True)
                act_payload.setChecked(
                    not self._mitm_panel._payload_container.isHidden()
                )
                act_payload.toggled.connect(
                    self._mitm_panel._payload_container.setVisible
                )
                tab_menu.addAction(act_payload)
            else:
                rp_menu = None
                act_payload = None

            def _update_tab_menu(
                w=widget,
                a_l=act_left,
                a_r=act_right,
                l_w=left_widget,
                r_w=right_widget,
                rp=rp_menu,
                a_p=act_payload,
            ):
                is_open = self._tabs.indexOf(w) != -1
                a_l.setEnabled(is_open)
                a_r.setEnabled(is_open)
                a_l.setChecked(not l_w.isHidden())
                a_r.setChecked(not r_w.isHidden())
                if rp:
                    rp.setEnabled(is_open)
                if a_p:
                    is_http_selected = (
                        self._mitm_panel._vector_combo.currentText()
                        == "HTTP INJECTOR (Visual)"
                    )
                    a_p.setEnabled(is_open and is_http_selected)
                    a_p.setChecked(not self._mitm_panel._payload_container.isHidden())

            tab_menu.aboutToShow.connect(_update_tab_menu)

        view_menu.addSeparator()
        act_reset = QAction("Reset to Default", self)
        act_reset.triggered.connect(self._reset_tabs)
        view_menu.addAction(act_reset)

        # ── Tools Menu ──
        tools_menu = mb.addMenu("&Tools")
        act_arm = QAction("Arm Console", self)
        act_arm.triggered.connect(
            lambda: (
                self._attack_panel._toggle_arm()
                if not self._attack_panel._armed
                else None
            )
        )
        tools_menu.addAction(act_arm)
        act_disarm = QAction("Disarm Console", self)
        act_disarm.triggered.connect(
            lambda: (
                self._attack_panel._toggle_arm() if self._attack_panel._armed else None
            )
        )
        tools_menu.addAction(act_disarm)

        # ── Help Menu ──
        help_menu = mb.addMenu("&Help")
        act_about = QAction("&About S.P.E.C.T.R.E.", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _reset_tabs(self) -> None:
        while self._tabs.count() > 0:
            self._tabs.removeTab(0)
        for title, widget in self._available_tabs:
            self._show_tab(widget, title)
        # Ensure Defensive / Analytics (the first tab) is focused by default
        if self._tabs.count() > 0:
            self._tabs.setCurrentIndex(0)

    def _show_tab(self, widget: QWidget, title: str) -> None:
        idx = self._tabs.indexOf(widget)
        if idx == -1:
            self._tabs.addTab(widget, title)
            idx = self._tabs.indexOf(widget)
        self._tabs.setCurrentIndex(idx)
        self._update_tab_visibility()

    @Slot(int)
    def _on_tab_close_requested(self, index: int) -> None:
        self._tabs.removeTab(index)
        self._update_tab_visibility()

    @Slot(QPoint)
    def _show_tab_context_menu(self, pos: QPoint) -> None:
        index = self._tabs.tabBar().tabAt(pos)
        if index >= 0:
            menu = QMenu(self)
            close_action = menu.addAction("Close Tab")
            action = menu.exec(self._tabs.tabBar().mapToGlobal(pos))
            if action == close_action:
                self._on_tab_close_requested(index)

    def _update_tab_visibility(self) -> None:
        if self._tabs.count() == 0:
            self._tab_stack.setCurrentWidget(self._placeholder)
        else:
            self._tab_stack.setCurrentWidget(self._tabs)

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _refresh_all_graphs(self) -> None:
        """Clear and reset all graph data in the Defensive / Analytics left panel."""
        import numpy as np

        # Reset DSP engine history
        self._dsp.reset()

        # Clear left panel buffers and curves
        self._left._rssi_raw_buf.clear()
        self._left._rssi_smooth_buf.clear()
        self._left._throughput_buf.clear()

        # Reset RSSI scope
        self._left._curve_raw.setData([], [])
        self._left._curve_smooth.setData([], [])

        # Reset channel spectrum
        self._left._bar_spectrum.setOpts(height=[0] * 13)

        # Reset throughput graph
        self._left._curve_throughput.setData([], [])

        # Clear throughput window data
        self._throughput_samples.clear()
        self._packet_bytes_window.clear()

        # Reset spectrum engine
        self._spectrum.reset()

        self._log.log("All graphs refreshed and reset.", "OK")

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About S.P.E.C.T.R.E. Engine",
            "<h3>S.P.E.C.T.R.E. Engine OS v1.0</h3><p>Signal Processing & Electronic Cyber Security Reconnaissance Engine.</p><p>Copyright © 2026 SPECTRE Systems.</p>",
        )

    # ─── UI Construction ──────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._banner = Banner()
        self._banner.connect_requested.connect(self._on_connect_requested)
        self._banner.disconnect_requested.connect(self._on_disconnect_requested)
        self._banner.ma_window_changed.connect(self._on_ma_changed)
        root_layout.addWidget(self._banner)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{config.COLOR_BORDER};")
        root_layout.addWidget(sep)

        self._body_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._body_splitter.setHandleWidth(4)
        self._left = LeftPanel()
        self._right = RightPanel()
        self._body_splitter.addWidget(self._left)
        self._body_splitter.addWidget(self._right)
        self._body_splitter.setStretchFactor(0, config.LEFT_PANEL_RATIO)
        self._body_splitter.setStretchFactor(1, config.RIGHT_PANEL_RATIO)
        self._body_splitter.setSizes([1120, 480])

        self._tabs = QTabWidget()
        self._tabs.setMovable(True)
        self._tabs.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tabs.tabBar().customContextMenuRequested.connect(
            self._show_tab_context_menu
        )

        self._attack_panel = AttackPanel()
        self._attack_panel.attack_engaged.connect(self._on_attack_engaged)
        self._attack_panel.attack_aborted.connect(self._on_attack_aborted)
        self._attack_panel.host_ap_toggled.connect(self._on_host_ap_toggled)

        self._mitm_panel.terminate_passive_selected.connect(
            self._on_terminate_passive_selected
        )
        self._mitm_panel.terminate_all_passive.connect(self._on_terminate_all_passive)

        self._available_tabs = [
            ("DEFENSIVE / ANALYTICS", self._body_splitter),
            ("OFFENSIVE / ATTACK", self._attack_panel),
            ("MAN-IN-THE-MIDDLE", self._mitm_panel),
            ("NETWORK RECON / INTEL", self._recon_panel),
            ("DOCUMENTATION / AI", self._doc_panel),
        ]

        self._tab_stack = QStackedWidget()
        self._placeholder = QWidget()
        ph_layout = QVBoxLayout(self._placeholder)
        ph_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_label = QLabel("+\n\nOpen a new panel from the View menu")
        ph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_label.setStyleSheet("color: #00FF41; font-size: 24px; font-weight: bold;")
        ph_layout.addWidget(ph_label)

        self._tab_stack.addWidget(self._placeholder)
        self._tab_stack.addWidget(self._tabs)
        root_layout.addWidget(self._tab_stack, stretch=1)
        self._reset_tabs()

        self._status = self._right.status
        self._log = self._right.log
        self._timeline = self._right.timeline
        self._ids_rules_widget = self._right.ids_rules

        self._status.set_connection("--", config.SERIAL_BAUD, False)
        self._status.set_dsp_active(False)
        self._status.set_threat(ThreatLevel.SECURE, 0.0, 0)

    # ─── Connection Management ───────────────────────────────────────────────
    @Slot(str, bool)
    def _on_connect_requested(self, port: str, demo: bool) -> None:
        if self._connected:
            return
        self._log.log(f"Opening {port} @ {config.SERIAL_BAUD} baud …", "INFO")
        self._dsp.reset()
        self._recon.reset()
        self._threat.reset()
        self._ids.reset()
        self._pmkid.reset()
        self._spectrum.reset()
        self._pkt_timestamps.clear()
        self._packet_bytes_window.clear()
        self._throughput_samples.clear()

        self._receiver = TelemetryReceiver(port=port, baud=config.SERIAL_BAUD)
        self._receiver.packet_received.connect(self._on_packet)
        self._receiver.scan_result.connect(self._on_packet)
        self._receiver.status_changed.connect(self._on_status_msg)
        self._receiver.error_occurred.connect(self._on_error)
        self._receiver.target_locked.connect(self._on_target_locked)
        self._receiver.connected.connect(self._on_connected)
        self._receiver.disconnected.connect(self._on_disconnected)
        self._status.set_target("--")
        self._receiver.start()

    @Slot()
    def _on_disconnect_requested(self) -> None:
        self._stop_receiver()

    def _stop_receiver(self) -> None:
        if self._receiver is not None:
            self._receiver.stop()
            if not self._receiver.wait(3000):
                self._receiver.terminate()
            self._receiver = None

    # ─── Telemetry Thread Slots ──────────────────────────────────────────────
    @Slot(dict)
    def _on_packet(self, pkt: dict) -> None:
        now = time.monotonic()
        self._pkt_timestamps.append(now)
        payload_size = pkt.get("payload_size", 0)
        if isinstance(payload_size, (int, float)) and payload_size > 0:
            self._packet_bytes_window.append((now, payload_size))
        cutoff = now - 1.0
        while self._packet_bytes_window and self._packet_bytes_window[0][0] < cutoff:
            self._packet_bytes_window.popleft()

        channel = pkt.get("channel")
        if channel is not None:
            channel = int(channel)
        raw, smoothed = self._dsp.push(pkt["rssi"], channel=channel)
        self._pending_raw = raw
        self._pending_smooth = smoothed
        self._data_dirty = True

        self._spectrum.add_packet(pkt)
        threat = self._threat.update(pkt)
        events = self._recon.process(pkt)
        triggered_ids = self._ids.process_packet(pkt)

        if pkt.get("subtype") == 11 and pkt.get("bssid") and pkt.get("ssid"):
            self._pmkid.simulate_capture(pkt["ssid"], pkt["bssid"], "AA:BB:CC:DD:EE:FF")

        if not hasattr(self, "_last_ui_update"):
            self._last_ui_update = 0.0
        if now - self._last_ui_update < 0.066:
            return
        self._last_ui_update = now

        if pkt.get("subtype") == 12:
            # Throttle the RX log: max once per 0.5s per source MAC
            src = pkt.get("bssid", "UNKNOWN")
            if not hasattr(self, "_deauth_rx_times"):
                self._deauth_rx_times: dict = {}
            last_rx = self._deauth_rx_times.get(src, 0.0)
            if now - last_rx >= 0.5:
                self._log.log(f"DEAUTH FRAME DETECTED | SRC: {src}", "RX")
                self._deauth_rx_times[src] = now

        if not hasattr(self, "_last_deauth_alert_log"):
            self._last_deauth_alert_log = 0.0
        if not hasattr(self, "_was_under_attack"):
            self._was_under_attack = False

        if threat.deauth_level == ThreatLevel.ALERT:
            self._was_under_attack = True
            # Throttle: log the ALERT message at most once per second
            if now - self._last_deauth_alert_log >= 1.0:
                conc_pct = int(threat.src_concentration * 100)
                persist_s = threat.persistence
                # Label based on persistence — call it what it is
                if persist_s >= 5:
                    label = "CONFIRMED DEAUTH FLOOD ATTACK"
                elif persist_s >= 2:
                    label = "SUSTAINED DEAUTH ATTACK"
                else:
                    label = "DEAUTH ATTACK DETECTED"
                self._log.log(
                    f"{label} | {threat.deauth_rate:.1f} f/s | "
                    f"SRC: {threat.top_src} ({conc_pct}% of frames) | "
                    f"Duration: {persist_s}s",
                    "ALERT",
                )
                self._last_deauth_alert_log = now
                self._timeline.add_event(
                    "ALERT",
                    f"{label}: {threat.deauth_rate:.1f}/s from {threat.top_src}"
                )
        elif threat.deauth_level == ThreatLevel.WARNING:
            # High-ish rate but spread across many sources → likely congestion
            if now - self._last_deauth_alert_log >= 2.0:
                self._log.log(
                    f"ELEVATED DEAUTH RATE — {threat.deauth_rate:.1f} f/s "
                    f"(multi-source, likely congestion, not an attack)",
                    "WARN",
                )
                self._last_deauth_alert_log = now
        else:
            # Attack has ended — notify once
            if self._was_under_attack:
                self._log.log("DEAUTH THREAT CLEARED — network traffic returned to normal.", "OK")
                self._timeline.add_event("OK", "Deauth attack ended")
                self._was_under_attack = False

        for ev in events:
            level = "ALERT" if ev.event_type == ReconEventType.ROGUE_AP else "RECON"
            self._log.log(ev.message, level)
            if ev.event_type == ReconEventType.ROGUE_AP:
                self._timeline.add_event(level, ev.message)

        for rule_id in triggered_ids:
            rule_status = next(
                (r for r in self._ids.get_rule_status() if r["id"] == rule_id), None
            )
            if rule_status:
                # Throttle IDS alerts: once per 2 seconds per rule
                if not hasattr(self, "_last_ids_alert_times"):
                    self._last_ids_alert_times: dict = {}
                last_ids = self._last_ids_alert_times.get(rule_id, 0.0)
                if now - last_ids >= 2.0:
                    self._log.log(
                        f"IDS TRIGGER: {rule_status['name']} (Rate exceeded threshold)",
                        "ALERT",
                    )
                    self._timeline.add_event(
                        "ALERT", f"IDS: {rule_status['name']} triggered"
                    )
                    self._last_ids_alert_times[rule_id] = now

    @Slot()
    def _on_connected(self) -> None:
        self._connected = True
        self._current_port = self._receiver.port if self._receiver else "--"
        self._banner.set_connected(True, self._current_port)
        self._status.set_connection(self._current_port, config.SERIAL_BAUD, True)
        self._status.set_dsp_active(True, self._dsp.ma_window)
        self._timer.start()
        self._log.log("Telemetry stream ONLINE", "OK")

    @Slot()
    def _on_disconnected(self) -> None:
        self._connected = False
        self._banner.set_connected(False)
        self._status.set_connection(self._current_port, config.SERIAL_BAUD, False)
        self._status.set_dsp_active(False)
        self._status.set_target("--")
        self._timer.stop()
        self._log.log("Telemetry stream OFFLINE", "WARN")

    @Slot(dict)
    def _on_target_locked(self, target: dict) -> None:
        target_str = f"{target.get('ssid', 'UNKNOWN')} [{target.get('bssid', '--')}]"
        self._status.set_target(target_str)
        self._log.log(f"Passive sniffer target lock detected: {target_str}", "OK")

    @Slot(str)
    def _on_status_msg(self, msg: str) -> None:
        self._log.log(msg, "DEBUG")

    @Slot(str)
    def _on_error(self, msg: str) -> None:
        self._log.log(msg, "ALERT")

    @Slot(int)
    def _on_ma_changed(self, window: int) -> None:
        self._dsp.set_ma_window(window)
        self._status.set_dsp_active(self._connected, window)
        self._log.log(f"Moving average window → {window} samples", "DEBUG")

    def _on_ids_alert(self, rule, rate) -> None:
        self._log.log(f"IDS ALERT: {rule.name} — {rate:.1f} pkts/s", "ALERT")

    # ─── Attack Handling ─────────────────────────────────────────────────────
    @Slot(str, str, int)
    def _on_attack_engaged(self, target: str, vector: str, intensity: int) -> None:
        self._status.set_target(target)
        is_l2_attack = any(x in vector for x in ["ARP", "DHCP", "DNS", "ICMP"])
        if is_l2_attack:
            self._simulator.start(target, vector, intensity)
            self._log.log(
                f"SOFTWARE L2/L3 ATTACK ENGAGED: {vector} -> {target}", "EXEC"
            )
            if hasattr(self, "_l2_worker") and self._l2_worker.isRunning():
                self._l2_worker.stop()
            from core.l2_engine import L2Engine

            self._l2_worker = L2Engine(vector, target, intensity)
            self._l2_worker.log_signal.connect(lambda msg, lvl: self._log.log(msg, lvl))
            self._l2_worker.start()
        else:
            self._simulator.start(target, vector, intensity)
            self._log.log(f"SOFTWARE OFFENSE ENGAGED: {vector} @ {intensity}%", "EXEC")
            if self._receiver and self._connected:
                vector_safe = vector.split()[0]
                cmd = f"CMD:ATTACK,{vector_safe},{target},{intensity}"
                self._receiver.send_command(cmd)
                self._log.log(f"ESP32 RF TRANSMISSION INITIATED | CMD: {cmd}", "WARN")

    @Slot()
    def _on_attack_aborted(self) -> None:
        self._simulator.stop()
        self._log.log("Software offense halted.", "INFO")
        if hasattr(self, "_l2_worker") and self._l2_worker.isRunning():
            self._l2_worker.stop()
            self._log.log("L2 Attack Worker halted.", "INFO")
        if self._receiver and self._connected:
            self._receiver.send_command("CMD:STOP_SIM")
            self._log.log("ESP32 RF transmission halted.", "INFO")

    @Slot(bool)
    def _on_host_ap_toggled(self, active: bool) -> None:
        cmd = f"CMD:HOST_AP,{1 if active else 0}"
        if self._receiver and self._connected:
            self._receiver.send_command(cmd)
        if active:
            demo_pkt = {
                "prefix": "MGMT",
                "subtype": 8,
                "rssi": -30,
                "payload_size": 120,
                "bssid": "DE:AD:BE:EF:00:00",
                "ssid": "SPECTRE_DEMO_AP",
                "channel": 6,
            }
            self._on_packet(demo_pkt)

    # ─── Render Timer ────────────────────────────────────────────────────────
    @Slot()
    def _on_timer(self) -> None:
        now = time.monotonic()
        cutoff = now - 1.0
        recent_bytes = sum(
            size for ts, size in self._packet_bytes_window if ts > cutoff
        )
        throughput_kbs = (recent_bytes / 1024.0) / 1.0
        self._throughput_samples.append(throughput_kbs)
        self._status.set_throughput(throughput_kbs)
        self._left.update_throughput(self._throughput_samples)

        if self._data_dirty and self._pending_raw is not None:
            self._left.update_rssi(self._pending_raw, self._pending_smooth)
            self._data_dirty = False

        try:
            result = self._dsp.get_channel_counts()
            if result is not None and len(result) == 2:
                channels, counts = result
                self._left.update_spectrum(channels, counts)
            else:
                self._left.update_spectrum(np.array([]), np.array([]))
        except Exception as e:
            self._log.log(f"DSP spectrum update skipped: {e}", "DEBUG")

        fake = {"prefix": "MGT", "rssi": 0, "payload_size": 0, "subtype": 0}
        threat = self._threat.update(fake)
        self._status.set_threat(
            threat.deauth_level, threat.deauth_rate, self._threat.total_deauths
        )
        self._status.set_throughput(threat.throughput_kbs)

        recent_pkts = sum(1 for t in self._pkt_timestamps if t > cutoff)
        self._status.set_packet_stats(self._dsp.total_packets, recent_pkts)
        self._status.set_recon_stats(
            self._recon.known_ap_count,
            self._recon.rogue_ap_count,
            self._recon.hidden_net_count,
        )

        ap_count = self._recon.known_ap_count
        if self._data_dirty or (
            self._timer.isActive() and getattr(self, "_last_ap_count", -1) != ap_count
        ):
            targets = []
            for bssid in self._recon._known_aps:
                ssids = self._recon._bssid_to_ssids.get(bssid, set())
                display = f"{sorted(ssids)[0]} ({bssid})" if ssids else bssid
                targets.append((display, bssid))
            self._attack_panel.update_targets(targets)
            self._last_ap_count = ap_count

        if hasattr(self, "_ids_rules_widget"):
            self._ids_rules_widget.update_rules(self._ids.get_rule_status())

        if int(now) % 2 == 0 and self._connected:
            occ = self._spectrum.calculate_occupancy(6)
            self._timeline.add_event(
                "INFO",
                f"Ch6 Occ: Mgmt {occ.management_pct:.0f}% | Data {occ.data_pct:.0f}% | Beacons: {occ.beacon_count}",
            )

    # ─── MITM Handling ───────────────────────────────────────────────────────
    @Slot(str, str, str, int, str)
    def _on_mitm_started(
        self,
        target: str,
        gateway: str,
        vector: str,
        intensity: int,
        block_target: str = "",
    ) -> None:
        is_passive = (
            "CREDENTIAL" in vector
            or "HARVEST" in vector
            or "PASSIVE" in vector
            or "INJECT" in vector
            or "HTTP" in vector
            or "RST" in vector
            or "BLOCK" in vector
            or "COOKIE" in vector
            or "SESSION" in vector
            or "JWT" in vector  # <--- ADD THIS
        )

        if is_passive:
            # ── FIX: Check RST/BLOCK *BEFORE* INJECT/HTTP ──
            if "RST" in vector or "BLOCK" in vector:
                passive_id = f"RST_Blocker_{len(self._passive_engines) + 1}"
            elif "INJECT" in vector or "HTTP" in vector:
                passive_id = f"Injector_{len(self._passive_engines) + 1}"
            elif "SESSION" in vector or "JWT" in vector:  # <--- ADD THIS
                passive_id = f"Cookie_Sniffer_{len(self._passive_engines) + 1}"
            else:
                passive_id = f"Harvester_{len(self._passive_engines) + 1}"

            # Pass block_target to the engine
            engine = MITMEngine(target, gateway, vector, intensity, block_target)

            engine.log_signal.connect(self._mitm_panel.log_message)
            if hasattr(engine, "passive_log_signal"):
                engine.passive_log_signal.connect(self._mitm_panel.log_passive)
            engine.packet_generated.connect(self._on_packet)
            engine.finished.connect(
                lambda pid=passive_id: self._cleanup_passive_engine(pid)
            )

            engine.start()
            self._passive_engines[passive_id] = engine
            self._mitm_panel.update_passive_dropdown(passive_id, is_adding=True)
            self._log.log(f"Passive Module Engaged: {passive_id} ({vector})", "EXEC")

            if "CREDENTIAL" in vector or "HARVEST" in vector:
                self._web_server.set_harvester_active(True)
            elif "INJECT" in vector or "HTTP" in vector:
                self._web_server.set_injector_active(True)
            elif "SESSION" in vector or "JWT" in vector:  # <--- ADD THIS
                self._web_server.set_session_test_active(True)
                return

        engine_key = "ARP" if "ARP" in vector else "DNS"
        if (
            engine_key in self._mitm_engines
            and self._mitm_engines[engine_key].isRunning()
        ):
            self._log.log(f"{vector} is already active.", "INFO")
            return

        engine = MITMEngine(target, gateway, vector, intensity)
        engine.log_signal.connect(self._mitm_panel.log_message)
        engine.packet_generated.connect(self._on_packet)
        engine.finished.connect(
            lambda key=engine_key: self._mitm_engines.pop(key, None)
        )
        engine.start()
        self._mitm_engines[engine_key] = engine
        self._log.log(f"MITM Module Engaged: {vector}", "EXEC")

    def _cleanup_passive_engine(self, passive_id: str) -> None:
        if passive_id in self._passive_engines:
            del self._passive_engines[passive_id]
        self._mitm_panel.update_passive_dropdown(passive_id, is_adding=False)
        if not self._passive_engines:
            self._web_server.set_harvester_active(False)
            self._web_server.set_injector_active(False)
            self._web_server.set_session_test_active(False)
            self._log.log("Web Server reverted to NORMAL INDEX PAGE mode.", "INFO")
            self._mitm_panel.reset_passive_button()

    @Slot(str)
    def _on_terminate_passive_selected(self, passive_id: str) -> None:
        if passive_id in self._passive_engines:
            engine = self._passive_engines[passive_id]
            engine.stop()
            del self._passive_engines[passive_id]
            self._mitm_panel.update_passive_dropdown(passive_id, is_adding=False)
            self._log.log(f"Passive Module Halted: {passive_id}", "INFO")
            if not self._passive_engines:
                self._web_server.set_harvester_active(False)
                self._web_server.set_injector_active(False)
                self._mitm_panel.reset_passive_button()

    @Slot()
    def _on_terminate_all_passive(self) -> None:
        for pid, engine in list(self._passive_engines.items()):
            engine.stop()
        self._passive_engines.clear()
        self._mitm_panel._passive_dropdown.clear()
        self._mitm_panel._passive_dropdown.addItem("No Passive Modules Active")
        self._mitm_panel._passive_dropdown.setEnabled(False)
        self._mitm_panel._terminate_selected_passive_btn.setEnabled(False)
        self._mitm_panel._terminate_all_passive_btn.setEnabled(False)
        self._web_server.set_harvester_active(False)
        self._web_server.set_injector_active(False)
        self._web_server.set_session_test_active(False)
        self._mitm_panel.reset_passive_button()

    @Slot()
    def _on_mitm_stopped(self) -> None:
        for key, engine in list(self._mitm_engines.items()):
            if engine.isRunning():
                engine.stop()
        self._mitm_engines.clear()
        for pid, engine in list(self._passive_engines.items()):
            if engine.isRunning():
                engine.stop()
        self._passive_engines.clear()
        self._mitm_panel.update_passive_dropdown("DUMMY_ID", is_adding=False)
        self._mitm_panel.reset_passive_button()
        self._web_server.set_harvester_active(False)
        self._web_server.set_injector_active(False)

    @Slot(str, str)
    def _on_payload_updated(self, payload_type: str, custom_script: str) -> None:
        attacker_ip = "192.168.1.108"
        if self._mitm_engines:
            attacker_ip = list(self._mitm_engines.values())[0].attacker_ip
        elif self._passive_engines:
            attacker_ip = list(self._passive_engines.values())[0].attacker_ip
        self._web_server.set_injector_payload(payload_type, custom_script, attacker_ip)
        for pid, engine in self._passive_engines.items():
            if "Injector" in pid and engine.isRunning():
                engine.set_payload(payload_type, custom_script)

    def _start_recon_scan(self):
        subnet = self._recon_panel._subnet_input.text().strip()
        if not subnet:
            self._log.log("Invalid subnet.", "CRIT")
            return

        if self._scanner_thread and self._scanner_thread.isRunning():
            self._log.log("Scan already in progress.", "WARN")
            return

        self._recon_panel.clear_tree()  # Changed from _clear_table
        self._recon_panel.set_status("Scanning...")
        self._log.log(f"Starting Network Recon on {subnet}", "EXEC")

        self._scanner_thread = NetworkScanner(subnet)
        self._scanner_thread.device_found.connect(
            lambda d: self._recon_panel.add_device(
                d["ip"], d["mac"], d["vendor"], d.get("os", "Unknown")
            )
        )
        self._scanner_thread.device_found.connect(
            lambda d: self._recon_panel.add_device(d["ip"], d["mac"], d["vendor"])
        )
        self._scanner_thread.scan_finished.connect(self._on_scan_finished)
        self._scanner_thread.log_signal.connect(self._log.log)
        self._scanner_thread.start()

    def _on_scan_finished(self):
        self._recon_panel.set_status("Idle")
        self._log.log("Network Recon scan finished.", "INFO")

    def _start_port_scan(self, target_ip: str):
        """Starts a port scan on the specified device IP."""
        try:
            if not target_ip:
                self._log.log("Port scan failed: No IP provided.", "CRIT")
                return

            if self._port_scanner_thread and self._port_scanner_thread.isRunning():
                self._log.log("Port scan already in progress.", "WARN")
                return

            self._recon_panel.set_status(f"Scanning ports on {target_ip}...")
            self._log.log(f"Starting TCP Port Scan on {target_ip}", "EXEC")

            # Find the tree item and clear existing ports
            for i in range(self._recon_panel._tree.topLevelItemCount()):
                item = self._recon_panel._tree.topLevelItem(i)
                if item.text(0) == target_ip:
                    item.takeChildren()
                    item.setText(4, "0")
                    break

            # Initialize and start the scanner
            self._port_scanner_thread = PortScanner(target_ip)
            self._port_scanner_thread.port_found.connect(
                lambda port, service: self._recon_panel.add_open_port(
                    target_ip, port, service
                )
            )
            self._port_scanner_thread.scan_finished.connect(self._on_port_scan_finished)
            self._port_scanner_thread.log_signal.connect(self._log.log)
            self._port_scanner_thread.start()

        except Exception as e:
            self._log.log(f"Port scan failed to start: {str(e)}", "CRIT")

    def _on_port_scan_finished(self):
        self._recon_panel.set_status("Idle")
        self._log.log("Port scan finished.", "INFO")

    def closeEvent(self, event) -> None:
        self._timer.stop()
        self._stop_receiver()
        if hasattr(self, "_web_server"):
            self._web_server.stop()
        for engine in list(self._mitm_engines.values()):
            engine.stop()
        for engine in list(self._passive_engines.values()):
            engine.stop()
        super().closeEvent(event)

