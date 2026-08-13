# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ui.main_window._window import MainWindow

from PySide6.QtCore import Qt, Slot, QTimer, QPoint
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import QMessageBox
import numpy as np
import time
import config
from core.settings_manager import SettingsManager
from core.network.recon import ReconEventType
from core.analytics.threat import ThreatLevel

class MenuBuilderMixin:
    # This is a mixin for MainWindow
    def _create_menus(self) -> None:
        mb = self.menuBar()
    
        # ── File Menu ──
        file_menu = mb.addMenu("&File")
        act_exit = QAction(QIcon.fromTheme("application-exit"), "E&xit", self)
        act_exit.setShortcut(QKeySequence.Quit)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)
    
        # ── Edit Menu ──
        edit_menu = mb.addMenu("&Edit")
        act_clear_log = QAction(QIcon.fromTheme("edit-clear"), "Clear Event Log", self)
        act_clear_log.triggered.connect(lambda: self._log.clear())
        edit_menu.addAction(act_clear_log)
        act_reset_dsp = QAction(QIcon.fromTheme("view-refresh"), "Reset DSP History", self)
        act_reset_dsp.triggered.connect(lambda: self._dsp.reset())
        edit_menu.addAction(act_reset_dsp)
    
        # ── View Menu ──
        view_menu = mb.addMenu("&View")
        act_fullscreen = QAction(QIcon.fromTheme("view-fullscreen"), "Toggle Full Screen", self)
        act_fullscreen.setShortcut(QKeySequence(Qt.Key.Key_F11))
        act_fullscreen.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(act_fullscreen)
        view_menu.addSeparator()
    
        for title, widget in self._available_tabs:
            if title == "L1/L2 WIFI ANALYZER":
                act_open = QAction(f"Show {title.title()}", self)
                act_open.triggered.connect(
                    lambda checked=False, w=widget, t=title: self._show_tab(w, t)
                )
                view_menu.addAction(act_open)
                continue
    
            tab_menu = view_menu.addMenu(f"Show {title.title()}")
            act_open = QAction("Open Panel", self)
            act_open.triggered.connect(
                lambda checked=False, w=widget, t=title: self._show_tab(w, t)
            )
            tab_menu.addAction(act_open)
            tab_menu.addSeparator()
    
            if title == "DEFENSIVE / ANALYTICS":
                left_widget = self._left
                right_widget = self._right
            elif title == "OFFENSIVE / ATTACK":
                left_widget = self._attack_panel._left_container
                right_widget = self._attack_panel._right_container
            elif title == "MAN-IN-THE-MIDDLE":
                left_widget = self._mitm_panel._left_container
                right_widget = self._mitm_panel._right_container
            elif title == "NETWORK RECON / INTEL":
                left_widget = self._recon_panel._left_container
                right_widget = self._recon_panel._right_container
            else:  # DOCUMENTATION / AI
                left_widget = self._doc_panel._left_container
                right_widget = self._doc_panel._right_container
    
            act_left = QAction("Show Left Panel", self)
            act_left.setCheckable(True)
            act_left.setChecked(not left_widget.isHidden())
            act_left.toggled.connect(left_widget.setVisible)
            tab_menu.addAction(act_left)
    
            act_right = QAction("Show Right Panel", self)
            act_right.setCheckable(True)
            act_right.setChecked(not right_widget.isHidden())
            act_right.toggled.connect(right_widget.setVisible)
            tab_menu.addAction(act_right)
    
            if title == "DEFENSIVE / ANALYTICS":
                rp_menu = tab_menu.addMenu("Right Panel Elements")
                for i in range(self._right._tabs.count()):
                    tab_text = self._right._tabs.tabText(i)
                    act_rp = QAction(tab_text.title(), self)
                    act_rp.setCheckable(True)
                    act_rp.setChecked(self._right._tabs.isTabVisible(i))
                    act_rp.toggled.connect(
                        lambda checked, idx=i: self._right._tabs.setTabVisible(
                            idx, checked
                        )
                    )
                    rp_menu.addAction(act_rp)
    
                tab_menu.addSeparator()
                act_refresh = QAction("Refresh All Graphs", self)
                act_refresh.triggered.connect(self._refresh_all_graphs)
                tab_menu.addAction(act_refresh)
    
                act_payload = None
            elif title == "MAN-IN-THE-MIDDLE":
                rp_menu = None
                act_payload = QAction("Show HTTP Payload Config", self)
                act_payload.setCheckable(True)
                act_payload.setChecked(
                    not self._mitm_panel._payload_pane.isHidden()
                )
                act_payload.toggled.connect(
                    self._mitm_panel._payload_pane.setVisible
                )
                tab_menu.addAction(act_payload)
            else:
                rp_menu = None
                act_payload = None
    
            def _update_tab_menu(
                w=widget,
                a_l=act_left,
                a_r=act_right,
                l_w=left_widget,
                r_w=right_widget,
                rp=rp_menu,
                a_p=act_payload,
            ):
                is_open = self._tabs.indexOf(w) != -1
                a_l.setEnabled(is_open)
                a_r.setEnabled(is_open)
                a_l.setChecked(not l_w.isHidden())
                a_r.setChecked(not r_w.isHidden())
                if rp:
                    rp.setEnabled(is_open)
                if a_p:
                    is_http_selected = (
                        self._mitm_panel._config_pane.vector_combo.currentText()
                        == "HTTP INJECTOR (Visual)"
                    )
                    a_p.setEnabled(is_open and is_http_selected)
                    a_p.setChecked(not self._mitm_panel._payload_pane.isHidden())
    
            tab_menu.aboutToShow.connect(_update_tab_menu)
    
        view_menu.addSeparator()
        act_reset = QAction("Reset to Default", self)
        act_reset.triggered.connect(self._reset_tabs)
        view_menu.addAction(act_reset)
    
        # ── Tools Menu ──
        tools_menu = mb.addMenu("&Tools")
        act_arm = QAction(QIcon.fromTheme("media-record"), "Arm Console", self)
        act_arm.triggered.connect(
            lambda: (
                self._attack_panel._toggle_arm()
                if not self._attack_panel._armed
                else None
            )
        )
        tools_menu.addAction(act_arm)
        act_disarm = QAction(QIcon.fromTheme("media-playback-stop"), "Disarm Console", self)
        act_disarm.triggered.connect(
            lambda: (
                self._attack_panel._toggle_arm() if self._attack_panel._armed else None
            )
        )
        tools_menu.addAction(act_disarm)
    
        # ── Settings Menu ──
        settings_menu = mb.addMenu("&Settings")
        act_settings = QAction(QIcon.fromTheme("preferences-system"), "Open Settings...", self)
        act_settings.setShortcut(QKeySequence("Ctrl+,"))
        act_settings.triggered.connect(self._open_settings)
        settings_menu.addAction(act_settings)
    
        # ── Help Menu ──
        help_menu = mb.addMenu("&Help")
        act_about = QAction(QIcon.fromTheme("help-about"), "&About S.P.E.C.T.R.E.", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _show_tab(self, widget: QWidget, title: str) -> None:
        idx = self._tabs.indexOf(widget)
        if idx == -1:
            self._tabs.addTab(widget, title)
            idx = self._tabs.indexOf(widget)
        self._tabs.setCurrentIndex(idx)
        self._update_tab_visibility()
