#!/bin/bash

# ── Colors for Terminal Output ──
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=========================================${NC}"
echo -e "${GREEN}  S.P.E.C.T.R.E. Exhibition Setup Script ${NC}"
echo -e "${YELLOW}=========================================${NC}"

# 1. Fix X11 Permissions (Allows GUI to run with sudo)
echo -e "${GREEN}[1/4]${NC} Granting X11 permissions for GUI..."
xhost +local: >/dev/null 2>&1

# 2. Enable IP Forwarding (Crucial for MITM attacks to keep victim online)
echo -e "${GREEN}[2/4]${NC} Enabling IP Forwarding..."
sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1

# 3. Free Port 80 (Kills Apache/Nginx if they are blocking our Web Server)
echo -e "${GREEN}[3/4]${NC} Clearing Port 80 for Dynamic Web Server..."
fuser -k 80/tcp >/dev/null 2>&1 || true

# 4. Launch the Application via Virtual Environment
echo -e "${GREEN}[4/4]${NC} Launching S.P.E.C.T.R.E. Engine OS..."
echo -e "${YELLOW}-----------------------------------------${NC}"
sudo env XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR ./.venv/bin/python main.py
