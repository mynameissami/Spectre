# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
styles/theme.py — S.P.E.C.T.R.E. Theme & Stylesheet Builder

Provides:
    build_qss()             — Builds the full QSS string from current config
    apply_pyqtgraph_theme() — Configures PyQtGraph defaults
    make_plot_widget()      — Factory for consistently styled PlotWidgets

QSS is built on-demand from config module values, enabling runtime
theme switching without restarting the application.
"""

from __future__ import annotations

import pyqtgraph as pg
import config
from styles.palette import rgba


def build_qss(font: "FontSettings | None" = None) -> str:
    """
    Build and return the complete QSS stylesheet string.

    Reads colour and font values from the `config` module at call time,
    so this can be called repeatedly after a theme or font change.

    Args:
        font: Optional FontSettings. If None, reads from SettingsManager.
    """
    from core.settings_manager import SettingsManager
    s = SettingsManager.instance().settings

    f = font or s.font


    return f"""
/* ── Global ─────────────────────────────────────────────────────────────────── */
* {{
    font-family: "Lexend";
    font-size: {f.global_ui}px;
    font-weight: medium;
    color: {config.COLOR_TEXT_PRIMARY};
    outline: none;
}}

QToolTip {{
    background-color: {config.COLOR_PANEL_BG};
    color: {config.COLOR_TEXT_PRIMARY};
    border: 1px solid {config.COLOR_ACCENT_CYAN};
    padding: 4px;
    font-size: {f.labels}px;
}}

QMainWindow {{
    background-color: {config.COLOR_BG};
}}

/* ── Panels ─────────────────────────────────────────────────────────────────── */
QFrame#panel {{
    background-color: {config.COLOR_PANEL_BG};
    border: none;
}}

/* ── Banner ─────────────────────────────────────────────────────────────────── */
QFrame#banner {{
    background-color: {config.COLOR_PANEL_BG};
    border-bottom: 2px solid {config.COLOR_ACCENT_GREEN};
    border-radius: 0px;
}}

/* ── Menu Bar ───────────────────────────────────────────────────────────────── */
QMenuBar {{
    background-color: {config.COLOR_BG};
    border-bottom: 1px solid {config.COLOR_BORDER};
    color: {config.COLOR_TEXT_PRIMARY};
    font-size: {f.menu_bar}px;
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 6px 12px;
}}

QMenuBar::item:selected {{
    background-color: {config.COLOR_ACCENT_GREEN};
    color: {config.COLOR_BG};
}}

QMenu {{
    background-color: {config.COLOR_BG};
    border: 1px solid {config.COLOR_BORDER};
    color: {config.COLOR_TEXT_PRIMARY};
    font-size: {f.menu_bar}px;
}}

QMenu::item {{
    padding: 6px 24px 6px 36px;
}}

QMenu::item:selected {{
    background-color: {config.COLOR_ACCENT_GREEN};
    color: {config.COLOR_BG};
}}

QMenu::indicator {{
    width: 12px;
    height: 12px;
    left: 12px;
    border: 1px solid {config.COLOR_ACCENT_GREEN};
}}

QMenu::indicator:checked {{
    background-color: {config.COLOR_ACCENT_GREEN};
}}

QMenu::indicator:unchecked {{
    background-color: transparent;
}}

/* ── Labels ─────────────────────────────────────────────────────────────────── */
QLabel {{
    background-color: transparent;
}}

QLabel#title {{
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 3px;
    color: {config.COLOR_ACCENT_GREEN};
}}

QLabel#subtitle {{
    font-size: {max(f.labels - 2, 8)}px;
    color: {config.COLOR_TEXT_DIM};
    letter-spacing: 2px;
}}

QLabel#section_header {{
    font-size: {f.labels}px;
    font-weight: bold;
    letter-spacing: 2px;
    color: {config.COLOR_ACCENT_RED};
    padding: 4px 0px;
    border-bottom: 2px solid {config.COLOR_ACCENT_RED};
}}

QLabel#status_key {{
    font-size: {max(f.labels - 2, 8)}px;
    color: {config.COLOR_TEXT_DIM};
    letter-spacing: 1px;
}}

QLabel#status_value {{
    font-size: {f.labels}px;
    font-weight: bold;
    color: {config.COLOR_ACCENT_GREEN};
}}

