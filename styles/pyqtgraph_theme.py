# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
styles/pyqtgraph_theme.py — PyQtGraph theming helpers.
"""

from __future__ import annotations
import pyqtgraph as pg
import config

def apply_pyqtgraph_theme() -> None:
    """Configure PyQtGraph defaults to match the current theme."""
    from core.settings_manager import SettingsManager
    s = SettingsManager.instance().settings
    pg.setConfigOptions(
        antialias=s.antialiasing,
        useOpenGL=s.use_opengl,
        enableExperimental=False,
        foreground=config.COLOR_TEXT_PRIMARY,
        background=config.COLOR_PLOT_BG,
    )

def make_plot_widget(title: str = "", y_label: str = "", x_label: str = "") -> pg.PlotWidget:
    """
    Factory: return a styled PlotWidget ready to embed in any layout.
    Uses current config colours so it respects the active theme.
    """
    from core.settings_manager import SettingsManager
    font_size = f"{SettingsManager.instance().settings.font.plots}pt"

    pw = pg.PlotWidget()
    pw.setBackground(config.COLOR_PLOT_BG)
    pw.showGrid(x=True, y=True, alpha=0.18)
    pw.getPlotItem().getAxis("bottom").setPen(pg.mkPen(config.COLOR_PLOT_GRID))
    pw.getPlotItem().getAxis("left").setPen(pg.mkPen(config.COLOR_PLOT_GRID))
    pw.getPlotItem().getAxis("bottom").setTextPen(pg.mkPen(config.COLOR_TEXT_DIM))
    pw.getPlotItem().getAxis("left").setTextPen(pg.mkPen(config.COLOR_TEXT_DIM))

    if title:
        pw.setTitle(title, color=config.COLOR_ACCENT_CYAN, size=font_size)
    if y_label:
        pw.setLabel("left", y_label, color=config.COLOR_TEXT_DIM, size="9pt")
    if x_label:
        pw.setLabel("bottom", x_label, color=config.COLOR_TEXT_DIM, size="9pt")

    return pw
