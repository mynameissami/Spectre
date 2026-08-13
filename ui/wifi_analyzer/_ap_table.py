# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/wifi_analyzer/_ap_table.py — Access Point Table Widget
"""

from typing import List, Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
import config

class APTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 7, parent)
        self.setHorizontalHeaderLabels(["SSID", "BSSID", "Channel", "Freq (MHz)", "Signal (dBm)", "Security", "Vendor"])
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {config.COLOR_PLOT_BG};
                alternate-background-color: {config.COLOR_PANEL_BG};
                color: {config.COLOR_TEXT_PRIMARY};
                gridline-color: {config.COLOR_PLOT_GRID};
                border: none;
            }}
            QHeaderView {{
                background-color: {config.COLOR_PLOT_BG};
            }}
            QHeaderView::section {{
                background-color: {config.COLOR_PANEL_BG};
                color: {config.COLOR_ACCENT_CYAN};
                font-weight: bold;
                border: 1px solid {config.COLOR_PLOT_GRID};
                padding: 4px;
            }}
        """)

    def update_table(self, results: List[Dict[str, Any]], mesh_roaming: bool, mesh_target: str) -> None:
        self.setRowCount(0)
        row_idx = 0
        for ap in results:
            if mesh_roaming and ap['ssid'] != mesh_target:
                continue
            self.insertRow(row_idx)
            self.setItem(row_idx, 0, QTableWidgetItem(ap['ssid']))
            self.setItem(row_idx, 1, QTableWidgetItem(ap['bssid']))
            self.setItem(row_idx, 2, QTableWidgetItem(str(ap['channel'])))
            self.setItem(row_idx, 3, QTableWidgetItem(str(ap['freq'])))
            
            rssi_item = QTableWidgetItem(f"{ap['rssi']:.1f}")
            if ap['rssi'] > -50:
                rssi_item.setForeground(Qt.GlobalColor.green)
            elif ap['rssi'] < -80:
                rssi_item.setForeground(Qt.GlobalColor.red)
            else:
                rssi_item.setForeground(Qt.GlobalColor.yellow)
                
            self.setItem(row_idx, 4, rssi_item)
            self.setItem(row_idx, 5, QTableWidgetItem(ap['security']))
            self.setItem(row_idx, 6, QTableWidgetItem(ap['vendor']))
            row_idx += 1

    def refresh_theme(self) -> None:
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {config.COLOR_PLOT_BG};
                alternate-background-color: {config.COLOR_PANEL_BG};
                color: {config.COLOR_TEXT_PRIMARY};
                gridline-color: {config.COLOR_PLOT_GRID};
                border: none;
            }}
            QHeaderView {{
                background-color: {config.COLOR_PLOT_BG};
            }}
            QHeaderView::section {{
                background-color: {config.COLOR_PANEL_BG};
                color: {config.COLOR_ACCENT_CYAN};
                font-weight: bold;
                border: 1px solid {config.COLOR_PLOT_GRID};
                padding: 4px;
            }}
        """)
