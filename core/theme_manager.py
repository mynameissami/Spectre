# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/theme_manager.py — Runtime Theme Engine

Defines colour palettes for each theme and applies them by mutating
the config module's colour constants, then regenerating the QSS
stylesheet. No app restart required.

Available themes:
    dark_hacker   — Default green-on-black matrix aesthetic
    monochrome    — Clean white/silver on near-black
    deep_blue     — Naval radar, navy base with cyan accents
    blood_red     — Aggressive dark crimson accent palette
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication


# ─── Theme Palette Dataclass ──────────────────────────────────────────────────

@dataclass(frozen=True)
class ThemePalette:
    """A complete colour palette for one visual theme."""
    name: str
    display_name: str

    # Backgrounds
    bg: str
    panel_bg: str
    border: str
    plot_bg: str
    plot_grid: str

    # Accent colours
    accent_primary: str     # Main action colour (buttons, active tabs)
    accent_secondary: str   # Info / highlight colour
    accent_red: str         # Critical / alert
    accent_orange: str      # Warning

    # Text
    text_primary: str
    text_dim: str

    # Plot traces
    raw_rssi: str
    smooth_rssi: str

    # Spectrum
    spectrum_base: str
    spectrum_hot: str

    # Banner
    banner_bg: str
    banner_border: str


# ─── Built-in Palettes ────────────────────────────────────────────────────────

THEMES: dict[str, ThemePalette] = {
    "dark_hacker": ThemePalette(
        name="dark_hacker",
        display_name="Dark Hacker",
        bg="#0A0A0A",
        panel_bg="#0F0F0F",
        border="#1A1A2E",
        plot_bg="#050508",
        plot_grid="#1A1A2E",
        accent_primary="#00FF41",
        accent_secondary="#00D4FF",
        accent_red="#FF3333",
        accent_orange="#FFA500",
        text_primary="#E0E0E0",
        text_dim="#5A5A6A",
        raw_rssi="#FF3333",
        smooth_rssi="#00FF41",
        spectrum_base="#00D4FF",
        spectrum_hot="#FFA500",
        banner_bg="#050508",
        banner_border="#00FF41",
    ),

    "monochrome": ThemePalette(
        name="monochrome",
        display_name="Monochrome",
        bg="#0D0D0D",
        panel_bg="#141414",
        border="#2E2E2E",
        plot_bg="#080808",
        plot_grid="#222222",
        accent_primary="#E0E0E0",
        accent_secondary="#AAAAAA",
        accent_red="#CC3333",
        accent_orange="#CC7700",
        text_primary="#D0D0D0",
        text_dim="#555555",
        raw_rssi="#888888",
        smooth_rssi="#FFFFFF",
        spectrum_base="#999999",
        spectrum_hot="#CCCCCC",
        banner_bg="#080808",
        banner_border="#AAAAAA",
    ),

    "deep_blue": ThemePalette(
        name="deep_blue",
        display_name="Deep Blue",
        bg="#030712",
        panel_bg="#070D1A",
        border="#0F1F3D",
        plot_bg="#020510",
        plot_grid="#0A1428",
        accent_primary="#00BFFF",
        accent_secondary="#4488FF",
        accent_red="#FF4455",
        accent_orange="#FF8800",
        text_primary="#C0D8FF",
        text_dim="#3A5070",
        raw_rssi="#FF4455",
        smooth_rssi="#00BFFF",
        spectrum_base="#4488FF",
        spectrum_hot="#00BFFF",
        banner_bg="#020510",
        banner_border="#00BFFF",
    ),

    "blood_red": ThemePalette(
        name="blood_red",
        display_name="Blood Red",
        bg="#080005",
        panel_bg="#100008",
        border="#2A0010",
        plot_bg="#050003",
        plot_grid="#1A000A",
        accent_primary="#FF2244",
        accent_secondary="#FF6688",
        accent_red="#FF0000",
        accent_orange="#FF6600",
        text_primary="#F0C0C8",
        text_dim="#602030",
        raw_rssi="#FF0000",
        smooth_rssi="#FF2244",
        spectrum_base="#FF6688",
        spectrum_hot="#FF2244",
        banner_bg="#050003",
        banner_border="#FF2244",
    ),
}


from PySide6.QtCore import QObject, Signal

# ─── Theme Manager Singleton ──────────────────────────────────────────────────

class ThemeManager(QObject):
    """
    Singleton that applies a chosen ThemePalette at runtime by:
    1. Mutating the `config` module's colour constants.
    2. Rebuilding the QSS via `styles.theme.build_qss()`.
    3. Calling `QApplication.setStyleSheet()`.
    """
    theme_changed = Signal()

    _instance: "ThemeManager | None" = None

    def __init__(self, parent=None):
        super().__init__(parent)

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def apply(self, theme_name: str, app: "QApplication") -> None:
        """Apply the named theme to the running QApplication."""
        palette = THEMES.get(theme_name, THEMES["dark_hacker"])
        self._mutate_config(palette)

        # Clear the pixmap cache so that any re-generated SVGs are reloaded
        from PySide6.QtGui import QPixmapCache
        QPixmapCache.clear()

        # Rebuild and apply the stylesheet
        from styles import build_qss
        app.setStyleSheet(build_qss())
        
        self.theme_changed.emit()

    def _mutate_config(self, p: ThemePalette) -> None:
        """Write palette values into the config module in-place."""
        import config
        config.COLOR_BG = p.bg
        config.COLOR_PANEL_BG = p.panel_bg
        config.COLOR_BG_PANEL = p.panel_bg
        config.COLOR_BORDER = p.border
        config.COLOR_PLOT_BG = p.plot_bg
        config.COLOR_PLOT_GRID = p.plot_grid
        config.COLOR_ACCENT_GREEN = p.accent_primary
        config.COLOR_ACCENT_CYAN = p.accent_secondary
        config.COLOR_ACCENT_RED = p.accent_red
        config.COLOR_ACCENT_ORANGE = p.accent_orange
        config.COLOR_TEXT_PRIMARY = p.text_primary
        config.COLOR_TEXT_DIM = p.text_dim
        config.COLOR_RAW_RSSI = p.raw_rssi
        config.COLOR_SMOOTH_RSSI = p.smooth_rssi
        config.COLOR_SPECTRUM_BASE = p.spectrum_base
        config.COLOR_SPECTRUM_HOT = p.spectrum_hot
        
        # Dynamically regenerate SVG assets using the new theme color
        import os
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
        os.makedirs(assets_dir, exist_ok=True)
        
        up_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{p.accent_secondary}">
  <path d="M7 14l5-5 5 5H7z"/>
</svg>'''
        with open(os.path.join(assets_dir, 'up-arrow.svg'), 'w') as f:
            f.write(up_svg)
            
        down_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{p.accent_secondary}">
  <path d="M7 10l5 5 5-5H7z"/>
</svg>'''
        with open(os.path.join(assets_dir, 'down-arrow.svg'), 'w') as f:
            f.write(down_svg)

    @property
    def available_themes(self) -> dict[str, str]:
        """Returns {theme_name: display_name} for all built-in themes."""
        return {k: v.display_name for k, v in THEMES.items()}
