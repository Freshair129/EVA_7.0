# =============================================================================
# EVA TOOL v1.0
# Unified Tool Interface for LLM Integration
#
# Architecture:
#   LLM Phase 1 (Cognitive Scan) → EVA Tool → LLM Phase 2 (Response Shaping)
#
# Pipeline:
#   Stimulus → EHM → ESS → EVA Matrix → Artifact Qualia → RMS → Pulse → MSP
#
# Outputs:
#   - Emotion state (9D EVA Matrix)
#   - Pulse snapshot (mode, arousal, flags)
#   - Reflex directives (urgency, cognitive_drive, withdrawal)
#   - Memory encoding (RMS output)
#   - Qualia snapshot (phenomenology)
#   - MSP references (if query enabled)
# =============================================================================

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import json

# Add component paths
base_path = Path(__file__).parent.parent
sys.path.append(str(base_path / "ESS_Emotive_Signaling_System"))
sys.path.append(str(base_path / "EVA_Metric"))
sys.path.append(str(base_path / "Artifact_Qualia"))
sys.path.append(str(base_path / "Resonance_Memory_System"))
sys.path.append(str(base_path / "Pulse"))
sys.path.append(str(base_path / "Memory_&_Soul_Passaport"))

# Import components
from EHM import EHM
from ESS import ESS, ISR, IRE
from eva_matrix_engine import EVAMatrix9D_CompleteEngine
from Artifact_Qualia import ArtifactQualiaCore, RIMSemantic
from rms_v6 import RMSEngineV6
from pulse_engine import PulseEngineV2
from MSP import MSP


# =============================================================================
# Configuration
# =============================================================================

# ESS half-life configuration (seconds)
HALF_LIFE = {
    "AD": 120, "DA": 60, "CT": 3600, "5HT": 1800, "NA": 300,
    "CRH": 600, "TEST": 7200, "CORT": 5400, "ES": 14400, "PRL": 1800,
    "MT": 3600, "OX": 180, "VP": 600, "EN": 300, "ACh": 10,
    "DYN": 600, "GABA": 30, "GLU": 60, "HIS": 300, "AEA": 600,
    "BDNF": 86400, "NPY": 1800, "PEA": 60
}


# =============================================================================
# Data Contracts
# =============================================================================

@dataclass
class EVAToolResult:
    """
    Complete EVA Tool output for LLM consumption
    """
    # Core state
    emotion_state: Dict[str, float]      # 9D EVA Matrix state
    pulse_snapshot: Dict[str, Any]       # Pulse mode, arousal, flags
    reflex_directives: Dict[str, float]  # Reflex vector from ESS

    # Memory & phenomenology
    qualia_snapshot: Dict[str, Any]      # Artifact Qualia output
    memory_encoding: Dict[str, Any]      # RMS output

    # MSP integration (optional)
    memory_refs: List[str]               # Episode references
    allowed_recall: List[Dict]           # Memory allowed for LLM

    # Metadata
    ess_id: str                          # ESS session ID
    timestamp: str                       # ISO timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


# =============================================================================
# EVA Tool
# =============================================================================

