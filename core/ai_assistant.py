# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/ai_assistant.py — Context-Aware AI Assistant using Groq API
"""

import re
import config
from groq import Groq
from core.spectre_docs import SPECTRE_DOCUMENTATION


class SpectreAI:
    def __init__(self):
        self.api_key = config.GROQ_API_KEY
        self.client = None

        if self.api_key and self.api_key.strip() != "":
            try:
                self.client = Groq(api_key=self.api_key)
                print("[AI Assistant] ✅ Groq API key loaded (llama-3.3-70b-versatile).")
            except Exception as e:
                print(f"[AI Assistant] ⚠️ Failed to initialize Groq client: {e}")
        else:
            print("[AI Assistant] ⚠️ GROQ_API_KEY missing. AI Assistant disabled.")

    def ask(self, user_question: str) -> str:
        if not self.client:
            return (
                "AI Assistant is offline. Please check your GROQ_API_KEY in config.py."
            )

        try:
            # Strip HTML tags for the AI prompt to save tokens, but keep the structure
            clean_docs = re.sub(r"<[^>]+>", "", SPECTRE_DOCUMENTATION)

            system_prompt = f"""You are the official AI assistant for S.P.E.C.T.R.E. Engine OS.
You have access to the complete technical documentation of the software below.
Answer the user's questions accurately based ONLY on this documentation.
Be concise, technical, and helpful.

DOCUMENTATION:
{clean_docs}
"""

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question},
                ],
                temperature=0.3,
                max_completion_tokens=1024,
            )

            raw_content = response.choices[0].message.content

            # Strip <think> tags from Qwen3 reasoning output
            if "</think>" in raw_content:
                clean_content = raw_content.split("</think>")[-1].strip()
            elif "<think>" in raw_content:
                clean_content = raw_content.split("<think>")[0].strip()
            else:
                clean_content = raw_content.strip()

            return clean_content if clean_content else "I couldn't generate a response."

        except Exception as e:
            return f"Error communicating with AI: {str(e)}"
