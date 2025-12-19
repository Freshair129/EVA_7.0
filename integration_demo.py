# =============================================================================
# EVA 7.0 INTEGRATION DEMO
# Full Pipeline: LLM → EHM → ESS → EVA Matrix → Artifact Qualia → RMS
# =============================================================================

import sys
from pathlib import Path

# Add component paths
sys.path.append(str(Path(__file__).parent / "ESS_Emotive_Signaling_System"))
sys.path.append(str(Path(__file__).parent / "EVA_Metric"))
sys.path.append(str(Path(__file__).parent / "Artifact_Qualia"))
sys.path.append(str(Path(__file__).parent / "Resonance_Memory_System"))

# Import components
from EHM import EHM
from ESS import ESS, ISR, IRE
from eva_matrix_engine import EVAMatrix9D_CompleteEngine
from Artifact_Qualia import ArtifactQualiaCore, RIMSemantic
from rms_v6 import RMSEngineV6

# =============================================================================
# Configuration
# =============================================================================

# ESS half-life configuration (seconds)
HALF_LIFE = {
    "AD": 120,      # Adrenaline
    "DA": 60,       # Dopamine
    "CT": 3600,     # Cortisol
    "5HT": 1800,    # Serotonin
    "NA": 300,      # Noradrenaline
    "CRH": 600,     # CRH
    "TEST": 7200,   # Testosterone
    "CORT": 5400,   # Corticosterone
    "ES": 14400,    # Estrogen
    "PRL": 1800,    # Prolactin
    "MT": 3600,     # Melatonin
    "OX": 180,      # Oxytocin
    "VP": 600,      # Vasopressin
    "EN": 300,      # Endorphin
    "ACh": 10,      # Acetylcholine
    "DYN": 600,     # Dynorphin
    "GABA": 30,     # GABA
    "GLU": 60,      # Glutamate
    "HIS": 300,     # Histamine
    "AEA": 600,     # Anandamide
    "BDNF": 86400,  # BDNF (long-term)
    "NPY": 1800,    # NPY
    "PEA": 60,      # PEA
}


# =============================================================================
# EVA Pipeline
# =============================================================================

class EVAPipeline:
    """
    Complete EVA processing pipeline
    """

    def __init__(self):
        print("[Pipeline] Initializing EVA components...")

        # Initialize all components
        self.ehm = EHM()
        self.isr = ISR(HALF_LIFE)
        self.ire = IRE()
        self.ess = ESS(self.isr, self.ire, base_path=Path("ESS_logs"))
        self.eva_matrix = EVAMatrix9D_CompleteEngine()
        self.artifact_qualia = ArtifactQualiaCore()
        self.rms = RMSEngineV6()

        # Start ESS session
        self.ess_id = self.ess.start(
            session_id="integration_demo",
            episode_id="demo_001"
        )

        print(f"[Pipeline] ESS session started: {self.ess_id}")
        print("[Pipeline] All components ready!\n")

    def process(self, stimulus_vector: dict, rim_semantic: dict = None, delta_t_ms: int = 33):
        """
        Process one tick through the full pipeline

        Args:
            stimulus_vector: From LLM Phase 1 (e.g., {"stress": 0.8, "warmth": 0.3})
            rim_semantic: RIM context (e.g., {"impact_level": "medium", "impact_trend": "stable"})
            delta_t_ms: Time delta in milliseconds

        Returns:
            Complete output from all components
        """

        print("="*80)
        print("EVA PIPELINE PROCESSING")
        print("="*80)

        # Default RIM semantic
        if rim_semantic is None:
            rim_semantic = {
                "impact_level": "medium",
                "impact_trend": "stable"
            }

        # -------------------------------------------------------------------------
        # 1. EHM: Stimulus → Hormone Doses
        # -------------------------------------------------------------------------
        print("\n[1] EHM: Mapping stimulus to hormone doses...")
        D_Total_H = self.ehm.map(stimulus_vector)

        # Show top hormones
        top_hormones = sorted(D_Total_H.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"    Top 5 hormones:")
        for chem, dose in top_hormones:
            unit = self.ehm.chemicals[chem].get("unit", "N/A").replace("μ", "u")
            print(f"      {chem}: {dose:.2f} {unit}")

        # -------------------------------------------------------------------------
        # 2. ESS: Hormone Doses → C_Mod + Reflexes
        # -------------------------------------------------------------------------
        print("\n[2] ESS: Processing PK/PD...")
        ess_output = self.ess.tick_once(
            stimulus_vector=stimulus_vector,
            D_Total_H=D_Total_H,
            R_profile_path=None,  # Optional: persona bias
            delta_t_ms=delta_t_ms
        )

        C_Mod = ess_output["C_Mod"]
        reflex_vector = ess_output["reflex_vector"]

        print(f"    Reflex Vector:")
        for reflex, value in reflex_vector.items():
            print(f"      {reflex}: {value:.3f}")

        # -------------------------------------------------------------------------
        # 3. EVA Matrix: C_Mod → 9D Psychological State
        # -------------------------------------------------------------------------
        print("\n[3] EVA Matrix: Transforming to 9D state...")
        eva_output = self.eva_matrix.process_tick(C_Mod)
        eva_state = eva_output["axes_9d"]

        print(f"    5D Core Axes:")
        print(f"      stress_load: {eva_state['stress_load']:.3f}")
        print(f"      social_warmth: {eva_state['social_warmth']:.3f}")
        print(f"      drive_level: {eva_state['drive_level']:.3f}")
        print(f"      cognitive_clarity: {eva_state['cognitive_clarity']:.3f}")
        print(f"      joy_level: {eva_state['joy_level']:.3f}")

        # -------------------------------------------------------------------------
        # 4. Artifact Qualia: EVA State + RIM → Phenomenology
        # -------------------------------------------------------------------------
        print("\n[4] Artifact Qualia: Integrating phenomenology...")
        rim_obj = RIMSemantic(
            impact_level=rim_semantic["impact_level"],
            impact_trend=rim_semantic["impact_trend"],
            affected_domains=["emotional", "relational"]
        )

        qualia = self.artifact_qualia.integrate(eva_state, rim_obj)

        print(f"    Qualia Snapshot:")
        print(f"      intensity: {qualia.intensity:.3f}")
        print(f"      tone: {qualia.tone}")
        print(f"      coherence: {qualia.coherence:.3f}")
        print(f"      depth: {qualia.depth:.3f}")

        # -------------------------------------------------------------------------
        # 5. RMS: EVA State + Reflexes → Memory Encoding
        # -------------------------------------------------------------------------
        print("\n[5] RMS: Encoding memory texture...")
        rms_output = self.rms.process(eva_state, reflex_vector, rim_semantic)

        print(f"    Memory Encoding:")
        print(f"      intensity: {rms_output.intensity:.3f}")
        print(f"      trauma_flag: {rms_output.trauma_flag}")
        print(f"      memory_color (top 3):")

        top_colors = sorted(rms_output.memory_color.items(), key=lambda x: x[1], reverse=True)[:3]
        for color_axis, value in top_colors:
            print(f"        {color_axis}: {value:.3f}")

        # -------------------------------------------------------------------------
        # Return Complete Output
        # -------------------------------------------------------------------------
        print("\n" + "="*80)
        print("PIPELINE COMPLETE")
        print("="*80 + "\n")

        return {
            "stimulus_vector": stimulus_vector,
            "D_Total_H": D_Total_H,
            "C_Mod": C_Mod,
            "reflex_vector": reflex_vector,
            "eva_state": eva_state,
            "qualia": qualia,
            "rms_output": rms_output
        }


