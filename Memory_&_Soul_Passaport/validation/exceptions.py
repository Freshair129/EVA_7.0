# =============================================================================
# MSP Validation Exceptions
# Custom exception hierarchy for validation errors
# =============================================================================

from typing import List, Dict, Any


class MSPValidationError(Exception):
    """Base exception for all MSP validation errors"""

    def __init__(self, message: str, errors: List[str] = None, context: Dict[str, Any] = None):
        super().__init__(message)
        self.errors = errors or []
        self.context = context or {}

    def __str__(self):
        base = super().__str__()
        if self.errors:
            error_list = "\n  - ".join(self.errors)
            base += f"\n  Errors:\n  - {error_list}"
        return base


# =============================================================================
# Tier 1: Blocking Errors (strict mode)
# =============================================================================

class SchemaViolationError(MSPValidationError):
    """JSON schema validation failed"""
    pass


class MissingRequiredFieldError(MSPValidationError):
    """Required field is missing"""
    pass


class InvalidEnumValueError(MSPValidationError):
    """Enum field has invalid value"""
    pass


class OutOfRangeError(MSPValidationError):
    """Numeric value is out of valid range"""
    pass


class ForbiddenFieldError(MSPValidationError):
    """Data contains forbidden fields (LLM boundary violation)"""
    pass


class EpistemicBoundaryViolation(MSPValidationError):
    """LLM attempted to make authoritative claims (epistemic violation)"""
    pass


class StructuralValidationError(MSPValidationError):
    """Data structure is invalid"""
    pass


class StateValidationError(MSPValidationError):
    """indexed_state validation failed (eva_matrix, qualia, reflex)"""
    pass


class CrosslinkValidationError(MSPValidationError):
    """Crosslink structure or references are invalid"""
    pass


# =============================================================================
# Tier 2: Warning-level Errors (warn mode)
# =============================================================================

class MSPValidationWarning(MSPValidationError):
    """Base class for warnings (non-blocking in warn mode)"""
    pass


class UnusualIDFormatWarning(MSPValidationWarning):
    """ID format doesn't match expected pattern"""
    pass


class NonStandardNamingWarning(MSPValidationWarning):
    """Field naming doesn't follow conventions"""
    pass


class MissingOptionalFieldWarning(MSPValidationWarning):
    """Optional but recommended field is missing"""
    pass


# =============================================================================
# Semantic-specific Errors
# =============================================================================

class ConsolidationThresholdError(MSPValidationError):
    """Semantic entry doesn't meet consolidation threshold (confidence <= 0.7)"""
    pass


class ConceptFormatError(MSPValidationError):
    """Concept field doesn't match lowercase_snake_case format"""
    pass


class ConfidenceUpdateError(MSPValidationError):
    """Confidence update calculation failed"""
    pass


# =============================================================================
# Sensory-specific Errors
# =============================================================================

class InterpretationInSensoryError(MSPValidationError):
    """Sensory data contains interpretation (forbidden)"""
    pass


class InvalidDataTypeError(MSPValidationError):
    """data_type field has invalid value"""
    pass
