# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/settings/about_tab.py — About Tab

Displays application info, version, license, and contributor info.
"""

from __future__ import annotations

import config
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)


class AboutTab(QWidget):
    """Informational tab showing app version, license, and links."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._title = QLabel(config.APP_NAME)
        self._title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {config.COLOR_ACCENT_GREEN};"
            " letter-spacing: 3px;"
        )
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._version = QLabel(config.APP_VERSION)
        self._version.setStyleSheet(
            f"font-size: 12px; color: {config.COLOR_TEXT_DIM}; letter-spacing: 2px;"
        )
        self._version.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._desc = QLabel(
            "Signal Processing & Electronic Cyber Security Reconnaissance Engine\n\n"
            "A real-time telemetry processing, spectrum visualization, and wireless "
            "diagnostics platform featuring an ESP32 hardware edge sensor node."
        )
        self._desc.setWordWrap(True)
        self._desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._desc.setStyleSheet(f"color: {config.COLOR_TEXT_PRIMARY}; font-size: 11px;")

        self._license_lbl = QLabel(
            "Licensed under the GNU Affero General Public License v3.0 (AGPL-3.0)"
        )
        self._license_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._license_lbl.setStyleSheet(
            f"color: {config.COLOR_ACCENT_CYAN}; font-size: 12px;"
        )

        self._copyright_lbl = QLabel("Copyright © 2026 M. Sami Furqan. All rights reserved.")
        self._copyright_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._copyright_lbl.setStyleSheet(
            f"color: {config.COLOR_TEXT_DIM}; font-size: 12px;"
        )

        self._disclaimer = QLabel(
            "DISCLAIMER: This software is for educational purposes and authorized network "
            "security auditing only. The authors accept no liability for misuse."
        )
        self._disclaimer.setWordWrap(True)
        self._disclaimer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._disclaimer.setStyleSheet(
            f"color: {config.COLOR_ACCENT_ORANGE}; font-size: 12px;"
        )

        for widget in [self._title, self._version, self._desc, self._license_lbl, self._copyright_lbl, self._disclaimer]:
            layout.addWidget(widget)
        layout.addStretch()

    def refresh_theme(self) -> None:
        """Refresh inline styles after a theme change."""
        self._title.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {config.COLOR_ACCENT_GREEN};"
            " letter-spacing: 3px;"
        )
        self._version.setStyleSheet(
            f"font-size: 12px; color: {config.COLOR_TEXT_DIM}; letter-spacing: 2px;"
        )
        self._desc.setStyleSheet(f"color: {config.COLOR_TEXT_PRIMARY}; font-size: 11px;")
        self._license_lbl.setStyleSheet(
            f"color: {config.COLOR_ACCENT_CYAN}; font-size: 12px;"
        )
        self._copyright_lbl.setStyleSheet(
            f"color: {config.COLOR_TEXT_DIM}; font-size: 12px;"
        )
        self._disclaimer.setStyleSheet(
            f"color: {config.COLOR_ACCENT_ORANGE}; font-size: 12px;"
        )
