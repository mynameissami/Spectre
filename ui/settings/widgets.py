# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/settings/widgets.py — Reusable Settings UI Primitives

Provides small, composable widget helpers used across the settings tabs.
Keeping them here avoids repetition and makes each tab's code clean.
"""

from __future__ import annotations

import config
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSlider,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QListView,
)


class ComboBox(QComboBox):
    """
    A globally styled QComboBox that replaces the native OS popup view
    with a QListView to ensure stylesheets (like borders/margins) apply
    perfectly across all platforms without native artifacting (e.g., white strips).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setView(QListView())
        
        # The user specifically requested the visual style of the Target BSSID dropdown.
        # Setting editable=True forces Qt to use a different rendering path for both the
        # button and the popup container, completely bypassing the native OS menu borders
        # (which cause the white strips). We make the line edit read-only to preserve
        # standard dropdown behavior.
        self.setEditable(True)
        le = self.lineEdit()
        if le is not None:
            le.setReadOnly(True)
            le.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            le.setCursor(Qt.CursorShape.ArrowCursor)


class LabelledSlider(QWidget):
    """
    A horizontal slider with a live-updating value label.

    Emits valueChanged(int) when the slider moves.
    """

    valueChanged = Signal(int)

    def __init__(
        self,
        label: str,
        minimum: int,
        maximum: int,
        value: int,
        suffix: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._suffix = suffix

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel(label)
        lbl.setFixedWidth(160)
        lbl.setStyleSheet(f"color: {config.COLOR_TEXT_DIM}; font-size: 13px;")

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setMinimum(minimum)
        self._slider.setMaximum(maximum)
        self._slider.setValue(value)
        self._slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: none;
                height: 4px;
                background: {config.COLOR_PLOT_GRID};
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {config.COLOR_ACCENT_CYAN};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {config.COLOR_ACCENT_CYAN};
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {config.COLOR_TEXT_PRIMARY};
            }}
        """)

        self._value_label = QLabel(f"{value}{suffix}")
        self._value_label.setFixedWidth(50)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._value_label.setStyleSheet(
            f"color: {config.COLOR_ACCENT_CYAN}; font-weight: bold; font-size: 13px;"
        )

        self._slider.valueChanged.connect(self._on_value_changed)

        layout.addWidget(lbl)
        layout.addWidget(self._slider, stretch=1)
        layout.addWidget(self._value_label)

    def _on_value_changed(self, v: int) -> None:
        self._value_label.setText(f"{v}{self._suffix}")
        self.valueChanged.emit(v)

    def value(self) -> int:
        return self._slider.value()

    def setValue(self, v: int) -> None:
        self._slider.setValue(v)

    def refresh_theme(self) -> None:
        self._slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: none;
                height: 4px;
                background: {config.COLOR_PLOT_GRID};
                border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {config.COLOR_ACCENT_CYAN};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {config.COLOR_ACCENT_CYAN};
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {config.COLOR_TEXT_PRIMARY};
            }}
        """)
        self._value_label.setStyleSheet(
            f"color: {config.COLOR_ACCENT_CYAN}; font-weight: bold; font-size: 13px;"
        )


def make_group(title: str) -> tuple[QWidget, QVBoxLayout]:
    """Create a flat section container (replaces QGroupBox) and return the container and inner layout."""
    container = QWidget()
    root_layout = QVBoxLayout(container)
    root_layout.setContentsMargins(0, 16, 0, 24)
    root_layout.setSpacing(16)

    # Flat title header
    hdr = QLabel(title)
    hdr.setStyleSheet(f"""
        color: {config.COLOR_ACCENT_CYAN};
        font-weight: bold;
        font-size: 16px;
        letter-spacing: 1px;
    """)
    root_layout.addWidget(hdr)

    # Inner layout for actual contents
    content_widget = QWidget()
    inner_layout = QVBoxLayout(content_widget)
    inner_layout.setContentsMargins(0, 0, 0, 0)
    inner_layout.setSpacing(8)
    
    root_layout.addWidget(content_widget)

    return container, inner_layout
