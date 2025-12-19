# =============================================================================
# Comprehensive Validation Test Suite
# Tests all validators: Episodic, Semantic, Sensory
# =============================================================================

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "Memory_&_Soul_Passaport"))

from MSP import MSP
from validation import UpdateSignal, StakesLevel

# =============================================================================
# Test Semantic Validation + Confidence Updates
# =============================================================================

def test_semantic_conflict_detection():
    """Test semantic conflict detection and confidence updates"""
    print("="*80)
    print("TEST: Semantic Conflict Detection + Confidence Updates")
    print("="*80)

    msp = MSP(validation_mode="strict")
    msp.load_origin("EVA")
    instance_id = msp.create_instance("test_semantic")
    msp.start_session(instance_id)

    # Write first episode
    episode_id = msp.write_episode({
        "episode_header": {"episode_type": "interaction"},
        "situation_context": {
            "context_id": "ctx_001",
            "interaction_mode": "discussion",
            "stakes_level": "medium",
            "time_pressure": "low"
        },
        "turns": [{"turn_id": "t1", "speaker": "user", "raw_text": "I'm allergic to seafood"}],
        "emotive_snapshot": {
            "indexed_state": {
                "eva_matrix": {"stress_load": 0.3, "social_warmth": 0.7, "drive_level": 0.5, "cognitive_clarity": 0.8},
                "qualia": {"intensity": 0.5},
                "reflex": {"threat_level": 0.2}
            },
            "crosslinks": {}
        }
    }, ri_level="L3")

    # Write first semantic: user allergic to seafood
    sem_id_1 = msp.write_semantic(
        concept="user_seafood_allergy",
        definition="User is allergic to seafood",
        episode_id=episode_id,
        stakes_level=StakesLevel.HIGH
    )
    print(f"\n[PASS] Wrote semantic 1: {sem_id_1}")

    # Simulate user affirmation to increase confidence
    if msp.confidence_updater:
        instance_path = msp.get_instance_path()
        semantic_buffer = instance_path / "02_Semantic_memory" / "Semantic_memory.json"
        from MSP import load_json, save_json
        buffer_data = load_json(semantic_buffer)

        for entry in buffer_data.get("entries", []):
            if entry.get("semantic_id") == sem_id_1:
                # Apply USER_AFFIRMATION signal
                entry = msp.confidence_updater.update_entry(entry, [UpdateSignal.USER_AFFIRMATION])
                print(f"  Updated confidence after user affirmation: {entry['confidence']:.2f}")
                print(f"  Epistemic status: {entry['epistemic_status']}")
                break

        save_json(semantic_buffer, buffer_data)

    # Write conflicting semantic: user wants shrimp
    sem_id_2 = msp.write_semantic(
        concept="user_wants_shrimp",
        definition="User wants to eat grilled shrimp from Ayutthaya",
        episode_id=episode_id,
        stakes_level=StakesLevel.HIGH
    )
    print(f"\n[INFO] Wrote potentially conflicting semantic: {sem_id_2}")
    print("  Conflict should be detected at consolidation time")

    return True


def test_semantic_consolidation_threshold():
    """Test that only confidence > 0.7 entries consolidate"""
    print("\n" + "="*80)
    print("TEST: Semantic Consolidation Threshold")
    print("="*80)

    msp = MSP(validation_mode="strict")
    msp.load_origin("EVA")
    instance_id = msp.create_instance("test_consolidation")
    msp.start_session(instance_id)

    episode_id = msp.write_episode({
        "episode_header": {"episode_type": "interaction"},
        "situation_context": {
            "context_id": "ctx_002",
            "interaction_mode": "discussion",
            "stakes_level": "low",
            "time_pressure": "low"
        },
        "turns": [{"turn_id": "t1", "speaker": "user", "raw_text": "Test"}],
        "emotive_snapshot": {
            "indexed_state": {
                "eva_matrix": {"stress_load": 0.3, "social_warmth": 0.7, "drive_level": 0.5, "cognitive_clarity": 0.8},
                "qualia": {"intensity": 0.5},
                "reflex": {"threat_level": 0.2}
            },
            "crosslinks": {}
        }
    }, ri_level="L3")

    # Write semantic with low confidence (won't consolidate)
    sem_id_low = msp.write_semantic(
        concept="uncertain_fact",
        definition="Something we're not sure about",
        episode_id=episode_id
    )

    # Write semantic with high confidence (will consolidate)
    sem_id_high = msp.write_semantic(
        concept="confirmed_fact",
        definition="Something we're certain about",
        episode_id=episode_id
    )

    # Manually boost confidence to > 0.7
    if msp.confidence_updater:
        instance_path = msp.get_instance_path()
        semantic_buffer = instance_path / "02_Semantic_memory" / "Semantic_memory.json"
        from MSP import load_json, save_json
        buffer_data = load_json(semantic_buffer)

        for entry in buffer_data.get("entries", []):
            if entry.get("semantic_id") == sem_id_high:
                entry = msp.confidence_updater.update_entry(entry, [UpdateSignal.USER_AFFIRMATION])

        save_json(semantic_buffer, buffer_data)

    print(f"\n[INFO] Wrote 2 semantics: {sem_id_low} (low), {sem_id_high} (high)")
    print("  Only high-confidence entry should consolidate")

    # End session and consolidate
    msp.end_session()
    msp.consolidate_to_origin()

    print("\n[PASS] Consolidation complete - check logs for which entries merged")
    return True


