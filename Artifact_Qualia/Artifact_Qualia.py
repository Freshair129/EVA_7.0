# =============================================================================
# Artifact Qualia Core v1
# Phenomenological Experience Integrator
#
# Role:
#   - Integrate EVA Matrix state + RIM semantic impact
#   - Produce lived experience snapshot (qualia)
#
# Invariants:
#   - No optimization
#   - No memory admission
#   - No relationship evaluation
#   - No numeric impact scores
# =============================================================================

from dataclasses import dataclass
from typing import Dict, List
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
class RIMSemantic:
    impact_level: str              # low | medium | high
    impact_trend: str              # rising | stable | fading
    affected_domains: List[str]


@dataclass
class QualiaSnapshot:
    """
    Lived phenomenological snapshot.
    This is NOT memory, NOT decision, NOT evaluation.
    """
    intensity: float
    tone: str
    coherence: float
    depth: float
    texture: Dict[str, float]


# =============================================================================
# Artifact Qualia Core
# =============================================================================

class ArtifactQualiaCore:
    """
    Artifact Qualia Core v1
    """

    def __init__(self):
        self._last_intensity: float = 0.3
        self._last_coherence: float = 0.6

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def integrate(
        self,
        eva_state: Dict[str, float],
        rim_semantic: RIMSemantic
    ) -> QualiaSnapshot:
        """
        eva_state:
          output from EVA Matrix (continuous state)
        rim_semantic:
          semantic impact from RIM (no numbers)
        """

        intensity = self._compute_intensity(eva_state, rim_semantic)
        coherence = self._compute_coherence(eva_state, rim_semantic)
        depth = self._compute_depth(eva_state)
        tone = self._derive_tone(eva_state, rim_semantic)
        texture = self._build_texture(eva_state, rim_semantic)

        self._last_intensity = intensity
        self._last_coherence = coherence

        return QualiaSnapshot(
            intensity=intensity,
            tone=tone,
            coherence=coherence,
            depth=depth,
            texture=texture
        )

    # -------------------------------------------------------------------------
    # Internal Mechanics
    # -------------------------------------------------------------------------

    def _compute_intensity(
        self,
        eva: Dict[str, float],
        rim: RIMSemantic
    ) -> float:
        """
        How strong the experience feels.
        """

        base = clamp(
            eva.get("baseline_arousal", 0.0) +
            eva.get("emotional_tension", 0.0)
        )

        impact_boost = {
            "low": 0.0,
            "medium": 0.1,
            "high": 0.25,
        }.get(rim.impact_level, 0.0)

        trend_mod = {
            "rising": 1.1,
            "stable": 1.0,
            "fading": 0.85,
        }.get(rim.impact_trend, 1.0)

        raw = clamp((base + impact_boost) * trend_mod)

        return smooth(self._last_intensity, raw, alpha=0.65)

    # -------------------------------------------------------------------------

    def _compute_coherence(
        self,
        eva: Dict[str, float],
        rim: RIMSemantic
    ) -> float:
        """
        How internally consistent the experience feels.
        """

        stability = eva.get("coherence", 0.5)
        momentum = eva.get("momentum", 0.5)

        disruption = {
            "low": 0.05,
            "medium": 0.15,
            "high": 0.30,
        }.get(rim.impact_level, 0.1)

        raw = clamp(stability + momentum - disruption)

        return smooth(self._last_coherence, raw, alpha=0.7)

    # -------------------------------------------------------------------------

    def _compute_depth(self, eva: Dict[str, float]) -> float:
        """
        Sense of experiential depth / immersion.
        """

        calm = eva.get("calm_depth", 0.0)
        tension = eva.get("emotional_tension", 0.0)

        raw = clamp(calm * 0.6 + tension * 0.4)

        return raw

    # -------------------------------------------------------------------------

    def _derive_tone(
        self,
        eva: Dict[str, float],
        rim: RIMSemantic
    ) -> str:
        """
        Coarse phenomenological tone (non-emotional labels).
        """

        if eva.get("calm_depth", 0.0) > 0.6:
            return "quiet"

        if eva.get("emotional_tension", 0.0) > 0.7:
            return "charged"

        if rim.impact_trend == "fading":
            return "settling"

        return "neutral"

    # -------------------------------------------------------------------------

    def _build_texture(
        self,
        eva: Dict[str, float],
        rim: RIMSemantic
    ) -> Dict[str, float]:
        """
        Texture vector for RMS / MSP (not memory decision).
        """

        texture = {
            "emotional": eva.get("emotional_tension", 0.0),
            "relational": eva.get("baseline_arousal", 0.0),
            "identity": eva.get("coherence", 0.0),
            "ambient": eva.get("momentum", 0.0),
        }

        # amplify affected domains slightly (bounded)
        for d in rim.affected_domains:
            if d in texture:
                texture[d] = clamp(texture[d] * 1.15)

        return texture
