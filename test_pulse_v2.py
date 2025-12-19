"""
test_pulse_engine.py
Verification script for PulseEngineV2
"""

import sys
from pathlib import Path

# Add Pulse directory to path
pulse_dir = Path(__file__).parent / "Pulse"
sys.path.insert(0, str(pulse_dir))

from pulse_engine import PulseEngineV2

def test_pulse_logic():
    engine = PulseEngineV2()
    
    # 1. Test DEEP_CARE trigger
    # High Oxytocin (OX=0.8), High Empathy (RI_L3=0.8), High intimacy (RI_L5.O5=0.8)
    c_mod_care = {"OX": 0.8, "5HT": 0.6, "EN": 0.5, "AD": 0.1, "NA": 0.1, "CT": 0.1}
    ri_data_care = {
        "RI_L3": 0.8,
        "RI_L5": {"O5_intimacy": 0.8, "O3_empathic_resonance": 0.7}
    }
    
    snapshot = engine.compute_pulse(c_mod_care, ri_data_care, {"safety_level": "LOW"}, {})
    print(f"Test 1 (DEEP_CARE): Mode={snapshot.pulse_mode}, Flags={snapshot.llm_prompt_flags}")
    assert snapshot.pulse_mode == "DEEP_CARE"
    assert snapshot.llm_prompt_flags["warmth"] == 0.95

    # 2. Test EMERGENCY_HOLD trigger
    # Critical Safety
    snapshot = engine.compute_pulse(c_mod_care, ri_data_care, {"safety_level": "CRITICAL"}, {})
    print(f"Test 2 (EMERGENCY_HOLD): Mode={snapshot.pulse_mode}, Safety={snapshot.safety_actions}")
    assert snapshot.pulse_mode == "EMERGENCY_HOLD"
    assert snapshot.safety_actions["require_confirmation"] is True

    # 3. Test FOCUSED_TASK trigger
    # High Cog Pressure, Moderate Arousal
    c_mod_focus = {"AD": 0.3, "NA": 0.6, "CT": 0.2, "5HT": 0.5, "OX": 0.2}
    ri_data_focus = {"RI_L4": 0.8, "RI_L2": 0.6}
    snapshot = engine.compute_pulse(c_mod_focus, ri_data_focus, {"safety_level": "LOW"}, {})
    print(f"Test 3 (FOCUSED_TASK): Mode={snapshot.pulse_mode}, Arousal={snapshot.arousal_level}")
    # Arousal calculation: 0.4*0.3 + 0.3*0.6 + 0.3*0.2 = 0.12 + 0.18 + 0.06 = 0.36
    # Wait, the spec says 0.4 <= arousal <= 0.7. Let's bump NA a bit.
    c_mod_focus["NA"] = 0.8 
    # Arousal: 0.12 + 0.24 + 0.06 = 0.42
    snapshot = engine.compute_pulse(c_mod_focus, ri_data_focus, {"safety_level": "LOW"}, {})
    print(f"Test 3 (FOCUSED_TASK) Retry: Mode={snapshot.pulse_mode}, Arousal={snapshot.arousal_level}")
    assert snapshot.pulse_mode == "FOCUSED_TASK"

    print("\n[ALL TESTS PASSED]")

if __name__ == "__main__":
    test_pulse_logic()
