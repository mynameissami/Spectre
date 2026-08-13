# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/wifi_analyzer/_color.py — Stable color assignment for BSSIDs
"""

class BSSIDColorRegistry:
    def __init__(self):
        self._bssid_colors = {}
        self._color_counter = 0

    def get_color(self, bssid: str) -> str:
        """Return a stable, unique color for the given BSSID."""
        if bssid not in self._bssid_colors:
            # Golden angle in degrees for maximum hue separation
            golden_ratio = 0.6180339887
            hue = (self._color_counter * golden_ratio * 360.0) % 360.0
            # High saturation & medium-high lightness for vibrancy on dark bg
            sat = 85
            light = 60
            # Convert HSL to hex
            h = hue / 360.0
            s = sat / 100.0
            l = light / 100.0
            if s == 0:
                r = g = b = l
            else:
                def hue2rgb(p: float, q: float, t: float) -> float:
                    if t < 0: t += 1
                    if t > 1: t -= 1
                    if t < 1/6: return p + (q - p) * 6 * t
                    if t < 1/2: return q
                    if t < 2/3: return p + (q - p) * (2/3 - t) * 6
                    return p
                q = l * (1 + s) if l < 0.5 else l + s - l * s
                p = 2 * l - q
                r = hue2rgb(p, q, h + 1/3)
                g = hue2rgb(p, q, h)
                b = hue2rgb(p, q, h - 1/3)
            self._bssid_colors[bssid] = "#{:02X}{:02X}{:02X}".format(
                int(r * 255), int(g * 255), int(b * 255)
            )
            self._color_counter += 1
        return self._bssid_colors[bssid]
