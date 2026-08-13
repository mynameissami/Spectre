# Cross-Platform Notes

S.P.E.C.T.R.E. is built with PySide6 (Qt) and Python, making it inherently cross-platform. However, some features depend on OS-level networking capabilities, specifically raw sockets for Scapy-based attacks.

---

## Compatibility Matrix

| Feature | Linux | macOS | Windows |
|---|:---:|:---:|:---:|
| GUI (all panels, themes, settings) | ✅ | ✅ | ✅ |
| ESP32 Hardware Mode (serial) | ✅ | ✅ | ✅ |
| Demo / Simulator Mode | ✅ | ✅ | ✅ |
| AI Assistant (Groq API) | ✅ | ✅ | ✅ |
| Scapy Attacks (ARP, DNS, L2) | ✅ | ✅ | ✅ ¹ |
| MITM (ARP/DNS Spoofing) | ✅ | ✅ | ✅ ¹ |
| Network Scanner (ARP discovery) | ✅ | ✅ | ✅ ¹ |
| Splash Video (FFmpeg backend) | ✅ | ✅ | ✅ ² |

---

## 1. Windows Specifics

Windows does not natively expose raw sockets to Python the way Linux does.

### Npcap Installation (Required for Scapy)
To use any MITM or Network Scanning features on Windows, you **MUST** install Npcap:
1. Download from [npcap.com](https://npcap.com/)
2. During installation, **check** the box: *"Install Npcap in WinPcap API-compatible mode"*
3. Restart your terminal after installation

*(Npcap is often installed alongside Wireshark. If you already have Wireshark installed with WinPcap compatibility, you're good to go).*

### Launching on Windows
You must run S.P.E.C.T.R.E. as an Administrator:
1. Open an **Administrator Command Prompt** or PowerShell
2. Activate your virtual environment: `.venv\Scripts\activate.bat`
3. Run: `python main.py`

---

## 2. macOS Specifics

macOS is extremely strict with BPF (Berkeley Packet Filter) devices.

### BPF Permissions
To run Scapy network features (MITM, network scanning, L2/L3 attacks), you must run the tool as `root`:

```bash
sudo ./.venv/bin/python main.py
```

---

## 3. Linux Specifics

Linux is the native environment for S.P.E.C.T.R.E. and provides the best experience for raw socket access.

### Launching on Linux
Run with `sudo` for raw socket access:
```bash
sudo ./.venv/bin/python main.py
```

### X11 / Wayland GUI Issues as Root
Sometimes running a GUI app with `sudo` on Linux fails because the root user doesn't have access to your X11/Wayland display server.

If you get a `qt.qpa.xcb: could not connect to display` error, you can use the `setup_demo.sh` script (or set the env vars manually):

```bash
sudo env XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR ./.venv/bin/python main.py
```

---

## 4. Hardware Mode (Cross-Platform Advantage)

The major advantage of S.P.E.C.T.R.E. is that **802.11 monitor mode and injection are offloaded to the ESP32 via Serial**.

Because PySerial works perfectly on all platforms:
- You **do not** need special Wi-Fi drivers on Windows/macOS.
- You **do not** need a compatible monitor-mode USB Wi-Fi adapter.
- Features like the Wi-Fi Analyzer, Sonar Mode, Deauth floods, and Beacon spam work flawlessly on Windows, Mac, and Linux without any OS hacking.

---

**See also:** [[Installation]] · [[Getting Started]]
