# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/right_panel/_panel.py — Diagnostics Control Node & Telemetry Management Grid
"""

import time
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFrame,
    QTabWidget,
    QTextEdit,
)
import config
from core.analytics.threat import ThreatLevel

from ui.right_panel._status import StatusPanel
from ui.right_panel._event_log import EventLog
from ui.right_panel._timeline import TimelineWidget
from ui.right_panel._ids_rules import IDSRulesWidget

class RightPanel(QWidget):
    """Diagnostics Control Node & Telemetry Management Grid."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── Status Dashboard ────────────────────────────────────────────
        self.status = StatusPanel()
        layout.addWidget(self.status)

        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.Shape.HLine)
        self._sep.setStyleSheet(f"color:{config.COLOR_BORDER};")
        layout.addWidget(self._sep)

        # ── Tabbed Analytics & Logs ─────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setMovable(True)
        self._tabs.setStyleSheet(
            f"QTabWidget::pane {{ border: 1px solid {config.COLOR_BORDER}; background: {config.COLOR_BG}; }}"
        )

        # Tab 1: Live Log
        self.log = EventLog()
        self._tabs.addTab(self.log, "LIVE TELEMETRY LOG")

        # Tab 2: Attack Timeline
        self.timeline = TimelineWidget()
        self._tabs.addTab(self.timeline, "ATTACK TIMELINE")

        # Tab 3: IDS Rules
        self.ids_rules = IDSRulesWidget()
        self._tabs.addTab(self.ids_rules, "IDS RULES ENGINE")

        # Tab 4: Recon Summary
        self._recon_summary = QTextEdit()
        self._recon_summary.setReadOnly(True)
        self._recon_summary.setStyleSheet(f"""
            background-color: {config.COLOR_BG};
            color: {config.COLOR_TEXT_PRIMARY};
            font-family: monospace;
        """)
        self._tabs.addTab(self._recon_summary, "RECON SUMMARY")
        
        # Hide IDS Rules and Recon Summary by default to avoid clutter
        self._tabs.setTabVisible(2, False)
        self._tabs.setTabVisible(3, False)

        layout.addWidget(self._tabs, stretch=1)

    def refresh_theme(self) -> None:
        """Refresh all inline styles after a theme change."""
        self._sep.setStyleSheet(f"color:{config.COLOR_BORDER};")
        self._tabs.setStyleSheet(
            f"QTabWidget::pane {{ border: 1px solid {config.COLOR_BORDER}; background: {config.COLOR_BG}; }}"
        )
        self._recon_summary.setStyleSheet(f"""
            background-color: {config.COLOR_BG};
            color: {config.COLOR_TEXT_PRIMARY};
            font-family: monospace;
        """)
        self.log.refresh_theme()
        self.timeline.refresh_theme()
        self.ids_rules.refresh_theme()

    # ─── Public API (Matches main_window.py expectations) ────────────────

    def set_connection(self, port: str, baud: int, connected: bool) -> None:
        self.status.set_connection(port, baud, connected)

    def set_dsp_active(self, active: bool, window: int = 0) -> None:
        self.status.set_dsp_active(active, window)

    def set_threat(self, level: ThreatLevel, rate: float, total: int) -> None:
        self.status.set_threat(level, rate, total)

    def set_throughput(self, kbs: float) -> None:
        self.status.set_throughput(kbs)

    def set_packet_stats(self, total: int, pps: int) -> None:
        self.status.set_packet_stats(total, pps)

    def set_recon_stats(self, aps: int, rogues: int, hidden: int) -> None:
        self.status.set_recon_stats(aps, rogues, hidden)
        self._recon_summary.setHtml(f"""
        <span style="color:{config.COLOR_ACCENT_CYAN}">KNOWN APs:</span> {aps}<br>
        <span style="color:{config.COLOR_ACCENT_RED}">ROGUE/HONEYPOT:</span> {rogues}<br>
        <span style="color:{config.COLOR_ACCENT_ORANGE}">HIDDEN NETWORKS:</span> {hidden}<br>
        <span style="color:{config.COLOR_TEXT_DIM}">Last Update:</span> {time.strftime("%H:%M:%S")}
        """)

    def set_target(self, target_str: str) -> None:
        self.status.set_target(target_str)
