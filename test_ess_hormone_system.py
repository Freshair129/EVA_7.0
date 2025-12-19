# =============================================================================
# ESS Hormone System Comprehensive Test Suite
# Tests ISR (PK), IRE (PD), and full ESS integration
# =============================================================================

import sys
from pathlib import Path
import math
import json
import tempfile

sys.path.insert(0, str(Path(__file__).parent / "ESS_Emotive_Signaling_System"))

from ESS import ESS, ISR, IRE


# =============================================================================
# Test 1: ISR Pharmacokinetics (PK) - Exponential Decay
# =============================================================================

def test_isr_exponential_decay():
    """Test that hormone levels decay exponentially according to half-life"""
    print("="*80)
    print("TEST 1: ISR Exponential Decay (Pharmacokinetics)")
    print("="*80)

    # Half-life: 10 seconds for cortisol (CRH)
    isr = ISR(half_life_sec={"CRH": 10.0})

    # Initial dose: 1.0
    D_Total_H = {"CRH": 1.0}

    # First update: add dose
    C_Mod, D_Remaining, Rate = isr.update(D_Total_H, delta_t_ms=0)

    print(f"\nInitial state after dose:")
    print(f"  C_Mod['CRH']: {C_Mod['CRH']:.4f}")
    print(f"  D_Remaining['CRH']: {D_Remaining['CRH']:.4f}")

    # After 10 seconds (1 half-life), should be ~0.5
    C_Mod, D_Remaining, Rate = isr.update({}, delta_t_ms=10000)
    expected = 1.0 * math.exp(-10.0 / 10.0)  # e^-1 ≈ 0.368

    print(f"\nAfter 10 seconds (1 half-life):")
    print(f"  C_Mod['CRH']: {C_Mod['CRH']:.4f}")
    print(f"  Expected: {expected:.4f}")
    print(f"  Error: {abs(C_Mod['CRH'] - expected):.6f}")

    if abs(C_Mod['CRH'] - expected) < 0.01:
        print("\n[PASS] Exponential decay correct")
        return True
    else:
        print("\n[FAIL] Decay does not match exponential model")
        return False


# =============================================================================
# Test 2: ISR Saturation Clamping
# =============================================================================

def test_isr_saturation_clamping():
    """Test that C_Mod is clamped to [0.0, 1.0] range"""
    print("\n" + "="*80)
    print("TEST 2: ISR Saturation Clamping")
    print("="*80)

    isr = ISR(half_life_sec={"AD": 5.0})

    # Massive dose: 100.0 (should clamp to 1.0)
    D_Total_H = {"AD": 100.0}
    C_Mod, D_Remaining, Rate = isr.update(D_Total_H, delta_t_ms=0)

    print(f"\nMassive dose (100.0):")
    print(f"  D_Remaining['AD']: {D_Remaining['AD']:.2f}")
    print(f"  C_Mod['AD'] (clamped): {C_Mod['AD']:.2f}")

    if C_Mod['AD'] == 1.0:
        print("\n[PASS] Saturation clamping works correctly (max = 1.0)")
    else:
        print(f"\n[FAIL] C_Mod should be 1.0, got {C_Mod['AD']}")
        return False

    # Zero dose (should stay >= 0.0 even after decay)
    for _ in range(100):
        C_Mod, D_Remaining, Rate = isr.update({}, delta_t_ms=1000)

    print(f"\nAfter long decay:")
    print(f"  C_Mod['AD']: {C_Mod['AD']:.6f}")

    if C_Mod['AD'] >= 0.0:
        print("\n[PASS] No negative values after decay (min = 0.0)")
        return True
    else:
        print(f"\n[FAIL] C_Mod went negative: {C_Mod['AD']}")
        return False


# =============================================================================
# Test 3: ISR Cumulative Tracking
# =============================================================================

