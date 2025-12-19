# =============================================================================
# ESS.py
# Emotive Signaling System (ESS)
#
# Integrated:
#   - ISR.update(): Pharmacokinetics (PK)
#   - IRE.compute_reflex(): Receptor PD + Hill model
#   - Persona R_profile loading
#
# Canonical IDs:
#   - ess_id
#   - episode_id
#
# Outputs:
#   - C_Mod          → EVA Matrix
#   - reflex_vector  → RMS / Reflex consumers
#
# Invariants:
#   - No language
#   - No memory write
#   - No phenomenology
# =============================================================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from pathlib import Path
import json
import math
import time
import uuid


# -----------------------------------------------------------------------------
# Utils
# -----------------------------------------------------------------------------

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# ISR — Internal Substance Regulator (PK)
# -----------------------------------------------------------------------------

class ISR:
    """
    Owns hormone state over time (PK).
    """

    def __init__(self, half_life_sec: Dict[str, float]):
        self.half_life = half_life_sec
        self.C_Mod = {k: 0.0 for k in half_life_sec}
        self.D_Remaining = {k: 0.0 for k in half_life_sec}
        self.D_Cumulative = {k: 0.0 for k in half_life_sec}

    def update(self, D_Total_H: Dict[str, float], delta_t_ms: int):
        dt = delta_t_ms / 1000.0
        Rate_Actual = {}

        for chem, hl in self.half_life.items():
            incoming = D_Total_H.get(chem, 0.0)

            # Absorption
            self.D_Remaining[chem] += incoming

            # Exponential decay
            decay = math.exp(-dt / hl)
            self.D_Remaining[chem] *= decay

            # Saturation (normalized)
            prev = self.C_Mod[chem]
            self.C_Mod[chem] = clamp(self.D_Remaining[chem], 0.0, 1.0)

            # Rate after clamp
            Rate_Actual[chem] = (self.C_Mod[chem] - prev) / dt if dt > 0 else 0.0

            # Chronic exposure integral
            self.D_Cumulative[chem] += self.C_Mod[chem] * dt

        return (
            dict(self.C_Mod),
            dict(self.D_Remaining),
            dict(Rate_Actual),
        )


# -----------------------------------------------------------------------------
# IRE — Internal Reflex Engine (PD)
# -----------------------------------------------------------------------------

