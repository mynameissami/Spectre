# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/recon_panel.py — Network Reconnaissance & Intel Panel (Phase 4)
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QLineEdit,
    QHeaderView,
    QSplitter,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from ui.topology_map import TopologyMap
import config


class ReconPanel(QWidget):
    port_scan_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        hdr = QLabel("[ NETWORK RECONNAISSANCE & INTEL ]")
        hdr.setObjectName("section_header")
        hdr.setStyleSheet(
            f"color: {config.COLOR_ACCENT_CYAN}; border-bottom: 2px solid {config.COLOR_ACCENT_CYAN}; font-size: 13px; padding-bottom: 4px;"
        )
        layout.addWidget(hdr)

        ctrl_frame = QFrame()
        ctrl_frame.setObjectName("panel")
        ctrl_layout = QVBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(12, 8, 12, 8)
        ctrl_layout.setSpacing(6)

        ctrl_row = QHBoxLayout()
        
        subnet_lbl = QLabel("SUBNET:")
        subnet_lbl.setObjectName("status_key")
        ctrl_row.addWidget(subnet_lbl)

        self._subnet_input = QLineEdit()
        # Auto-detect local subnet
        default_subnet = "192.168.1.0/24"
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            parts = local_ip.split('.')
            default_subnet = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        except Exception:
            pass

        self._subnet_input.setText(default_subnet)
        self._subnet_input.setStyleSheet(
            f"background-color: #08080C; border: 1px solid {config.COLOR_BORDER}; padding: 6px; color: {config.COLOR_TEXT_PRIMARY}; border-radius: 3px;"
        )
        ctrl_row.addWidget(self._subnet_input, stretch=2)

        self._scan_btn = QPushButton("START NETWORK SCAN")
        self._scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._scan_btn.setStyleSheet(
            f"color: {config.COLOR_ACCENT_CYAN}; border-color: {config.COLOR_ACCENT_CYAN}; padding: 8px 15px; font-size: 11px; font-weight: bold;"
        )
        ctrl_row.addWidget(self._scan_btn)

        self._port_scan_btn = QPushButton("SCAN PORTS (SELECTED)")
        self._port_scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._port_scan_btn.setEnabled(False)
        self._port_scan_btn.setStyleSheet(f"""
            QPushButton {{ color: {config.COLOR_ACCENT_ORANGE}; border-color: {config.COLOR_ACCENT_ORANGE}; padding: 8px 15px; font-size: 11px; font-weight: bold; }}
            QPushButton:disabled {{ color: {config.COLOR_TEXT_DIM}; border-color: {config.COLOR_BORDER}; }}
        """)
        self._port_scan_btn.clicked.connect(self._on_port_scan_clicked)
        ctrl_row.addWidget(self._port_scan_btn)

        ctrl_row.addSpacing(20)

        self._status_lbl = QLabel("STATUS: IDLE")
        self._status_lbl.setStyleSheet(f"color: {config.COLOR_TEXT_DIM}; font-weight: bold; font-size: 11px;")
        ctrl_row.addWidget(self._status_lbl)

        ctrl_layout.addLayout(ctrl_row)
        layout.addWidget(ctrl_frame)

        # Splitter for Tree and Map
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(4)
        main_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {config.COLOR_BORDER};
                width: 2px;
            }}
        """)

        # Tree Widget (Left)
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.setSpacing(4)

        tree_hdr = QLabel("[ DEVICE LIST ]")
        tree_hdr.setStyleSheet(
            f"color: {config.COLOR_ACCENT_CYAN}; font-weight: bold; font-size: 11px;"
        )
        tree_layout.addWidget(tree_hdr)

        self._tree = QTreeWidget()
        self._tree.setColumnCount(6)
        self._tree.setHeaderLabels(
            ["IP ADDRESS", "MAC ADDRESS", "VENDOR", "OS", "STATUS", "PORTS"]
        )
        self._tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tree.setStyleSheet(f"""
            QTreeWidget {{ 
                background-color: {config.COLOR_BG_PANEL}; 
                color: {config.COLOR_TEXT_PRIMARY}; 
                border: 1px solid {config.COLOR_BORDER}; 
                border-radius: 4px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px;
                border-bottom: 1px solid #151520;
            }}
            QTreeWidget::item:selected {{
                background-color: #1A1A2E;
                color: {config.COLOR_ACCENT_CYAN};
            }}
            QHeaderView::section {{ 
                background-color: #0A0A0F; 
                color: {config.COLOR_ACCENT_CYAN}; 
                padding: 6px; 
                border: none; 
                border-bottom: 1px solid {config.COLOR_BORDER};
                font-weight: bold;
                font-size: 10px;
            }}
        """)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)
        tree_layout.addWidget(self._tree)
        main_splitter.addWidget(tree_container)

        # Topology Map (Right)
        map_container = QWidget()
        map_layout = QVBoxLayout(map_container)
        map_layout.setContentsMargins(12, 0, 0, 0)
        map_layout.setSpacing(4)

        map_hdr = QLabel("[ NETWORK TOPOLOGY ]")
        map_hdr.setStyleSheet(
            f"color: {config.COLOR_ACCENT_GREEN}; font-weight: bold; font-size: 11px;"
        )
        map_layout.addWidget(map_hdr)

        self._topology_map = TopologyMap()
        self._topology_map.setMinimumWidth(250)
        map_layout.addWidget(self._topology_map)
        main_splitter.addWidget(map_container)

        main_splitter.setStretchFactor(0, 6)
        main_splitter.setStretchFactor(1, 4)

        self._left_container = tree_container
        self._right_container = map_container

        layout.addWidget(main_splitter, stretch=1)

    def _on_selection_changed(self):
        selected = self._tree.selectedItems()
        self._port_scan_btn.setEnabled(selected and selected[0].parent() is None)

    def _on_port_scan_clicked(self):
        selected = self._tree.selectedItems()
        if selected and selected[0].parent() is None:
            self.port_scan_requested.emit(selected[0].text(0))

    def add_device(self, ip: str, mac: str, vendor: str, os_name: str = "Unknown"):
        # Check if IP already exists
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item.text(0) == ip:
                item.setText(1, mac)
                item.setText(2, vendor)
                item.setText(3, os_name)
                return

        item = QTreeWidgetItem(self._tree)
        item.setText(0, ip)
        item.setText(1, mac)
        item.setText(2, vendor)
        item.setText(3, os_name)
        item.setText(4, "ONLINE")
        item.setText(5, "0")
        item.setForeground(4, Qt.GlobalColor.green)

        # Add to Topology Map
        is_gateway = ip.endswith(".1")  # Simple heuristic for gateway
        self._topology_map.add_device(ip, os_name, is_gateway)

    def add_open_port(self, ip: str, port: int, service: str):
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item.text(0) == ip:
                child = QTreeWidgetItem(item)
                child.setText(2, f"Port {port}")
                child.setText(3, service)
                child.setText(4, "OPEN")
                child.setForeground(4, Qt.GlobalColor.green)
                current_count = int(item.text(5)) if item.text(5).isdigit() else 0
                item.setText(5, str(current_count + 1))
                item.setExpanded(True)
                return

    def clear_tree(self):
        self._tree.clear()
        self._topology_map.clear_map()

    def set_status(self, text: str):
        self._status_lbl.setText(f"STATUS: {text.upper()}")
