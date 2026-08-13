# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/wifi_analyzer/_channel_rating.py — Channel Rating Analyzer
"""

from typing import List, Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel
import config

class ChannelRatingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        
        self._scroll = QWidget()
        self._scroll_layout = QVBoxLayout(self._scroll)
        self._scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self._scroll)
        self._layout.addWidget(scroll_area)

    def update_rating(self, results: List[Dict[str, Any]], is_5ghz: bool) -> None:
        ch_min, ch_max = (36, 165) if is_5ghz else (1, 14)
        
        # Calculate channel congestion
        channel_scores = {ch: 10.0 for ch in range(ch_min, ch_max + 1)}
        
        for ap in results:
            ch = ap['channel']
            if ch_min <= ch <= ch_max:
                # Co-channel penalty (heavy) based on RSSI
                penalty = max(0, (ap['rssi'] + 100) / 10) 
                channel_scores[ch] = max(0, channel_scores[ch] - penalty)
                
                # Adjacent channel penalty (lighter)
                if ch > ch_min: channel_scores[ch-1] = max(0, channel_scores[ch-1] - penalty*0.5)
                if ch < ch_max: channel_scores[ch+1] = max(0, channel_scores[ch+1] - penalty*0.5)

        # Clear layout
        while self._scroll_layout.count():
            item = self._scroll_layout.takeAt(0)
            if item is not None:
                w = item.widget()
                if w is not None:
                    w.deleteLater()
            
        title_text = "5 GHz Channel Ratings" if is_5ghz else "2.4 GHz Channel Ratings"
        title = QLabel(title_text)
        title.setStyleSheet(f"color: {config.COLOR_ACCENT_CYAN}; font-weight: bold; font-size: 16px;")
        self._scroll_layout.addWidget(title)
        
        best_ch = max(channel_scores, key=lambda k: channel_scores[k])
        
        # For 5GHz, limit to common non-DFS channels to avoid excessive scrolling
        display_channels = [36, 40, 44, 48, 149, 153, 157, 161, 165] if is_5ghz else range(1, 14)
        
        for ch in display_channels:
            score = channel_scores[ch]
            stars = round((score / 10.0) * 10)
            star_str = "★" * stars + "☆" * (10 - stars)
            
            color = config.COLOR_ACCENT_GREEN if stars >= 7 else (config.COLOR_ACCENT_ORANGE if stars >= 4 else config.COLOR_ACCENT_RED)
            
            lbl = QLabel(f"CH {ch:03d} | <span style='color: {color};'>{star_str}</span> ({score:.1f}/10)")
            lbl.setStyleSheet(f"color: {config.COLOR_TEXT_PRIMARY}; font-size: 14px; font-family: monospace;")
            if ch == best_ch:
                lbl.setText(lbl.text() + f" &nbsp; <span style='color: {config.COLOR_ACCENT_CYAN}; font-weight: bold;'>[RECOMMENDED]</span>")
            self._scroll_layout.addWidget(lbl)
