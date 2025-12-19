# =============================================================================
# Sensory Validator
# Validation for sensory memory - NO interpretation allowed
# =============================================================================

from pathlib import Path
from typing import Dict, Any, Optional

from .base_validator import BaseValidator, ValidationResult
from .schema_validator import SchemaValidator
from .rules.forbidden_fields import SENSORY_FORBIDDEN_FIELDS
from .exceptions import (
    InterpretationInSensoryError,
    InvalidDataTypeError,
)


class SensoryValidator(BaseValidator):
    """
    Sensory memory validator - enforces NO interpretation policy
    Sensory data represents evidence, not meaning
    """

    # Valid enum values
    DATA_TYPES = ["text", "audio", "visual", "multimodal"]
    CAPTURE_CHANNELS = ["user_input", "system_ui", "external_sensor"]
    CAPTURE_QUALITIES = ["low", "medium", "high"]

    # Allowed feature_snapshot fields (measurable features only)
    ALLOWED_FEATURES = ["pitch", "volume", "tempo", "pause_length", "tone_descriptor"]

    # Interpretive keywords that should NOT appear in sensory data
    INTERPRETIVE_KEYWORDS = [
        "emotion", "feeling", "mood", "intent", "intention", "meaning",
        "angry", "happy", "sad", "excited", "frustrated", "confused",
        "wants", "desires", "believes", "thinks", "feels",
        "aggressive", "friendly", "hostile", "warm", "cold",
        "sarcastic", "sincere", "lying", "honest"
    ]

    def __init__(
        self,
        schema_path: Optional[Path] = None,
        strict_mode: bool = True,
        audit_log_path: Optional[Path] = None
    ):
        """
        Initialize sensory validator

        Args:
            schema_path: Path to Sensory_Memory_Schema_v2.json
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

        self._audit_log("INFO", "Sensory validator initialized", {
            "schema_path": str(schema_path) if schema_path else "none",
            "strict_mode": strict_mode
        })

    def validate(self, entry: Dict[str, Any]) -> ValidationResult:
        """
        Validate sensory entry

        Args:
            entry: Sensory entry to validate

        Returns:
            ValidationResult
        """
        result = self._create_result()

        self._audit_log("INFO", "Starting sensory validation")

        # Phase 1: Structural validation
        structural_result = self._validate_structure(entry)
        result.merge(structural_result)

        # Phase 2: Interpretation detection (CRITICAL)
        interpretation_result = self._validate_no_interpretation(entry)
        result.merge(interpretation_result)

        # Phase 3: Data type validation
        data_type_result = self._validate_data_type(entry)
        result.merge(data_type_result)

        # Phase 4: Forbidden fields
        forbidden_result = self._validate_forbidden_fields(entry)
        result.merge(forbidden_result)

        # Log result
        if result.valid:
            self._audit_log("INFO", "Sensory validation PASSED", {
                "sensory_id": entry.get("sensory_id"),
                "data_type": entry.get("data_type"),
                "warnings": len(result.warnings)
            })
        else:
            self._audit_log("ERROR", "Sensory validation FAILED", {
                "sensory_id": entry.get("sensory_id"),
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
        required = ["sensory_id", "session_id", "episode_ref", "timestamp",
                   "data_type", "data_source", "sensory_payload"]
        self._check_required_fields(entry, required, result)

        # data_type enum
        if "data_type" in entry:
            self._check_enum_value(
                entry["data_type"],
                self.DATA_TYPES,
                "data_type",
                result
            )

        # data_source structure
        if "data_source" in entry:
            data_source = entry["data_source"]
            if not isinstance(data_source, dict):
                result.add_error("'data_source' must be an object")
            else:
                # Check required fields
                if "source_name" not in data_source:
                    result.add_error("'data_source' missing 'source_name'")
                if "capture_channel" not in data_source:
                    result.add_error("'data_source' missing 'capture_channel'")

                # Check capture_channel enum
                if "capture_channel" in data_source:
                    self._check_enum_value(
                        data_source["capture_channel"],
                        self.CAPTURE_CHANNELS,
                        "data_source.capture_channel",
                        result
                    )

        # sensory_payload structure
        if "sensory_payload" not in entry:
            result.add_error("Missing 'sensory_payload'")
        elif not isinstance(entry["sensory_payload"], dict):
            result.add_error("'sensory_payload' must be an object")

        return result

    # =========================================================================
    # Phase 2: Interpretation Detection (CRITICAL)
    # =========================================================================

    def _validate_no_interpretation(self, entry: Dict[str, Any]) -> ValidationResult:
        """
        CRITICAL: Detect and reject interpretation in sensory data
        Sensory data must be descriptive only, NOT interpretive
        """
        result = self._create_result()
        result.add_info("Phase 2: Interpretation detection (CRITICAL)")

        sensory_payload = entry.get("sensory_payload", {})

        # Check raw_content for interpretive language
        raw_content = sensory_payload.get("raw_content", "")
        if raw_content and isinstance(raw_content, str):
            detected_keywords = self._detect_interpretive_keywords(raw_content)
            if detected_keywords:
                result.add_error(
                    f"Interpretive language detected in raw_content: {detected_keywords}"
                )

        # Check feature_snapshot for invalid fields
        feature_snapshot = sensory_payload.get("feature_snapshot", {})
        if feature_snapshot and isinstance(feature_snapshot, dict):
            invalid_features = set(feature_snapshot.keys()) - set(self.ALLOWED_FEATURES)
            if invalid_features:
                result.add_error(
                    f"Invalid features in feature_snapshot: {invalid_features}. "
                    f"Only measurable features allowed: {self.ALLOWED_FEATURES}"
                )

        return result

    def _detect_interpretive_keywords(self, text: str) -> list:
        """Detect interpretive keywords in text"""
        text_lower = text.lower()
        detected = []

        for keyword in self.INTERPRETIVE_KEYWORDS:
            if keyword in text_lower:
                detected.append(keyword)

        return detected

    # =========================================================================
    # Phase 3: Data Type Validation
    # =========================================================================

    def _validate_data_type(self, entry: Dict[str, Any]) -> ValidationResult:
        """Validate data_type consistency"""
        result = self._create_result()
        result.add_info("Phase 3: Data type validation")

        data_type = entry.get("data_type")
        sensory_payload = entry.get("sensory_payload", {})

        if not data_type:
            return result

        # For audio type, expect feature_snapshot with audio features
        if data_type == "audio":
            feature_snapshot = sensory_payload.get("feature_snapshot", {})
            audio_features = ["pitch", "volume", "tempo"]
            has_audio_features = any(f in feature_snapshot for f in audio_features)

            if feature_snapshot and not has_audio_features:
                result.add_warning(
                    f"data_type is 'audio' but no audio features (pitch/volume/tempo) found"
                )

        return result

    # =========================================================================
    # Phase 4: Forbidden Fields
    # =========================================================================

    def _validate_forbidden_fields(self, entry: Dict[str, Any]) -> ValidationResult:
        """Scan for forbidden fields"""
        result = self._create_result()
        result.add_info("Phase 4: Forbidden fields check")

        self._scan_for_forbidden_fields(
            entry,
            SENSORY_FORBIDDEN_FIELDS,
            result
        )

        return result

    # =========================================================================
    # Strict Validation
    # =========================================================================

    def validate_strict(self, entry: Dict[str, Any]) -> None:
        """
        Validate entry, raising exception on failure

        Args:
            entry: Sensory entry to validate

        Raises:
            MSPValidationError: If validation fails
        """
        result = self.validate(entry)
        if not result.valid:
            from .exceptions import MSPValidationError
            raise MSPValidationError(
                "Sensory validation failed",
                errors=result.errors,
                context={"sensory_id": entry.get("sensory_id")}
            )
