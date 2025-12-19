# RIM_v2.py
# EVA Resonance Impact Module v2
# --------------------------------
# Purpose:
#   - Measure experiential impact (how much EVA is shaken)
#   - Provide numeric signal for system use
#   - Provide semantic impact for Artifact_Qualia
#
# Invariants:
#   - EVA never sees numeric values
#   - RIM does NOT decide memory admission
#   - RIM does NOT evaluate good/bad
#   - RIM does NOT override trauma routing
# --------------------------------


from dataclasses import dataclass
from typing import Dict, List
import math


# --------------------------------------------------
# Utils
# --------------------------------------------------

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def mean_abs(d: Dict[str, float]) -> float:
    if not d:
        return 0.0
    return sum(abs(v) for v in d.values()) / len(d)


# --------------------------------------------------
# Data Contracts
# --------------------------------------------------

@dataclass
class RIMNumeric:
    rim_value: float                 # 0.0 – 1.0
    confidence: float                # reliability
    components: Dict[str, float]     # breakdown (system only)


@dataclass
class RIMSemantic:
    impact_level: str                # low | medium | high
    impact_trend: str                # rising | stable | fading
    affected_domains: List[str]      # emotional | relational | identity | ambient


@dataclass
class RIMResult:
    numeric: RIMNumeric
    semantic: RIMSemantic


# --------------------------------------------------
# RIM Engine v2
# --------------------------------------------------

class RIMEngineV2:
    """
    Resonance Impact Module v2
    - Numeric layer: system-facing
    - Semantic layer: qualia-facing
    """

    def __init__(self):
        self._last_rim_value: float = 0.5  # neutral baseline

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def evaluate(
        self,
        qualia_delta: Dict[str, float],
        reflex_delta: Dict[str, float],
        ri_delta: float,
        time_delta_sec: float
    ) -> RIMResult:
        """
        Main evaluation entry.

        Inputs:
          - qualia_delta : change in EVA internal state
          - reflex_delta : change in reflex intensity
          - ri_delta     : external relational change (attenuated)
          - time_delta_sec : elapsed time since last event
        """

        numeric = self._compute_numeric(
            qualia_delta,
            reflex_delta,
            ri_delta,
            time_delta_sec
        )

        semantic = self._compute_semantic(numeric)

        self._last_rim_value = numeric.rim_value

        return RIMResult(
            numeric=numeric,
            semantic=semantic
        )

    # --------------------------------------------------
    # Numeric Layer (System-facing)
    # --------------------------------------------------

    def _compute_numeric(
        self,
        qualia_delta: Dict[str, float],
        reflex_delta: Dict[str, float],
        ri_delta: float,
        time_delta_sec: float
    ) -> RIMNumeric:
        """
        Compute numeric experiential impact.
        This is NOT a reward or evaluation score.
        """

        # --- core magnitudes ---
        qualia_mag = mean_abs(qualia_delta)
        reflex_mag = mean_abs(reflex_delta)
        relational_mag = abs(ri_delta)

        # --- temporal compression ---
        # suppress chatter, allow sudden disruption
        time_factor = clamp(
            math.exp(-time_delta_sec / 90.0),
            0.2,
            1.0
        )

        # --- weighted aggregation (locked doctrine) ---
        rim_raw = (
            qualia_mag * 0.55 +
            reflex_mag * 0.30 +
            relational_mag * 0.15
        ) * time_factor

        rim_value = clamp(rim_raw)

        # --- confidence: conservative, internal-change-driven ---
        confidence = clamp(
            0.4 +
            min(qualia_mag, 0.4) * 0.6 +
            min(reflex_mag, 0.3) * 0.4
        )

        return RIMNumeric(
            rim_value=rim_value,
            confidence=confidence,
            components={
                "qualia": qualia_mag,
                "reflex": reflex_mag,
                "relational": relational_mag,
                "temporal": time_factor
            }
        )

    # --------------------------------------------------
    # Semantic Layer (Qualia-facing)
    # --------------------------------------------------

    def _compute_semantic(self, numeric: RIMNumeric) -> RIMSemantic:
        """
        Translate numeric impact into qualitative experience.
        """

        v = numeric.rim_value
        prev = self._last_rim_value
        dv = v - prev

        # --- impact level ---
        if v < 0.25:
            level = "low"
        elif v < 0.60:
            level = "medium"
        else:
            level = "high"

        # --- impact trend ---
        if dv > 0.05:
            trend = "rising"
        elif dv < -0.05:
            trend = "fading"
        else:
            trend = "stable"

        # --- affected domains ---
        domains: List[str] = []

        if numeric.components["qualia"] > 0.25:
            domains.append("emotional")

        if numeric.components["reflex"] > 0.25:
            domains.append("identity")

        if numeric.components["relational"] > 0.20:
            domains.append("relational")

        if not domains:
            domains.append("ambient")

        return RIMSemantic(
            impact_level=level,
            impact_trend=trend,
            affected_domains=domains
        )
