# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/right_panel.py — Diagnostics & Telemetry Management Grid
Contains:
  - System Status Dashboard (Connection, DSP, Threat, Recon, Target)
  - Live Event Log
  - Attack Timeline & Correlation View
  - IDS Rules Engine Status
  - Reconnaissance Summary
"""

import time
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QTabWidget,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QScrollArea,
)
from PySide6.QtCore import Qt
import config
from core.threat import ThreatLevel


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

    # ─── API Methods Called by main_window.py ──────────────────────────
    def set_connection(self, port: str, baud: int, connected: bool) -> None:
        state = "ONLINE" if connected else "OFFLINE"
        color = config.COLOR_ACCENT_GREEN if connected else config.COLOR_ACCENT_RED
        self.set(
            "connection",
            f'<span style="color:{color}">{port} @ {baud} [{state}]</span>',
        )

    def set_dsp_active(self, active: bool, window: int = 0) -> None:
        state = "ACTIVE" if active else "IDLE"
        color = config.COLOR_ACCENT_GREEN if active else config.COLOR_TEXT_DIM
        self.set("dsp", f'<span style="color:{color}">{state} (MA:{window})</span>')

    def set_threat(self, level: ThreatLevel, rate: float, total: int) -> None:
        colors = {
            ThreatLevel.SECURE: config.COLOR_ACCENT_GREEN,
            ThreatLevel.WARNING: config.COLOR_ACCENT_ORANGE,
            ThreatLevel.ALERT: config.COLOR_ACCENT_RED,
        }
        color = colors.get(level, config.COLOR_TEXT_PRIMARY)
        self.set(
            "threat",
            f'<span style="color:{color}">{level.name} ({rate:.1f}/s | {total})</span>',
        )

    def set_throughput(self, kbs: float) -> None:
        self.set("throughput", f"{kbs:.2f} KB/s")

    def set_packet_stats(self, total: int, pps: int) -> None:
        self.set("pps", f"{pps} pps (Total: {total})")

    def set_recon_stats(self, aps: int, rogues: int, hidden: int) -> None:
        self.set("recon", f"APs:{aps} | 🚨{rogues} | ⚠{hidden}")

    def set_target(self, target_str: str) -> None:
        self.set("target", target_str if target_str else "--")


class EventLog(QWidget):
    """Asynchronous terminal logging interface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._log.setStyleSheet(f"""
            background-color: {config.COLOR_BG};
            color: {config.COLOR_TEXT_PRIMARY};
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 10pt;
        """)
        layout.addWidget(self._log)

    def log(self, message: str, level: str = "INFO") -> None:
        colors = {
            "INFO": config.COLOR_ACCENT_CYAN,
            "WARN": config.COLOR_ACCENT_ORANGE,
            "ALERT": config.COLOR_ACCENT_RED,
            "OK": config.COLOR_ACCENT_GREEN,
            "EXEC": "#FF00FF",
            "DEBUG": config.COLOR_TEXT_DIM,
        }
        color = colors.get(level, config.COLOR_TEXT_PRIMARY)
        timestamp = time.strftime("%H:%M:%S.%f")[:-3]

        line = (
            f'<span style="color:{config.COLOR_TEXT_DIM};">[{timestamp}]</span> '
            f'<span style="color:{color}; font-weight:bold;">[{level:5s}]</span> '
            f'<span style="color:{config.COLOR_TEXT_PRIMARY};">{message}</span>'
        )
        self._log.append(line)
        sb = self._log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear(self) -> None:
        """Clear all log entries."""
        self._log.clear()


