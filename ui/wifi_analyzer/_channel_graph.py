# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/wifi_analyzer/_channel_graph.py — Parabolic Channel Interference Graph
"""

import numpy as np
import pyqtgraph as pg
from typing import List, Dict, Any
import config

class ChannelGraphWidget(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMenuEnabled(False)
        self.setBackground(config.COLOR_PLOT_BG)
        self.setLabel('bottom', 'Channel')
        self.setLabel('left', 'RSSI (dBm)')
        self.setYRange(-95, -20)
        self.showGrid(x=True, y=True, alpha=0.3)
        self.set_band(is_5ghz=False)

    def set_band(self, is_5ghz: bool) -> None:
        self.setTitle(f"{'5' if is_5ghz else '2.4'} GHz Parabolic Channel Interference", color=config.COLOR_ACCENT_CYAN)
        if is_5ghz:
            self.setXRange(36, 165)
        else:
            self.setXRange(1, 14)

    def update_graph(self, results: List[Dict[str, Any]], is_5ghz: bool, 
                    mesh_roaming: bool, mesh_target: str, color_registry) -> None:
        self.clear()
        
        for ap in results:
            ch = ap['channel']
            if is_5ghz and not (36 <= ch <= 165): continue
            if not is_5ghz and not (1 <= ch <= 14): continue
            
            if mesh_roaming and ap['ssid'] != mesh_target:
                continue
            
            # Draw Parabola: y = a(x-h)^2 + k
            span = 2.0 if ap.get('width', 20) == 20 else (4.0 if ap.get('width', 20) == 40 else 8.0)
            
            x_vals = np.linspace(ch - span, ch + span, 50)
            a = (-100.0 - ap['rssi']) / (span**2)
            y_vals = a * (x_vals - ch)**2 + ap['rssi']
            
            color = color_registry.get_color(ap['bssid'])
            pen = pg.mkPen(color, width=2)
            
            fill_color = pg.QtGui.QColor(color)
            fill_color.setAlpha(40)
            brush = pg.mkBrush(fill_color)

            curve = pg.PlotCurveItem(x=x_vals, y=y_vals, pen=pen, brush=brush, fillLevel=-100)
            self.addItem(curve)
            
            text = pg.TextItem(ap['ssid'], color=color, anchor=(0.5, 1))
            text.setPos(ch, ap['rssi'])
            self.addItem(text)

    def refresh_theme(self, is_5ghz: bool) -> None:
        self.setBackground(config.COLOR_PLOT_BG)
        self.setTitle(f"{'5' if is_5ghz else '2.4'} GHz Parabolic Channel Interference", color=config.COLOR_ACCENT_CYAN)
