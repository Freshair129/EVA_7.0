# =============================================================================
# RMS ENGINE v6.0
# Resonance Memory System (EVA_Matrix–based)
#
# Role:
#   - Paint memory texture from EVA_Matrix state
#   - Protect system via trauma channel
#   - Harmonize tone to preserve identity continuity
#
# Invariants:
#   - No memory admission
#   - No importance evaluation
#   - No septad / legacy emotion abstraction
# =============================================================================

from dataclasses import dataclass
from typing import Dict
import math


# =============================================================================
# Utils
# =============================================================================

def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def smooth(prev: float, now: float, alpha: float = 0.7) -> float:
    return alpha * prev + (1 - alpha) * now


# =============================================================================
# Data Contracts
# =============================================================================

@dataclass
class RMSOutput:
    memory_color: Dict[str, float]
    intensity: float
    trauma_flag: bool


# =============================================================================
# RMS Engine v6
# =============================================================================

class RMSEngineV6:
    """
    Resonance Memory System v6
    """

    def __init__(self):
        # Internal smoothing memory (NOT episodic memory)
        self._last_color = {
            "stress": 0.2,
            "warmth": 0.5,
            "clarity": 0.5,
            "drive": 0.3,
            "calm": 0.4,
        }
        self._last_intensity = 0.3

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def process(
        self,
        eva_matrix: Dict[str, float],
        reflex_state: Dict[str, float],
        rim_semantic: Dict[str, str]
    ) -> RMSOutput:
        """
        eva_matrix:
          continuous EVA_Matrix state (source of truth)

        reflex_state:
          must include threat_level ∈ [0,1]

        rim_semantic:
          impact_level / impact_trend (context only)
        """

        trauma_flag = self._detect_trauma(reflex_state)

        color = self._generate_color(eva_matrix)
        intensity = self._compute_intensity(eva_matrix, rim_semantic)

        # Trauma de-intensification (protective)
        if trauma_flag:
            color = {k: v * 0.45 for k, v in color.items()}
            intensity *= 0.5

        # Harmonize (smooth)
        color = {
            k: smooth(self._last_color[k], v, alpha=0.65)
            for k, v in color.items()
        }
        intensity = smooth(self._last_intensity, intensity, alpha=0.7)

        self._last_color = color
        self._last_intensity = intensity

        return RMSOutput(
            memory_color=color,
            intensity=intensity,
            trauma_flag=trauma_flag
        )

    # -------------------------------------------------------------------------
    # Core Logic
    # -------------------------------------------------------------------------

    def _generate_color(self, eva: Dict[str, float]) -> Dict[str, float]:
        """
        Project EVA_Matrix → memory color axes
        """

        stress = clamp(
            eva.get("emotional_tension", 0.0) +
            eva.get("baseline_arousal", 0.0)
        )

        warmth = clamp(
            eva.get("calm_depth", 0.0) +
            eva.get("relational_tone", 0.0)
        )

        clarity = clamp(
            eva.get("coherence", 0.0)
        )

        drive = clamp(
            eva.get("momentum", 0.0) +
            eva.get("baseline_arousal", 0.0)
        )

        calm = clamp(
            eva.get("calm_depth", 0.0) -
            eva.get("emotional_tension", 0.0)
        )

        return {
            "stress": stress,
            "warmth": warmth,
            "clarity": clarity,
            "drive": drive,
            "calm": calm,
        }

    # -------------------------------------------------------------------------

    def _compute_intensity(
        self,
        eva: Dict[str, float],
        rim: Dict[str, str]
    ) -> float:
        """
        Overall affective intensity (non-evaluative)
        """

        base = clamp(
            eva.get("baseline_arousal", 0.0) +
            eva.get("emotional_tension", 0.0)
        )

        impact_boost = {
            "low": 0.0,
            "medium": 0.1,
            "high": 0.25,
        }.get(rim.get("impact_level"), 0.1)

        trend_mod = {
            "rising": 1.1,
            "stable": 1.0,
            "fading": 0.85,
        }.get(rim.get("impact_trend"), 1.0)

        return clamp((base + impact_boost) * trend_mod)

    # -------------------------------------------------------------------------

    def _detect_trauma(self, reflex: Dict[str, float]) -> bool:
        """
        Trauma detection based purely on threat reflex
        """

        threat = reflex.get("threat_level", 0.0)
        return threat > 0.85
