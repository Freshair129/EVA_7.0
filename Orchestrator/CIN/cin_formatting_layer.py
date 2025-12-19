# ============================================================
# CIN FORMATTING LAYER — EVA 5.5-AI
# With Formatting Rules Enforcement
# ============================================================

import json


class CINFormattingLayer:

    def __init__(self, max_bytes=8192):
        self.max_bytes = max_bytes

    # ----------------------------------------------------------
    # Byte Clamp
    # ----------------------------------------------------------
    def clamp_size(self, text):
        data = text.encode("utf-8")
        if len(data) <= self.max_bytes:
            return text
        return data[:self.max_bytes].decode("utf-8", errors="ignore")

    # ----------------------------------------------------------
    # Converts dict/list → human readable formatted block
    # With indentation + bullet formatting
    # ----------------------------------------------------------
    def format_block(self, content, level=0):
        """
        Formatting rules applied:
        - lists → bullet points
        - nested lists/dicts → indented bullets
        - avoid long unreadable JSON chunks
        """
        indent = "  " * level
        bullet = indent + "- "

        # list → bullet list
        if isinstance(content, list):
            if len(content) == 0:
                return indent + "(empty)\n"
            text = ""
            for item in content:
                if isinstance(item, (dict, list)):
                    text += bullet + "\n" + self.format_block(item, level + 1)
                else:
                    text += bullet + str(item) + "\n"
            return text

        # dict → key: value with newline per item
        elif isinstance(content, dict):
            if len(content) == 0:
                return indent + "(empty)\n"
            text = ""
            for k, v in content.items():
                key_line = f"{indent}- **{k}**: "
                if isinstance(v, (dict, list)):
                    text += key_line + "\n" + self.format_block(v, level + 1)
                else:
                    text += key_line + str(v) + "\n"
            return text

        # primitive → simple text
        else:
            return indent + str(content) + "\n"

    # ----------------------------------------------------------
    # Format Section with Title
    # ----------------------------------------------------------
    def format_section(self, title, content):
        """
        Enforce formatting rules:
        - paragraph separation
        - newlines for new ideas
        """
        if content in (None, {}, [], ""):
            return ""

        formatted_body = self.format_block(content)
        return f"{title}\n{formatted_body}\n"

    # ----------------------------------------------------------
    # MAIN FORMATTER
    # ----------------------------------------------------------
    def format(self, ctx):
        """
        Core formatting rules applied:
        - Paragraph style
        - Bullet points for lists
        - Separate ideas per line
        - Important keys in **bold**
        """

        text = "[EVA CONTEXT v6.0 - Boss Resonance Enveloped]\n---\n\n"

        # 1. Temporal Awareness
        text += self.format_section("## Temporal Awareness", ctx.get("temporal"))

        # 2. Genesis: My Root Identity
        text += self.format_section("## Genesis: My Root Identity", ctx.get("genesis_identity"))

        # 3. Boss: My Creator's Resonance
        text += self.format_section("## Boss: My Creator's Resonance", ctx.get("boss_resonance"))

        # 4. Soul: My Inner Core
        text += self.format_section("## Soul: My Inner Core", ctx.get("soul_core"))

        # 5. Self-Awareness (Systems)
        text += self.format_section("## System Awareness", ctx.get("system_awareness"))

        # 6. Persona State
        text += self.format_section("## Persona State", ctx.get("active_persona"))

        # 7. Emotional State (9D)
        text += self.format_section("## Emotional State (9D)", ctx.get("emotional_state"))

        # 8. Session Brief
        text += self.format_section("## Session context", ctx.get("session_context"))

        # 9. Episodic Archive (Verbatim Trace)
        text += self.format_section("## Episodic Archive", ctx.get("episodic_archive"))

        # 10. Directives
        text += self.format_section("## EVA Directives", ctx.get("directives"))

        # clamp to safe size
        return self.clamp_size(text)