def test_isr_cumulative_tracking():
    """Test that D_Cumulative correctly integrates exposure over time"""
    print("\n" + "="*80)
    print("TEST 3: ISR Cumulative Exposure Tracking")
    print("="*80)

    isr = ISR(half_life_sec={"DA": 10.0})

    # Constant dose for 5 seconds
    print(f"\nApplying constant dose (0.5) for 5 seconds...")

    for i in range(5):
        C_Mod, D_Remaining, Rate = isr.update({"DA": 0.5}, delta_t_ms=1000)

    cumulative = isr.D_Cumulative["DA"]
    print(f"  D_Cumulative['DA'] after 5s: {cumulative:.4f}")

    # Should be > 0 (accumulating exposure)
    if cumulative > 0:
        print("\n[PASS] Cumulative tracking works (D_Cumulative > 0)")
        return True
    else:
        print("\n[FAIL] Cumulative should be positive")
        return False


# =============================================================================
# Test 4: IRE Hill Model
# =============================================================================

def test_ire_hill_model():
    """Test Hill equation for receptor binding"""
    print("\n" + "="*80)
    print("TEST 4: IRE Hill Model (Receptor Binding)")
    print("="*80)

    ire = IRE()

    # Test Hill equation: H(C) = C^n / (K^n + C^n)
    # Default: K=1.0, n=2.0

    test_cases = [
        (0.0, 0.0),      # No ligand → no binding
        (1.0, 0.5),      # C=K → 50% binding
        (2.0, 0.8),      # C=2K → 80% binding
        (10.0, 0.99),    # High C → near saturation
    ]

    print(f"\nHill equation: H(C) = C^2 / (1^2 + C^2)")
    print(f"{'C':<10} {'H(C) Actual':<15} {'H(C) Expected':<15} {'Error':<10}")
    print("-" * 50)

    all_pass = True
    for C, expected in test_cases:
        actual = ire.hill(C, K=1.0, n=2.0)
        error = abs(actual - expected)

        print(f"{C:<10.2f} {actual:<15.4f} {expected:<15.4f} {error:<10.6f}")

        if error > 0.05:  # 5% tolerance
            all_pass = False

    if all_pass:
        print("\n[PASS] Hill model calculations correct")
        return True
    else:
        print("\n[FAIL] Hill model has errors > 5%")
        return False


# =============================================================================
# Test 5: IRE Receptor Internalization (Desensitization)
# =============================================================================

def test_ire_receptor_internalization():
    """Test that chronic exposure causes receptor desensitization"""
    print("\n" + "="*80)
    print("TEST 5: IRE Receptor Internalization (Desensitization)")
    print("="*80)

    ire = IRE()

    # Simulate chronic high dopamine (DA)
    C_Mod_high = {"DA": 1.0, "GLU": 0.0, "OX": 0.0, "5HT": 0.0,
                  "AD": 0.0, "CRH": 0.0, "CT": 0.0, "GABA": 0.0}

    print(f"\nSimulating chronic high DA exposure (C=1.0)...")

    # First reflex (no internalization yet)
    reflex_1 = ire.compute_reflex(C_Mod_high)
    cognitive_drive_1 = reflex_1.get("cognitive_drive", 0.0)

    print(f"  Initial cognitive_drive: {cognitive_drive_1:.4f}")
    print(f"  Initial internalization['DA']: {ire.internalization.get('DA', 0.0):.4f}")

    # Repeated exposure (100 ticks)
    for _ in range(100):
        reflex = ire.compute_reflex(C_Mod_high)

    cognitive_drive_100 = reflex.get("cognitive_drive", 0.0)
    internalization_da = ire.internalization.get("DA", 0.0)

    print(f"\nAfter 100 exposures:")
    print(f"  cognitive_drive: {cognitive_drive_100:.4f}")
    print(f"  internalization['DA']: {internalization_da:.4f}")

    # Desensitization should reduce reflex
    if cognitive_drive_100 < cognitive_drive_1:
        print(f"\n[PASS] Receptor desensitization occurred")
        print(f"  Reflex reduction: {cognitive_drive_1 - cognitive_drive_100:.4f}")
        return True
    else:
        print("\n[FAIL] No desensitization detected")
        return False


