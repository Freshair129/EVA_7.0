"""k_impact_engine.py
EVA 6.0 — K_Impact Engine

This module computes K_Impact: a 0.0–1.0 scalar that represents
how important a given episode is for long‑term knowledge formation
(GKS, meta‑learning, promotion to blocks, etc.).

It is intentionally separated from MAS_engine so that:
- MAS_engine can remain a generic metric hub (no GKS‑specific logic)
- K_Impact can evolve with GKS / meta‑learning without breaking other systems

Dependencies (expected interfaces)
----------------------------------
This module expects MAS_engine to expose:

    from dataclasses import dataclass

    @dataclass
    class MeaningInputs:
        self_identity: float
        self_discrepancy: float
        self_compassion: float
        relation_bond: float
        relation_belonging: float
        world_purpose: float
        world_belief_shift: float

    @dataclass
    class IntegrationInputs:
        paradox_tension: float
        reframe_depth: float
        symbolic_density: float
        trauma_link: float
        temporal_integration: float

    @dataclass
    class EthicalInputs:
        harm_risk: float
        value_conflict: float
        autonomy_risk: float
        boundary_violate: float
        conscience_ping: float

    def compute_m_core(m: MeaningInputs) -> float: ...
    def compute_i_core(i: IntegrationInputs) -> float: ...
    def compute_e_core(e: EthicalInputs) -> float: ...

If your MAS_engine uses slightly different names, adapt the imports
below accordingly.
"""

from __future__ import annotations

from dataclasses import dataclass

# NOTE: these imports assume MAS_engine implements the interfaces described above.
# If needed, adjust module / symbol names to match your codebase.
try:
    from MAS_engine import (
        MeaningInputs,
        IntegrationInputs,
        EthicalInputs,
        compute_m_core,
        compute_i_core,
        compute_e_core,
    )
