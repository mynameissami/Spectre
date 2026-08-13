# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/wifi_scanner.py — Layer 1/2 Wi-Fi Analyzer Scanner
Uses `iw` for native Linux scanning, with a robust exhibition simulation fallback.
"""

import time
import subprocess
import re
import random
from typing import Dict, List, Any
from PySide6.QtCore import QThread, Signal
from core.oui import lookup as get_vendor

def freq_to_channel(freq: int) -> int:
    """Convert Frequency (MHz) to Channel number."""
    if freq == 2484:
        return 14
    elif 2412 <= freq <= 2472:
        return int((freq - 2407) / 5)
    elif 5170 <= freq <= 5825:
        return int((freq - 5000) / 5)
    elif 5955 <= freq <= 7115:
        return int((freq - 5950) / 5)
    return 0

class WiFiScanner(QThread):
    """
    Background thread that scans for ambient WiFi networks.
    Emits scan_results_ready(list[dict]) every few seconds.
    """
    scan_results_ready = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = True
        self._is_paused = False
        self._interface = self._get_default_interface()
        self._use_simulation = not bool(self._interface)
        
        # Simulation state
        self._simulated_aps = self._generate_simulated_aps()

    def stop(self):
        self._is_running = False
        self.wait()

    def set_paused(self, paused: bool):
        self._is_paused = paused

    def run(self):
        import asyncio
        asyncio.run(self._async_run())

    async def _async_run(self):
        import asyncio
        while self._is_running:
            if not self._is_paused:
                if self._use_simulation:
                    results = self._simulate_scan()
                else:
                    loop = asyncio.get_running_loop()
                    # Run blocking iw_scan in an executor so it doesn't block the loop
                    results = await loop.run_in_executor(None, self._iw_scan)
                    if not results:  # Fallback if iw fails (e.g. no root)
                        self._use_simulation = True
                        results = self._simulate_scan()
                self.scan_results_ready.emit(results)
            await asyncio.sleep(0.5)

    def _get_default_interface(self) -> str:
        try:
            out = subprocess.check_output(['iw', 'dev'], stderr=subprocess.DEVNULL).decode()
            match = re.search(r'Interface\s+([a-zA-Z0-9_]+)', out)
            if match:
                return match.group(1)
        except Exception:
            pass
        return ""

    def _iw_scan(self) -> List[Dict[str, Any]]:
        results = []
        try:
            # Requires root. If run without root, will likely return empty/fail.
            out = subprocess.check_output(['sudo', '-n', 'iw', 'dev', self._interface, 'scan'], stderr=subprocess.DEVNULL).decode()
            
            # Parsing iw scan output
            networks = out.split('BSS ')
            for network in networks[1:]:
                ap = {}
                bssid_match = re.search(r'^([0-9a-fA-F:]{17})', network)
                if not bssid_match:
                    continue
                ap['bssid'] = bssid_match.group(1).upper()
                
                ssid_match = re.search(r'SSID:\s*(.*)', network)
                ap['ssid'] = ssid_match.group(1).strip() if ssid_match else "<hidden>"
                
                freq_match = re.search(r'freq:\s*(\d+)', network)
                ap['freq'] = int(freq_match.group(1)) if freq_match else 2412
                ap['channel'] = freq_to_channel(ap['freq'])
                
                sig_match = re.search(r'signal:\s*([-0-9.]+)\s*dBm', network)
                ap['rssi'] = float(sig_match.group(1)) if sig_match else -90.0
                
                # Basic security parsing
                if "WPA" in network or "RSN" in network:
                    ap['security'] = "WPA2/WPA3"
                elif "WEP" in network:
                    ap['security'] = "WEP"
                else:
                    ap['security'] = "Open"
                
                ap['vendor'] = get_vendor(ap['bssid'])
                ap['width'] = 20  # Default fallback
                if "VHT Operation" in network or "HT operation" in network:
                    if "channel width: 1" in network: ap['width'] = 40
                    elif "channel width: 2" in network: ap['width'] = 80
                    elif "channel width: 3" in network: ap['width'] = 160

                results.append(ap)
        except Exception:
            pass
        return results

    def _generate_simulated_aps(self) -> List[Dict[str, Any]]:
        """Generate realistic static AP data for exhibition simulation."""
        vendors = ["00:1A:11", "00:14:22", "00:25:9C", "F8:1A:67", "C0:C1:C0"]
        ssids = ["Corporate_Guest", "Lab_5G", "IOT_Network", "SPECTRE_LOCAL", "DIRECT-ROKU", "Home_WiFi", "Starbucks WiFi", "Xfinity_WiFi"]
        aps = []
        for i in range(12):
            freq = random.choice([2412, 2437, 2462, 5180, 5220, 5745])
            bssid = f"{random.choice(vendors)}:{random.randint(10,99):02X}:{random.randint(10,99):02X}:{random.randint(10,99):02X}"
            aps.append({
                "bssid": bssid,
                "ssid": random.choice(ssids) + f"_{i}",
                "freq": freq,
                "channel": freq_to_channel(freq),
                "rssi": random.uniform(-85, -35),
                "security": random.choice(["WPA2/WPA3", "Open", "WPA3-SAE"]),
                "vendor": get_vendor(bssid),
                "width": random.choice([20, 40, 80]),
                "base_rssi": random.uniform(-80, -40)
            })
        return aps

    def _simulate_scan(self) -> List[Dict[str, Any]]:
        """Add slight noise to the RSSI of simulated APs to make charts dynamic."""
        results = []
        for ap in self._simulated_aps:
            ap_copy = ap.copy()
            # Random walk the RSSI
            ap["base_rssi"] += random.uniform(-2.0, 2.0)
            ap["base_rssi"] = max(-95, min(-20, ap["base_rssi"]))
            ap_copy["rssi"] = round(ap["base_rssi"], 1)
            results.append(ap_copy)
        return results