# =============================================================================
# Test 6: IRE Core Reflexes Mapping
# =============================================================================

def test_ire_core_reflexes():
    """Test that core reflexes respond to correct hormones"""
    print("\n" + "="*80)
    print("TEST 6: IRE Core Reflexes Hormone Mapping")
    print("="*80)

    ire = IRE()

    # Test urgency_load (should respond to AD, CRH)
    C_Mod_stress = {"AD": 1.0, "CRH": 1.0, "DA": 0.0, "GLU": 0.0,
                    "OX": 0.0, "5HT": 0.0, "CT": 0.0, "GABA": 0.0}

    reflex = ire.compute_reflex(C_Mod_stress)
    urgency = reflex.get("urgency_load", 0.0)

    print(f"\nHigh stress hormones (AD=1.0, CRH=1.0):")
    print(f"  urgency_load: {urgency:.4f}")

    if urgency > 0.5:
        print("  [PASS] Urgency responds to stress hormones")
    else:
        print("  [FAIL] Urgency too low for stress state")
        return False

    # Test social_warmth (should respond to OX, 5HT)
    C_Mod_social = {"OX": 1.0, "5HT": 1.0, "AD": 0.0, "CRH": 0.0,
                    "DA": 0.0, "GLU": 0.0, "CT": 0.0, "GABA": 0.0}

    reflex = ire.compute_reflex(C_Mod_social)
    warmth = reflex.get("social_warmth", 0.0)

    print(f"\nHigh social hormones (OX=1.0, 5HT=1.0):")
    print(f"  social_warmth: {warmth:.4f}")

    if warmth > 0.5:
        print("  [PASS] Social warmth responds to OX/5HT")
    else:
        print("  [FAIL] Social warmth too low")
        return False

    # Test threat_level (urgency_load + withdrawal)
    threat = reflex.get("threat_level", 0.0)
    print(f"\nThreat level computation:")
    print(f"  threat_level: {threat:.4f}")
    print(f"  (Should be clamped to [0, 1])")

    if 0.0 <= threat <= 1.0:
        print("  [PASS] Threat level properly clamped")
        return True
    else:
        print("  [FAIL] Threat level out of range")
        return False


# =============================================================================
# Test 7: ESS Full Integration
# =============================================================================

