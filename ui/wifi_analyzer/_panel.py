# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/wifi_analyzer/_panel.py — WiFi Analyzer Tab Orchestrator
"""

from typing import List, Dict, Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QComboBox, QCheckBox
)
import config
from core.network.wifi_scanner import WiFiScanner
from core.hardware.sonar_engine import SonarEngine
from ui.settings.widgets import ComboBox

from ui.wifi_analyzer._color import BSSIDColorRegistry
from ui.wifi_analyzer._channel_graph import ChannelGraphWidget
from ui.wifi_analyzer._time_graph import TimeGraphWidget
from ui.wifi_analyzer._channel_rating import ChannelRatingWidget
from ui.wifi_analyzer._ap_table import APTableWidget


class WifiAnalyzerPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scanner = WiFiScanner(self)
        self._sonar = SonarEngine(self)
        
        self._mesh_target_ssid = ""
        self._color_registry = BSSIDColorRegistry()
        
        self._build_ui()
        
        self._scanner.scan_results_ready.connect(self._on_scan_results)
        self._scanner.start()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Top Control Bar
        ctrl_bar = QHBoxLayout()
        
        self._pause_btn = QPushButton("⏸ PAUSE SNAPSHOT")
        self._pause_btn.setCheckable(True)
        self._pause_btn.clicked.connect(self._toggle_pause)
        
        self._refresh_btn = QPushButton("⟳ FORCE REFRESH")
        self._refresh_btn.clicked.connect(self._force_refresh)
        
        self._band_combo = ComboBox()
        self._band_combo.addItems(["2.4 GHz Band", "5 GHz Band"])
        self._band_combo.currentTextChanged.connect(self._on_band_changed)
        self._band_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        
        ctrl_bar.addWidget(self._band_combo)
        
        self._mesh_roaming_cb = QCheckBox("Mesh Roaming Mode")
        self._mesh_roaming_cb.setStyleSheet(f"color: {config.COLOR_ACCENT_CYAN}; font-weight: bold;")
        self._mesh_roaming_cb.stateChanged.connect(self._on_mesh_roaming_toggled)
        ctrl_bar.addWidget(self._mesh_roaming_cb)
        
        self._mesh_ssid_combo = ComboBox()
        self._mesh_ssid_combo.setEditable(True)
        self._mesh_ssid_combo.lineEdit().setPlaceholderText("Target SSID...")
        self._mesh_ssid_combo.hide()
        self._mesh_ssid_combo.currentTextChanged.connect(self._on_mesh_ssid_changed)
        ctrl_bar.addWidget(self._mesh_ssid_combo)

        ctrl_bar.addStretch()
        
        self._sonar_combo = ComboBox()
        self._sonar_combo.setEditable(True)
        self._sonar_combo.lineEdit().setPlaceholderText("Target BSSID...")
        ctrl_bar.addWidget(self._sonar_combo)
        
        self._sonar_btn = QPushButton("SONAR")
        self._sonar_btn.setCheckable(True)
        self._sonar_btn.clicked.connect(self._toggle_sonar)
        ctrl_bar.addWidget(self._sonar_btn)
        
        ctrl_bar.addWidget(self._refresh_btn)
        ctrl_bar.addWidget(self._pause_btn)
        layout.addLayout(ctrl_bar)
        
        self._style_buttons()

        # Main Tabs
        self._tabs = QTabWidget()

        # 1. Channel Graph
        self._channel_graph = ChannelGraphWidget()
        self._tabs.addTab(self._channel_graph, "Channel Graph")

        # 2. Time Graph
        self._time_graph = TimeGraphWidget()
        self._tabs.addTab(self._time_graph, "Time Graph")

        # 3. Channel Rating
        self._channel_rating = ChannelRatingWidget()
        self._tabs.addTab(self._channel_rating, "Channel Rating")

        # 4. Access Point List
        self._table = APTableWidget()
        self._tabs.addTab(self._table, "Access Point List")

        layout.addWidget(self._tabs)

    def _on_band_changed(self, text: str) -> None:
        is_5ghz = "5 GHz" in text
        self._channel_graph.set_band(is_5ghz)
        self._force_refresh()

    def _toggle_pause(self) -> None:
        self._scanner.set_paused(self._pause_btn.isChecked())

    def _force_refresh(self) -> None:
        """Clear all stored data and graphs to force a fresh canvas."""
        self._time_graph.reset_data()
        self._table.setRowCount(0)
        self._channel_graph.clear()
        
        # Unpause if currently paused to immediately resume scanning
        if self._pause_btn.isChecked():
            self._pause_btn.setChecked(False)
            self._toggle_pause()

    def _toggle_sonar(self) -> None:
        if self._sonar_btn.isChecked():
            self._sonar_btn.setStyleSheet(f"background-color: {config.COLOR_ACCENT_RED}; color: white; font-weight: bold;")
            self._sonar.start()
        else:
            self._style_buttons() # Reset to default
            self._sonar.stop()

    def _on_mesh_roaming_toggled(self, state: int) -> None:
        if state == Qt.CheckState.Checked.value:
            self._mesh_ssid_combo.show()
            # Populate dropdown with unique SSIDs from current results
            ssids = set()
            for r in range(self._table.rowCount()):
                ssid_item = self._table.item(r, 0)
                if ssid_item and ssid_item.text():
                    ssids.add(ssid_item.text())
            self._mesh_ssid_combo.clear()
            self._mesh_ssid_combo.addItems(sorted(list(ssids)))
        else:
            self._mesh_ssid_combo.hide()

    def _on_mesh_ssid_changed(self, text: str) -> None:
        self._mesh_target_ssid = text

    def _on_scan_results(self, results: List[Dict[str, Any]]) -> None:
        is_5ghz = "5 GHz" in self._band_combo.currentText()
        mesh_roaming = self._mesh_roaming_cb.isChecked()
        
        self._table.update_table(results, mesh_roaming, self._mesh_target_ssid)
        
        # Populate Sonar Combo safely
        current_items = set(self._sonar_combo.itemText(idx) for idx in range(self._sonar_combo.count()))
        for ap in results:
            display_text = f"{ap['ssid']} ({ap['bssid'].upper()})"
            if display_text not in current_items:
                self._sonar_combo.addItem(display_text)

        # Sonar Logic
        if self._sonar.is_active():
            target_text = self._sonar_combo.currentText().strip()
            if "(" in target_text and target_text.endswith(")"):
                target_bssid = target_text.split("(")[-1].strip(")")
            else:
                target_bssid = target_text.upper()
                
            target_rssi = -100.0
            for ap in results:
                if ap['bssid'].upper() == target_bssid:
                    target_rssi = ap['rssi']
                    break
            self._sonar.set_rssi(target_rssi)

        self._channel_graph.update_graph(results, is_5ghz, mesh_roaming, self._mesh_target_ssid, self._color_registry)
        self._time_graph.update_graph(results, mesh_roaming, self._mesh_target_ssid, self._color_registry)
        self._channel_rating.update_rating(results, is_5ghz)

    def _style_buttons(self) -> None:
        default_style = f"""
            QPushButton {{
                background-color: {config.COLOR_PANEL_BG};
                color: {config.COLOR_TEXT_PRIMARY};
                border: 1px solid {config.COLOR_BORDER};
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:checked {{
                background-color: {config.COLOR_ACCENT_RED};
                color: #FFF;
            }}
            QPushButton:hover {{
                background-color: {config.COLOR_ACCENT_CYAN};
                color: {config.COLOR_BG};
            }}
        """
        self._pause_btn.setStyleSheet(default_style)
        self._refresh_btn.setStyleSheet(default_style)
        if hasattr(self, '_sonar_btn'):
            self._sonar_btn.setStyleSheet(default_style)

    def refresh_theme(self) -> None:
        self._style_buttons()
        is_5ghz = "5 GHz" in self._band_combo.currentText()
        self._channel_graph.refresh_theme(is_5ghz)
        self._time_graph.refresh_theme()
        self._table.refresh_theme()
        
        self._tabs.style().unpolish(self._tabs)
        self._tabs.style().polish(self._tabs)
        self._tabs.tabBar().style().unpolish(self._tabs.tabBar())
        self._tabs.tabBar().style().polish(self._tabs.tabBar())
        self._tabs.update()
