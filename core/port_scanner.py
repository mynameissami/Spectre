# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/port_scanner.py — Multi-threaded TCP Port & Service Scanner
"""

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from PySide6.QtCore import QThread, Signal

# Top 50 most common ports to scan for speed and relevance
COMMON_PORTS = [
    21,
    22,
    23,
    25,
    53,
    69,
    80,
    110,
    111,
    135,
    139,
    143,
    443,
    445,
    993,
    995,
    1723,
    3306,
    3389,
    5432,
    5900,
    8080,
    8443,
    8888,
    9090,
]

# Simple service mapping
SERVICE_MAP = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    69: "TFTP",
    80: "HTTP",
    110: "POP3",
    111: "RPC",
    135: "MSRPC",
    139: "NetBIOS",
    143: "IMAP",
    443: "HTTPS",
    445: "SMB",
    993: "IMAPS",
    995: "POP3S",
    1723: "PPTP",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    8080: "HTTP-Proxy",
    8443: "HTTPS-Alt",
    8888: "HTTP-Alt",
    9090: "Web-Console",
}


class PortScanner(QThread):
    port_found = Signal(int, str)  # port, service_name
    scan_finished = Signal()
    log_signal = Signal(str, str)

    def __init__(self, target_ip: str, ports: list = None, parent=None):
        super().__init__(parent)
        self.target_ip = target_ip
        self.ports = ports or COMMON_PORTS
        self._running = False

    def run(self):
        self._running = True
        self.log_signal.emit(f"Starting TCP Port Scan on {self.target_ip}...", "INFO")

        open_ports = []

        # Use ThreadPoolExecutor for fast, concurrent scanning
        with ThreadPoolExecutor(max_workers=50) as executor:
            # Submit all port checks
            future_to_port = {
                executor.submit(self._check_port, port): port for port in self.ports
            }

            for future in as_completed(future_to_port):
                if not self._running:
                    break
                port = future_to_port[future]
                try:
                    is_open = future.result()
                    if is_open:
                        service = SERVICE_MAP.get(port, "Unknown")
                        open_ports.append(port)
                        self.port_found.emit(port, service)
                except Exception:
                    pass

        self.log_signal.emit(
            f"Scan complete. Found {len(open_ports)} open ports.", "INFO"
        )
        self.scan_finished.emit()

    def _check_port(self, port: int) -> bool:
        """Attempts a TCP connect to the port. Returns True if open."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)  # 1 second timeout per port
        try:
            result = sock.connect_ex((self.target_ip, port))
            return result == 0
        except Exception:
            return False
        finally:
            sock.close()

    def stop(self):
        self._running = False