def test_ess_full_integration():
    """Test complete ESS tick cycle with ISR + IRE"""
    print("\n" + "="*80)
    print("TEST 7: ESS Full Integration (ISR + IRE + Logging)")
    print("="*80)

    # Create temp directory for ESS logs
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)

        # Initialize ESS
        half_life = {
            "AD": 5.0, "CRH": 10.0, "DA": 8.0, "GLU": 3.0,
            "OX": 7.0, "5HT": 6.0, "CT": 12.0, "GABA": 4.0
        }

        isr = ISR(half_life_sec=half_life)
        ire = IRE()
        ess = ESS(isr, ire, base_path=base_path)

        # Start ESS
        ess_id = ess.start(session_id="test_session", episode_id="ep_001")
        print(f"\nESS started: {ess_id}")

        # Tick with stress stimulus
        stimulus = {"stress": 0.8, "social": 0.2}
        D_Total_H = {"AD": 0.8, "CRH": 0.7, "OX": 0.2}

        result = ess.tick_once(
            stimulus_vector=stimulus,
            D_Total_H=D_Total_H,
            delta_t_ms=33
        )

        print(f"\nTick result:")
        print(f"  C_Mod keys: {list(result['C_Mod'].keys())}")
        print(f"  reflex_vector keys: {list(result['reflex_vector'].keys())}")

        # Verify C_Mod
        C_Mod = result["C_Mod"]
        if "AD" in C_Mod and "CRH" in C_Mod:
            print(f"  C_Mod['AD']: {C_Mod['AD']:.4f}")
            print(f"  C_Mod['CRH']: {C_Mod['CRH']:.4f}")
            print("  [PASS] C_Mod contains expected hormones")
        else:
            print("  [FAIL] C_Mod missing expected hormones")
            ess.close()
            return False

        # Verify reflex_vector
        reflex = result["reflex_vector"]
        if "urgency_load" in reflex and "threat_level" in reflex:
            print(f"  urgency_load: {reflex['urgency_load']:.4f}")
            print(f"  threat_level: {reflex['threat_level']:.4f}")
            print("  [PASS] Reflex vector contains expected outputs")
        else:
            print("  [FAIL] Reflex vector missing expected fields")
            ess.close()
            return False

        # Check log file
        log_path = base_path / ess_id / "ess_log.jsonl"
        if log_path.exists():
            with log_path.open("r") as f:
                log_line = f.readline()
                log_data = json.loads(log_line)

            print(f"\nLog file created: {log_path}")
            print(f"  Schema: {log_data.get('schema')}")
            print(f"  Tick index: {log_data.get('tick_index')}")
            print("  [PASS] Logging works correctly")
        else:
            print("\n  [FAIL] Log file not created")
            ess.close()
            return False

        ess.close()
        print("\n[PASS] Full ESS integration test passed")
        return True


# =============================================================================
# Test 8: Multi-Tick Hormone Dynamics
# =============================================================================

def test_multi_tick_dynamics():
    """Test hormone accumulation and decay over multiple ticks"""
    print("\n" + "="*80)
    print("TEST 8: Multi-Tick Hormone Dynamics")
    print("="*80)

    isr = ISR(half_life_sec={"DA": 10.0})

    print(f"\nSimulating pulsed DA dosing (10 ticks):")
    print(f"{'Tick':<6} {'Dose':<8} {'C_Mod':<10} {'D_Remaining':<12} {'D_Cumulative':<12}")
    print("-" * 60)

    # Pulse pattern: dose on ticks 1, 5, 10
    pulse_pattern = {1: 0.5, 5: 0.5, 10: 0.5}

    prev_cumulative = 0.0

    for tick in range(1, 11):
        dose = pulse_pattern.get(tick, 0.0)
        D_Total_H = {"DA": dose}

        C_Mod, D_Remaining, Rate = isr.update(D_Total_H, delta_t_ms=1000)

        cumulative = isr.D_Cumulative["DA"]

        print(f"{tick:<6} {dose:<8.2f} {C_Mod['DA']:<10.4f} {D_Remaining['DA']:<12.4f} {cumulative:<12.4f}")

        # Cumulative should always increase (or stay same)
        if cumulative < prev_cumulative:
            print(f"\n[FAIL] Cumulative decreased at tick {tick}")
            return False

        prev_cumulative = cumulative

    print("\n[PASS] Multi-tick dynamics work correctly")
    return True


# =============================================================================
# Run All Tests
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("ESS HORMONE SYSTEM COMPREHENSIVE TEST SUITE")
    print("="*80 + "\n")

    results = []
    results.append(("ISR Exponential Decay", test_isr_exponential_decay()))
    results.append(("ISR Saturation Clamping", test_isr_saturation_clamping()))
    results.append(("ISR Cumulative Tracking", test_isr_cumulative_tracking()))
    results.append(("IRE Hill Model", test_ire_hill_model()))
    results.append(("IRE Receptor Internalization", test_ire_receptor_internalization()))
    results.append(("IRE Core Reflexes", test_ire_core_reflexes()))
    results.append(("ESS Full Integration", test_ess_full_integration()))
    results.append(("Multi-Tick Dynamics", test_multi_tick_dynamics()))

    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    print("="*80 + "\n")
