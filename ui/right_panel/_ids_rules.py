# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/right_panel/_ids_rules.py — IDS Rules View
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
import config

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

    def refresh_theme(self) -> None:
        """Refresh inline styles after a theme change."""
        self._table.setStyleSheet(f"""
            background-color: {config.COLOR_BG};
            color: {config.COLOR_TEXT_PRIMARY};
            gridline-color: {config.COLOR_BORDER};
        """)
