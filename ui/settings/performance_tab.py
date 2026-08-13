# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/settings/performance_tab.py — Performance Settings Tab

Handles:
    - Plot FPS (render timer interval)
    - PyQtGraph antialiasing toggle
    - OpenGL rendering toggle
"""

from __future__ import annotations

import copy

import config
from core.settings_manager import AppSettings
from ui.settings.widgets import LabelledSlider, make_group

from PySide6.QtWidgets import (
    QCheckBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class PerformanceTab(QWidget):
    """Tab widget for performance and rendering settings."""

    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings

        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(12, 12, 12, 24)

        layout.addWidget(self._build_render_group())
        layout.addStretch()

    def _build_render_group(self) -> QWidget:
        group, layout = make_group("Rendering & Performance")

        self._desc = QLabel(
            "Tune the render pipeline to balance visual quality and CPU usage. "
            "Reducing plot FPS significantly lowers CPU load when streaming live telemetry."
        )
        self._desc.setWordWrap(True)
        self._desc.setStyleSheet(f"color: {config.COLOR_TEXT_DIM}; font-size: 12px;")
        layout.addWidget(self._desc)

        # ── FPS Slider ────────────────────────────────────────────────────
        self._fps_slider = LabelledSlider(
            "Plot FPS Target",
            minimum=10,
            maximum=120,
            value=self._settings.plot_fps,
            suffix=" fps",
        )
        layout.addWidget(self._fps_slider)

        self._fps_note = QLabel(
            "Note: Lower FPS reduces CPU usage. 30 fps is a good balance for live data."
        )
        self._fps_note.setWordWrap(True)
        self._fps_note.setStyleSheet(f"color: {config.COLOR_ACCENT_ORANGE}; font-size: 12px;")
        layout.addWidget(self._fps_note)

        # ── Antialiasing ──────────────────────────────────────────────────
        self._antialias_check = QCheckBox("Enable Antialiasing (smoother curves)")
        self._antialias_check.setChecked(self._settings.antialiasing)
        self._antialias_check.setStyleSheet(
            f"color: {config.COLOR_TEXT_PRIMARY}; font-size: 11px; padding: 4px 0;"
        )
        layout.addWidget(self._antialias_check)

        # ── OpenGL ────────────────────────────────────────────────────────
        self._opengl_check = QCheckBox("Use OpenGL Rendering (experimental, may crash)")
        self._opengl_check.setChecked(self._settings.use_opengl)
        self._opengl_check.setStyleSheet(
            f"color: {config.COLOR_TEXT_PRIMARY}; font-size: 11px; padding: 4px 0;"
        )
        layout.addWidget(self._opengl_check)

        self._opengl_note = QLabel(
            "Warning: OpenGL is experimental and may cause instability on some systems. "
            "A restart is required for OpenGL changes to take effect."
        )
        self._opengl_note.setWordWrap(True)
        self._opengl_note.setStyleSheet(f"color: {config.COLOR_ACCENT_RED}; font-size: 12px;")
        layout.addWidget(self._opengl_note)

        return group

    def refresh_theme(self) -> None:
        """Refresh inline styles after a theme change."""
        self._desc.setStyleSheet(f"color: {config.COLOR_TEXT_DIM}; font-size: 12px;")
        self._fps_note.setStyleSheet(f"color: {config.COLOR_ACCENT_ORANGE}; font-size: 12px;")
        self._antialias_check.setStyleSheet(
            f"color: {config.COLOR_TEXT_PRIMARY}; font-size: 11px; padding: 4px 0;"
        )
        self._opengl_check.setStyleSheet(
            f"color: {config.COLOR_TEXT_PRIMARY}; font-size: 11px; padding: 4px 0;"
        )
        self._opengl_note.setStyleSheet(f"color: {config.COLOR_ACCENT_RED}; font-size: 12px;")

    # ── Public API ─────────────────────────────────────────────────────────

    def collect(self) -> AppSettings:
        """Return AppSettings with the current UI state merged in."""
        result = copy.deepcopy(self._settings)
        result.plot_fps = self._fps_slider.value()
        result.antialiasing = self._antialias_check.isChecked()
        result.use_opengl = self._opengl_check.isChecked()
        return result
