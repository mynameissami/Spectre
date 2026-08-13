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

class MITMHandlerMixin:
    # This is a mixin for MainWindow
    @Slot(str, str, str, int, str)
    def _on_mitm_started(
        self,
        target: str,
        gateway: str,
        vector: str,
        intensity: int,
        block_target: str = "",
    ) -> None:
        is_passive = (
            "CREDENTIAL" in vector
            or "HARVEST" in vector
            or "PASSIVE" in vector
            or "INJECT" in vector
            or "HTTP" in vector
            or "RST" in vector
            or "BLOCK" in vector
            or "COOKIE" in vector
            or "SESSION" in vector
            or "JWT" in vector  # <--- ADD THIS
        )
    
        if is_passive:
            # ── FIX: Check RST/BLOCK *BEFORE* INJECT/HTTP ──
            if "RST" in vector or "BLOCK" in vector:
                passive_id = f"RST_Blocker_{len(self._passive_engines) + 1}"
            elif "INJECT" in vector or "HTTP" in vector:
                passive_id = f"Injector_{len(self._passive_engines) + 1}"
            elif "SESSION" in vector or "JWT" in vector:  # <--- ADD THIS
                passive_id = f"Cookie_Sniffer_{len(self._passive_engines) + 1}"
            else:
                passive_id = f"Harvester_{len(self._passive_engines) + 1}"
    
            # Pass block_target to the engine
            engine = MITMEngine(target, gateway, vector, intensity, block_target)
    
            engine.log_signal.connect(self._mitm_panel.log_message)
            if hasattr(engine, "passive_log_signal"):
                engine.passive_log_signal.connect(self._mitm_panel.log_passive)
            engine.packet_generated.connect(self._on_packet)
            engine.finished.connect(
                lambda pid=passive_id: self._cleanup_passive_engine(pid)
            )
    
            engine.start()
            self._passive_engines[passive_id] = engine
            self._mitm_panel.update_passive_dropdown(passive_id, is_adding=True)
            self._log.log(f"Passive Module Engaged: {passive_id} ({vector})", "EXEC")
    
            if "CREDENTIAL" in vector or "HARVEST" in vector:
                self._web_server.set_harvester_active(True)
            elif "INJECT" in vector or "HTTP" in vector:
                self._web_server.set_injector_active(True)
            elif "SESSION" in vector or "JWT" in vector:  # <--- ADD THIS
                self._web_server.set_session_test_active(True)
                return
    
        engine_key = "ARP" if "ARP" in vector else "DNS"
        if (
            engine_key in self._mitm_engines
            and self._mitm_engines[engine_key].isRunning()
        ):
            self._log.log(f"{vector} is already active.", "INFO")
            return
    
        engine = MITMEngine(target, gateway, vector, intensity)
        engine.log_signal.connect(self._mitm_panel.log_message)
        engine.packet_generated.connect(self._on_packet)
        engine.finished.connect(
            lambda key=engine_key: self._mitm_engines.pop(key, None)
        )
        engine.start()
        self._mitm_engines[engine_key] = engine
        self._log.log(f"MITM Module Engaged: {vector}", "EXEC")

    @Slot()
    def _on_mitm_stopped(self) -> None:
        for key, engine in list(self._mitm_engines.items()):
            if engine.isRunning():
                engine.stop()
        self._mitm_engines.clear()
        for pid, engine in list(self._passive_engines.items()):
            if engine.isRunning():
                engine.stop()
        self._passive_engines.clear()
        self._mitm_panel.update_passive_dropdown("DUMMY_ID", is_adding=False)
        self._mitm_panel.reset_passive_button()
        self._web_server.set_harvester_active(False)
        self._web_server.set_injector_active(False)

    @Slot(str, str)
    def _on_payload_updated(self, payload_type: str, custom_script: str) -> None:
        from core.web_server import get_local_ip
        attacker_ip = get_local_ip()
        if self._mitm_engines:
            attacker_ip = list(self._mitm_engines.values())[0].attacker_ip
        elif self._passive_engines:
            attacker_ip = list(self._passive_engines.values())[0].attacker_ip
        self._web_server.set_injector_payload(payload_type, custom_script, attacker_ip)
        for pid, engine in self._passive_engines.items():
            if "Injector" in pid and engine.isRunning():
                engine.set_payload(payload_type, custom_script)

    @Slot(str)
    def _on_terminate_passive_selected(self, passive_id: str) -> None:
        if passive_id in self._passive_engines:
            engine = self._passive_engines[passive_id]
            engine.stop()
            del self._passive_engines[passive_id]
            self._mitm_panel.update_passive_dropdown(passive_id, is_adding=False)
            self._log.log(f"Passive Module Halted: {passive_id}", "INFO")
            if not self._passive_engines:
                self._web_server.set_harvester_active(False)
                self._web_server.set_injector_active(False)
                self._mitm_panel.reset_passive_button()

    @Slot()
    def _on_terminate_all_passive(self) -> None:
        for pid, engine in list(self._passive_engines.items()):
            engine.stop()
        self._passive_engines.clear()
        self._mitm_panel._controls_pane.passive_dropdown.clear()
        self._mitm_panel._controls_pane.passive_dropdown.addItem("No Passive Modules Active")
        self._mitm_panel._controls_pane.passive_dropdown.setEnabled(False)
        self._mitm_panel._controls_pane.terminate_selected_passive_btn.setEnabled(False)
        self._mitm_panel._controls_pane.terminate_all_passive_btn.setEnabled(False)
        self._web_server.set_harvester_active(False)
        self._web_server.set_injector_active(False)
        self._web_server.set_session_test_active(False)
        self._mitm_panel.reset_passive_button()
