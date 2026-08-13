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

class ConnectionHandlerMixin:
    # This is a mixin for MainWindow
        def _start_recon_scan(self):
            subnet = self._recon_panel._subnet_input.text().strip()
            if not subnet:
                self._log.log("Invalid subnet.", "CRIT")
                return
    
            if self._scanner_thread and self._scanner_thread.isRunning():
                self._log.log("Scan already in progress.", "WARN")
                return
    
            self._recon_panel.clear_tree()  # Changed from _clear_table
            self._recon_panel.set_status("Scanning...")
            self._log.log(f"Starting Network Recon on {subnet}", "EXEC")
    
            self._scanner_thread = NetworkScanner(subnet)
            self._scanner_thread.device_found.connect(
                lambda d: self._recon_panel.add_device(
                    d["ip"], d["mac"], d["vendor"], d.get("os", "Unknown"), d.get("latency", "-")
                )
            )
            self._scanner_thread.scan_finished.connect(self._on_scan_finished)
            self._scanner_thread.log_signal.connect(self._log.log)
            self._scanner_thread.start()

        def _start_port_scan(self, target_ip: str):
            """Starts a port scan on the specified device IP."""
            try:
                if not target_ip:
                    self._log.log("Port scan failed: No IP provided.", "CRIT")
                    return
    
                if self._port_scanner_thread and self._port_scanner_thread.isRunning():
                    self._log.log("Port scan already in progress.", "WARN")
                    return
    
                self._recon_panel.set_status(f"Scanning ports on {target_ip}...")
                self._log.log(f"Starting TCP Port Scan on {target_ip}", "EXEC")
    
                # Find the tree item and clear existing ports
                for i in range(self._recon_panel._tree.topLevelItemCount()):
                    item = self._recon_panel._tree.topLevelItem(i)
                    if item.text(0) == target_ip:
                        item.takeChildren()
                        item.setText(4, "0")
                        break
    
                # Initialize and start the scanner
                self._port_scanner_thread = PortScanner(target_ip)
                self._port_scanner_thread.port_found.connect(
                    lambda port, service: self._recon_panel.add_open_port(
                        target_ip, port, service
                    )
                )
                self._port_scanner_thread.scan_finished.connect(self._on_port_scan_finished)
                self._port_scanner_thread.log_signal.connect(self._log.log)
                self._port_scanner_thread.start()
    
            except Exception as e:
                self._log.log(f"Port scan failed to start: {str(e)}", "CRIT")
