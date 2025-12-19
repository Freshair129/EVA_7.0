# ============================================================
# PROMPT RULE LAYER — EVA 5.5
# Controls final rules applied to CIN Context + LLM behavior
# ============================================================

class PromptRuleLayer:

    def __init__(self):
        pass

    # ----------------------------------------------------------
    def apply_rules(self, context_block):
        """
        Apply strict high-level rules to the CIN context BEFORE
        it reaches the LLM. This ensures compliance, stability,
        and persona consistency.
        """

        rules = [
            "LLM must not modify memory or internal state.",
            "LLM must follow persona_state exactly as injected.",
            "LLM must obey formatting rules: paragraph spacing, bullets, bolding.",
            "LLM must avoid over-explaining unless explicitly requested.",
            "LLM must treat sensory/reflex signals as tone guidelines.",
            "LLM must not hallucinate user profile data.",
            "LLM must output in the required LLM_BLOCK contract."
        ]

        context_block["prompt_rules"] = rules
        return context_block
