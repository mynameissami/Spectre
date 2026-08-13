# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/right_panel/_status.py — Status Grid Dashboard
"""

from PySide6.QtWidgets import QWidget, QGridLayout, QLabel
import config
from core.analytics.threat import ThreatLevel

class StatusPanel(QWidget):
    """Compact status indicator grid for the right panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._labels = {}
        keys = ["connection", "dsp", "threat", "throughput", "pps", "recon", "target"]
        for i, key in enumerate(keys):
            lbl_key = QLabel(f"{key.upper()}:")
            lbl_key.setObjectName("status_key")
            lbl_val = QLabel("--")
            lbl_val.setObjectName("status_value")
            layout.addWidget(lbl_key, i, 0)
            layout.addWidget(lbl_val, i, 1)
            self._labels[key] = lbl_val

    def set(self, key: str, value: str) -> None:
        if key in self._labels:
            self._labels[key].setText(value)

    def set_connection(self, port: str, baud: int, is_connected: bool) -> None:
        if is_connected:
            self.set("connection", f"<span style='color: {config.COLOR_ACCENT_GREEN};'>{port} @ {baud} bps</span>")
        else:
            self.set("connection", f"<span style='color: {config.COLOR_TEXT_DIM};'>DISCONNECTED</span>")

    def set_dsp_active(self, is_active: bool, ma_window: int = 15) -> None:
        if is_active:
            self.set("dsp", f"<span style='color: {config.COLOR_ACCENT_CYAN};'>ACTIVE (MA={ma_window})</span>")
        else:
            self.set("dsp", f"<span style='color: {config.COLOR_TEXT_DIM};'>INACTIVE</span>")

    def set_threat(self, level: ThreatLevel, score: float, count: int) -> None:
        color = config.COLOR_ACCENT_GREEN
        if level == ThreatLevel.WARNING:
            color = config.COLOR_ACCENT_ORANGE
        elif level == ThreatLevel.ALERT:
            color = config.COLOR_ACCENT_RED
        self.set("threat", f"<span style='color: {color};'>{level.name} ({count}) [Risk: {score:.1f}]</span>")

    def set_target(self, target: str) -> None:
        if target and target != "--":
            self.set("target", f"<span style='color: {config.COLOR_ACCENT_RED};'>{target}</span>")
        else:
            self.set("target", f"<span style='color: {config.COLOR_TEXT_DIM};'>--</span>")

    def set_throughput(self, kbps: float) -> None:
        self.set("throughput", f"{kbps:.1f} KB/s")

    def set_packet_stats(self, total: int, recent: int) -> None:
        self.set("pps", f"{recent} PPS | Total: {total}")

    def set_recon_stats(self, devices: int, new_devices: int) -> None:
        self.set("recon", f"{devices} nodes (+{new_devices})")
