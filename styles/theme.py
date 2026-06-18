# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
styles/theme.py — S.P.E.C.T.R.E. Dark Industrial Theme
Provides QSS stylesheet and PyQtGraph plot configuration.
"""

from __future__ import annotations

import pyqtgraph as pg

import config


# ─── Master QSS Stylesheet ────────────────────────────────────────────────────

QSS = f"""
/* ── Global ────────────────────────────────────────────────────────────────── */
* {{
    font-family: "Lexend";
    font-size: 12px;
    font-weight: medium;
    color: {config.COLOR_TEXT_PRIMARY};
    outline: none;
}}

QToolTip {{
    background-color: {config.COLOR_PANEL_BG};
    color: {config.COLOR_TEXT_PRIMARY};
    border: 1px solid {config.COLOR_ACCENT_CYAN};
    padding: 4px;
    font-size: 11px;
}}

QMainWindow, QWidget {{
    background-color: {config.COLOR_BG};
}}

/* ── Panels ─────────────────────────────────────────────────────────────────── */
QFrame#panel {{
    background-color: {config.COLOR_PANEL_BG};
    border: 1px solid {config.COLOR_BORDER};
    border-radius: 4px;
}}

/* ── Banner ─────────────────────────────────────────────────────────────────── */
QFrame#banner {{
    background-color: #050508;
    border-bottom: 2px solid {config.COLOR_ACCENT_GREEN};
    border-radius: 0px;
}}

/* ── Labels ─────────────────────────────────────────────────────────────────── */
QLabel#title {{
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 3px;
    color: {config.COLOR_ACCENT_GREEN};
}}

QLabel#subtitle {{
    font-size: 10px;
    color: {config.COLOR_TEXT_DIM};
    letter-spacing: 2px;
}}

QLabel#section_header {{
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 2px;
    color: {config.COLOR_ACCENT_CYAN};
    padding: 4px 0px;
    border-bottom: 1px solid {config.COLOR_BORDER};
}}

QLabel#status_key {{
    font-size: 10px;
    color: {config.COLOR_TEXT_DIM};
    letter-spacing: 1px;
}}

QLabel#status_value {{
    font-size: 11px;
    font-weight: bold;
    color: {config.COLOR_ACCENT_GREEN};
}}

QLabel#status_value_alert {{
    font-size: 11px;
    font-weight: bold;
    color: {config.COLOR_ACCENT_RED};
}}

QLabel#status_value_warn {{
    font-size: 11px;
    font-weight: bold;
    color: {config.COLOR_ACCENT_ORANGE};
}}

QLabel#status_value_dim {{
    font-size: 11px;
    color: {config.COLOR_TEXT_DIM};
}}

QLabel#big_status {{
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 2px;
    padding: 4px 12px;
    border-radius: 4px;
}}

QLabel#big_status_running {{
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 2px;
    color: {config.COLOR_BG};
    background-color: {config.COLOR_ACCENT_GREEN};
    padding: 4px 12px;
    border-radius: 4px;
}}

QLabel#big_status_paused {{
    font-size: 13px;
    font-weight: bold;
    letter-spacing: 2px;
    color: {config.COLOR_BG};
    background-color: {config.COLOR_TEXT_DIM};
    padding: 4px 12px;
    border-radius: 4px;
}}

/* ── Buttons ─────────────────────────────────────────────────────────────────── */
QPushButton {{
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 6px 20px;
    border: 1px solid {config.COLOR_ACCENT_GREEN};
    border-radius: 3px;
    background-color: transparent;
    color: {config.COLOR_ACCENT_GREEN};
}}

QPushButton:hover {{
    background-color: {config.COLOR_ACCENT_GREEN};
    color: {config.COLOR_BG};
}}

QPushButton:pressed {{
    background-color: #009922;
    color: {config.COLOR_BG};
}}

QPushButton:disabled {{
    border-color: {config.COLOR_TEXT_DIM};
    color: {config.COLOR_TEXT_DIM};
}}

QPushButton#disconnect_btn {{
    border-color: {config.COLOR_ACCENT_RED};
    color: {config.COLOR_ACCENT_RED};
}}

QPushButton#disconnect_btn:hover {{
    background-color: {config.COLOR_ACCENT_RED};
    color: {config.COLOR_BG};
}}

/* ── ComboBox ─────────────────────────────────────────────────────────────────── */
QComboBox {{
    font-size: 11px;
    padding: 5px 10px;
    border: 1px solid {config.COLOR_BORDER};
    border-radius: 3px;
    background-color: #0F0F18;
    color: {config.COLOR_TEXT_PRIMARY};
    min-width: 140px;
}}

