import re

with open("ui/main_window/_packet_handler.py", "r") as f:
    content = f.read()

# Replace _on_packet
old_on_packet = """    @Slot(dict)
    def _on_packet(self, pkt: dict) -> None:
        now = time.monotonic()
        self._pkt_timestamps.append(now)"""

new_on_packet = """    @Slot(dict)
    def _on_packet(self, pkt: dict) -> None:
        if not hasattr(self, "_packet_queue"):
            import collections
            self._packet_queue = collections.deque()
        self._packet_queue.append(pkt)

    def _process_packet(self, pkt: dict, now: float) -> None:
        self._pkt_timestamps.append(now)"""

content = content.replace(old_on_packet, new_on_packet)

# Remove the 0.066 throttle block
throttle_block = """        if not hasattr(self, "_last_ui_update"):
            self._last_ui_update = 0.0
        if now - self._last_ui_update < 0.066:
            return
        self._last_ui_update = now

"""
content = content.replace(throttle_block, "")

# Replace _on_timer start
old_on_timer = """    @Slot()
    def _on_timer(self) -> None:
        now = time.monotonic()
        cutoff = now - 1.0"""

new_on_timer = """    @Slot()
    def _on_timer(self) -> None:
        now = time.monotonic()
        
        # Batch process all pending packets
        if hasattr(self, "_packet_queue"):
            processed = 0
            while self._packet_queue and processed < 1000:
                pkt = self._packet_queue.popleft()
                self._process_packet(pkt, now)
                processed += 1

        cutoff = now - 1.0"""

content = content.replace(old_on_timer, new_on_timer)

with open("ui/main_window/_packet_handler.py", "w") as f:
    f.write(content)
