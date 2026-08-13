# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/settings/appearance_tab.py — Appearance Settings Tab

Handles:
    - Theme selection (radio-button grid)
    - Per-widget font size sliders (global, menu, labels,
      buttons, event log, tables, plot axes)

All changes are applied live to a staging copy of the settings,
then committed on "Apply" or "OK" in the parent dialog.
"""

from __future__ import annotations

import config
from core.settings_manager import AppSettings, FontSettings
from core.theme_manager import THEMES
from ui.settings.widgets import LabelledSlider, make_group

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)


class AppearanceTab(QWidget):
    """
    Tab widget for appearance settings.

    Emits `preview_requested(theme_name)` when the user selects a
    different theme radio button (for live preview if wired up).
    """

    preview_requested = Signal(str)
    font_preview_requested = Signal(FontSettings)

    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings

        # ── Scroll container for full content ──────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(24)
        content_layout.setContentsMargins(12, 12, 12, 24)

        content_layout.addWidget(self._build_theme_group())
        content_layout.addSpacing(32)
        content_layout.addWidget(self._build_font_group())
        content_layout.addStretch()

        scroll.setWidget(content)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

    # ── Theme Selection ────────────────────────────────────────────────────

    def _build_theme_group(self) -> QWidget:
        group, layout = make_group("Visual Theme")

        self._theme_desc = QLabel("Select a colour scheme. The change is previewed instantly and saved when you click Apply or OK.")
        self._theme_desc.setWordWrap(True)
        self._theme_desc.setStyleSheet(f"color: {config.COLOR_TEXT_DIM}; font-size: 12px;")
        layout.addWidget(self._theme_desc)

        layout_cards = QHBoxLayout()
        layout_cards.setSpacing(16)
        self._theme_group = QButtonGroup(self)

        for theme_key, palette in THEMES.items():
            btn = QPushButton(palette.display_name)
            btn.setCheckable(True)
            btn.setProperty("theme_key", theme_key)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    color: {config.COLOR_TEXT_PRIMARY};
                    background-color: {config.COLOR_PANEL_BG};
                    font-size: 14px;
                    font-weight: bold;
                    padding: 16px 24px;
                    border: 2px solid {config.COLOR_BORDER};
                    border-radius: 6px;
                }}
                QPushButton:checked {{
                    border-color: {palette.accent_primary};
                    color: {palette.accent_primary};
                    background-color: {palette.bg};
                }}
                QPushButton:hover:!checked {{
                    border-color: {config.COLOR_TEXT_DIM};
                    background-color: {palette.bg};
                }}
            """)
            if theme_key == self._settings.theme:
                btn.setChecked(True)
            self._theme_group.addButton(btn)
            layout_cards.addWidget(btn)

        layout_cards.addStretch()

        self._theme_group.buttonClicked.connect(
            lambda btn: self.preview_requested.emit(btn.property("theme_key"))
        )
        layout.addLayout(layout_cards)
        return group

    # ── Font Size Controls ─────────────────────────────────────────────────

    def _build_font_group(self) -> QWidget:
        group, layout = make_group("Font Sizes")

        self._font_desc = QLabel(
            "Adjust font sizes for individual UI regions. "
            "Changes apply immediately when you click Apply."
        )
        self._font_desc.setWordWrap(True)
        self._font_desc.setStyleSheet(f"color: {config.COLOR_TEXT_DIM}; font-size: 12px;")
        layout.addWidget(self._font_desc)

        f = self._settings.font
        self._font_sliders: dict[str, LabelledSlider] = {}

        font_fields = [
            ("global_ui",  "Global UI",        f.global_ui,  8, 20, "px"),
            ("menu_bar",   "Menu Bar",          f.menu_bar,   8, 18, "px"),
            ("labels",     "Labels & Headers",  f.labels,     8, 18, "px"),
            ("buttons",    "Buttons",           f.buttons,    8, 18, "px"),
            ("event_log",  "Event Log",         f.event_log,  7, 18, "px"),
            ("tables",     "Tables & Lists",    f.tables,     7, 18, "px"),
            ("plots",      "Plot Axis Labels",  f.plots,      7, 16, "px"),
        ]

        for key, label, value, mn, mx, suffix in font_fields:
            slider = LabelledSlider(label, mn, mx, value, suffix)
            self._font_sliders[key] = slider
            slider.valueChanged.connect(self._emit_font_preview)
            layout.addWidget(slider)

        return group

    def _emit_font_preview(self) -> None:
        font = FontSettings(
            **{k: s.value() for k, s in self._font_sliders.items()}
        )
        self.font_preview_requested.emit(font)

    # ── Public API ─────────────────────────────────────────────────────────

    def collect(self) -> AppSettings:
        """Return an AppSettings reflecting the current UI state."""
        checked = self._theme_group.checkedButton()
        theme = checked.property("theme_key") if checked else self._settings.theme

        font = FontSettings(
            **{key: slider.value() for key, slider in self._font_sliders.items()}
        )
        import copy
        result = copy.deepcopy(self._settings)
        result.theme = theme
        result.font = font
        return result

    def refresh_theme(self) -> None:
        """Refresh inline styles after a theme change."""
        self._theme_desc.setStyleSheet(f"color: {config.COLOR_TEXT_DIM}; font-size: 12px;")
        self._font_desc.setStyleSheet(f"color: {config.COLOR_TEXT_DIM}; font-size: 12px;")
        for slider in self._font_sliders.values():
            if hasattr(slider, "refresh_theme"):
                slider.refresh_theme()