except ImportError:
    # Lightweight fallback types so this module can be imported in isolation
    # (e.g. during early development or static analysis).
    # In production EVA, MAS_engine MUST be available.
    @dataclass
    class MeaningInputs:  # type: ignore[override]
        self_identity: float
        self_discrepancy: float
        self_compassion: float
        relation_bond: float
        relation_belonging: float
        world_purpose: float
        world_belief_shift: float

    @dataclass
    class IntegrationInputs:  # type: ignore[override]
        paradox_tension: float
        reframe_depth: float
        symbolic_density: float
        trauma_link: float
        temporal_integration: float

    @dataclass
    class EthicalInputs:  # type: ignore[override]
        harm_risk: float
        value_conflict: float
        autonomy_risk: float
        boundary_violate: float
        conscience_ping: float

    def compute_m_core(m: MeaningInputs) -> float:  # type: ignore[override]
        # simple placeholder: unweighted average
        vals = [
            m.self_identity,
            m.self_discrepancy,
            m.self_compassion,
            m.relation_bond,
            m.relation_belonging,
            m.world_purpose,
            m.world_belief_shift,
        ]
        return sum(vals) / len(vals)

    def compute_i_core(i: IntegrationInputs) -> float:  # type: ignore[override]
        vals = [
            i.paradox_tension,
            i.reframe_depth,
            i.symbolic_density,
            i.trauma_link,
            i.temporal_integration,
        ]
        return sum(vals) / len(vals)

    def compute_e_core(e: EthicalInputs) -> float:  # type: ignore[override]
        vals = [
            e.harm_risk,
            e.value_conflict,
            e.autonomy_risk,
            e.boundary_violate,
            e.conscience_ping,
        ]
        return sum(vals) / len(vals)


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp scalar x into [lo, hi]."""
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


@dataclass
class KImpactInputs:
    """Inputs required to compute K_Impact for a single episode.

    All scalar values must be normalised into [0.0, 1.0] *before* calling
    this engine.

    Attributes
    ----------
    ri_global:
        Global resonance score (0–1) from ri_engine.

    rim_score:
        Interaction impact score (0–1) from rim_engine.

    meaning:
        MeaningInputs describing how strongly this episode touches
        self / relation / world meaning.

    integration:
        IntegrationInputs describing paradox / reframe / trauma / temporal
        integration for this episode.

    ethical:
        EthicalInputs describing harm risk, value conflict, autonomy risk,
        boundary risk, and conscience activation.
    """

    ri_global: float
    rim_score: float
    meaning: MeaningInputs
    integration: IntegrationInputs
    ethical: EthicalInputs


@dataclass
class KImpactResult:
    """Full result bundle for K_Impact computation.

    Attributes
    ----------
    k_impact:
        Final K_Impact in [0.0, 1.0]. This is the primary scalar used by
        GKS / Meta Learning Loop / block promotion.

    core:
        Core impact before ethical bonus.

    risk_conscience:
        Aggregate risk / conscience score in [0.0, 1.0].

    bonus:
        Bonus added on top of `core` based on `risk_conscience`.

    m_core, i_core, e_core:
        Meaning / Integration / Ethical core scores actually used in
        the computation, exposed here for diagnostics and logging.
    """

    k_impact: float
    core: float
    risk_conscience: float
    bonus: float
    m_core: float
    i_core: float
    e_core: float


def _compute_risk_conscience(
    e_core: float, ri_global: float, rim_score: float
) -> float:
    """Compute aggregated risk / conscience signal R_risk_conscience.

    Formula (from K_Impact_Variables_v1 spec):

        R_risk_conscience_raw =
            0.70 * E_core    +
            0.15 * RIM_score +
            0.15 * RI_global

        R_risk_conscience = clamp(R_risk_conscience_raw, 0.0, 1.0)
    """
    raw = 0.70 * e_core + 0.15 * rim_score + 0.15 * ri_global
    return clamp(raw, 0.0, 1.0)


def _risk_bonus(r_risk_conscience: float) -> float:
    """Map risk / conscience aggregate into a bonus term.

    Step function (from spec):

        if R_risk_conscience <= 0.2:  bonus = 0.00
        elif <= 0.5:                  bonus = 0.05
        elif <= 0.8:                  bonus = 0.10
        else:                         bonus = 0.15
    """
    x = r_risk_conscience
    if x <= 0.2:
        return 0.00
    if x <= 0.5:
        return 0.05
    if x <= 0.8:
        return 0.10
    return 0.15


def compute_k_impact(inputs: KImpactInputs) -> KImpactResult:
    """Compute K_Impact for a single episode.

    This is the *only* public function most systems need to call.

    Steps
    -----
    1. Compute M_core / I_core / E_core via MAS_engine.
    2. Compute `core` impact:

           core =
               0.135 * RIM_score +
               0.230 * RI_global +
               0.325 * M_core    +
               0.310 * I_core

    3. Compute aggregated risk / conscience:

           R_risk_conscience = f(E_core, RIM_score, RI_global)

    4. Map that into `bonus` in {0.0, 0.05, 0.10, 0.15}.
    5. K_raw = core + bonus, then clamp to [0.0, 1.0].

    Returns
    -------
    KImpactResult
        Bundle containing k_impact and all intermediate scores for logging.
    """
    ri_global = clamp(inputs.ri_global, 0.0, 1.0)
    rim_score = clamp(inputs.rim_score, 0.0, 1.0)

    m_core = clamp(compute_m_core(inputs.meaning), 0.0, 1.0)
    i_core = clamp(compute_i_core(inputs.integration), 0.0, 1.0)
    e_core = clamp(compute_e_core(inputs.ethical), 0.0, 1.0)

    core = (
        0.135 * rim_score +
        0.230 * ri_global +
        0.325 * m_core +
        0.310 * i_core
    )

    r_risk = _compute_risk_conscience(e_core=e_core,
                                      ri_global=ri_global,
                                      rim_score=rim_score)
    bonus = _risk_bonus(r_risk)

    k_raw = core + bonus
    k_impact = clamp(k_raw, 0.0, 1.0)

    return KImpactResult(
        k_impact=k_impact,
        core=core,
        risk_conscience=r_risk,
        bonus=bonus,
        m_core=m_core,
        i_core=i_core,
        e_core=e_core,
    )


__all__ = [
    "MeaningInputs",
    "IntegrationInputs",
    "EthicalInputs",
    "KImpactInputs",
    "KImpactResult",
    "compute_k_impact",
]