class TimelineWidget(QWidget):
    """Visual attack timeline with state correlation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._timeline = QTextEdit()
        self._timeline.setReadOnly(True)
        self._timeline.setStyleSheet(f"""
            background-color: {config.COLOR_BG};
            color: {config.COLOR_TEXT_PRIMARY};
            font-family: 'Consolas', monospace;
            font-size: 10pt;
        """)
        layout.addWidget(self._timeline)

    def add_event(self, event_type: str, message: str) -> None:
        colors = {
            "ALERT": config.COLOR_ACCENT_RED,
            "RECON": config.COLOR_ACCENT_ORANGE,
            "INFO": config.COLOR_ACCENT_CYAN,
        }
        color = colors.get(event_type, config.COLOR_TEXT_PRIMARY)
        timestamp = time.strftime("%H:%M:%S")

        html = (
            f'<span style="color:{config.COLOR_TEXT_DIM}">[{timestamp}]</span> '
            f'<span style="color:{color}; font-weight:bold">[{event_type}]</span> '
            f'<span style="color:{config.COLOR_TEXT_PRIMARY}">{message}</span><br>'
        )
        self._timeline.insertHtml(html)
        self._timeline.verticalScrollBar().setValue(
            self._timeline.verticalScrollBar().maximum()
        )


class IDSRulesWidget(QWidget):
    """Table view of active IDS detection rules."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(
            ["RULE ID", "SEVERITY", "THRESHOLD", "STATUS"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.setStyleSheet(f"""
            background-color: {config.COLOR_BG};
            color: {config.COLOR_TEXT_PRIMARY};
            gridline-color: {config.COLOR_BORDER};
        """)
        layout.addWidget(self._table)

    def update_rules(self, rules: list[dict]) -> None:
        self._table.setRowCount(len(rules))
        for row, rule in enumerate(rules):
            self._table.setItem(row, 0, QTableWidgetItem(rule["id"]))
            self._table.setItem(row, 1, QTableWidgetItem(rule["severity"]))
            
            # Show live rate / threshold
            rate_item = QTableWidgetItem(f"{rule.get('current_rate', 0.0):.1f} / {rule['threshold']}/s")
            self._table.setItem(row, 2, rate_item)
            
            if not rule["enabled"]:
                status = "DISABLED"
                color = Qt.GlobalColor.darkGray
            elif rule.get("is_triggered", False):
                status = "🚨 TRIGGERED"
                color = Qt.GlobalColor.red
            else:
                status = "MONITORING"
                color = Qt.GlobalColor.green
                
            item = QTableWidgetItem(status)
            item.setForeground(color)
            self._table.setItem(row, 3, item)


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

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{config.COLOR_BORDER};")
        layout.addWidget(sep)

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

        layout.addWidget(self._tabs, stretch=1)

    # ─── Public API (Matches main_window.py expectations) ────────────────

    def set_connection(self, port: str, baud: int, connected: bool) -> None:
        state = "ONLINE" if connected else "OFFLINE"
        color = config.COLOR_ACCENT_GREEN if connected else config.COLOR_ACCENT_RED
        self.status.set(
            "connection",
            f'<span style="color:{color}">{port} @ {baud} [{state}]</span>',
        )

    def set_dsp_active(self, active: bool, window: int = 0) -> None:
        state = "ACTIVE" if active else "IDLE"
        color = config.COLOR_ACCENT_GREEN if active else config.COLOR_TEXT_DIM
        self.status.set(
            "dsp", f'<span style="color:{color}">{state} (MA:{window})</span>'
        )

    def set_threat(self, level: ThreatLevel, rate: float, total: int) -> None:
        colors = {
            ThreatLevel.SECURE: config.COLOR_ACCENT_GREEN,
            ThreatLevel.WARNING: config.COLOR_ACCENT_ORANGE,
            ThreatLevel.ALERT: config.COLOR_ACCENT_RED,
        }
        color = colors.get(level, config.COLOR_TEXT_PRIMARY)
        self.status.set(
            "threat",
            f'<span style="color:{color}">{level.name} ({rate:.1f}/s | {total})</span>',
        )

    def set_throughput(self, kbs: float) -> None:
        self.status.set("throughput", f"{kbs:.2f} KB/s")

    def set_packet_stats(self, total: int, pps: int) -> None:
        self.status.set("pps", f"{pps} pps (Total: {total})")

    def set_recon_stats(self, aps: int, rogues: int, hidden: int) -> None:
        self.status.set("recon", f"APs:{aps} | 🚨{rogues} | ⚠{hidden}")
        self._recon_summary.setHtml(f"""
        <span style="color:{config.COLOR_ACCENT_CYAN}">KNOWN APs:</span> {aps}<br>
        <span style="color:{config.COLOR_ACCENT_RED}">ROGUE/HONEYPOT:</span> {rogues}<br>
        <span style="color:{config.COLOR_ACCENT_ORANGE}">HIDDEN NETWORKS:</span> {hidden}<br>
        <span style="color:{config.COLOR_TEXT_DIM}">Last Update:</span> {time.strftime("%H:%M:%S")}
        """)

    def set_target(self, target_str: str) -> None:
        self.status.set("target", target_str if target_str else "--")
