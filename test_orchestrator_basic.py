"""
Test Two-Phase Orchestrator (Basic - No LLM Required)

This test verifies the orchestrator structure without actual LLM calls
"""

import sys
from pathlib import Path

# Add paths
sys.path.append(str(Path(__file__).parent / "Orchestrator"))

from eva_tool import EVATool

def test_eva_tool_integration():
    """Test EVA Tool integration"""
    print("="*80)
    print("EVA TOOL INTEGRATION TEST")
    print("="*80)

    # Initialize EVA Tool
    eva_tool = EVATool(enable_msp=False)
    eva_tool.start_session("integration_test", "test_001")

    # Test Case 1: High Stress
    print("\n[TEST 1] High Stress Stimulus")
    result1 = eva_tool.process(
        stimulus_vector={"stress": 0.9, "anxiety": 0.8, "threat": 0.7},
        ri_data={
            "RI_L1": 0.8, "RI_L2": 0.7, "RI_L3": 0.5, "RI_L4": 0.9,
            "RI_L5": {}, "RI_global": 0.75,
            "RZ_state": {"RZ_active": False, "RZ_class": "NORMAL"}
        },
        umbrella={"safety_level": "HIGH"}
    )

    print(f"[OK] Pulse Mode: {result1.pulse_snapshot['pulse_mode']}")
    print(f"[OK] Arousal: {result1.pulse_snapshot['arousal_level']:.2f}")
    print(f"[OK] Safety Actions: {result1.pulse_snapshot['safety_actions']}")
    print(f"[OK] Trauma Flag: {result1.memory_encoding['trauma_flag']}")

    # Assertions
    assert result1.pulse_snapshot['arousal_level'] > 0.5, "High stress should have high arousal"
    assert result1.reflex_directives['threat_level'] > 0.5, "Threat level should be elevated"

    # Test Case 2: Warmth & Connection
    print("\n[TEST 2] Warmth & Connection Stimulus")
    result2 = eva_tool.process(
        stimulus_vector={"warmth": 0.9, "bonding": 0.8, "affection": 0.7},
        ri_data={
            "RI_L1": 0.3, "RI_L2": 0.4, "RI_L3": 0.9, "RI_L4": 0.3,
            "RI_L5": {"O5_intimacy": 0.85, "O3_empathic_resonance": 0.8},
            "RI_global": 0.6,
            "RZ_state": {"RZ_active": False, "RZ_class": "NORMAL"}
        },
        umbrella={"safety_level": "LOW"}
    )

    print(f"[OK] Pulse Mode: {result2.pulse_snapshot['pulse_mode']}")
    print(f"[OK] Valence: {result2.pulse_snapshot['valence_level']:.2f}")
    print(f"[OK] Warmth Flag: {result2.pulse_snapshot['llm_prompt_flags']['warmth']:.2f}")
    print(f"[OK] Trauma Flag: {result2.memory_encoding['trauma_flag']}")

    # Assertions
    assert result2.pulse_snapshot['pulse_mode'] == "DEEP_CARE", "Should be in DEEP_CARE mode"
    assert result2.pulse_snapshot['llm_prompt_flags']['warmth'] > 0.8, "Warmth flag should be high"

    # Test Case 3: Cognitive Task
    print("\n[TEST 3] Cognitive Task Stimulus")
    result3 = eva_tool.process(
        stimulus_vector={"novelty": 0.7, "curiosity": 0.6, "mastery": 0.5},
        ri_data={
            "RI_L1": 0.5, "RI_L2": 0.6, "RI_L3": 0.4, "RI_L4": 0.8,
            "RI_L5": {}, "RI_global": 0.6,
            "RZ_state": {"RZ_active": False, "RZ_class": "NORMAL"}
        },
        umbrella={"safety_level": "LOW"}
    )

    print(f"[OK] Pulse Mode: {result3.pulse_snapshot['pulse_mode']}")
    print(f"[OK] Cognitive Mode: {result3.pulse_snapshot['cognitive_mode']}")
    print(f"[OK] Directness Flag: {result3.pulse_snapshot['llm_prompt_flags']['directness']:.2f}")

    # End session
    eva_tool.end_session()

    print("\n" + "="*80)
    print("ALL TESTS PASSED [OK]")
    print("="*80)


def test_orchestrator_structure():
    """Test orchestrator can be imported and initialized"""
    print("\n" + "="*80)
    print("ORCHESTRATOR STRUCTURE TEST")
    print("="*80)

    try:
        from two_phase_orchestrator import TwoPhaseOrchestrator, Phase1Output, OrchestrationResult
        print("[OK] Orchestrator classes imported successfully")

        # Test data structures
        test_phase1 = Phase1Output(
            intent="test",
            stimulus_vector={"stress": 0.5},
            emotion_detected="neutral",
            call_eva_tool=False,
            reasoning="test",
            raw_response="test"
        )
        print("[OK] Phase1Output dataclass works")

        print("\n[INFO] To test full orchestrator with LLM:")
        print("  1. Set GOOGLE_API_KEY in .env file")
        print("  2. Run: python Orchestrator/two_phase_orchestrator.py")

    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False

    print("\n" + "="*80)
    print("STRUCTURE TEST PASSED [OK]")
    print("="*80)

    return True


if __name__ == "__main__":
    # Run tests
    test_eva_tool_integration()
    test_orchestrator_structure()

    print("\n" + "="*80)
    print("BASIC ORCHESTRATOR TESTS COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("  1. Add GOOGLE_API_KEY to .env file")
    print("  2. Test with real LLM: python Orchestrator/two_phase_orchestrator.py")
    print("  3. Integrate CIN v6 for full context injection")
    print("  4. Add MSP memory query and write")