QLabel#status_value_alert {{
    font-size: {f.labels}px;
    font-weight: bold;
    color: {config.COLOR_ACCENT_RED};
}}

QLabel#status_value_warn {{
    font-size: {f.labels}px;
    font-weight: bold;
    color: {config.COLOR_ACCENT_ORANGE};
}}

QLabel#status_value_dim {{
    font-size: {f.labels}px;
    color: {config.COLOR_TEXT_DIM};
}}

QLabel#big_status {{
    font-size: {f.labels + 1}px;
    font-weight: bold;
    letter-spacing: 2px;
    padding: 4px 12px;
    border-radius: 4px;
}}

QLabel#big_status_running {{
    font-size: {f.labels + 1}px;
    font-weight: bold;
    letter-spacing: 2px;
    color: {config.COLOR_BG};
    background-color: {config.COLOR_ACCENT_GREEN};
    padding: 4px 12px;
    border-radius: 4px;
}}

QLabel#big_status_paused {{
    font-size: {f.labels + 1}px;
    font-weight: bold;
    letter-spacing: 2px;
    color: {config.COLOR_BG};
    background-color: {config.COLOR_TEXT_DIM};
    padding: 4px 12px;
    border-radius: 4px;
}}

/* ── Buttons ─────────────────────────────────────────────────────────────────── */
QPushButton {{
    font-size: {f.buttons}px;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 6px 20px;
    border: none;
    border-bottom: 2px solid {config.COLOR_ACCENT_GREEN};
    background-color: {rgba(config.COLOR_ACCENT_GREEN, 0.15)};
    color: {config.COLOR_ACCENT_GREEN};
}}

QPushButton:hover {{
    background-color: {config.COLOR_ACCENT_GREEN};
    color: {config.COLOR_BG};
}}

QPushButton:pressed {{
    background-color: {config.COLOR_ACCENT_ORANGE};
    color: {config.COLOR_BG};
}}

QPushButton:disabled {{
    border-bottom-color: {config.COLOR_TEXT_DIM};
    color: {config.COLOR_TEXT_DIM};
}}

QPushButton#disconnect_btn {{
    border-bottom-color: {config.COLOR_ACCENT_RED};
    color: {config.COLOR_ACCENT_RED};
}}

QPushButton#disconnect_btn:hover {{
    background-color: {config.COLOR_ACCENT_RED};
    color: {config.COLOR_BG};
}}

/* ── LineEdit ─────────────────────────────────────────────────────────────────── */
QLineEdit {{
    font-size: {f.buttons}px;
    padding: 5px 10px;
    border: none;
    border-bottom: 2px solid {config.COLOR_BORDER};
    background-color: {config.COLOR_PANEL_BG};
    color: {config.COLOR_TEXT_PRIMARY};
}}

QLineEdit:focus {{
    border-bottom-color: {config.COLOR_ACCENT_CYAN};
}}

/* ── ComboBox ─────────────────────────────────────────────────────────────────── */
QComboBox {{
    font-size: {f.buttons}px;
    padding: 6px 10px;
    border: 1px solid {config.COLOR_BORDER};
    background-color: {config.COLOR_BG};
    color: {config.COLOR_TEXT_PRIMARY};
    min-width: 140px;
    outline: none;
}}

QComboBox:hover, QComboBox:focus {{
    border: 1px solid {config.COLOR_ACCENT_CYAN};
}}


QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid {config.COLOR_BORDER};
    background-color: {config.COLOR_PANEL_BG};
}}

QComboBox::drop-down:hover {{
    background-color: {rgba(config.COLOR_ACCENT_CYAN, 0.1)};
}}

QComboBox::down-arrow {{
    width: 14px;
    height: 14px;
    image: url(assets/down-arrow.svg);
}}

QComboBox QAbstractItemView {{
    background-color: {config.COLOR_PANEL_BG};
    border: 1px solid {config.COLOR_BORDER};
    outline: none;
    padding: 0px;
    margin: 0px;
    selection-background-color: {config.COLOR_BORDER};
    selection-color: {config.COLOR_TEXT_PRIMARY};
    color: {config.COLOR_TEXT_PRIMARY};
}}

