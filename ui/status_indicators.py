# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/status_indicators.py — Diagnostics Status Panel
QLabel-based indicators for DSP status, threat level, throughput, and COM info.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
)

import config
from core.threat import ThreatLevel


class StatusIndicators(QWidget):
    """
    Compact status readout widget for the right diagnostics panel.
    Displays: DSP status, Deauth threat level, Throughput KB/s, COM port info,
    recon stats, and packet counters.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        # Section header
        hdr = QLabel("◈  SYSTEM DIAGNOSTICS")
        hdr.setObjectName("section_header")
        layout.addWidget(hdr)

        # Grid of key→value rows
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 1)

        row = 0

        def add_row(label: str, obj_name: str = "status_value") -> QLabel:
            nonlocal row
            k = QLabel(label)
            k.setObjectName("status_key")
            k.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            v = QLabel("--")
            v.setObjectName(obj_name)
            v.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            grid.addWidget(k, row, 0)
            grid.addWidget(v, row, 1)
            row += 1
            return v

        self._lbl_target       = add_row("ACTIVE TARGET")
        self._lbl_dsp_status   = add_row("DSP ENGINE")
        self._lbl_ma_window    = add_row("MA WINDOW")
        self._lbl_deauth       = add_row("DEAUTH STATUS")
        self._lbl_deauth_rate  = add_row("DEAUTH RATE")
        self._lbl_total_dauth  = add_row("TOTAL DEAUTHS")

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{config.COLOR_BORDER};")
        grid.addWidget(sep, row, 0, 1, 2)
        row += 1

        self._lbl_load         = add_row("THROUGHPUT")
        self._lbl_packets      = add_row("PACKETS RX")
        self._lbl_pps          = add_row("PKT / SEC")

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color:{config.COLOR_BORDER};")
        grid.addWidget(sep2, row, 0, 1, 2)
        row += 1

        self._lbl_ap_count     = add_row("APs SEEN")
        self._lbl_rogue_count  = add_row("ROGUE APs")
        self._lbl_hidden_count = add_row("HIDDEN NETS")

        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet(f"color:{config.COLOR_BORDER};")
        grid.addWidget(sep3, row, 0, 1, 2)
        row += 1

        self._lbl_port         = add_row("PORT")
        self._lbl_baud         = add_row("BAUD")
        self._lbl_connection   = add_row("LINK")

        layout.addLayout(grid)
        layout.addStretch()

        # Large deauth threat badge at bottom
        self._badge = _ThreatBadge()
        layout.addWidget(self._badge)

    # ─── Update API ────────────────────────────────────────────────────────────

    def set_target(self, target: str) -> None:
        self._lbl_target.setText(target or "--")
        if target and target != "--":
            self._lbl_target.setObjectName("status_value_alert")
        else:
            self._lbl_target.setObjectName("status_value_dim")
        self._lbl_target.setStyleSheet("")

    def set_dsp_active(self, active: bool, ma_window: int = config.MA_WINDOW) -> None:
        if active:
            self._lbl_dsp_status.setText("ACTIVE")
            self._lbl_dsp_status.setObjectName("status_value")
        else:
            self._lbl_dsp_status.setText("IDLE")
            self._lbl_dsp_status.setObjectName("status_value_dim")
        self._lbl_dsp_status.setStyleSheet("")          # force QSS refresh
        self._lbl_ma_window.setText(f"{ma_window} smp")

    def set_threat(self, level: ThreatLevel, rate: float, total: int) -> None:
        rate_str  = f"{rate:.1f} /s"
        total_str = str(total)

        self._lbl_deauth_rate.setText(rate_str)
        self._lbl_total_dauth.setText(total_str)

        if level == ThreatLevel.ALERT:
            self._lbl_deauth.setText("⚠ ALERT")
            self._lbl_deauth.setObjectName("status_value_alert")
        elif level == ThreatLevel.WARNING:
            self._lbl_deauth.setText("⚡ WARNING")
            self._lbl_deauth.setObjectName("status_value_warn")
        else:
            self._lbl_deauth.setText("✔ SECURE")
            self._lbl_deauth.setObjectName("status_value")

        self._lbl_deauth.setStyleSheet("")
        self._badge.set_level(level)

    def set_throughput(self, kbs: float) -> None:
        self._lbl_load.setText(f"{kbs:.2f} KB/s")

    def set_packet_stats(self, total: int, pps: float) -> None:
        self._lbl_packets.setText(f"{total:,}")
        self._lbl_pps.setText(f"{pps:.0f}")

    def set_recon_stats(self, ap_count: int, rogue: int, hidden: int) -> None:
        self._lbl_ap_count.setText(str(ap_count))
        self._lbl_rogue_count.setText(str(rogue))
        if rogue > 0:
            self._lbl_rogue_count.setObjectName("status_value_alert")
        else:
            self._lbl_rogue_count.setObjectName("status_value")
        self._lbl_rogue_count.setStyleSheet("")

        self._lbl_hidden_count.setText(str(hidden))
        if hidden > 0:
            self._lbl_hidden_count.setObjectName("status_value_warn")
        else:
            self._lbl_hidden_count.setObjectName("status_value")
        self._lbl_hidden_count.setStyleSheet("")

    def set_connection(self, port: str, baud: int, connected: bool) -> None:
        self._lbl_port.setText(port or "--")
        self._lbl_baud.setText(f"{baud:,}")
        if connected:
            self._lbl_connection.setText("● ONLINE")
            self._lbl_connection.setObjectName("status_value")
        else:
            self._lbl_connection.setText("○ OFFLINE")
            self._lbl_connection.setObjectName("status_value_dim")
        self._lbl_connection.setStyleSheet("")


class _ThreatBadge(QWidget):
    """Large colour-coded threat level badge."""

    _STYLES = {
        ThreatLevel.SECURE:  (config.COLOR_ACCENT_GREEN,  "■  SECURE"),
        ThreatLevel.WARNING: (config.COLOR_ACCENT_ORANGE, "▲  WARNING"),
        ThreatLevel.ALERT:   (config.COLOR_ACCENT_RED,    "● DEAUTH ALERT"),
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)

        self._lbl = QLabel("■  SECURE")
        self._lbl.setObjectName("big_status")
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._lbl)
        self.set_level(ThreatLevel.SECURE)

    def set_level(self, level: ThreatLevel) -> None:
        color, text = self._STYLES[level]
        self._lbl.setText(text)
        self._lbl.setStyleSheet(
            f"font-size:13px; font-weight:bold; letter-spacing:2px;"
            f" color:{config.COLOR_BG}; background-color:{color};"
            f" padding:6px 12px; border-radius:4px;"
        )