# =============================================================================
# Demo Scenarios
# =============================================================================

def demo_scenario_1_high_stress():
    """Scenario 1: User is stressed and anxious"""

    print("\n" + "="*80)
    print("SCENARIO 1: HIGH STRESS & ANXIETY")
    print("="*80 + "\n")

    pipeline = EVAPipeline()

    # Simulate LLM Phase 1 output
    stimulus = {
        "stress": 0.9,
        "danger": 0.7,
        "uncertainty": 0.8,
        "social_threat": 0.6
    }

    rim = {
        "impact_level": "high",
        "impact_trend": "rising"
    }

    result = pipeline.process(stimulus, rim)

    return result


def demo_scenario_2_warmth():
    """Scenario 2: User is feeling warmth and connection"""

    print("\n" + "="*80)
    print("SCENARIO 2: WARMTH & CONNECTION")
    print("="*80 + "\n")

    pipeline = EVAPipeline()

    stimulus = {
        "affection": 0.9,
        "social_safety": 0.8,
        "touch": 0.7,
        "comfort": 0.6,
        "calm": 0.5
    }

    rim = {
        "impact_level": "medium",
        "impact_trend": "stable"
    }

    result = pipeline.process(stimulus, rim)

    return result


def demo_scenario_3_mixed():
    """Scenario 3: Mixed emotions (stress + hope)"""

    print("\n" + "="*80)
    print("SCENARIO 3: MIXED (STRESS + HOPE)")
    print("="*80 + "\n")

    pipeline = EVAPipeline()

    stimulus = {
        "stress": 0.6,
        "hope": 0.7,
        "novelty": 0.5,
        "cognitive_load": 0.8,
        "focus": 0.6
    }

    rim = {
        "impact_level": "medium",
        "impact_trend": "rising"
    }

    result = pipeline.process(stimulus, rim)

    return result


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("EVA 7.0 FULL PIPELINE INTEGRATION DEMO")
    print("="*80)

    # Run all scenarios
    demo_scenario_1_high_stress()
    demo_scenario_2_warmth()
    demo_scenario_3_mixed()

    print("\n" + "="*80)
    print("ALL SCENARIOS COMPLETE")
    print("="*80 + "\n")
