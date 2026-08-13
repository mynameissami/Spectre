# Troubleshooting

Here are solutions to common issues you might encounter while using S.P.E.C.T.R.E.

---

## 🖥️ GUI & Display Issues

### `qt.qpa.xcb: could not connect to display` (Linux)
**Issue:** You ran `sudo python main.py` and the app crashed instantly.
**Cause:** The root user doesn't have permission to access your X11/Wayland display server.
**Solution:**
Use the provided launch script which passes your `XDG_RUNTIME_DIR` to the root environment:
```bash
sudo env XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR ./.venv/bin/python main.py
```

### Splash Video Doesn't Play / Black Screen
**Issue:** The app launches but the intro video is just a black screen or throws FFmpeg errors in the console.
**Cause:** Missing multimedia codecs for PySide6 in your OS.
**Solution:**
This is harmless and doesn't affect functionality. You can safely ignore it, or install the OS multimedia plugins:
- Ubuntu/Debian: `sudo apt install ffmpeg gstreamer1.0-libav`
- Windows: Usually works out of the box, or install K-Lite Codec Pack.

---

## 📡 Hardware & Serial Issues

### `Serial error: could not open port /dev/ttyUSB0: [Errno 13] Permission denied`
**Issue:** Cannot connect to the ESP32 on Linux.
**Cause:** Your user is not in the `dialout` group.
**Solution:**
Run the app as root (`sudo`), OR add your user to the dialout group:
```bash
sudo usermod -a -G dialout $USER
```
Then log out and back in.

### Serial Stream Connects but Shows No Data
**Issue:** You clicked "CONNECT", the banner turned green, but no Wi-Fi data appears.
**Cause:** The ESP32 is not in `STREAMING` mode.
**Solution:**
1. Check the physical TFT screen on the ESP32.
2. Use the physical `UP` or `DOWN` buttons to navigate.
3. Press `SELECT` to lock onto a target or return to scanning. Ensure the serial baud rate matches `115200`.

### ESP32 Keeps Restarting (Brown-out)
**Issue:** When starting an RF attack (Deauth/Beacon), the ESP32 screen flashes white and the serial connection drops.
**Cause:** Voltage drop (brown-out). The RF amplifier draws peak current when injecting packets.
**Solution:**
Place a `10µF` to `100µF` capacitor between the `3V3` and `GND` pins on the ESP32 to smooth out power spikes.

---

## 🌐 Network & MITM Issues

### `CRITICAL: Scapy not installed.`
**Issue:** Network attacks and MITM features are disabled.
**Solution:**
```bash
pip install scapy
```
*(Windows users must also install [Npcap](https://npcap.com/) in WinPcap compatible mode).*

### DNS Spoofing / MITM Doesn't Work on Windows
**Issue:** You engage MITM but no traffic is intercepted, or you get socket errors.
**Cause:** Npcap is missing, or you aren't running as Administrator.
**Solution:**
1. Install Npcap with "WinPcap API-compatible mode".
2. Open an Administrator Command Prompt.
3. Run `python main.py` from the elevated prompt.

### Web Server Fails to Start (Port 80 In Use)
**Issue:** `[WebServer] ❌ CRITICAL: Could not start server on port 80.`
**Cause:** Another service (like Apache, Nginx, or Skype) is already using port 80.
**Solution:**
Identify and stop the conflicting service:
```bash
sudo lsof -i :80
# Kill the PID using port 80
sudo kill -9 <PID>
```

---

## 🤖 AI Assistant Issues

### `Groq API Error` or Assistant Won't Respond
**Issue:** The AI assistant tab shows an error when you ask a question.
**Cause:** Missing or invalid API key.
**Solution:**
1. Ensure you have a `.env` file in the root directory: `GROQ_API_KEY="your_key"`
2. Verify you have an active internet connection.
3. Check your quota on the Groq Console.
