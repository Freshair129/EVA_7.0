# ============================================================
# RI ENGINE v5.0 — EVA Cognitive Resonance Layer
# Deterministic & EHM-independent
# ============================================================

import numpy as np


class RIEngine:

    def __init__(self):
        # weight configuration from RI spec
        self.weights = {
            "ER": 0.25,
            "IF": 0.30,
            "SR": 0.30,
            "CR": 0.15
        }

    # ---------------------------------------------------------
    # Emotional Resonance (ER) — low-dim user emotion only
    # ---------------------------------------------------------
    def compute_ER(self, user_emotion, llm_interpret_emotion):
        keys = ["arousal", "valence", "tension"]

        diffs = []
        for k in keys:
            user_val = user_emotion.get(k, 0)
            eva_val = llm_interpret_emotion.get(k, 0)
            diffs.append(abs(user_val - eva_val))

        ER = 1 - (sum(diffs) / len(diffs))
        return max(0.0, min(1.0, ER))

    # ---------------------------------------------------------
    # Intent Fit (IF)
    # ---------------------------------------------------------
    def compute_IF(self, llm_intent, clarity, tension):
        if llm_intent in ["DEFINE", "EXPLAIN", "ANALYZE"]:
            return clarity

        elif llm_intent in ["REASSURE", "SAFETY"]:
            return 1 - tension

        return (clarity + (1 - tension)) / 2

    # ---------------------------------------------------------
    # Semantic Resonance (SR)
    # ---------------------------------------------------------
    def compute_SR(self, summary_vec, episodic_vec):
        a = np.array(summary_vec)
        b = np.array(episodic_vec)

        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom < 1e-8:
            return 0.0

        sr = float(np.dot(a, b) / denom)
        return max(0.0, min(1.0, sr))

    # ---------------------------------------------------------
    # Contextual Resonance (CR)
    # ---------------------------------------------------------
    def compute_CR(self, flow_score, personalization_score):
        CR = (flow_score * 0.6) + (personalization_score * 0.4)
        return max(0.0, min(1.0, CR))

    # ---------------------------------------------------------
    # MAIN RI CALCULATION
    # ---------------------------------------------------------
    def compute_RI(self,
                   llm_summary_vector,
                   episodic_context_vector,
                   user_emotion,
                   llm_emotion_estimate,
                   clarity,
                   tension,
                   llm_intent,
                   flow_score,
                   personalization_score):

        ER = self.compute_ER(user_emotion, llm_emotion_estimate)
        IF = self.compute_IF(llm_intent, clarity, tension)
        SR = self.compute_SR(llm_summary_vector, episodic_context_vector)
        CR = self.compute_CR(flow_score, personalization_score)

        RI = (
            ER * self.weights["ER"] +
            IF * self.weights["IF"] +
            SR * self.weights["SR"] +
            CR * self.weights["CR"]
        )

        return {
            "ER": ER,
            "IF": IF,
            "SR": SR,
            "CR": CR,
            "RI_total": float(max(0.0, min(1.0, RI)))
        }
