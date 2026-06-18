# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
ui/doc_panel.py — Documentation & AI Assistant Panel
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QSplitter,
    QFrame,
)
from PySide6.QtCore import Qt, Signal, QThread
from core.ai_assistant import SpectreAI
from core.spectre_docs import SPECTRE_DOCUMENTATION
import config


class AIWorker(QThread):
    response_ready = Signal(str)

    def __init__(self, ai_engine, question):
        super().__init__()
        self.ai_engine = ai_engine
        self.question = question

    def run(self):
        answer = self.ai_engine.ask(self.question)
        self.response_ready.emit(answer)


class DocPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ai_engine = SpectreAI()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        hdr = QLabel("[ DOCUMENTATION & AI ASSISTANT ]")
        hdr.setObjectName("section_header")
        hdr.setStyleSheet(
            f"color: {config.COLOR_ACCENT_CYAN}; border-bottom: 2px solid {config.COLOR_ACCENT_CYAN}; font-size: 13px; padding-bottom: 4px;"
        )
        layout.addWidget(hdr)

        # Main Splitter (Docs Left, AI Right)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(4)
        main_splitter.setStyleSheet(f"""
            QSplitter::handle {{ background: {config.COLOR_BORDER}; width: 2px; }}
        """)

        # ── Left Side: Documentation ─
        doc_container = QWidget()
        doc_layout = QVBoxLayout(doc_container)
        doc_layout.setContentsMargins(0, 0, 0, 0)

        doc_hdr = QLabel("[ KNOWLEDGE BASE ]")
        doc_hdr.setStyleSheet(
            f"color: {config.COLOR_ACCENT_GREEN}; font-weight: bold; font-size: 11px;"
        )
        doc_layout.addWidget(doc_hdr)

        self._doc_viewer = QTextEdit()
        self._doc_viewer.setReadOnly(True)
        self._doc_viewer.setHtml(SPECTRE_DOCUMENTATION)
        self._doc_viewer.setStyleSheet(f"""
            QTextEdit {{
                background-color: {config.COLOR_BG_PANEL};
                color: {config.COLOR_TEXT_PRIMARY};
                border: 1px solid {config.COLOR_BORDER};
                border-radius: 4px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                padding: 10px;
            }}
        """)
        doc_layout.addWidget(self._doc_viewer)
        main_splitter.addWidget(doc_container)

        # ── Right Side: AI Chat ──
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(12, 0, 0, 0)

        chat_hdr = QLabel("[ S.P.E.C.T.R.E. AI ASSISTANT ]")
        chat_hdr.setStyleSheet(
            f"color: {config.COLOR_ACCENT_ORANGE}; font-weight: bold; font-size: 11px;"
        )
        chat_layout.addWidget(chat_hdr)

        self._chat_history = QTextEdit()
        self._chat_history.setReadOnly(True)
        self._chat_history.setStyleSheet(f"""
            QTextEdit {{
                background-color: {config.COLOR_BG_PANEL};
                color: {config.COLOR_TEXT_PRIMARY};
                border: 1px solid {config.COLOR_BORDER};
                border-radius: 4px;
                font-family: monospace;
                font-size: 12px;
            }}
        """)
        chat_layout.addWidget(self._chat_history)

        # Input Area
        input_frame = QFrame()
        input_frame.setStyleSheet(
            f"border: 1px solid {config.COLOR_BORDER}; border-radius: 4px;"
        )
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(5, 5, 5, 5)
        input_layout.setSpacing(5)

        self._chat_input = QLineEdit()
        self._chat_input.setPlaceholderText("Ask about S.P.E.C.T.R.E. features...")
        self._chat_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #08080C;
                color: {config.COLOR_TEXT_PRIMARY};
                border: none;
                padding: 5px;
            }}
        """)
        self._chat_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self._chat_input)

        self._send_btn = QPushButton("SEND")
        self._send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_ACCENT_ORANGE};
                color: #000;
                font-weight: bold;
                border: none;
                border-radius: 3px;
                padding: 5px 15px;
            }}
            QPushButton:disabled {{ background-color: {config.COLOR_BORDER}; color: {config.COLOR_TEXT_DIM}; }}
        """)
        self._send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self._send_btn)

        chat_layout.addWidget(input_frame)
        main_splitter.addWidget(chat_container)

        main_splitter.setStretchFactor(0, 3)  # Docs take 75%
        main_splitter.setStretchFactor(1, 1)  # Chat takes 25%

        self._left_container = doc_container
        self._right_container = chat_container

        layout.addWidget(main_splitter, stretch=1)

        # Welcome message
        self._append_to_chat(
            "AI",
            "Hello! I am the S.P.E.C.T.R.E. AI Assistant. Ask me anything about the system architecture, MITM attacks, or network reconnaissance features.",
        )

    @staticmethod
    def _md_to_html(text: str) -> str:
        """Convert a subset of Markdown to HTML for display in QTextEdit."""
        import re
        # Escape any existing HTML first to prevent injection
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # Bold: **text** or __text__
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
        # Italic: *text* or _text_ (single, not double)
        text = re.sub(r'\*(?!\*)(.+?)(?<!\*)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(?!_)(.+?)(?<!_)_', r'<em>\1</em>', text)
        # Inline code: `code`
        text = re.sub(
            r'`(.+?)`',
            r'<code style="background:#1a1a2e; color:#00ff9d; padding:1px 4px; border-radius:3px;">\1</code>',
            text
        )
        # Newlines → <br>
        text = text.replace('\n', '<br>')
        return text

    def _append_to_chat(self, sender: str, message: str):
        color = (
            config.COLOR_ACCENT_ORANGE if sender == "AI" else config.COLOR_ACCENT_CYAN
        )
        # Apply markdown → HTML only for AI responses
        if sender == "AI":
            body = self._md_to_html(message)
        else:
            # User messages: just escape HTML and convert newlines
            import html as _html
            body = _html.escape(message).replace('\n', '<br>')

        html = (
            f'<span style="color: {color}; font-weight: bold;">[{sender}]:</span> '
            f'<span style="color: {config.COLOR_TEXT_PRIMARY};">{body}</span><br><br>'
        )
        self._chat_history.append(html)
        self._chat_history.verticalScrollBar().setValue(
            self._chat_history.verticalScrollBar().maximum()
        )

    def _send_message(self):
        question = self._chat_input.text().strip()
        if not question:
            return

        self._append_to_chat("USER", question)
        self._chat_input.clear()
        self._send_btn.setEnabled(False)
        self._chat_input.setEnabled(False)

        # Start AI worker in background
        self._worker = AIWorker(self._ai_engine, question)
        self._worker.response_ready.connect(self._on_ai_response)
        self._worker.start()

    def _on_ai_response(self, answer: str):
        self._append_to_chat("AI", answer)
        self._send_btn.setEnabled(True)
        self._chat_input.setEnabled(True)
        self._chat_input.setFocus()
