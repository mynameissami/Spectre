# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/network_scanner.py — Active Network Scanner, OUI Lookup & OS Fingerprinting
"""

import ipaddress
from PySide6.QtCore import QThread, Signal

try:
    from scapy.all import ARP, Ether, srp, IP, ICMP, sr1, conf

    conf.verb = 0
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

from core.oui_database import get_vendor as local_oui_lookup

try:
    from mac_vendor_lookup import MacLookup

    mac_lib_lookup = MacLookup()
    MAC_LIB_AVAILABLE = True
except ImportError:
    MAC_LIB_AVAILABLE = False
from core.groq_vendor_lookup import GroqVendorLookup


def _guess_os(ttl: int) -> str:
    """Guesses OS based on standard initial TTL values."""
    if ttl <= 64:
        return "Linux/Android/macOS"
    elif ttl <= 128:
        return "Windows"
    elif ttl <= 255:
        return "Network Device/Router"
    return "Unknown"


def _lookup_vendor(mac_prefix: str, ai_lookup: GroqVendorLookup) -> str:
    mac_prefix = mac_prefix.upper()
    vendor = local_oui_lookup(mac_prefix)
    if vendor != "Unknown Device":
        return vendor
    if MAC_LIB_AVAILABLE:
        try:
            lib_vendor = mac_lib_lookup.lookup(mac_prefix)
            if lib_vendor and lib_vendor.lower() != "unknown":
                return lib_vendor
        except Exception:
            pass
    if ai_lookup.is_available():
        return ai_lookup.lookup_vendor(mac_prefix)
    return "Unknown Device"


class NetworkScanner(QThread):
    device_found = Signal(dict)  # {'ip': str, 'mac': str, 'vendor': str, 'os': str}
    scan_finished = Signal()
    log_signal = Signal(str, str)

    def __init__(self, subnet: str, parent=None):
        super().__init__(parent)
        self.subnet = subnet
        self._running = False
        self.ai_lookup = GroqVendorLookup()

    def run(self):
        if not SCAPY_AVAILABLE:
            self.log_signal.emit("CRITICAL: Scapy not installed.", "CRIT")
            self.scan_finished.emit()
            return

        self._running = True
        if "/" not in self.subnet:
            try:
                ip = ipaddress.ip_address(self.subnet)
                self.subnet = str(ipaddress.ip_network(f"{ip}/24", strict=False))
            except ValueError:
                self.log_signal.emit(f"Invalid subnet format: {self.subnet}", "CRIT")
                self.scan_finished.emit()
                return

        self.log_signal.emit(f"Starting ARP Sweep on {self.subnet}...", "INFO")

        try:
            ans, unans = srp(
                Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=self.subnet),
                timeout=3,
                verbose=0,
                inter=0.05,
            )

            for snd, rcv in ans:
                if not self._running:
                    break
                ip_addr = rcv[ARP].psrc
                mac_addr = rcv[ARP].hwsrc.upper()
                vendor = _lookup_vendor(mac_addr[:8], self.ai_lookup)

                # ─ OS Fingerprinting via ICMP Ping ──
                os_name = "Unknown"
                try:
                    # Send a quick ICMP ping to get the TTL
                    ping_reply = sr1(IP(dst=ip_addr) / ICMP(), timeout=1, verbose=0)
                    if ping_reply and ping_reply.haslayer(IP):
                        os_name = _guess_os(ping_reply[IP].ttl)
                except Exception:
                    pass  # Device might block ICMP, OS remains Unknown

                self.device_found.emit(
                    {"ip": ip_addr, "mac": mac_addr, "vendor": vendor, "os": os_name}
                )

        except Exception as e:
            self.log_signal.emit(f"Scan Error: {str(e)}", "CRIT")
        finally:
            self.scan_finished.emit()
            self.log_signal.emit("Scan complete.", "INFO")

    def stop(self):
        self._running = False
