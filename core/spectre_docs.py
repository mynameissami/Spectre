# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/spectre_docs.py — Comprehensive Technical Documentation for S.P.E.C.T.R.E. Engine
Designed for Exhibition Presentation and AI Context Injection.
"""

SPECTRE_DOCUMENTATION = """
<html>
<head>
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #E0E0E0; }
    h1 { color: #00FF41; border-bottom: 2px solid #00FF41; padding-bottom: 10px; font-size: 28px; }
    h2 { color: #00BFFF; border-left: 4px solid #00BFFF; padding-left: 10px; margin-top: 30px; font-size: 20px; }
    h3 { color: #FFD700; margin-top: 20px; font-size: 16px; }
    p { margin-bottom: 12px; color: #C0C0C0; }
    ul, ol { margin-bottom: 15px; padding-left: 25px; }
    li { margin-bottom: 6px; color: #D0D0D0; }
    code { background-color: #1A1A2E; color: #00FF41; padding: 2px 6px; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 13px; }
    blockquote { background-color: #0A0A0F; border-left: 4px solid #FF4500; margin: 15px 0; padding: 10px 15px; color: #A0A0A0; font-style: italic; }
    .highlight { color: #FF4500; font-weight: bold; }
    .tech-spec { background-color: #0F0F1A; border: 1px solid #1A1A2E; padding: 10px; border-radius: 5px; margin: 10px 0; }
</style>
</head>
<body>

<h1>S.P.E.C.T.R.E. Engine OS v1.0</h1>
<p><b>Signal Processing & Electronic Cyber Security Reconnaissance Engine</b><br>
<i>A unified, multi-threaded platform bridging hardware telemetry, real-time spectrum analysis, and active network exploitation.</i></p>

<h2>1. Core System Architecture & Telemetry Pipeline</h2>
<p>S.P.E.C.T.R.E. is built on a highly optimized, asynchronous architecture using PySide6 and Scapy. It is designed to process thousands of packets per second without freezing the graphical user interface.</p>
<ul>
    <li><b>MainWindow Controller:</b> The central hub that owns all UI sub-widgets, manages the <code>TelemetryReceiver</code> QThread, and drives the 60Hz render loop via a <code>QTimer</code>.</li>
    <li><b>Hardware Telemetry Pipeline:</b> <code>ESP32 Sniffer -> Serial Port -> TelemetryReceiver (QThread) -> _on_packet() Router -> DSP/Recon/Threat Engines -> UI Throttling (15Hz) -> Rendering</code>.</li>
    <li><b>UI Throttling Algorithm:</b> To prevent GUI lag during massive packet floods (50-150+ pps), the system implements a strict 66ms (15Hz) UI update cap. Core data processing runs on every packet, but UI redraws are batched.</li>
    <li><b>Attack Simulator:</b> Generates synthetic packet data to visualize attack intensity on the UI graphs in real-time, even when physical ESP32 hardware is disconnected.</li>
</ul>

<h2>2. Defensive / Analytics Tab</h2>
<p>This module focuses on passive monitoring, signal processing, and threat detection.</p>
<ul>
    <li><b>DSP Engine (Digital Signal Processing):</b> Processes raw RSSI (Received Signal Strength Indicator) telemetry. Applies a configurable Moving Average (MA) filter to smooth out environmental noise and visualize true signal trends. Tracks total packet counts and channel distributions.</li>
    <li><b>Spectrum Analyzer:</b> Calculates real-time channel occupancy. Distinguishes between Management, Control, and Data frames to visualize RF congestion and identify crowded channels.</li>
    <li><b>Threat Monitor:</b> Continuously tracks deauthentication floods. Calculates the deauth rate (frames/sec). If the rate exceeds the configurable threshold, it triggers an <span class="highlight">ALERT</span> state and logs high-severity spikes to the Timeline.</li>
    <li><b>IDS (Intrusion Detection System):</b> Monitors packet rates against predefined rules. Dynamically calculates live packet rates per rule and triggers alerts when specific thresholds are breached.</li>
    <li><b>PMKID Simulator:</b> Simulates PMKID capture events when Auth frames (subtype 11) containing SSID and BSSID are detected, demonstrating WPA3/WPA2 handshake vulnerabilities.</li>
</ul>

<h2>3. Offensive / Attack Tab</h2>
<p>Provides both hardware-level and software-level network disruption capabilities.</p>
<ul>
    <li><b>ESP32 RF Attacks:</b> Sends serial commands to connected ESP32 hardware to perform hardware-level RF jamming, beacon flooding, and deauthentication attacks.</li>
    <li><b>Software L2/L3 Attacks:</b> Executes network-level attacks directly from the host machine using the <code>L2Engine</code> and Scapy (e.g., DHCP Starvation, ICMP Flood, ARP Flood).</li>
    <li><b>Host AP Toggle:</b> Commands the ESP32 to broadcast a fake "SPECTRE_DEMO_AP" to test client isolation and rogue AP detection mechanisms.</li>
</ul>

<h2>4. Man-In-The-Middle (MITM) Suite</h2>
<p>The MITM engine uses Scapy for raw packet manipulation and a Dynamic Web Server for payload serving.</p>
<ul>
    <li><b>ARP Poisoning:</b> Sends bidirectional ARP replies to trick the target and gateway into sending their traffic through the attacker's machine. Generates fake L2 packets for UI visualization.</li>
    <li><b>DNS Spoofing:</b> Intercepts UDP Port 53 queries. Forges DNS responses to redirect any queried domain to the attacker's IP address.</li>
    <li><b>Credential Harvester:</b> Passively sniffs TCP Port 80. Parses HTTP POST requests for keywords (user, pass, email, login, auth, token). Extracts and logs Session Cookies.</li>
    <li><b>HTTP Injector (Visual):</b> Intercepts HTTP HTML responses. Injects custom JavaScript payloads (Black/Green screen, Alerts, Redirects, or Custom Scripts). Automatically recalculates Content-Length headers and strips TCP/IP checksums for seamless injection.</li>
    <li><b>TCP RST Injector (Precision Block):</b> Sniffs TCP Port 80 & 443. Forges bidirectional TCP Reset (RST) packets with calculated sequence numbers (Seq + Payload Length) to silently kill specific connections to target IPs or domains without corrupting the rest of the stream.</li>
    <li><b>Session & JWT Sniffer:</b> Extracts session cookies and Bearer tokens from HTTP headers to demonstrate session hijacking vulnerabilities.</li>
    <li><b>Dynamic Web Server:</b> A threaded HTTP server (Port 80) that serves a Fake Login Page for credential harvesting, or an Injected Index Page for JS payload delivery. Supports custom payload configuration and direct UI logging.</li>
    <li><b>Passive Module Management:</b> Allows concurrent execution of multiple passive engines (Harvesters, Injectors, RST Blockers) with individual termination controls.</li>
</ul>

<h2>5. Network Reconnaissance & Intelligence</h2>
<p>A professional-grade network mapping tool featuring a 3-tier identification system.</p>
<ul>
    <li><b>ARP Sweep:</b> Discovers all live devices on the local subnet by broadcasting ARP requests with a 4-second timeout to catch sleeping devices.</li>
    <li><b>3-Tier Hybrid OUI Lookup:</b> Identifies device vendors using a robust fallback chain:
        <ol>
            <li><b>Tier 1:</b> Local OUI Database (Fastest, custom mappings).</li>
            <li><b>Tier 2:</b> <code>mac-vendor-lookup</code> Python library (Comprehensive, offline).</li>
            <li><b>Tier 3:</b> Groq AI Fallback (Qwen3-32B thinking model) for rare/unknown vendors.</li>
        </ol>
    </li>
    <li><b>OS Fingerprinting:</b> Pings discovered devices via ICMP and analyzes the TTL (Time To Live) of the response.
        <br><i>TTL <= 64: Linux/Android/macOS | TTL <= 128: Windows | TTL <= 255: Network Device/Router</i>
    </li>
    <li><b>Multi-threaded Port Scanner:</b> Uses <code>ThreadPoolExecutor</code> (50 workers) to rapidly scan the top 50 common TCP ports (21, 22, 80, 443, 3389, etc.) and map running services.</li>
    <li><b>Visual Topology Map:</b> A <code>QGraphicsView</code> node-graph showing the network layout. The Gateway is a Gold node in the center; other devices branch out radially, color-coded by their guessed OS (Blue=Windows, Green=Linux, Orange=Network).</li>
</ul>

<h2>6. AI Integration & Context-Aware RAG</h2>
<ul>
    <li><b>Context-Aware RAG (Retrieval-Augmented Generation):</b> The AI Assistant uses Groq's API (<code>qwen/qwen3-32b</code>). It injects the entire S.P.E.C.T.R.E. documentation as a system prompt, ensuring answers are strictly based on the software's actual capabilities.</li>
    <li><b>Thinking Model Handling:</b> Qwen3 is a reasoning model that outputs internal thoughts in <code>&lt;think&gt;</code> tags. The AI engine uses robust string splitting to strip these tags and extract only the final, clean answer.</li>
    <li><b>Background Processing:</b> AI queries run in a dedicated <code>QThread</code> (AIWorker) to ensure the UI remains completely responsive while waiting for API responses.</li>
</ul>

<h2>7. Core Signals & Data Flow</h2>
<p>S.P.E.C.T.R.E. relies heavily on PySide6 Signals and Slots for thread-safe communication between the backend engines and the frontend UI:</p>
<ul>
    <li><code>packet_generated</code>: Emitted by engines to update UI graphs and spectrum analyzers.</li>
    <li><code>log_signal</code> & <code>passive_log_signal</code>: Route text logs to the MITM Event Log and Passive Event Log.</li>
    <li><code>harvester_status_changed</code>: Toggles the Web Server between Fake Login and Normal modes.</li>
    <li><code>payload_updated</code>: Syncs the UI's custom JS editor with the running MITM engines and Web Server.</li>
    <li><code>device_found</code>: Emits IP, MAC, Vendor, and OS data from the Network Scanner to the Recon Tree and Topology Map.</li>
    <li><code>port_scan_requested</code>: Triggers the multi-threaded TCP scanner on a selected device.</li>
    <li><code>mitm_started</code> & <code>mitm_stopped</code>: Controls the lifecycle of active and passive MITM engines.</li>
    <li><code>target_locked</code>: Emitted when the passive sniffer identifies a specific target BSSID/SSID.</li>
</ul>

<blockquote>
<b>Exhibition Note:</b> S.P.E.C.T.R.E. demonstrates a complete understanding of the OSI model, from Layer 1 (RF/Serial) to Layer 7 (HTTP/JS Injection), combined with modern AI integration for automated network intelligence.
</blockquote>

</body>
</html>
"""
