# Installation

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | Required |
| pip | Latest | Comes with Python |
| git | Any | For cloning the repo |
| Npcap | Latest | **Windows only** — required for Scapy raw sockets |

## 1. Clone the Repository

```bash
git clone https://github.com/mynameissami/Spectre.git
cd Spectre
```

## 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

| OS | Command |
|---|---|
| **Linux / macOS** | `source .venv/bin/activate` |
| **Windows (cmd)** | `.venv\Scripts\activate.bat` |
| **Windows (PowerShell)** | `.venv\Scripts\Activate.ps1` |

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:

| Package | Purpose |
|---|---|
| `PySide6` | Qt6 GUI framework |
| `pyqtgraph` | High-performance plotting |
| `numpy` | Signal processing & DSP |
| `pyserial` | ESP32 serial communication |
| `scapy` | Raw packet crafting (L2/L3 attacks, MITM) |
| `groq` | AI Assistant API client |
| `python-dotenv` | `.env` file loading |

## 4. API Key (Optional)

If you want the AI Assistant module, create a `.env` file in the project root:

```env
GROQ_API_KEY="your_api_key_here"
```

Get a free API key at [console.groq.com](https://console.groq.com/).

## 5. Windows-Specific: Install Npcap

Scapy requires Npcap on Windows for raw socket access:

1. Download from [npcap.com](https://npcap.com/)
2. During installation, **check** the box: *"Install Npcap in WinPcap API-compatible mode"*
3. Restart your terminal after installation

Without Npcap, the GUI will still launch and Demo mode will work, but MITM, network scanning, and L2/L3 attacks will be unavailable.

## 6. macOS-Specific: BPF Permissions

macOS restricts Berkeley Packet Filter (BPF) devices. You must run with `sudo` for any Scapy-based features (MITM, network scanning, attacks):

```bash
sudo ./.venv/bin/python main.py
```

---

**Next:** [[Getting Started]]