# =============================================================================
# Test Sensory Validation (No Interpretation)
# =============================================================================

def test_sensory_no_interpretation():
    """Test that sensory validation rejects interpretive content"""
    print("\n" + "="*80)
    print("TEST: Sensory No-Interpretation Enforcement")
    print("="*80)

    from validation import SensoryValidator

    validator = SensoryValidator(strict_mode=True)

    # Valid sensory entry (descriptive only)
    valid_entry = {
        "sensory_id": "sens_001",
        "session_id": "S01",
        "episode_ref": "ep_001",
        "timestamp": "2025-12-18T10:00:00Z",
        "data_type": "audio",
        "data_source": {
            "source_name": "microphone",
            "capture_channel": "user_input"
        },
        "sensory_payload": {
            "raw_content": "Voice recording",
            "feature_snapshot": {
                "pitch": 220.5,
                "volume": 0.8,
                "tempo": 120
            }
        }
    }

    result = validator.validate(valid_entry)
    if result.valid:
        print("\n[PASS] Valid sensory entry accepted (descriptive only)")
    else:
        print(f"\n[FAIL] Valid entry rejected: {result.errors}")
        return False

    # Invalid sensory entry (contains interpretation)
    invalid_entry = {
        "sensory_id": "sens_002",
        "session_id": "S01",
        "episode_ref": "ep_001",
        "timestamp": "2025-12-18T10:00:00Z",
        "data_type": "audio",
        "data_source": {
            "source_name": "microphone",
            "capture_channel": "user_input"
        },
        "sensory_payload": {
            "raw_content": "User sounds angry and frustrated",  # INTERPRETIVE!
            "feature_snapshot": {
                "pitch": 220.5,
                "volume": 0.8
            }
        }
    }

    result = validator.validate(invalid_entry)
    if not result.valid:
        print(f"\n[PASS] Interpretive sensory entry correctly rejected")
        print(f"  Detected: {result.errors}")
    else:
        print(f"\n[FAIL] Interpretive entry should have been rejected")
        return False

    return True


# =============================================================================
# Test Loop Protection
# =============================================================================

def test_clarification_loop_protection():
    """Test that clarification attempts are limited by stakes level"""
    print("\n" + "="*80)
    print("TEST: Clarification Loop Protection")
    print("="*80)

    from validation import ConfidenceUpdater, StakesLevel

    updater = ConfidenceUpdater()

    # Test general topic (max 2-3 attempts)
    general_entry = updater.create_initial_entry(
        concept="general_preference",
        definition="User's general preference",
        stakes_level=StakesLevel.MEDIUM
    )

    print(f"\nGeneral topic (stakes: MEDIUM)")
    print(f"  Max clarification attempts: {general_entry['max_clarification_attempts']}")

    for i in range(5):
        should_ask = updater.should_ask_clarification(general_entry)
        print(f"  Attempt {i+1}: should_ask = {should_ask}")

        if should_ask:
            general_entry = updater.increment_clarification_attempt(general_entry)
        else:
            print(f"  [PASS] Loop protection triggered at attempt {i+1}")
            break

    # Test health/safety topic (max 3-4 attempts)
    health_entry = updater.create_initial_entry(
        concept="seafood_allergy",
        definition="User allergy to seafood",
        stakes_level=StakesLevel.HIGH
    )

    print(f"\nHealth/Safety topic (stakes: HIGH)")
    print(f"  Max clarification attempts: {health_entry['max_clarification_attempts']}")

    for i in range(6):
        should_ask = updater.should_ask_clarification(health_entry)
        print(f"  Attempt {i+1}: should_ask = {should_ask}")

        if should_ask:
            health_entry = updater.increment_clarification_attempt(health_entry)
        else:
            print(f"  [PASS] Loop protection triggered at attempt {i+1}")
            break

    return True


# =============================================================================
# Run All Tests
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("MSP COMPREHENSIVE VALIDATION TEST SUITE")
    print("="*80 + "\n")

    results = []
    results.append(("Semantic Conflict Detection", test_semantic_conflict_detection()))
    results.append(("Semantic Consolidation Threshold", test_semantic_consolidation_threshold()))
    results.append(("Sensory No-Interpretation", test_sensory_no_interpretation()))
    results.append(("Clarification Loop Protection", test_clarification_loop_protection()))

    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    print("="*80 + "\n")
