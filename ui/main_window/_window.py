from __future__ import annotations
from ui.mitm import MITMPanel
from core.web_server import DynamicWebServer
from core.mitm import MITMEngine
import time
from ui.doc_panel import DocPanel
from collections import deque
from typing import Optional
from core.network.network_scanner import NetworkScanner
from core.network.port_scanner import PortScanner
from ui.recon_panel import ReconPanel
import numpy as np
from PySide6.QtCore import Qt, QTimer, Slot, QPoint
from core.hardware.simulator import AttackSimulator
from PySide6.QtGui import QAction, QIcon, QKeySequence
from core.settings_manager import SettingsManager
from ui.settings.settings_panel import SettingsPanel
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
from core.hardware.telemetry import TelemetryReceiver
from core.analytics.dsp import DSPEngine
from core.network.recon import ReconEngine, ReconEventType
from core.analytics.threat import ThreatMonitor, ThreatLevel
from core.analytics.ids_engine import IDSEngine
from core.analytics.pmkid_sim import PMKIDSimulator
from core.analytics.spectrum_analysis import SpectrumAnalyzer
from ui.banner import Banner
from ui.left_panel import LeftPanel
from ui.right_panel import RightPanel
from ui.attack import AttackPanel
from ui.wifi_analyzer import WifiAnalyzerPanel

from ui.main_window._menu_builder import MenuBuilderMixin
from ui.main_window._packet_handler import PacketHandlerMixin
from ui.main_window._connection_handler import ConnectionHandlerMixin
from ui.main_window._mitm_handler import MITMHandlerMixin

class MainWindow(QMainWindow, MenuBuilderMixin, PacketHandlerMixin, ConnectionHandlerMixin, MITMHandlerMixin):
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

        fps = SettingsManager.instance().settings.plot_fps
        self._timer = QTimer(self)
        self._timer.setInterval(max(8, 1000 // fps))
        self._timer.timeout.connect(self._on_timer)

        # Register for settings changes (theme, FPS, fonts)
        SettingsManager.instance().subscribe(self._on_settings_changed)

        # Live-preview: refresh all inline styles when theme changes (before Apply)
        from core.theme_manager import ThemeManager
        ThemeManager.instance().theme_changed.connect(self._refresh_all_theme)

        self._log.log("S.P.E.C.T.R.E. Engine OS v1.0 initialised", "OK")

    def _reset_tabs(self) -> None:
        while self._tabs.count() > 0:
            self._tabs.removeTab(0)
        for title, widget in self._available_tabs:
            self._show_tab(widget, title)
        # Ensure Defensive / Analytics (the first tab) is focused by default
        if self._tabs.count() > 0:
            self._tabs.setCurrentIndex(0)

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

    def _open_settings(self) -> None:
        """Switch to the Settings panel overlay."""
        self._tab_stack.setCurrentWidget(self._settings_panel)

    def _close_settings(self) -> None:
        """Close Settings panel overlay and return to main tabs."""
        self._tab_stack.setCurrentWidget(self._tabs)

    def _on_settings_changed(self, settings) -> None:
        """Called by SettingsManager when settings are applied."""
        # Update render timer to match new FPS setting
        fps = settings.plot_fps
        self._timer.setInterval(max(8, 1000 // fps))

        # Refresh all inline-styled UI panels for the new theme
        self._refresh_all_theme()

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About S.P.E.C.T.R.E. Engine",
            "<h3>S.P.E.C.T.R.E. Engine OS v1.0</h3><p>Signal Processing & Electronic Cyber Security Reconnaissance Engine.</p><p>Copyright © 2026 SPECTRE Systems.</p>",
        )

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

        self._settings_panel = SettingsPanel()
        self._settings_panel.close_requested.connect(self._close_settings)

        self._wifi_panel = WifiAnalyzerPanel()

        self._available_tabs = [
            ("DEFENSIVE / ANALYTICS", self._body_splitter),
            ("L1/L2 WIFI ANALYZER", self._wifi_panel),
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
        ph_label.setStyleSheet(
            f"color: {config.COLOR_ACCENT_GREEN}; font-size: 24px; font-weight: bold;"
        )
        ph_layout.addWidget(ph_label)

        self._tab_stack.addWidget(self._placeholder)
        self._tab_stack.addWidget(self._tabs)
        self._tab_stack.addWidget(self._settings_panel)
        root_layout.addWidget(self._tab_stack, stretch=1)
        self._reset_tabs()

        self._status = self._right.status
        self._log = self._right.log
        self._timeline = self._right.timeline
        self._ids_rules_widget = self._right.ids_rules

        self._status.set_connection("--", config.SERIAL_BAUD, False)
        self._status.set_dsp_active(False)
        self._status.set_threat(ThreatLevel.SECURE, 0.0, 0)

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
            from core.network.l2_engine import L2Engine

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

    def _on_scan_finished(self):
        self._recon_panel.set_status("Idle")
        self._log.log("Network Recon scan finished.", "INFO")

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
            
        if hasattr(self, '_wifi_panel'):
            self._wifi_panel.stop()
            
        if hasattr(self, '_scanner_thread') and self._scanner_thread:
            self._scanner_thread.stop()
            
        if hasattr(self, '_port_scanner_thread') and self._port_scanner_thread:
            self._port_scanner_thread.stop()
        
        from PySide6.QtWidgets import QApplication
        QApplication.quit()
        
        super().closeEvent(event)
