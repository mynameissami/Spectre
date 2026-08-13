# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/wifi_analyzer/_time_graph.py — Rolling RSSI History Graph
"""

import pyqtgraph as pg
from typing import List, Dict, Any
import config

class TimeGraphWidget(pg.PlotWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMenuEnabled(False)
        self.setBackground(config.COLOR_PLOT_BG)
        self.setTitle("Rolling Signal Strength History", color=config.COLOR_ACCENT_CYAN)
        self.setLabel('bottom', 'Time (s)')
        self.setLabel('left', 'RSSI (dBm)')
        self.setYRange(-95, -20)
        self.showGrid(x=True, y=True, alpha=0.3)
        
        self._time_data: Dict[str, list] = {}
        self._time_x = 0

    def reset_data(self) -> None:
        self._time_data.clear()
        self.clear()

    def update_graph(self, results: List[Dict[str, Any]], mesh_roaming: bool, 
                    mesh_target: str, color_registry) -> None:
        self._time_x += 1
        
        # Deduplicate results by BSSID
        unique_aps = {}
        for ap in results:
            bssid = ap['bssid']
            if bssid not in unique_aps or ap['rssi'] > unique_aps[bssid]['rssi']:
                unique_aps[bssid] = ap
        
        active_bssids = set(unique_aps.keys())
        
        # Age out old networks
        stale_bssids = []
        for bssid in list(self._time_data.keys()):
            if bssid not in active_bssids:
                self._time_data[bssid].append((self._time_x, -100.0))
                if len(self._time_data[bssid]) >= 10 and all(d[1] == -100.0 for d in self._time_data[bssid][-10:]):
                    stale_bssids.append(bssid)
        
        for bssid in stale_bssids:
            del self._time_data[bssid]
        
        # Update with new data
        for bssid, ap in unique_aps.items():
            if bssid not in self._time_data:
                self._time_data[bssid] = []
            self._time_data[bssid].append((self._time_x, ap['rssi']))
            
        # Global truncate
        for bssid in self._time_data:
            if len(self._time_data[bssid]) > 60:
                self._time_data[bssid] = self._time_data[bssid][-60:]

        self.clear()
        
        for bssid, data in self._time_data.items():
            if not data or data[-1][1] == -100.0: 
                continue
                
            if mesh_roaming:
                ssid = ""
                for ap in results:
                    if ap['bssid'] == bssid:
                        ssid = ap['ssid']
                        break
                if ssid != mesh_target:
                    continue
            
            x = [d[0] for d in data]
            y = [d[1] for d in data]
            color = color_registry.get_color(bssid)
            pen = pg.mkPen(color, width=2)
            self.plot(x, y, pen=pen, name=bssid)

    def refresh_theme(self) -> None:
        self.setBackground(config.COLOR_PLOT_BG)
        self.setTitle("Rolling Signal Strength History", color=config.COLOR_ACCENT_CYAN)
