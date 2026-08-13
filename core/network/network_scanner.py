# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/network_scanner.py — Hybrid Network Scanner (Scapy ARP + Nmap Deep Scan)
Licensed under AGPL-3.0 | Copyright (c) 2026 M. Sami Furqan
"""

import ipaddress
import asyncio
import re
from PySide6.QtCore import QThread, Signal

try:
    from scapy.all import ARP, Ether, srp, IP, ICMP, sr1, conf

    conf.verb = 0
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

try:
    import nmap

    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False

from core.oui import lookup as local_oui_lookup

try:
    from mac_vendor_lookup import MacLookup

    mac_lib_lookup = MacLookup()
    MAC_LIB_AVAILABLE = True
except ImportError:
    MAC_LIB_AVAILABLE = False

from core.ai.groq_vendor_lookup import GroqVendorLookup


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


def _nmap_deep_scan(ip_addr: str) -> tuple:
    """
    Uses Nmap to perform fast service version detection and OS fingerprinting.
    Returns (os_name, [(port, service_name, version), ...])
    """
    if not NMAP_AVAILABLE:
        return "Unknown", []

    try:
        nm = nmap.PortScanner()
        # -F: Fast mode (top 100 ports)
        # -sV: Service version detection
        # -O: OS detection
        # --osscan-guess: Aggressive OS guessing
        # -T4: Faster timing template
        nm.scan(ip_addr, arguments="-F -sV -O --osscan-guess -T4")

        host_data = nm[ip_addr]

        # 1. Extract OS
        os_name = "Unknown"
        if "osmatch" in host_data and host_data["osmatch"]:
            # Get the most accurate OS match (highest accuracy)
            os_name = host_data["osmatch"][0]["name"]
        elif "osclass" in host_data and host_data["osclass"]:
            os_name = host_data["osclass"][0]["osfamily"]

        # 2. Extract Ports and Services
        open_ports = []
        if "tcp" in host_data:
            for port, info in host_data["tcp"].items():
                if info["state"] == "open":
                    service = info["name"]
                    version = info.get("version", "")
                    product = info.get("product", "")

                    # Format: "HTTP (Apache 2.4.41)"
                    display_service = service.upper()
                    if product:
                        display_service = (
                            f"{display_service} ({product} {version})".strip()
                        )

                    open_ports.append((port, display_service))

        return os_name, sorted(open_ports)

    except Exception as e:
        print(f"[Nmap] Error scanning {ip_addr}: {e}")
        return "Unknown", []

async def _async_ping(ip: str) -> tuple[str, str]:
    """Returns (os_name, latency_str) based on ping TTL and time"""
    try:
        proc = await asyncio.create_subprocess_shell(
            f"ping -c 1 -W 1 {ip}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode()
        
        latency = "-"
        os_name = "Unknown"
        
        ttl_match = re.search(r"ttl=(\d+)", output, re.IGNORECASE)
        time_match = re.search(r"time=([\d.]+)\s*ms", output, re.IGNORECASE)
        
        if time_match:
            latency = f"{time_match.group(1)} ms"
            
        if ttl_match:
            ttl = int(ttl_match.group(1))
            if ttl <= 64:
                os_name = "Linux / macOS / Android"
            elif ttl <= 128:
                os_name = "Windows"
            else:
                os_name = "Cisco / Network Equip"
                
        return os_name, latency
    except Exception:
        return "Unknown", "-"


class NetworkScanner(QThread):
    device_found = Signal(dict)  # {'ip', 'mac', 'vendor', 'os'}
    ports_found = Signal(str, list)  # ip, [(port, service), ...]
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
        if NMAP_AVAILABLE:
            self.log_signal.emit(
                "Nmap engine loaded for deep service scanning.", "INFO"
            )

        try:
            # 1. Instant Local ARP Sweep (Layer 2)
            ans, unans = srp(
                Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=self.subnet),
                timeout=3,
                verbose=0,
                inter=0.05,
            )

            # 2. Process ARP Responses
            devices = []
            for snd, rcv in ans:
                if not self._running:
                    break

                ip_addr = rcv[ARP].psrc
                mac_addr = rcv[ARP].hwsrc.upper()
                vendor = _lookup_vendor(mac_addr[:8], self.ai_lookup)
                devices.append((ip_addr, mac_addr, vendor))

                # Emit device immediately so UI updates instantly
                self.device_found.emit(
                    {
                        "ip": ip_addr,
                        "mac": mac_addr,
                        "vendor": vendor,
                        "os": "Scanning...",
                        "latency": "..."
                    }
                )

            # 3. Async ICMP Ping Sweep (Latency & TTL OS Detection)
            self.log_signal.emit(f"Running ICMP Sweep for Latency & OS...", "INFO")
            
            async def ping_all():
                tasks = [_async_ping(d[0]) for d in devices]
                return await asyncio.gather(*tasks)
                
            ping_results = asyncio.run(ping_all())
            
            for (ip_addr, mac_addr, vendor), (os_name, latency) in zip(devices, ping_results):
                if not self._running:
                    break
                
                # If OS is Unknown from TTL, fallback to Nmap if available
                final_os = os_name
                if final_os == "Unknown" and NMAP_AVAILABLE:
                    self.log_signal.emit(f"Running Nmap deep scan on {ip_addr}...", "INFO")
                    nmap_os, open_ports = _nmap_deep_scan(ip_addr)
                    if nmap_os != "Unknown":
                        final_os = nmap_os
                    if open_ports:
                        self.ports_found.emit(ip_addr, open_ports)
                        self.log_signal.emit(f"Found {len(open_ports)} services on {ip_addr}", "INFO")
                
                self.device_found.emit(
                    {"ip": ip_addr, "mac": mac_addr, "vendor": vendor, "os": final_os, "latency": latency}
                )

        except Exception as e:
            self.log_signal.emit(f"Scan Error: {str(e)}", "CRIT")
        finally:
            self.scan_finished.emit()
            self.log_signal.emit("Scan complete.", "INFO")

    def stop(self):
        self._running = False
