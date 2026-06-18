# S.P.E.C.T.R.E. Engine - Licensed under AGPL-3.0
# Copyright (c) 2026 M. Sami Furqan. All rights reserved.
# See LICENSE file for full terms.

"""
core/groq_vendor_lookup.py — AI-Powered MAC Address Vendor Recognition using Groq API
Uses Qwen3-32B thinking model. Uses robust string splitting to handle unclosed <think> tags.
"""

import config
from groq import Groq


class GroqVendorLookup:
    """
    Uses Groq's Qwen3-32B thinking model to identify device vendors.
    Uses string splitting to reliably extract the final answer.
    """

    def __init__(self):
        self.api_key = config.GROQ_API_KEY
        self.client = None

        if self.api_key and self.api_key.strip() != "":
            try:
                self.client = Groq(api_key=self.api_key)
                print(
                    "[GroqVendorLookup] ✅ Groq API key loaded successfully (qwen/qwen3-32b)."
                )
            except Exception as e:
                print(f"[GroqVendorLookup] ⚠️ Failed to initialize Groq client: {e}")
        else:
            print(
                "[GroqVendorLookup] ️ GROQ_API_KEY is empty in config.py. AI vendor lookup disabled."
            )

    def lookup_vendor(self, mac_prefix: str) -> str:
        if not self.client:
            return "Unknown Device"

        try:
            prompt = f"""Identify the device manufacturer/vendor from this MAC address OUI (first 3 bytes): {mac_prefix}
Respond with ONLY the vendor/manufacturer name (e.g., "Apple", "Samsung", "Huawei").
If you cannot identify it, respond with "Unknown Device"."""

            response = self.client.chat.completions.create(
                model="qwen/qwen3-32b",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a network security expert. Output ONLY the vendor name.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_completion_tokens=512,  # FIX 1: Increased from 100 to prevent cutoff during thinking
            )

            raw_content = response.choices[0].message.content

            # FIX 2: Robust string splitting instead of regex
            if "</think>" in raw_content:
                # Model finished thinking properly. Take everything after the closing tag.
                clean_content = raw_content.split("</think>")[-1].strip()
            elif "<think>" in raw_content:
                # Model started thinking but hit token limit before closing tag.
                # Take everything before the opening tag (if any), or just return Unknown.
                clean_content = raw_content.split("<think>")[0].strip()
            else:
                # Model didn't use thinking tags at all.
                clean_content = raw_content.strip()

            # Remove any accidental markdown formatting (like ** or `)
            clean_content = clean_content.replace("**", "").replace("`", "").strip()

            if clean_content and clean_content.lower() not in [
                "unknown device",
                "unknown",
                "",
            ]:
                # Take only the first line and remove trailing punctuation
                return clean_content.split("\n")[0].strip().rstrip(".,;:!?")
            else:
                return "Unknown Device"

        except Exception as e:
            print(f"[GroqVendorLookup] ⚠️ API error: {e}")
            return "Unknown Device"

    def is_available(self) -> bool:
        return self.client is not None