class EVATool:
    """
    Unified EVA Tool for LLM Integration

    Combines all deterministic EVA components into a single tool interface
    that LLMs can call during Phase 1 → Phase 2 inference.
    """

    def __init__(
        self,
        msp_base_path: Path = None,
        enable_msp: bool = True,
        validation_mode: str = "strict"
    ):
        """
        Initialize EVA Tool

        Args:
            msp_base_path: Path to MSP base directory (default: project root)
            enable_msp: Enable MSP memory operations (default: True)
            validation_mode: MSP validation mode - "strict" | "warn" | "off"
        """
        print("[EVATool] Initializing components...")

        # Set base path
        if msp_base_path is None:
            msp_base_path = Path(__file__).parent.parent
        self.base_path = msp_base_path

        # Initialize core components
        self.ehm = EHM()
        self.isr = ISR(HALF_LIFE)
        self.ire = IRE()
        self.ess = ESS(self.isr, self.ire, base_path=self.base_path / "ESS_logs")
        self.eva_matrix = EVAMatrix9D_CompleteEngine()
        self.artifact_qualia = ArtifactQualiaCore()
        self.rms = RMSEngineV6()
        self.pulse = PulseEngineV2()

        # Initialize MSP (optional)
        self.enable_msp = enable_msp
        self.msp = None
        self.msp_instance_id = None
        self.msp_session_id = None

        if self.enable_msp:
            try:
                self.msp = MSP(base_path=msp_base_path, validation_mode=validation_mode)
                print(f"[EVATool] MSP initialized (validation: {validation_mode})")
            except Exception as e:
                print(f"[EVATool] WARNING: MSP initialization failed: {e}")
                self.enable_msp = False

        # Session state
        self.ess_id = None
        self.current_episode_id = None

        print("[EVATool] Initialization complete!\n")


    def start_session(
        self,
        session_id: str = "eva_session",
        episode_id: str = "ep_001",
        origin_name: str = "EVA"
    ):
        """
        Start EVA session (ESS + MSP)

        Args:
            session_id: Session identifier
            episode_id: Episode identifier
            origin_name: MSP origin name (default: "EVA")
        """
        # Start ESS session
        self.ess_id = self.ess.start(
            session_id=session_id,
            episode_id=episode_id
        )
        print(f"[EVATool] ESS session started: {self.ess_id}")

        # Start MSP session
        if self.enable_msp and self.msp is not None:
            try:
                self.msp.load_origin(origin_name)
                self.msp_instance_id = self.msp.create_instance(f"{session_id}_instance")
                self.msp_session_id = self.msp.start_session(session_id)
                print(f"[EVATool] MSP session started: {self.msp_session_id}")
            except Exception as e:
                print(f"[EVATool] WARNING: MSP session start failed: {e}")


    def process(
        self,
        stimulus_vector: Dict[str, float],
        user_context: Dict[str, Any] = None,
        rim_semantic: Dict[str, str] = None,
        ri_data: Dict[str, Any] = None,
        umbrella: Dict[str, Any] = None,
        session_meta: Dict[str, Any] = None,
        delta_t_ms: int = 33
    ) -> EVAToolResult:
        """
        Process stimulus through complete EVA pipeline

        Args:
            stimulus_vector: From LLM Phase 1 (e.g., {"stress": 0.8, "warmth": 0.3})
            user_context: Optional user context from CIN
            rim_semantic: RIM semantic context (impact_level, impact_trend, affected_domains)
            ri_data: RI data for Pulse Engine (RI_L1-L5, RI_global, RZ_state)
            umbrella: Safety umbrella data (safety_level)
            session_meta: Session metadata
            delta_t_ms: Time delta in milliseconds (default: 33ms ≈ 30fps)

        Returns:
            EVAToolResult with complete pipeline output
        """

        # Set defaults
        if rim_semantic is None:
            rim_semantic = {
                "impact_level": "medium",
                "impact_trend": "stable",
                "affected_domains": ["emotional"]
            }

        if ri_data is None:
            ri_data = {
                "RI_L1": 0.5, "RI_L2": 0.5, "RI_L3": 0.5, "RI_L4": 0.5,
                "RI_L5": {}, "RI_global": 0.5,
                "RZ_state": {"RZ_active": False, "RZ_class": "NORMAL"}
            }

        if umbrella is None:
            umbrella = {"safety_level": "LOW"}

        if session_meta is None:
            session_meta = {"turn_count": 0}

        print(f"\n[EVATool] Processing stimulus: {stimulus_vector}")

        # -------------------------------------------------------------------------
        # 1. EHM: Stimulus → Hormone Doses
        # -------------------------------------------------------------------------
        D_Total_H = self.ehm.map(stimulus_vector)

        # -------------------------------------------------------------------------
        # 2. ESS: PK/PD Processing
        # -------------------------------------------------------------------------
        ess_output = self.ess.tick_once(
            stimulus_vector=stimulus_vector,
            D_Total_H=D_Total_H,
            R_profile_path=None,  # TODO: Add persona bias support
            delta_t_ms=delta_t_ms
        )

        C_Mod = ess_output["C_Mod"]
        reflex_vector = ess_output["reflex_vector"]

        # -------------------------------------------------------------------------
        # 3. EVA Matrix: C_Mod → 9D Psychological State
        # -------------------------------------------------------------------------
        eva_output = self.eva_matrix.process_tick(C_Mod)
        eva_state = eva_output["axes_9d"]

        # -------------------------------------------------------------------------
        # 4. Pulse Engine v2: Operational Rhythm
        # -------------------------------------------------------------------------
        pulse_snapshot = self.pulse.compute_pulse(
            c_mod=C_Mod,
            ri_data=ri_data,
            umbrella=umbrella,
            session_meta=session_meta
        )

        # -------------------------------------------------------------------------
        # 5. Artifact Qualia: Phenomenological Integration
        # -------------------------------------------------------------------------
        rim_obj = RIMSemantic(
            impact_level=rim_semantic["impact_level"],
            impact_trend=rim_semantic["impact_trend"],
            affected_domains=rim_semantic["affected_domains"]
        )

        qualia = self.artifact_qualia.integrate(eva_state, rim_obj)

        # -------------------------------------------------------------------------
        # 6. RMS: Memory Encoding
        # -------------------------------------------------------------------------
        rms_output = self.rms.process(eva_state, reflex_vector, rim_semantic)

        # -------------------------------------------------------------------------
        # 7. MSP: Memory Query & Write (optional)
        # -------------------------------------------------------------------------
        memory_refs = []
        allowed_recall = []

        if self.enable_msp and self.msp is not None and user_context is not None:
            # TODO: Implement MSP query based on user_context
            # TODO: Write episode if needed
            pass

        # -------------------------------------------------------------------------
        # 8. Build Tool Result
        # -------------------------------------------------------------------------
        from datetime import datetime, timezone

        result = EVAToolResult(
            emotion_state=eva_state,
            pulse_snapshot={
                "pulse_id": pulse_snapshot.pulse_id,
                "pulse_mode": pulse_snapshot.pulse_mode,
                "arousal_level": pulse_snapshot.arousal_level,
                "valence_level": pulse_snapshot.valence_level,
                "cognitive_mode": pulse_snapshot.cognitive_mode,
                "pacing": pulse_snapshot.pacing,
                "llm_prompt_flags": pulse_snapshot.llm_prompt_flags,
                "safety_actions": pulse_snapshot.safety_actions,
                "debug_tags": pulse_snapshot.debug_tags
            },
            reflex_directives=reflex_vector,
            qualia_snapshot={
                "intensity": qualia.intensity,
                "tone": qualia.tone,
                "coherence": qualia.coherence,
                "depth": qualia.depth,
                "texture": qualia.texture
            },
            memory_encoding={
                "memory_color": rms_output.memory_color,
                "intensity": rms_output.intensity,
                "trauma_flag": rms_output.trauma_flag
            },
            memory_refs=memory_refs,
            allowed_recall=allowed_recall,
            ess_id=self.ess_id or "no_session",
            timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        )

        print(f"[EVATool] Processing complete")
        print(f"  Pulse Mode: {pulse_snapshot.pulse_mode}")
        print(f"  Arousal: {pulse_snapshot.arousal_level:.3f}")
        print(f"  Threat Level: {reflex_vector.get('threat_level', 0):.3f}")
        print(f"  Trauma Flag: {rms_output.trauma_flag}")

        return result


    def end_session(self):
        """
        End EVA session (ESS + MSP)
        """
        # End ESS session
        if self.ess_id:
            self.ess.close()
            print(f"[EVATool] ESS session ended: {self.ess_id}")

        # End MSP session
        if self.enable_msp and self.msp is not None and self.msp_session_id:
            try:
                session_summary = self.msp.end_session()
                print(f"[EVATool] MSP session ended: {self.msp_session_id}")
                print(f"  Episodes written: {session_summary.get('episode_count', 0)}")
            except Exception as e:
                print(f"[EVATool] WARNING: MSP session end failed: {e}")


