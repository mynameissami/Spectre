# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/settings/settings_panel.py — Inline Settings Panel

A QWidget (not a dialog) that integrates directly into the main tab bar.
Provides the same Appearance, Performance, and About sections laid out as
a two-column inspector panel: left sidebar navigation, right content area.

Layout:
    ┌──────────────┬─────────────────────────────────┐
    │  NAVIGATION  │   CONTENT AREA                  │
    │  ──────────  │   (Appearance / Performance /   │
    │  Appearance  │    About — scrollable)           │
    │  Performance │                                  │
    │  About       │                                  │
    │              ├─────────────────────────────────┤
    │              │  [ Reset to Defaults ]  [ Apply ]│
    └──────────────┴─────────────────────────────────┘
"""

from __future__ import annotations

import copy

import config
from core.settings_manager import AppSettings, SettingsManager, FontSettings
from core.theme_manager import ThemeManager
from styles import apply_pyqtgraph_theme, build_qss
from ui.settings.about_tab import AboutTab
from ui.settings.appearance_tab import AppearanceTab
from ui.settings.performance_tab import PerformanceTab

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class SettingsPanel(QWidget):
    """
    Inline settings panel embedded as a tab in the main window.

    Uses a sidebar + stacked-content layout (VS Code / JetBrains style).
    """

    close_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._mgr = SettingsManager.instance()
        self._staged: AppSettings = copy.deepcopy(self._mgr.settings)
        self._build_ui()

        # Connect to theme manager for live updates
        ThemeManager.instance().theme_changed.connect(self.update_theme)

    # ── UI Construction ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Panel header ──────────────────────────────────────────────────
        header = self._make_header()
        root.addWidget(header)

        # ── Main body: sidebar + content ─────────────────────────────────
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # Initialize content stack first so sidebar can connect signals to it
        self._content = QStackedWidget()

        # Left sidebar
        sidebar = self._build_sidebar()
        body.addWidget(sidebar)

        # Vertical divider
        self._vdiv = QFrame()
        self._vdiv.setFrameShape(QFrame.Shape.VLine)
        self._vdiv.setStyleSheet(f"color: {config.COLOR_BORDER};")
        body.addWidget(self._vdiv)

        # Right content stack widgets
        self._appearance_tab = AppearanceTab(self._staged)
        self._appearance_tab.preview_requested.connect(self._on_preview_theme)
        self._appearance_tab.font_preview_requested.connect(self._on_preview_font)
        self._performance_tab = PerformanceTab(self._staged)
        self._about_tab = AboutTab()

        self._content.addWidget(self._appearance_tab)   # index 0
        self._content.addWidget(self._performance_tab)  # index 1
        self._content.addWidget(self._about_tab)        # index 2

        content_container = QWidget()
        content_container_layout = QVBoxLayout(content_container)
        content_container_layout.setContentsMargins(64, 32, 64, 32)
        content_container_layout.addWidget(self._content)

        body.addWidget(content_container, stretch=1)

        body_widget = QWidget()
        body_widget.setLayout(body)
        root.addWidget(body_widget, stretch=1)

        # ── Footer: action buttons ─────────────────────────────────────────
        footer = self._build_footer()
        root.addWidget(footer)

    def _make_header(self) -> QWidget:
        self._hdr_frame = QFrame()
        self._hdr_frame.setFixedHeight(44)
        self._hdr_frame.setStyleSheet(
            f"background-color: {config.COLOR_PANEL_BG};"
            f" border-bottom: 1px solid {config.COLOR_BORDER};"
        )
        layout = QHBoxLayout(self._hdr_frame)
        layout.setContentsMargins(20, 0, 20, 0)

        self._hdr_lbl = QLabel("SETTINGS")
        self._hdr_lbl.setStyleSheet(
            f"font-size: 15px; font-weight: bold; letter-spacing: 4px;"
            f" color: {config.COLOR_TEXT_PRIMARY};"
        )

        self._hdr_desc = QLabel("Customize appearance, performance, and behaviour.")
        self._hdr_desc.setStyleSheet(f"color: {config.COLOR_TEXT_DIM}; font-size: 12px;")

        self._close_btn = QPushButton("✕ CLOSE")
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setStyleSheet(f"""
            QPushButton {{
                color: {config.COLOR_TEXT_DIM};
                font-weight: bold;
                border: none;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {config.COLOR_TEXT_PRIMARY};
                background-color: {config.COLOR_BORDER};
            }}
        """)
        self._close_btn.clicked.connect(self.close_requested.emit)

        layout.addWidget(self._hdr_lbl)
        layout.addSpacing(16)
        layout.addWidget(self._hdr_desc)
        layout.addStretch()
        layout.addWidget(self._close_btn)
        return self._hdr_frame

    def _build_sidebar(self) -> QWidget:
        f = SettingsManager.instance().settings.font
        self._sidebar = QWidget()
        self._sidebar.setFixedWidth(180)
        self._sidebar.setStyleSheet(
            f"background-color: {config.COLOR_PANEL_BG};"
        )

        layout = QVBoxLayout(self._sidebar)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)

        self._nav = QListWidget()
        self._nav.setFrameShape(QFrame.Shape.NoFrame)
        self._nav.setStyleSheet(f"""
            QListWidget {{
                background-color: {config.COLOR_PANEL_BG};
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                padding: 16px 24px;
                font-size: {f.labels + 2}px;
                font-weight: bold;
                letter-spacing: 1px;
                color: {config.COLOR_TEXT_DIM};
                border: none;
                border-radius: 0px;
            }}
            QListWidget::item:selected {{
                background-color: {config.COLOR_BG};
                color: {config.COLOR_ACCENT_GREEN};
                border-left: 3px solid {config.COLOR_ACCENT_GREEN};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {config.COLOR_BG};
                color: {config.COLOR_TEXT_PRIMARY};
            }}
        """)

        sections = ["Appearance", "Performance", "About"]
        for name in sections:
            item = QListWidgetItem(name)
            self._nav.addItem(item)

        self._nav.setCurrentRow(0)
        self._nav.currentRowChanged.connect(self._content.setCurrentIndex)

        layout.addWidget(self._nav)
        return self._sidebar

    def _build_footer(self) -> QWidget:
        self._footer_frame = QFrame()
        self._footer_frame.setFixedHeight(52)
        self._footer_frame.setStyleSheet(
            f"background-color: {config.COLOR_PANEL_BG};"
            f" border-bottom: 1px solid {config.COLOR_BORDER};"
            f" border-top: 1px solid {config.COLOR_BORDER};"
        )

        layout = QHBoxLayout(self._footer_frame)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(10)

        # Reset button — left side
        self._reset_btn = QPushButton("Reset to Defaults")
        self._reset_btn.setStyleSheet(
            f"border-color: {config.COLOR_ACCENT_ORANGE};"
            f" color: {config.COLOR_ACCENT_ORANGE};"
        )
        self._reset_btn.clicked.connect(self._on_reset)

        # Unsaved-changes indicator
        self._unsaved_lbl = QLabel("")
        self._unsaved_lbl.setStyleSheet(
            f"color: {config.COLOR_TEXT_DIM}; font-size: 12px;"
        )

        # Apply button — right side
        self._apply_btn = QPushButton("Apply Changes")
        self._apply_btn.setMinimumWidth(120)
        self._apply_btn.clicked.connect(self._on_apply)

        layout.addWidget(self._reset_btn)
        layout.addStretch()
        layout.addWidget(self._unsaved_lbl)
        layout.addWidget(self._apply_btn)

        return self._footer_frame

    def update_theme(self) -> None:
        """Update inline styles when the theme changes."""
        from core.settings_manager import SettingsManager
        f = SettingsManager.instance().settings.font
        
        if hasattr(self, '_hdr_frame'):
            self._hdr_frame.setStyleSheet(
                f"background-color: {config.COLOR_PANEL_BG};"
                f" border-bottom: 1px solid {config.COLOR_BORDER};"
            )
            self._hdr_lbl.setStyleSheet(
                f"font-size: 15px; font-weight: bold; letter-spacing: 4px;"
                f" color: {config.COLOR_TEXT_PRIMARY};"
            )
            self._hdr_desc.setStyleSheet(f"color: {config.COLOR_TEXT_DIM}; font-size: 12px;")
            self._close_btn.setStyleSheet(f"""
                QPushButton {{
                    color: {config.COLOR_TEXT_DIM};
                    font-weight: bold;
                    border: none;
                    padding: 4px 12px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    color: {config.COLOR_TEXT_PRIMARY};
                    background-color: {config.COLOR_BORDER};
                }}
            """)
        
        if hasattr(self, '_sidebar'):
            self._sidebar.setStyleSheet(f"background-color: {config.COLOR_PANEL_BG};")
            self._nav.setStyleSheet(f"""
                QListWidget {{
                    background-color: {config.COLOR_PANEL_BG};
                    border: none;
                    outline: none;
                }}
                QListWidget::item {{
                    padding: 16px 24px;
                    font-size: {f.labels + 2}px;
                    font-weight: bold;
                    letter-spacing: 1px;
                    color: {config.COLOR_TEXT_DIM};
                    border: none;
                    border-radius: 0px;
                }}
                QListWidget::item:selected {{
                    background-color: {config.COLOR_BG};
                    color: {config.COLOR_ACCENT_GREEN};
                    border-left: 3px solid {config.COLOR_ACCENT_GREEN};
                }}
                QListWidget::item:hover:!selected {{
                    background-color: {config.COLOR_BG};
                    color: {config.COLOR_TEXT_PRIMARY};
                }}
            """)
        
        if hasattr(self, '_vdiv'):
            self._vdiv.setStyleSheet(f"color: {config.COLOR_BORDER};")
            
        if hasattr(self, '_footer_frame'):
            self._footer_frame.setStyleSheet(
                f"background-color: {config.COLOR_PANEL_BG};"
                f" border-bottom: 1px solid {config.COLOR_BORDER};"
                f" border-top: 1px solid {config.COLOR_BORDER};"
            )
            self._reset_btn.setStyleSheet(
                f"color: {config.COLOR_ACCENT_RED}; font-weight: bold; padding: 6px 12px;"
            )
            self._unsaved_lbl.setStyleSheet(f"color: {config.COLOR_ACCENT_ORANGE}; font-weight: bold; padding: 0 12px;")
            self._apply_btn.setStyleSheet(
                f"background-color: {config.COLOR_ACCENT_GREEN}; color: #000; font-weight: bold; padding: 6px 16px;"
            )

        # Refresh child tabs
        for tab in (self._about_tab, self._performance_tab):
            if hasattr(tab, "refresh_theme"):
                tab.refresh_theme()

    # ── Private Helpers ────────────────────────────────────────────────────

    def _collect(self) -> AppSettings:
        s = self._appearance_tab.collect()
        perf = self._performance_tab.collect()
        s.plot_fps = perf.plot_fps
        s.antialiasing = perf.antialiasing
        s.use_opengl = perf.use_opengl
        return s

    def _apply_settings(self, s: AppSettings) -> None:
        """Push settings into SettingsManager, rebuild QSS, notify observers."""
        app = QApplication.instance()
        ThemeManager.instance().apply(s.theme, app)

        mgr_s = self._mgr.settings
        mgr_s.theme = s.theme
        mgr_s.font = s.font
        mgr_s.plot_fps = s.plot_fps
        mgr_s.antialiasing = s.antialiasing
        mgr_s.use_opengl = s.use_opengl
        self._mgr.save()

        app.setStyleSheet(build_qss())
        apply_pyqtgraph_theme()
        self._mgr.notify()

        self._unsaved_lbl.setText("Settings saved.")

    # ── Slots ──────────────────────────────────────────────────────────────

    def _on_preview_theme(self, theme_name: str) -> None:
        """Live-preview without persisting."""
        app = QApplication.instance()
        ThemeManager.instance().apply(theme_name, app)
        app.setStyleSheet(build_qss())
        self._unsaved_lbl.setText("Unsaved changes — click Apply to save.")

    def _on_preview_font(self, font: FontSettings) -> None:
        """Live-preview fonts without persisting."""
        import config
        config.FONT_GLOBAL_UI = font.global_ui
        config.FONT_MENU_BAR = font.menu_bar
        config.FONT_LABELS = font.labels
        config.FONT_BUTTONS = font.buttons
        config.FONT_EVENT_LOG = font.event_log
        config.FONT_TABLES = font.tables
        config.FONT_PLOTS = font.plots

        app = QApplication.instance()
        from styles import build_qss
        app.setStyleSheet(build_qss())
        ThemeManager.instance().theme_changed.emit()
        self._unsaved_lbl.setText("Unsaved changes — click Apply to save.")

    def _on_apply(self) -> None:
        s = self._collect()
        self._apply_settings(s)
        self._staged = copy.deepcopy(self._mgr.settings)

    def _on_reset(self) -> None:
        msg = QMessageBox(self)
        msg.setWindowTitle("Reset to Defaults")
        msg.setText("Reset all settings to factory defaults?")
        msg.setIcon(QMessageBox.Icon.NoIcon)
        btn_yes = msg.addButton("Yes", QMessageBox.ButtonRole.YesRole)
        msg.addButton("No", QMessageBox.ButtonRole.NoRole)
        msg.exec()
        if msg.clickedButton() != btn_yes:
            return

        defaults = AppSettings()
        self._apply_settings(defaults)
        self._staged = copy.deepcopy(defaults)

        # Rebuild the panel content to reflect new defaults
        self._appearance_tab.deleteLater()
        self._performance_tab.deleteLater()
        self._appearance_tab = AppearanceTab(self._staged)
        self._appearance_tab.preview_requested.connect(self._on_preview_theme)
        self._appearance_tab.font_preview_requested.connect(self._on_preview_font)
        self._performance_tab = PerformanceTab(self._staged)
        self._content.insertWidget(0, self._appearance_tab)
        self._content.insertWidget(1, self._performance_tab)
        self._content.setCurrentIndex(self._nav.currentRow())