QComboBox QAbstractItemView::item {{
    padding: 6px 12px;
    min-height: 28px;
    border-bottom: 1px solid {rgba(config.COLOR_BORDER, 0.5)};
}}

QComboBox QAbstractItemView::item:selected {{
    background-color: {config.COLOR_BORDER};
}}

/* ── Spinbox ─────────────────────────────────────────────────────────────────── */
QSpinBox {{
    font-size: {f.buttons}px;
    padding: 4px 8px;
    border: none;
    border-bottom: 2px solid {config.COLOR_BORDER};
    background-color: {config.COLOR_PANEL_BG};
    color: {config.COLOR_TEXT_PRIMARY};
}}

QSpinBox:hover {{
    border-bottom-color: {config.COLOR_ACCENT_CYAN};
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
    image: url(assets/up-arrow.svg);
    width: 10px;
    height: 10px;
}}
QSpinBox::down-arrow {{
    image: url(assets/down-arrow.svg);
    width: 10px;
    height: 10px;
}}

/* ── Event Log & Chat ───────────────────────────────────────────────────────── */
QTextEdit#event_log {{
    background-color: {config.COLOR_BG};
    color: {config.COLOR_ACCENT_GREEN};
    font-size: {f.event_log}px;
    border: 1px solid {config.COLOR_BORDER};
    border-radius: 3px;
    padding: 4px;
}}

QTextEdit#doc_viewer {{
    background-color: {config.COLOR_PANEL_BG};
    color: {config.COLOR_TEXT_PRIMARY};
    border: 1px solid {config.COLOR_BORDER};
    border-radius: 4px;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
    padding: 10px;
}}

QTextEdit#chat_history {{
    background-color: {config.COLOR_PANEL_BG};
    color: {config.COLOR_TEXT_PRIMARY};
    border: 1px solid {config.COLOR_BORDER};
    border-radius: 4px;
    font-family: monospace;
    font-size: 12px;
}}

QFrame#chat_input_frame {{
    border: 1px solid {config.COLOR_BORDER};
    border-radius: 4px;
}}

/* ── Tree / Table Widgets ───────────────────────────────────────────────────── */
QTreeWidget, QTableWidget {{
    background-color: {config.COLOR_PANEL_BG};
    color: {config.COLOR_TEXT_PRIMARY};
    border: 1px solid {config.COLOR_BORDER};
    border-radius: 4px;
    font-size: {f.tables}px;
    outline: none;
    gridline-color: {config.COLOR_PLOT_GRID};
}}

QTreeWidget::item, QTableWidget::item {{
    padding: 4px;
    border-bottom: 1px solid {config.COLOR_BORDER};
    font-size: {f.tables}px;
}}

QTreeWidget::item:selected, QTableWidget::item:selected {{
    background-color: {config.COLOR_BG};
    color: {config.COLOR_ACCENT_CYAN};
}}

QHeaderView::section {{
    background-color: {config.COLOR_BG};
    color: {config.COLOR_ACCENT_CYAN};
    padding: 6px;
    border: none;
    border-bottom: 1px solid {config.COLOR_BORDER};
    font-weight: bold;
    font-size: {max(f.tables - 1, 8)}px;
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
    border: none;
    border-top: 1px solid {config.COLOR_BORDER};
    background-color: transparent;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {config.COLOR_TEXT_DIM};
    border: none;
    border-bottom: 2px solid transparent;
    min-width: 150px;
    padding: 10px 8px;
    font-size: {f.labels + 1}px;
    font-weight: bold;
    letter-spacing: 2px;
}}

QTabBar::tab:selected {{
    color: {config.COLOR_TEXT_PRIMARY};
    border-bottom: 2px solid {config.COLOR_ACCENT_CYAN};
}}

QTabBar::tab:hover:!selected {{
    color: {config.COLOR_TEXT_PRIMARY};
    background-color: transparent;
}}

/* ── Scroll Area ────────────────────────────────────────────────────────────── */
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {config.COLOR_BORDER};
    min-height: 30px;
    border-radius: 3px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* ── Slider ─────────────────────────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    height: 4px;
    background: {config.COLOR_BORDER};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {config.COLOR_ACCENT_GREEN};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}