# =============================================================================
# Testing
# =============================================================================

if __name__ == "__main__":
    print("="*80)
    print("EVA TOOL TEST")
    print("="*80)

    # Initialize EVA Tool (without MSP for testing)
    eva_tool = EVATool(enable_msp=False)

    # Start session
    eva_tool.start_session(session_id="test_session", episode_id="test_001")

    # Test stimulus 1: High stress
    print("\n" + "="*80)
    print("TEST 1: HIGH STRESS")
    print("="*80)

    result1 = eva_tool.process(
        stimulus_vector={"stress": 0.9, "threat": 0.8},
        ri_data={"RI_L1": 0.7, "RI_L2": 0.6, "RI_L3": 0.5, "RI_L4": 0.8,
                 "RI_L5": {}, "RI_global": 0.65,
                 "RZ_state": {"RZ_active": False, "RZ_class": "NORMAL"}},
        umbrella={"safety_level": "MEDIUM"}
    )

    print(f"\nResult:")
    print(f"  Pulse Mode: {result1.pulse_snapshot['pulse_mode']}")
    print(f"  Arousal: {result1.pulse_snapshot['arousal_level']}")
    print(f"  Warmth Flag: {result1.pulse_snapshot['llm_prompt_flags']['warmth']}")

    # Test stimulus 2: Warmth & connection
    print("\n" + "="*80)
    print("TEST 2: WARMTH & CONNECTION")
    print("="*80)

    result2 = eva_tool.process(
        stimulus_vector={"warmth": 0.9, "bonding": 0.8},
        ri_data={"RI_L1": 0.4, "RI_L2": 0.5, "RI_L3": 0.85, "RI_L4": 0.4,
                 "RI_L5": {"O5_intimacy": 0.8, "O3_empathic_resonance": 0.7},
                 "RI_global": 0.6,
                 "RZ_state": {"RZ_active": False, "RZ_class": "NORMAL"}},
        umbrella={"safety_level": "LOW"}
    )

    print(f"\nResult:")
    print(f"  Pulse Mode: {result2.pulse_snapshot['pulse_mode']}")
    print(f"  Valence: {result2.pulse_snapshot['valence_level']}")
    print(f"  Warmth Flag: {result2.pulse_snapshot['llm_prompt_flags']['warmth']}")

    # End session
    eva_tool.end_session()

    print("\n" + "="*80)
    print("EVA TOOL TEST COMPLETE")
    print("="*80)
