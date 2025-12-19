# =============================================================================
# Test MSP with Validation Layer
# =============================================================================

import sys
from pathlib import Path

# Add Memory_&_Soul_Passaport to path
sys.path.insert(0, str(Path(__file__).parent / "Memory_&_Soul_Passaport"))

from MSP import MSP

def test_valid_episode():
    """Test with valid episode data"""
    print("="*80)
    print("TEST 1: Valid Episode")
    print("="*80)

    msp = MSP(validation_mode="strict")
    msp.load_origin("EVA")
    instance_id = msp.create_instance()
    msp.start_session(instance_id)

    # Valid episode
    episode = {
        "episode_header": {
            "episode_type": "interaction"
        },
        "situation_context": {
            "context_id": "ctx_001",
            "interaction_mode": "discussion",
            "stakes_level": "medium",
            "time_pressure": "low"
        },
        "turns": [
            {
                "turn_id": "t1",
                "speaker": "user",
                "raw_text": "Hello EVA!"
            },
            {
                "turn_id": "t2",
                "speaker": "eva",
                "raw_text": "Hello! How can I help you?"
            }
        ],
        "emotive_snapshot": {
            "indexed_state": {
                "eva_matrix": {
                    "stress_load": 0.3,
                    "social_warmth": 0.7,
                    "drive_level": 0.5,
                    "cognitive_clarity": 0.8
                },
                "qualia": {
                    "intensity": 0.5
                },
                "reflex": {
                    "threat_level": 0.2
                }
            },
            "crosslinks": {}
        }
    }

    try:
        episode_id = msp.write_episode(episode, ri_level="L3")
        print(f"\n[PASS] Episode written successfully: {episode_id}")
        return True
    except Exception as e:
        print(f"\n[FAIL] Failed: {e}")
        return False


def test_invalid_episode_forbidden_field():
    """Test with forbidden field (should be rejected)"""
    print("\n" + "="*80)
    print("TEST 2: Invalid Episode (Forbidden Field)")
    print("="*80)

    msp = MSP(validation_mode="strict")
    msp.load_origin("EVA")
    instance_id = msp.create_instance("test_invalid")
    msp.start_session(instance_id)

    # Invalid: contains forbidden field "RI"
    episode = {
        "episode_header": {
            "episode_type": "interaction"
        },
        "situation_context": {
            "context_id": "ctx_002",
            "interaction_mode": "discussion",
            "stakes_level": "medium",
            "time_pressure": "low"
        },
        "turns": [
            {
                "turn_id": "t1",
                "speaker": "user",
                "raw_text": "Test"
            }
        ],
        "emotive_snapshot": {
            "indexed_state": {
                "eva_matrix": {
                    "stress_load": 0.3,
                    "social_warmth": 0.7,
                    "drive_level": 0.5,
                    "cognitive_clarity": 0.8
                },
                "qualia": {
                    "intensity": 0.5
                },
                "reflex": {
                    "threat_level": 0.2
                }
            },
            "crosslinks": {}
        },
        "RI": 3  # FORBIDDEN FIELD
    }

    try:
        episode_id = msp.write_episode(episode, ri_level="L3")
        print(f"\n[FAIL] Should have been rejected but was accepted: {episode_id}")
        return False
    except Exception as e:
        print(f"\n[PASS] Correctly rejected: {e}")
        return True


def test_invalid_episode_bad_enum():
    """Test with invalid enum value (should be rejected)"""
    print("\n" + "="*80)
    print("TEST 3: Invalid Episode (Bad Enum)")
    print("="*80)

    msp = MSP(validation_mode="strict")
    msp.load_origin("EVA")
    instance_id = msp.create_instance("test_enum")
    msp.start_session(instance_id)

    # Invalid: speaker value not in enum
    episode = {
        "episode_header": {
            "episode_type": "interaction"
        },
        "situation_context": {
            "context_id": "ctx_003",
            "interaction_mode": "discussion",
            "stakes_level": "medium",
            "time_pressure": "low"
        },
        "turns": [
            {
                "turn_id": "t1",
                "speaker": "robot",  # INVALID ENUM VALUE
                "raw_text": "Test"
            }
        ],
        "emotive_snapshot": {
            "indexed_state": {
                "eva_matrix": {
                    "stress_load": 0.3,
                    "social_warmth": 0.7,
                    "drive_level": 0.5,
                    "cognitive_clarity": 0.8
                },
                "qualia": {
                    "intensity": 0.5
                },
                "reflex": {
                    "threat_level": 0.2
                }
            },
            "crosslinks": {}
        }
    }

    try:
        episode_id = msp.write_episode(episode, ri_level="L3")
        print(f"\n[FAIL] Should have been rejected but was accepted: {episode_id}")
        return False
    except Exception as e:
        print(f"\n[PASS] Correctly rejected: {e}")
        return True


def test_validation_warn_mode():
    """Test validation in warn mode (should accept with warnings)"""
    print("\n" + "="*80)
    print("TEST 4: Warn Mode (Accept with Warnings)")
    print("="*80)

    msp = MSP(validation_mode="warn")  # WARN MODE
    msp.load_origin("EVA")
    instance_id = msp.create_instance("test_warn")
    msp.start_session(instance_id)

    # Has issues but should be accepted in warn mode
    episode = {
        "episode_header": {
            "episode_type": "interaction"
        },
        "situation_context": {
            "context_id": "ctx_004",
            "interaction_mode": "discussion",
            "stakes_level": "medium",
            "time_pressure": "low"
        },
        "turns": [
            {
                "turn_id": "t1",
                "speaker": "invalid_speaker",  # Bad enum
                "raw_text": "Test"
            }
        ],
        "emotive_snapshot": {
            "indexed_state": {
                "eva_matrix": {
                    "stress_load": 0.3,
                    "social_warmth": 0.7,
                    "drive_level": 0.5,
                    "cognitive_clarity": 0.8
                },
                "qualia": {
                    "intensity": 0.5
                },
                "reflex": {
                    "threat_level": 0.2
                }
            },
            "crosslinks": {}
        }
    }

    try:
        episode_id = msp.write_episode(episode, ri_level="L3")
        print(f"\n[PASS] Accepted with warnings: {episode_id}")
        return True
    except Exception as e:
        print(f"\n[FAIL] Should have been accepted in warn mode: {e}")
        return False


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("MSP VALIDATION LAYER INTEGRATION TESTS")
    print("="*80 + "\n")

    results = []
    results.append(("Valid Episode", test_valid_episode()))
    results.append(("Forbidden Field Rejection", test_invalid_episode_forbidden_field()))
    results.append(("Bad Enum Rejection", test_invalid_episode_bad_enum()))
    results.append(("Warn Mode Acceptance", test_validation_warn_mode()))

    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name}")

    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    print("="*80 + "\n")