QComboBox:hover {{
    border-color: {config.COLOR_ACCENT_CYAN};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {config.COLOR_ACCENT_CYAN};
}}

QComboBox QAbstractItemView {{
    background-color: #0F0F18;
    border: 1px solid {config.COLOR_ACCENT_CYAN};
    selection-background-color: {config.COLOR_ACCENT_GREEN};
    selection-color: {config.COLOR_BG};
    color: {config.COLOR_TEXT_PRIMARY};
}}

/* ── Spinbox ─────────────────────────────────────────────────────────────────── */
QSpinBox {{
    font-size: 11px;
    padding: 4px 8px;
    border: 1px solid {config.COLOR_BORDER};
    border-radius: 3px;
    background-color: #0F0F18;
    color: {config.COLOR_TEXT_PRIMARY};
}}

QSpinBox:hover {{
    border-color: {config.COLOR_ACCENT_CYAN};
}}

QSpinBox::up-button, QSpinBox::down-button {{
    width: 16px;
    border: none;
    background-color: transparent;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {config.COLOR_BORDER};
}}

QSpinBox::up-arrow {{
    image: none;
    width: 0px;
    height: 0px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid {config.COLOR_ACCENT_CYAN};
}}

QSpinBox::down-arrow {{
    image: none;
    width: 0px;
    height: 0px;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {config.COLOR_ACCENT_CYAN};
}}

/* ── Event Log ─────────────────────────────────────────────────────────────── */
QTextEdit#event_log {{
    background-color: #030305;
    color: {config.COLOR_ACCENT_GREEN};
    font-size: 10px;
    border: 1px solid {config.COLOR_BORDER};
    border-radius: 3px;
    padding: 4px;
}}

/* ── ScrollBar ──────────────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background-color: {config.COLOR_BG};
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {config.COLOR_BORDER};
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {config.COLOR_ACCENT_GREEN};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {config.COLOR_BG};
    height: 8px;
}}

QScrollBar::handle:horizontal {{
    background-color: {config.COLOR_BORDER};
    min-width: 20px;
    border-radius: 4px;
}}

/* ── Tabs ───────────────────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid #1A1A2E;
    background-color: #0A0A0A;
}}

QTabBar::tab {{
    background-color: #050508;
    color: #5A5A6A;
    border: 1px solid #1A1A2E;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 150px;
    padding: 8px;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 2px;
}}

QTabBar::tab:selected {{
    background-color: #0A0A0A;
    color: #00FF41;
    border-top: 2px solid #00FF41;
}}

QTabBar::tab:hover:!selected {{
    color: #E0E0E0;
    background-color: #0F0F18;
}}

/* ── Splitter ───────────────────────────────────────────────────────────────── */
QSplitter::handle {{
    background-color: {config.COLOR_BORDER};
}}

/* ── Separator ──────────────────────────────────────────────────────────────── */
QFrame[frameShape="4"],
QFrame[frameShape="5"] {{
    color: {config.COLOR_BORDER};
}}
"""


# ─── PyQtGraph Global Configuration ──────────────────────────────────────────

def apply_pyqtgraph_theme() -> None:
    """Configure PyQtGraph defaults to match the dark industrial theme."""
    pg.setConfigOptions(
        antialias=True,
        useOpenGL=False,          # Software render — more compatible
        enableExperimental=False,
        foreground=config.COLOR_TEXT_PRIMARY,
        background=config.COLOR_PLOT_BG,
    )


def make_plot_widget(title: str = "", y_label: str = "", x_label: str = "") -> pg.PlotWidget:
    """
    Factory: return a styled PlotWidget ready to embed in any layout.
    """
    pw = pg.PlotWidget()
    pw.setBackground(config.COLOR_PLOT_BG)
    pw.showGrid(x=True, y=True, alpha=0.18)
    pw.getPlotItem().getAxis("bottom").setPen(pg.mkPen(config.COLOR_PLOT_GRID))
    pw.getPlotItem().getAxis("left").setPen(pg.mkPen(config.COLOR_PLOT_GRID))
    pw.getPlotItem().getAxis("bottom").setTextPen(pg.mkPen(config.COLOR_TEXT_DIM))
    pw.getPlotItem().getAxis("left").setTextPen(pg.mkPen(config.COLOR_TEXT_DIM))

    if title:
        pw.setTitle(
            title,
            color=config.COLOR_ACCENT_CYAN,
            size="11pt",
        )
    if y_label:
        pw.setLabel("left",  y_label, color=config.COLOR_TEXT_DIM, size="9pt")
    if x_label:
        pw.setLabel("bottom", x_label, color=config.COLOR_TEXT_DIM, size="9pt")

    return pw
