# MITM Guide

The Man-In-The-Middle module provides active and passive network interception capabilities for authorized security testing.

> ⚠️ **All MITM features require root/administrator privileges and Scapy.**

---

## Overview

The MITM panel is divided into three main areas:

1. **Configuration Pane** — Set target IP, gateway IP, block targets, and attack vectors
2. **Controls Pane** — Engage/disengage attacks, manage passive modules
3. **Log Pane** — Dual-pane real-time logging (Active events + Passive/harvested data)

---

## Active Vectors

### ARP Spoofing (Cache Poisoning)

Poisons the ARP cache of a target device and the gateway, placing your machine in between.

**How it works:**
1. S.P.E.C.T.R.E. sends forged ARP replies to both the target and the gateway
2. The target believes your MAC address belongs to the gateway
3. The gateway believes your MAC address belongs to the target
4. All traffic flows through your machine

**Configuration:**
- **Target IP** — The victim's IP address
- **Gateway IP** — The router's IP address
- **Intensity** — Controls the rate of ARP reply packets

### DNS Spoofing (Redirection)

Intercepts DNS queries and returns forged responses pointing to your machine.

**How it works:**
1. S.P.E.C.T.R.E. listens for UDP port 53 traffic
2. When a DNS query is detected, it forges a response with your machine's IP
3. The victim's browser loads pages from the S.P.E.C.T.R.E. web server instead

**Configuration:**
- **Block Target** — Optionally specify a domain or IP to selectively intercept
- The Dynamic Web Server automatically starts on port 80

---

## Passive Modules

### Credential Harvester

Captures HTTP credentials from intercepted traffic:

1. The built-in web server serves a realistic login page (`mitm_demo_site/login.html`)
2. When a victim submits credentials, they are captured and displayed in the passive log
3. Harvested data is separated from active alerts in the dual-pane log view

### Payload Injector

Injects JavaScript payloads into intercepted HTTP responses:

| Payload Type | Description |
|---|---|
| **Black/Green Screen (Default)** | Sets body to black background with green text + alert |
| **Simple Alert Box** | Shows a JavaScript alert dialog |
| **Page Redirect** | Redirects victim to the attacker's IP |
| **Custom Payload** | Inject any arbitrary JavaScript/HTML |

The custom payload editor accepts raw HTML/JavaScript that gets injected before the `</body>` tag.

### Session Hijacking Test

Demonstrates cookie theft and session replay in a controlled environment using the `mitm_demo_site/session_test.html` page.

---

## How DNS Spoofing + Credential Harvesting Works (Step-by-Step)

1. Navigate to the **MAN-IN-THE-MIDDLE** tab
2. Enter the **Target IP** and **Gateway IP**
3. Select **DNS SPOOFING (Redirection)** as the attack vector
4. Click **ENGAGE** — this starts ARP poisoning + DNS interception
5. Enable the **CREDENTIAL HARVESTER** passive module
6. S.P.E.C.T.R.E. starts the `DynamicWebServer` on `0.0.0.0:80`
7. The `MITMEngine` intercepts UDP port 53 queries
8. When the victim requests any website, S.P.E.C.T.R.E. responds with your machine's IP (auto-detected at runtime)
9. The victim's browser loads the fake login page
10. Submitted credentials appear in the Passive Log pane

---

## Dynamic Web Server

The built-in HTTP server (`core/web_server.py`) dynamically serves different pages based on the active MITM mode:

| Mode | Page Served |
|---|---|
| No MITM active | `mitm_demo_site/index.html` |
| Harvester active | `mitm_demo_site/login.html` |
| Injector active | `mitm_demo_site/index.html` + injected payload |
| Session test active | `mitm_demo_site/session_test.html` |

The server binds to `0.0.0.0:80` and auto-detects the local IP address at runtime.

---

## MITM Controls Reference

| Button | Function |
|---|---|
| **ENGAGE** | Start the selected active attack vector |
| **DISENGAGE** | Stop all active attacks |
| **Passive Module Dropdown** | Select and start a passive module |
| **TERMINATE** | Stop a specific passive module |
| **TERMINATE ALL** | Stop all running passive modules |

---

**See also:** [[Attack Vectors]] · [[Features Overview]]
