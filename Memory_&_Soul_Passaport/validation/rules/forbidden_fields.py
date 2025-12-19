# =============================================================================
# Forbidden Fields Registry
# Field blacklists for each memory type (LLM boundary enforcement)
# =============================================================================

from typing import List, Set


# =============================================================================
# EPISODIC MEMORY FORBIDDEN FIELDS
# =============================================================================

EPISODIC_FORBIDDEN_FIELDS: List[str] = [
    # Metrics and Scores (MSP computation only)
    "RI",
    "RIM",
    "Resonance_impact",
    "salience_score",
    "memory_color_ref",

    # Physiology and ESS (system-generated)
    "dose_input",
    "D_Remaining",
    "D_Cumulative",
    "hormone_level",
    "PK_state",

    # Memory Control (MSP authority only)
    "promotion_level",
    "write_mode",
    "admission_priority",

    # Emotion Labels (no categorical labels allowed)
    "emotion_label",
    "primary_emotion",
    "emotional_label",
]

# Note: The following fields are allowed when coming from integration pipeline:
# - episode_id, turn_id, context_id (MSP generates but may be in proposal)
# - eva_matrix, qualia, reflex (from EVA Matrix, Artifact Qualia, RMS)
# - emotive_snapshot, indexed_state (wrappers for state)
# - threat_level (from reflex subsystem)
# These are validated for structure/range, not forbidden entirely.


# =============================================================================
# SEMANTIC MEMORY FORBIDDEN FIELDS
# =============================================================================

SEMANTIC_FORBIDDEN_FIELDS: List[str] = [
    # Control (MSP authority only)
    "promotion_level",
    "write_mode",
    "user_block",
]

# Note: The following are MSP-authoritative but NOT forbidden in final entry:
# - semantic_id, epistemic_status, confidence (MSP generates these)
# - created_at, last_updated, resolution_state (MSP manages)
# - related_blocks (MSP assigns)
# These should only be forbidden in LLM proposals, not in complete entries.


# =============================================================================
# SENSORY MEMORY FORBIDDEN FIELDS
# =============================================================================

SENSORY_FORBIDDEN_FIELDS: List[str] = [
    # Interpretation (LLM cannot interpret)
    "primary_emotion",
    "emotional_label",
    "intent",
    "meaning",
    "description_with_judgement",

    # Metrics and State (system-generated)
    "eva_matrix",
    "qualia",
    "reflex",
    "RI",
    "RIM",

    # Policy and Control (MSP authority)
    "GKS_trigger",
    "recall_priority",
    "awareness_hook",
    "promotion_hint",
]

# Note: The following are MSP-authoritative but NOT forbidden in final entry:
# - sensory_id, episode_ref, timestamp, checksum (MSP generates)
# These should only be forbidden in LLM proposals, not in complete entries.


# =============================================================================
# UTILITIES
# =============================================================================

def get_forbidden_fields(memory_type: str) -> Set[str]:
    """
    Get forbidden fields for a memory type

    Args:
        memory_type: "episodic", "semantic", or "sensory"

    Returns:
        Set of forbidden field names
    """
    memory_type_lower = memory_type.lower()

    if memory_type_lower == "episodic":
        return set(EPISODIC_FORBIDDEN_FIELDS)
    elif memory_type_lower == "semantic":
        return set(SEMANTIC_FORBIDDEN_FIELDS)
    elif memory_type_lower == "sensory":
        return set(SENSORY_FORBIDDEN_FIELDS)
    else:
        raise ValueError(f"Unknown memory type: {memory_type}")


def is_field_forbidden(field_name: str, memory_type: str) -> bool:
    """
    Check if a field is forbidden for a memory type

    Args:
        field_name: Field name to check
        memory_type: "episodic", "semantic", or "sensory"

    Returns:
        True if field is forbidden
    """
    forbidden_set = get_forbidden_fields(memory_type)
    return field_name in forbidden_set
