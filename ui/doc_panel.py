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
    QTextBrowser,
    QListWidget,
    QLineEdit,
    QSplitter,
    QFrame,
)
from PySide6.QtCore import Qt, Signal, QThread
from core.ai.ai_assistant import SpectreAI
from core.spectre_docs import get_wiki_pages
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
        self._wiki_pages = get_wiki_pages()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        hdr = QLabel("OFFLINE WIKI & AI ASSISTANT")
        hdr.setObjectName("section_header")
        layout.addWidget(hdr)

        # Main Splitter (Nav Left, Docs Center, AI Right)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(4)

        # ── Pane 1: Navigation ──
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_hdr = QLabel("PAGES")
        nav_hdr.setObjectName("section_header")
        nav_layout.addWidget(nav_hdr)
        self._nav_list = QListWidget()
        self._nav_list.setObjectName("doc_nav_list")
        for title in self._wiki_pages.keys():
            self._nav_list.addItem(title)
        self._nav_list.currentTextChanged.connect(self._on_page_selected)
        nav_layout.addWidget(self._nav_list)
        main_splitter.addWidget(nav_container)

        # ── Pane 2: Documentation ──
        doc_container = QWidget()
        doc_layout = QVBoxLayout(doc_container)
        doc_layout.setContentsMargins(12, 0, 0, 0)
        doc_hdr = QLabel("KNOWLEDGE BASE")
        doc_hdr.setObjectName("section_header")
        doc_layout.addWidget(doc_hdr)
        self._doc_viewer = QTextBrowser()
        self._doc_viewer.setObjectName("doc_viewer")
        self._doc_viewer.setReadOnly(True)
        self._doc_viewer.setOpenExternalLinks(False)
        doc_layout.addWidget(self._doc_viewer)
        main_splitter.addWidget(doc_container)

        # ── Pane 3: AI Chat ──
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(12, 0, 0, 0)
        chat_hdr = QLabel("S.P.E.C.T.R.E. AI ASSISTANT")
        chat_hdr.setObjectName("section_header")
        chat_layout.addWidget(chat_hdr)
        self._chat_history = QTextEdit()
        self._chat_history.setObjectName("chat_history")
        self._chat_history.setReadOnly(True)
        chat_layout.addWidget(self._chat_history)
        
        input_frame = QFrame()
        input_frame.setObjectName("chat_input_frame")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(5, 5, 5, 5)
        input_layout.setSpacing(5)
        self._chat_input = QLineEdit()
        self._chat_input.setPlaceholderText("Ask about S.P.E.C.T.R.E. features...")
        self._chat_input.setStyleSheet("border: none; background: transparent;")
        self._chat_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self._chat_input)
        self._send_btn = QPushButton("SEND")
        self._send_btn.setProperty("btnTheme", "orange")
        self._send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self._send_btn)
        chat_layout.addWidget(input_frame)
        main_splitter.addWidget(chat_container)

        # Set Stretch Factors (Nav: 20%, Doc: 50%, AI: 30%)
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 5)
        main_splitter.setStretchFactor(2, 3)

        self._left_container = nav_container
        self._right_container = chat_container

        layout.addWidget(main_splitter, stretch=1)

        # Load first page if available
        if self._nav_list.count() > 0:
            self._nav_list.setCurrentRow(0)

        self.refresh_theme()

        # Welcome message
        self._append_to_chat(
            "AI",
            "Hello! I am the S.P.E.C.T.R.E. AI Assistant. Ask me anything about the system architecture, MITM attacks, or network reconnaissance features.",
        )

    def refresh_theme(self):
        """Update inline styles when the theme changes."""
        self._nav_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {config.COLOR_BG};
                color: {config.COLOR_TEXT_PRIMARY};
                border: 1px solid {config.COLOR_BORDER};
            }}
            QListWidget::item:selected {{
                background-color: {config.COLOR_ACCENT_CYAN};
                color: {config.COLOR_BG};
            }}
        """)
        self._doc_viewer.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {config.COLOR_BG};
                color: {config.COLOR_TEXT_PRIMARY};
                border: 1px solid {config.COLOR_BORDER};
            }}
        """)
        self._chat_history.setStyleSheet(f"""
            QTextEdit {{
                background-color: {config.COLOR_BG};
                color: {config.COLOR_TEXT_PRIMARY};
                border: 1px solid {config.COLOR_BORDER};
            }}
        """)

    def _on_page_selected(self, title: str):
        if title in self._wiki_pages:
            self._doc_viewer.setMarkdown(self._wiki_pages[title])

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