class IRE:
    """
    Receptor PD + Reflex computation.
    """

    def __init__(self):
        self.internalization: Dict[str, float] = {}

    # ---------------- Hill Model ----------------

    @staticmethod
    def hill(C: float, K: float = 1.0, n: float = 2.0) -> float:
        if C <= 0:
            return 0.0
        return (C ** n) / (K ** n + C ** n)

    # ---------------- Persona R_profile ----------------

    def load_R_profile(self, path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as f:
            prof = json.load(f)

        assert prof.get("schema") == "EVA-R_Profile-v1", "Invalid R_profile schema"
        return prof

    # ---------------- Reflex Computation ----------------

    def compute_reflex(
        self,
        C_Mod: Dict[str, float],
        R_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:

        arche_weight = 1.0
        receptor_bias: Dict[str, float] = {}
        clamp_min, clamp_max = 0.1, 2.0

        if R_profile:
            arche_weight = R_profile["archetype"]["weight"]
            receptor_bias = R_profile.get("receptor_bias", {})
            cons = R_profile.get("constraints", {})
            clamp_min = cons.get("min", clamp_min)
            clamp_max = cons.get("max", clamp_max)

        CORE_REFLEXES = {
            "urgency_load": {"AD": 0.7, "CRH": 1.0},
            "cognitive_drive": {"DA": 1.0, "GLU": 0.8},
            "social_warmth": {"OX": 1.0, "5HT": 0.8},
            "withdrawal": {"CT": 1.0, "GABA": 0.7},
        }

        reflex_vector: Dict[str, float] = {}

        for reflex, chems in CORE_REFLEXES.items():
            acc = 0.0

            for chem, weight in chems.items():
                C = C_Mod.get(chem, 0.0)

                # Receptor sensitivity
                R_base = receptor_bias.get(chem, 1.0)
                R_eff = arche_weight * R_base

                # Chronic internalization
                internal = self.internalization.get(chem, 0.0)
                R_eff = clamp(R_eff * (1.0 - internal), clamp_min, clamp_max)

                # Hill PD
                H = self.hill(C)

                acc += H * R_eff * weight

                # Update internalization slowly
                self.internalization[chem] = clamp(
                    internal + (C * 0.01), 0.0, 0.5
                )

            reflex_vector[reflex] = clamp(acc, 0.0, 1.0)

        # -----------------------------------------------------------------
        # Standardized threat_level for RMS
        # -----------------------------------------------------------------
        reflex_vector["threat_level"] = clamp(
            reflex_vector.get("urgency_load", 0.0) +
            reflex_vector.get("withdrawal", 0.0),
            0.0,
            1.0
        )

        return reflex_vector


# -----------------------------------------------------------------------------
# ESS Context
# -----------------------------------------------------------------------------

@dataclass
class ESSContext:
    ess_id: str
    session_id: str
    episode_id: str
    start_ts: float = field(default_factory=time.time)


# -----------------------------------------------------------------------------
# ESS — Emotive Signaling System
# -----------------------------------------------------------------------------

class ESS:
    """
    System boundary for embodied emotive signaling.
    """

    def __init__(self, isr: ISR, ire: IRE, base_path: Path = Path("ESS")):
        self.isr = isr
        self.ire = ire
        self.base_path = base_path
        ensure_dir(self.base_path)

        self.context: Optional[ESSContext] = None
        self.tick_index = 0

    # ---------------- Lifecycle ----------------

    def start(self, session_id: str, episode_id: str) -> str:
        ess_id = f"ESS_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        self.context = ESSContext(
            ess_id=ess_id,
            session_id=session_id,
            episode_id=episode_id
        )
        self.tick_index = 0
        ensure_dir(self._ess_dir())
        return ess_id

    def close(self):
        self.context = None

    # ---------------- Tick ----------------

    def tick_once(
        self,
        stimulus_vector: Dict[str, float],
        D_Total_H: Dict[str, float],
        R_profile_path: Optional[Path] = None,
        delta_t_ms: int = 33
    ) -> Dict[str, Any]:

        assert self.context is not None, "ESS not started"
        self.tick_index += 1

        # PK
        C_Mod, D_Remaining, Rate_Actual = self.isr.update(
            D_Total_H, delta_t_ms
        )

        # Persona bias
        R_profile = None
        if R_profile_path:
            R_profile = self.ire.load_R_profile(R_profile_path)

        # PD + Reflex
        reflex_vector = self.ire.compute_reflex(C_Mod, R_profile)

        # Log telemetry
        self._log_tick(
            stimulus_vector,
            C_Mod,
            D_Remaining,
            Rate_Actual,
            delta_t_ms
        )

        # Official ESS output
        return {
            "C_Mod": C_Mod,
            "reflex_vector": reflex_vector
        }

    # ---------------- Logging ----------------

    def _log_tick(
        self,
        stimulus_vector: Dict[str, float],
        C_Mod: Dict[str, float],
        D_Remaining: Dict[str, float],
        Rate_Actual: Dict[str, float],
        delta_t_ms: int
    ):
        ctx = self.context
        assert ctx is not None

        record = {
            "schema": "EVA-ESS-Log-v1",
            "ess_id": ctx.ess_id,
            "episode_id": ctx.episode_id,
            "tick_index": self.tick_index,
            "timestamp": now_iso(),
            "stimulus_vector": stimulus_vector,
            "C_Mod": C_Mod,
            "D_Remaining": D_Remaining,
            "Rate_Actual": Rate_Actual,
            "time_tracking": {
                "delta_t_ms": delta_t_ms,
                "uptime_ms": int((time.time() - ctx.start_ts) * 1000)
            }
        }

        log_path = self._ess_dir() / "ess_log.jsonl"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # ---------------- Internal ----------------

    def _ess_dir(self) -> Path:
        assert self.context is not None
        return self.base_path / self.context.ess_id