QSlider::sub-page:horizontal {{
    background: {config.COLOR_ACCENT_GREEN};
    border-radius: 2px;
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

/* ── Dialog ─────────────────────────────────────────────────────────────────── */
QDialog {{
    background-color: {config.COLOR_BG};
}}

/* ── Dynamic Buttons ────────────────────────────────────────────────────────── */
QPushButton[btnTheme="red"], QPushButton[btnTheme="green"], QPushButton[btnTheme="orange"],
QPushButton[btnTheme="cyan"], QPushButton[btnTheme="dim"], QPushButton[btnTheme="gold"],
QPushButton[btnTheme="magenta"], QPushButton[btnTheme="purple"] {{
    border: none;
    padding: 6px 20px;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    border-radius: 0px;
}}

QPushButton[btnTheme="red"] {{ background-color: {rgba(config.COLOR_ACCENT_RED, 0.15)}; color: {config.COLOR_ACCENT_RED}; border-bottom: 2px solid {config.COLOR_ACCENT_RED}; }}
QPushButton[btnTheme="red"]:hover, QPushButton[btnTheme="red"][btnActive="true"] {{ background-color: {config.COLOR_ACCENT_RED}; color: {config.COLOR_BG}; }}

QPushButton[btnTheme="green"] {{ background-color: {rgba(config.COLOR_ACCENT_GREEN, 0.15)}; color: {config.COLOR_ACCENT_GREEN}; border-bottom: 2px solid {config.COLOR_ACCENT_GREEN}; }}
QPushButton[btnTheme="green"]:hover, QPushButton[btnTheme="green"][btnActive="true"] {{ background-color: {config.COLOR_ACCENT_GREEN}; color: {config.COLOR_BG}; }}

QPushButton[btnTheme="orange"] {{ background-color: {rgba(config.COLOR_ACCENT_ORANGE, 0.15)}; color: {config.COLOR_ACCENT_ORANGE}; border-bottom: 2px solid {config.COLOR_ACCENT_ORANGE}; }}
QPushButton[btnTheme="orange"]:hover, QPushButton[btnTheme="orange"][btnActive="true"] {{ background-color: {config.COLOR_ACCENT_ORANGE}; color: {config.COLOR_BG}; }}

QPushButton[btnTheme="cyan"] {{ background-color: {rgba(config.COLOR_ACCENT_CYAN, 0.15)}; color: {config.COLOR_ACCENT_CYAN}; border-bottom: 2px solid {config.COLOR_ACCENT_CYAN}; }}
QPushButton[btnTheme="cyan"]:hover, QPushButton[btnTheme="cyan"][btnActive="true"] {{ background-color: {config.COLOR_ACCENT_CYAN}; color: {config.COLOR_BG}; }}

QPushButton[btnTheme="dim"] {{ background-color: {rgba(config.COLOR_TEXT_DIM, 0.15)}; color: {config.COLOR_TEXT_DIM}; border-bottom: 2px solid {config.COLOR_TEXT_DIM}; }}
QPushButton[btnTheme="dim"]:hover, QPushButton[btnTheme="dim"][btnActive="true"] {{ background-color: {config.COLOR_TEXT_DIM}; color: {config.COLOR_BG}; }}

QPushButton[btnTheme="gold"] {{ background-color: {rgba('#FFD700', 0.15)}; color: #FFD700; border-bottom: 2px solid #FFD700; }}
QPushButton[btnTheme="gold"]:hover, QPushButton[btnTheme="gold"][btnActive="true"] {{ background-color: #FFD700; color: {config.COLOR_BG}; }}

QPushButton[btnTheme="magenta"] {{ background-color: {rgba('#FF00FF', 0.15)}; color: #FF00FF; border-bottom: 2px solid #FF00FF; }}
QPushButton[btnTheme="magenta"]:hover, QPushButton[btnTheme="magenta"][btnActive="true"] {{ background-color: #FF00FF; color: {config.COLOR_BG}; }}

QPushButton[btnTheme="purple"] {{ background-color: {rgba('#9D00FF', 0.15)}; color: #9D00FF; border-bottom: 2px solid #9D00FF; }}
QPushButton[btnTheme="purple"]:hover, QPushButton[btnTheme="purple"][btnActive="true"] {{ background-color: #9D00FF; color: {config.COLOR_BG}; }}

/* ── Custom Utilities ────────────────────────────────────────────────────────── */
"""


