# =============================================================================
# Semantic Validator
# Validation for semantic memory entries with conflict detection
# =============================================================================

from pathlib import Path
from typing import Dict, Any, Optional, List
import re

from .base_validator import BaseValidator, ValidationResult
from .schema_validator import SchemaValidator
from .rules.forbidden_fields import SEMANTIC_FORBIDDEN_FIELDS
from .confidence_updater import ConfidenceUpdater, detect_conflict
from .exceptions import (
    ConsolidationThresholdError,
    ConceptFormatError,
)


class SemanticValidator(BaseValidator):
    """
    Semantic memory validator with conflict detection
    """

    # Valid enum values
    EPISTEMIC_STATUSES = ["hypothesis", "provisional", "confirmed"]
    RESOLUTION_STATES = ["unresolved", "resolved", "suppressed"]

    # Consolidation threshold
    CONSOLIDATION_THRESHOLD = 0.7

    def __init__(
        self,
        schema_path: Optional[Path] = None,
        strict_mode: bool = True,
        audit_log_path: Optional[Path] = None
    ):
        """
        Initialize semantic validator

        Args:
            schema_path: Path to Semantic_Memory_Schema_v2.json
            strict_mode: If True, treat warnings as errors
            audit_log_path: Path to audit log file
        """
        super().__init__(strict_mode, audit_log_path)

        # Initialize schema validator
        if schema_path and schema_path.exists():
            self.schema_validator = SchemaValidator(
                schema_path=schema_path,
                strict_mode=strict_mode,
                audit_log_path=audit_log_path
            )
        else:
            self.schema_validator = None
            if schema_path:
                self.logger.warning(f"Schema file not found: {schema_path}")

        # Initialize confidence updater
        self.confidence_updater = ConfidenceUpdater()

        self._audit_log("INFO", "Semantic validator initialized", {
            "schema_path": str(schema_path) if schema_path else "none",
            "strict_mode": strict_mode
        })

    def validate(
        self,
        entry: Dict[str, Any],
        existing_entries: Optional[List[Dict[str, Any]]] = None
    ) -> ValidationResult:
        """
        Validate semantic entry

        Args:
            entry: Semantic entry to validate
            existing_entries: List of existing semantic entries (for conflict detection)

        Returns:
            ValidationResult
        """
        result = self._create_result()

        self._audit_log("INFO", "Starting semantic validation")

        # Phase 1: Structural validation
        structural_result = self._validate_structure(entry)
        result.merge(structural_result)

        # Phase 2: Concept format validation
        concept_result = self._validate_concept_format(entry)
        result.merge(concept_result)

        # Phase 3: Confidence validation
        confidence_result = self._validate_confidence(entry)
        result.merge(confidence_result)

        # Phase 4: Conflict detection
        if existing_entries:
            conflict_result = self._validate_conflicts(entry, existing_entries)
            result.merge(conflict_result)

        # Phase 5: Forbidden fields
        forbidden_result = self._validate_forbidden_fields(entry)
        result.merge(forbidden_result)

        # Log result
        if result.valid:
            self._audit_log("INFO", "Semantic validation PASSED", {
                "concept": entry.get("concept"),
                "confidence": entry.get("confidence"),
                "warnings": len(result.warnings)
            })
        else:
            self._audit_log("ERROR", "Semantic validation FAILED", {
                "concept": entry.get("concept"),
                "errors": result.errors
            })

        return result

    # =========================================================================
    # Phase 1: Structural Validation
    # =========================================================================

    def _validate_structure(self, entry: Dict[str, Any]) -> ValidationResult:
        """Validate basic structure"""
        result = self._create_result()
        result.add_info("Phase 1: Structural validation")

        # Required fields
        required = ["concept", "epistemic_status", "confidence", "derived_from"]
        self._check_required_fields(entry, required, result)

        # Epistemic status enum
        if "epistemic_status" in entry:
            self._check_enum_value(
                entry["epistemic_status"],
                self.EPISTEMIC_STATUSES,
                "epistemic_status",
                result
            )

        # Resolution state enum (if present)
        if "resolution_state" in entry:
            self._check_enum_value(
                entry["resolution_state"],
                self.RESOLUTION_STATES,
                "resolution_state",
                result
            )

        # Derived_from structure
        if "derived_from" in entry:
            derived = entry["derived_from"]
            if not isinstance(derived, dict):
                result.add_error("'derived_from' must be an object")
            elif "episode_id" not in derived:
                result.add_error("'derived_from' missing 'episode_id'")

        return result

    # =========================================================================
    # Phase 2: Concept Format Validation
    # =========================================================================

    def _validate_concept_format(self, entry: Dict[str, Any]) -> ValidationResult:
        """Validate concept naming format"""
        result = self._create_result()
        result.add_info("Phase 2: Concept format validation")

        concept = entry.get("concept")
        if not concept:
            return result

        # Check lowercase_snake_case format
        if not self._is_lowercase_snake_case(concept):
            result.add_error(
                f"Concept '{concept}' must be lowercase_snake_case format"
            )

        # Check for certainty encoding
        certainty_words = ["confirmed", "certain", "definite", "absolute", "proven"]
        if any(word in concept.lower() for word in certainty_words):
            result.add_warning(
                f"Concept '{concept}' appears to encode certainty (should be in epistemic_status instead)"
            )

        return result

    def _is_lowercase_snake_case(self, s: str) -> bool:
        """Check if string is lowercase_snake_case"""
        # Pattern: lowercase letters, numbers, and underscores only
        # Must start with letter, no consecutive underscores
        pattern = r'^[a-z][a-z0-9_]*[a-z0-9]$|^[a-z]$'
        return bool(re.match(pattern, s))

    # =========================================================================
    # Phase 3: Confidence Validation
    # =========================================================================

    def _validate_confidence(self, entry: Dict[str, Any]) -> ValidationResult:
        """Validate confidence value and consistency"""
        result = self._create_result()
        result.add_info("Phase 3: Confidence validation")

        confidence = entry.get("confidence")
        if confidence is None:
            return result

        # Range check
        self._check_range(confidence, 0.0, 1.0, "confidence", result)

        # Consistency with epistemic_status
        epistemic_status = entry.get("epistemic_status")
        if epistemic_status:
            expected_status = self.confidence_updater.get_epistemic_status(confidence)
            if epistemic_status != expected_status.value:
                result.add_warning(
                    f"Confidence {confidence} suggests '{expected_status.value}' "
                    f"but epistemic_status is '{epistemic_status}'"
                )

        return result

    # =========================================================================
    # Phase 4: Conflict Detection
    # =========================================================================

    def _validate_conflicts(
        self,
        entry: Dict[str, Any],
        existing_entries: List[Dict[str, Any]]
    ) -> ValidationResult:
        """Detect conflicts with existing entries"""
        result = self._create_result()
        result.add_info("Phase 4: Conflict detection")

        # Detect conflicts
        conflicting_concept = detect_conflict(entry, existing_entries)

        if conflicting_concept:
            result.add_warning(
                f"Conflict detected with existing concept: '{conflicting_concept}'"
            )
            result.context["conflict_detected"] = True
            result.context["conflicting_concept"] = conflicting_concept

            # Check if conflicts_with field is present
            conflicts_with = entry.get("conflicts_with", [])
            if conflicting_concept not in conflicts_with:
                result.add_info(
                    f"Consider adding '{conflicting_concept}' to conflicts_with field"
                )

        return result

    # =========================================================================
    # Phase 5: Forbidden Fields
    # =========================================================================

    def _validate_forbidden_fields(self, entry: Dict[str, Any]) -> ValidationResult:
        """Scan for forbidden fields"""
        result = self._create_result()
        result.add_info("Phase 5: Forbidden fields check")

        self._scan_for_forbidden_fields(
            entry,
            SEMANTIC_FORBIDDEN_FIELDS,
            result
        )

        return result

    # =========================================================================
    # Consolidation Validation
    # =========================================================================

    def validate_for_consolidation(self, entry: Dict[str, Any]) -> bool:
        """
        Check if entry meets consolidation threshold

        Args:
            entry: Semantic entry

        Returns:
            True if confidence > 0.7 and no blocking errors
        """
        confidence = entry.get("confidence", 0.0)

        if confidence <= self.CONSOLIDATION_THRESHOLD:
            self._audit_log("INFO", "Entry below consolidation threshold", {
                "concept": entry.get("concept"),
                "confidence": confidence,
                "threshold": self.CONSOLIDATION_THRESHOLD
            })
            return False

        # Basic validation
        result = self.validate(entry)

        if not result.valid:
            self._audit_log("WARNING", "Entry failed validation for consolidation", {
                "concept": entry.get("concept"),
                "errors": result.errors
            })
            return False

        self._audit_log("INFO", "Entry meets consolidation threshold", {
            "concept": entry.get("concept"),
            "confidence": confidence
        })
        return True

    # =========================================================================
    # Strict Validation
    # =========================================================================

    def validate_strict(
        self,
        entry: Dict[str, Any],
        existing_entries: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Validate entry, raising exception on failure

        Args:
            entry: Semantic entry to validate
            existing_entries: List of existing entries

        Raises:
            MSPValidationError: If validation fails
        """
        result = self.validate(entry, existing_entries)
        if not result.valid:
            from .exceptions import MSPValidationError
            raise MSPValidationError(
                "Semantic validation failed",
                errors=result.errors,
                context={"concept": entry.get("concept")}
            )
