# =============================================================================
# Confidence Updater
# Confidence scoring system for semantic memory with loop protection
# =============================================================================

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class UpdateSignal(Enum):
    """Confidence update signals"""
    REPEATED_OCCURRENCE = "repeated_occurrence"
    CONSISTENT_RECALL = "consistent_recall"
    USER_AFFIRMATION = "user_affirmation"
    IMPLICIT_USER_SIGNAL = "implicit_user_signal"
    SYSTEM_CROSS_VALIDATION = "system_cross_validation"
    CONFLICT_DETECTED = "conflict_detected"
    CONTRADICTION_BY_USER = "contradiction_by_user"
    INCONSISTENCY_OVER_TIME = "inconsistency_over_time"
    SYSTEM_NOISE_DETECTED = "system_noise_detected"


class ResolutionState(Enum):
    """Conflict resolution state"""
    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class EpistemicStatus(Enum):
    """Epistemic status levels"""
    HYPOTHESIS = "hypothesis"       # confidence < 0.45
    PROVISIONAL = "provisional"     # 0.45 ≤ confidence < 0.80
    CONFIRMED = "confirmed"         # confidence ≥ 0.80


class StakesLevel(Enum):
    """Stakes level for clarification limits"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"  # Health/Safety


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class SignalModifier:
    """Modifier value for a signal"""
    value: float
    max_applications: Optional[int] = None
    single_application: bool = False
    force_confirmed: bool = False


# Signal modifiers
SIGNAL_MODIFIERS: Dict[UpdateSignal, SignalModifier] = {
    UpdateSignal.REPEATED_OCCURRENCE: SignalModifier(value=0.05, max_applications=3),
    UpdateSignal.CONSISTENT_RECALL: SignalModifier(value=0.04, max_applications=3),
    UpdateSignal.USER_AFFIRMATION: SignalModifier(value=0.30, single_application=True, force_confirmed=True),
    UpdateSignal.IMPLICIT_USER_SIGNAL: SignalModifier(value=0.10),
    UpdateSignal.SYSTEM_CROSS_VALIDATION: SignalModifier(value=0.08),
    UpdateSignal.CONFLICT_DETECTED: SignalModifier(value=-0.20),
    UpdateSignal.CONTRADICTION_BY_USER: SignalModifier(value=-0.35),
    UpdateSignal.INCONSISTENCY_OVER_TIME: SignalModifier(value=-0.10),
    UpdateSignal.SYSTEM_NOISE_DETECTED: SignalModifier(value=-0.08),
}

# Resolution state multipliers
RESOLUTION_MULTIPLIERS: Dict[ResolutionState, Dict[str, float]] = {
    ResolutionState.UNRESOLVED: {"positive": 0.5, "negative": 1.0},
    ResolutionState.RESOLVED: {"positive": 1.0, "negative": 0.5},
    ResolutionState.SUPPRESSED: {"positive": 0.0, "negative": 0.0},
}

# Epistemic status thresholds
EPISTEMIC_THRESHOLDS = {
    EpistemicStatus.CONFIRMED: 0.80,
    EpistemicStatus.PROVISIONAL: 0.45,
}

# Loop protection: Max clarification attempts by stakes level
MAX_CLARIFICATION_ATTEMPTS = {
    StakesLevel.LOW: 2,
    StakesLevel.MEDIUM: 3,
    StakesLevel.HIGH: 4,  # Health/Safety gets more attempts
}


# =============================================================================
# Confidence Updater
# =============================================================================

class ConfidenceUpdater:
    """
    Manages confidence scoring for semantic memory entries
    with loop protection
    """

    def __init__(self, initial_confidence: float = 0.3):
        """
        Initialize confidence updater

        Args:
            initial_confidence: Starting confidence for new entries
        """
        self.initial_confidence = initial_confidence

    def calculate_confidence(
        self,
        current_confidence: float,
        signals: List[UpdateSignal],
        resolution_state: ResolutionState = ResolutionState.UNRESOLVED,
        signal_history: Optional[Dict[UpdateSignal, int]] = None
    ) -> float:
        """
        Calculate new confidence based on signals

        Args:
            current_confidence: Current confidence value
            signals: List of update signals to apply
            resolution_state: Current resolution state
            signal_history: History of how many times each signal was applied

        Returns:
            New confidence value (clamped to [0.0, 1.0])
        """
        if signal_history is None:
            signal_history = {}

        confidence = current_confidence
        multipliers = RESOLUTION_MULTIPLIERS[resolution_state]

        for signal in signals:
            modifier = SIGNAL_MODIFIERS[signal]

            # Check max applications
            times_applied = signal_history.get(signal, 0)
            if modifier.max_applications and times_applied >= modifier.max_applications:
                continue  # Skip if max applications reached

            # Check single application
            if modifier.single_application and times_applied > 0:
                continue

            # Apply multiplier based on sign
            value = modifier.value
            if value > 0:
                value *= multipliers["positive"]
            else:
                value *= multipliers["negative"]

            confidence += value

            # Force confirmed status if specified
            if modifier.force_confirmed and signal == UpdateSignal.USER_AFFIRMATION:
                confidence = max(confidence, EPISTEMIC_THRESHOLDS[EpistemicStatus.CONFIRMED])

        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, confidence))

    def get_epistemic_status(self, confidence: float) -> EpistemicStatus:
        """
        Get epistemic status from confidence value

        Args:
            confidence: Confidence value

        Returns:
            EpistemicStatus
        """
        if confidence >= EPISTEMIC_THRESHOLDS[EpistemicStatus.CONFIRMED]:
            return EpistemicStatus.CONFIRMED
        elif confidence >= EPISTEMIC_THRESHOLDS[EpistemicStatus.PROVISIONAL]:
            return EpistemicStatus.PROVISIONAL
        else:
            return EpistemicStatus.HYPOTHESIS

    def should_consolidate(self, confidence: float) -> bool:
        """
        Check if entry meets consolidation threshold

        Args:
            confidence: Confidence value

        Returns:
            True if confidence > 0.7
        """
        return confidence > 0.7

    def check_clarification_limit(
        self,
        attempts: int,
        stakes_level: StakesLevel
    ) -> bool:
        """
        Check if clarification attempts exceeded limit (loop protection)

        Args:
            attempts: Number of clarification attempts so far
            stakes_level: Stakes level of the topic

        Returns:
            True if limit exceeded (should force exit)
        """
        max_attempts = MAX_CLARIFICATION_ATTEMPTS[stakes_level]
        return attempts >= max_attempts

    def create_initial_entry(
        self,
        concept: str,
        definition: str,
        stakes_level: StakesLevel = StakesLevel.MEDIUM
    ) -> Dict[str, Any]:
        """
        Create initial semantic entry with starting confidence

        Args:
            concept: Concept name
            definition: Concept definition
            stakes_level: Stakes level (determines clarification limits)

        Returns:
            Semantic entry dict
        """
        initial_status = self.get_epistemic_status(self.initial_confidence)

        return {
            "concept": concept,
            "definition": definition,
            "epistemic_status": initial_status.value,
            "confidence": self.initial_confidence,
            "resolution_state": ResolutionState.UNRESOLVED.value,
            "signal_history": {},
            "clarification_attempts": 0,
            "stakes_level": stakes_level.value,
            "max_clarification_attempts": MAX_CLARIFICATION_ATTEMPTS[stakes_level],
        }

    def update_entry(
        self,
        entry: Dict[str, Any],
        signals: List[UpdateSignal]
    ) -> Dict[str, Any]:
        """
        Update semantic entry with new signals

        Args:
            entry: Current semantic entry
            signals: Update signals to apply

        Returns:
            Updated entry
        """
        # Extract current state
        current_confidence = entry.get("confidence", self.initial_confidence)
        resolution_state = ResolutionState(entry.get("resolution_state", "unresolved"))
        signal_history = entry.get("signal_history", {})

        # Convert signal_history keys from strings to UpdateSignal enums
        signal_history_enum = {}
        for key, value in signal_history.items():
            try:
                signal_history_enum[UpdateSignal(key)] = value
            except ValueError:
                pass

        # Calculate new confidence
        new_confidence = self.calculate_confidence(
            current_confidence,
            signals,
            resolution_state,
            signal_history_enum
        )

        # Update signal history
        for signal in signals:
            signal_key = signal.value
            signal_history[signal_key] = signal_history.get(signal_key, 0) + 1

        # Update epistemic status
        new_status = self.get_epistemic_status(new_confidence)

        # Update entry
        entry["confidence"] = new_confidence
        entry["epistemic_status"] = new_status.value
        entry["signal_history"] = signal_history

        # Check if confirmed (can resolve conflicts)
        if new_status == EpistemicStatus.CONFIRMED and resolution_state == ResolutionState.UNRESOLVED:
            entry["resolution_state"] = ResolutionState.RESOLVED.value

        return entry

    def increment_clarification_attempt(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Increment clarification attempt counter

        Args:
            entry: Semantic entry

        Returns:
            Updated entry with incremented counter
        """
        entry["clarification_attempts"] = entry.get("clarification_attempts", 0) + 1
        return entry

    def should_ask_clarification(self, entry: Dict[str, Any]) -> bool:
        """
        Check if should ask clarification question (loop protection)

        Args:
            entry: Semantic entry

        Returns:
            True if should ask, False if limit reached
        """
        attempts = entry.get("clarification_attempts", 0)
        stakes_level = StakesLevel(entry.get("stakes_level", "medium"))

        return not self.check_clarification_limit(attempts, stakes_level)

    def force_exit_loop(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Force exit clarification loop (accept current confidence)

        Args:
            entry: Semantic entry

        Returns:
            Updated entry with suppressed state
        """
        # Mark as suppressed if still unresolved
        if entry.get("resolution_state") == ResolutionState.UNRESOLVED.value:
            entry["resolution_state"] = ResolutionState.SUPPRESSED.value
            entry["forced_exit"] = True

        return entry


# =============================================================================
# Helper Functions
# =============================================================================

def detect_conflict(
    new_entry: Dict[str, Any],
    existing_entries: List[Dict[str, Any]]
) -> Optional[str]:
    """
    Detect if new entry conflicts with existing entries

    Args:
        new_entry: New semantic entry
        existing_entries: List of existing entries

    Returns:
        Concept name of conflicting entry, or None
    """
    new_concept = new_entry.get("concept", "")

    for existing in existing_entries:
        existing_concept = existing.get("concept", "")

        # Simple conflict detection: same concept with different definition
        if existing_concept == new_concept:
            if existing.get("definition") != new_entry.get("definition"):
                return existing_concept

        # Check explicit conflicts_with field
        conflicts_with = new_entry.get("conflicts_with", [])
        if existing_concept in conflicts_with:
            return existing_concept

    return None


def get_stakes_level_from_topic(concept: str, definition: str) -> StakesLevel:
    """
    Infer stakes level from concept/definition content

    Args:
        concept: Concept name
        definition: Concept definition

    Returns:
        StakesLevel
    """
    # Health/Safety keywords
    health_keywords = [
        "health", "safety", "allergy", "medical", "poison", "toxic",
        "danger", "harmful", "disease", "medication", "hospital",
        "สุขภาพ", "ความปลอดภัย", "แพ้", "อันตราย", "พิษ", "โรค"
    ]

    combined_text = f"{concept} {definition}".lower()

    for keyword in health_keywords:
        if keyword in combined_text:
            return StakesLevel.HIGH

    return StakesLevel.MEDIUM
