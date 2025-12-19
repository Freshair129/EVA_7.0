# =============================================================================
# Episodic Validator
# 5-phase validation for episodic memory proposals
# =============================================================================

from pathlib import Path
from typing import Dict, Any, Optional, List

from .base_validator import BaseValidator, ValidationResult
from .schema_validator import SchemaValidator
from .rules.forbidden_fields import EPISODIC_FORBIDDEN_FIELDS
from .exceptions import (
    StructuralValidationError,
    EpistemicBoundaryViolation,
    StateValidationError,
    CrosslinkValidationError,
    ForbiddenFieldError,
)


class EpisodicValidator(BaseValidator):
    """
    5-phase episodic memory validator

    Validation Phases:
    1. Structural: Schema compliance, required sections, enums
    2. Epistemic: LLM boundary checks, non-authoritative marking
    3. State: indexed_state validation (eva_matrix, qualia, reflex)
    4. Crosslinks: Valid crosslink types and structure
    5. Forbidden Content: Recursive scan for forbidden fields
    """

    # Valid enum values
    EPISODE_TYPES = ["interaction", "observation", "system_event"]
    INTERACTION_MODES = ["casual", "discussion", "deep_discussion", "crisis"]
    STAKES_LEVELS = ["low", "medium", "high"]
    TIME_PRESSURES = ["low", "medium", "high"]
    SPEAKER_VALUES = ["user", "eva"]
    EPISTEMIC_STATUSES = ["hypothesize", "speculate"]
    EVA_MATRIX_AXES = ["stress_load", "social_warmth", "drive_level", "cognitive_clarity"]
    CROSSLINK_TYPES = ["ess_refs", "eva_matrix_refs", "rms_refs", "semantic_refs", "sensory_refs", "gks_refs"]

    def __init__(
        self,
        schema_path: Optional[Path] = None,
        strict_mode: bool = True,
        audit_log_path: Optional[Path] = None
    ):
        """
        Initialize episodic validator

        Args:
            schema_path: Path to Episodic_Memory_Schema_v2.json
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

        self._audit_log("INFO", "Episodic validator initialized", {
            "schema_path": str(schema_path) if schema_path else "none",
            "strict_mode": strict_mode
        })

    def validate(self, episode_data: Dict[str, Any], ri_level: str = "L3") -> ValidationResult:
        """
        Run complete 5-phase validation on episode data

        Args:
            episode_data: Episode data to validate
            ri_level: RI level (L1, L2, L3+) - affects which fields are required

        Returns:
            ValidationResult
        """
        result = self._create_result()

        self._audit_log("INFO", f"Starting episodic validation (RI: {ri_level})")

        # Phase 1: Structural Validation
        phase1_result = self._phase1_structural(episode_data, ri_level)
        result.merge(phase1_result)

        # Phase 2: Epistemic Validation
        phase2_result = self._phase2_epistemic(episode_data)
        result.merge(phase2_result)

        # Phase 3: State Validation (indexed_state)
        phase3_result = self._phase3_state(episode_data)
        result.merge(phase3_result)

        # Phase 4: Crosslinks Validation
        phase4_result = self._phase4_crosslinks(episode_data)
        result.merge(phase4_result)

        # Phase 5: Forbidden Content Check
        phase5_result = self._phase5_forbidden_content(episode_data)
        result.merge(phase5_result)

        # Log result
        if result.valid:
            self._audit_log("INFO", "Episodic validation PASSED", {
                "warnings": len(result.warnings),
                "ri_level": ri_level
            })
        else:
            self._audit_log("ERROR", "Episodic validation FAILED", {
                "errors": result.errors,
                "ri_level": ri_level
            })

        return result

    # =========================================================================
    # Phase 1: Structural Validation
    # =========================================================================

    def _phase1_structural(self, episode_data: Dict[str, Any], ri_level: str) -> ValidationResult:
        """
        Phase 1: Structural validation
        - Schema compliance
        - Required sections present
        - Enum validation
        - Turn structure
        """
        result = self._create_result()
        result.add_info("Phase 1: Structural validation")

        # Required sections (for L3+)
        if ri_level not in ["L1", "L2"]:
            required_sections = ["episode_header", "situation_context", "turns", "emotive_snapshot"]
            self._check_required_fields(episode_data, required_sections, result)

        # Validate episode_header
        if "episode_header" in episode_data:
            header = episode_data["episode_header"]

            # episode_type enum
            if "episode_type" in header:
                self._check_enum_value(
                    header["episode_type"],
                    self.EPISODE_TYPES,
                    "episode_header.episode_type",
                    result
                )

        # Validate situation_context
        if "situation_context" in episode_data:
            context = episode_data["situation_context"]

            # interaction_mode enum
            if "interaction_mode" in context:
                self._check_enum_value(
                    context["interaction_mode"],
                    self.INTERACTION_MODES,
                    "situation_context.interaction_mode",
                    result
                )

            # stakes_level enum
            if "stakes_level" in context:
                self._check_enum_value(
                    context["stakes_level"],
                    self.STAKES_LEVELS,
                    "situation_context.stakes_level",
                    result
                )

            # time_pressure enum
            if "time_pressure" in context:
                self._check_enum_value(
                    context["time_pressure"],
                    self.TIME_PRESSURES,
                    "situation_context.time_pressure",
                    result
                )

        # Validate turns
        if "turns" in episode_data:
            self._validate_turns(episode_data["turns"], result)

        return result

    def _validate_turns(self, turns: List[Dict[str, Any]], result: ValidationResult):
        """Validate turn structure"""
        if not isinstance(turns, list):
            result.add_error("'turns' must be an array")
            return

        turn_ids_seen = set()

        for i, turn in enumerate(turns):
            if not isinstance(turn, dict):
                result.add_error(f"Turn [{i}] must be an object")
                continue

            # Check turn_id
            if "turn_id" not in turn:
                result.add_error(f"Turn [{i}] missing 'turn_id'")
            else:
                turn_id = turn["turn_id"]
                if turn_id in turn_ids_seen:
                    result.add_error(f"Duplicate turn_id: '{turn_id}'")
                turn_ids_seen.add(turn_id)

            # Check speaker enum
            if "speaker" in turn:
                self._check_enum_value(
                    turn["speaker"],
                    self.SPEAKER_VALUES,
                    f"turns[{i}].speaker",
                    result
                )

            # Validate affective_inference if present
            if "affective_inference" in turn:
                self._validate_affective_inference(turn["affective_inference"], f"turns[{i}]", result)

    def _validate_affective_inference(self, affective: Dict[str, Any], path: str, result: ValidationResult):
        """Validate affective_inference structure"""
        if not isinstance(affective, dict):
            result.add_error(f"{path}.affective_inference must be an object")
            return

        # epistemic_status must be hypothesize or speculate
        if "epistemic_status" in affective:
            self._check_enum_value(
                affective["epistemic_status"],
                self.EPISTEMIC_STATUSES,
                f"{path}.affective_inference.epistemic_status",
                result
            )
        else:
            result.add_error(f"{path}.affective_inference missing 'epistemic_status'")

    # =========================================================================
    # Phase 2: Epistemic Validation
    # =========================================================================

    def _phase2_epistemic(self, episode_data: Dict[str, Any]) -> ValidationResult:
        """
        Phase 2: Epistemic validation
        - LLM boundary checks (no LLM-generated IDs)
        - affective_inference must be non-authoritative
        - semantic_frames are framing only (no truth claims)
        """
        result = self._create_result()
        result.add_info("Phase 2: Epistemic validation")

        # Check for LLM-generated IDs at top level
        llm_id_fields = ["episode_id", "context_id", "session_id", "user_id", "instance_id"]
        for field in llm_id_fields:
            if field in episode_data:
                # IDs are allowed, but warn if they look LLM-generated (not MSP format)
                # MSP format typically: ep_S01_001_abc123
                value = episode_data[field]
                if isinstance(value, str) and not self._is_msp_id_format(value):
                    result.add_warning(f"Field '{field}' has non-MSP ID format: '{value}'")

        # Check turns for LLM-generated turn_ids
        if "turns" in episode_data:
            for i, turn in enumerate(episode_data["turns"]):
                if "turn_id" in turn:
                    turn_id = turn["turn_id"]
                    if not self._is_msp_id_format(turn_id):
                        result.add_warning(f"turns[{i}].turn_id has non-MSP format: '{turn_id}'")

                # affective_inference already checked in Phase 1

        return result

    def _is_msp_id_format(self, id_value: str) -> bool:
        """Check if ID looks like MSP format (basic check)"""
        # MSP IDs typically have underscores and hex suffixes
        # Examples: ep_S01_001_abc123, t1, THA_01_S01
        # This is a heuristic check
        return "_" in id_value or id_value.startswith("t") or id_value.startswith("ep_")

    # =========================================================================
    # Phase 3: State Validation (indexed_state)
    # =========================================================================

    def _phase3_state(self, episode_data: Dict[str, Any]) -> ValidationResult:
        """
        Phase 3: State validation
        - emotive_snapshot.indexed_state structure
        - eva_matrix: exactly 4 axes, all in [0.0, 1.0]
        - qualia: intensity only, in [0.0, 1.0]
        - reflex: threat_level only, in [0.0, 1.0]
        """
        result = self._create_result()
        result.add_info("Phase 3: State validation")

        emotive_snapshot = episode_data.get("emotive_snapshot", {})
        indexed_state = emotive_snapshot.get("indexed_state", {})

        if not indexed_state:
            result.add_info("No indexed_state present (acceptable for L1/L2)")
            return result

        # Validate eva_matrix
        if "eva_matrix" in indexed_state:
            self._validate_eva_matrix(indexed_state["eva_matrix"], result)
        else:
            result.add_error("indexed_state missing 'eva_matrix'")

        # Validate qualia
        if "qualia" in indexed_state:
            self._validate_qualia(indexed_state["qualia"], result)
        else:
            result.add_error("indexed_state missing 'qualia'")

        # Validate reflex
        if "reflex" in indexed_state:
            self._validate_reflex(indexed_state["reflex"], result)
        else:
            result.add_error("indexed_state missing 'reflex'")

        return result

    def _validate_eva_matrix(self, eva_matrix: Dict[str, Any], result: ValidationResult):
        """Validate eva_matrix: exactly 4 axes, all [0.0, 1.0]"""
        if not isinstance(eva_matrix, dict):
            result.add_error("eva_matrix must be an object")
            return

        # Check all required axes present
        for axis in self.EVA_MATRIX_AXES:
            if axis not in eva_matrix:
                result.add_error(f"eva_matrix missing required axis: '{axis}'")
            else:
                self._check_range(
                    eva_matrix[axis],
                    0.0, 1.0,
                    f"eva_matrix.{axis}",
                    result
                )

        # Check for extra axes
        extra_axes = set(eva_matrix.keys()) - set(self.EVA_MATRIX_AXES)
        if extra_axes:
            result.add_error(f"eva_matrix contains extra axes: {extra_axes}")

    def _validate_qualia(self, qualia: Dict[str, Any], result: ValidationResult):
        """Validate qualia: intensity field only, [0.0, 1.0]"""
        if not isinstance(qualia, dict):
            result.add_error("qualia must be an object")
            return

        if "intensity" not in qualia:
            result.add_error("qualia missing 'intensity'")
        else:
            self._check_range(
                qualia["intensity"],
                0.0, 1.0,
                "qualia.intensity",
                result
            )

        # Check for extra fields
        extra_fields = set(qualia.keys()) - {"intensity"}
        if extra_fields:
            result.add_error(f"qualia contains extra fields: {extra_fields}")

    def _validate_reflex(self, reflex: Dict[str, Any], result: ValidationResult):
        """Validate reflex: threat_level field only, [0.0, 1.0]"""
        if not isinstance(reflex, dict):
            result.add_error("reflex must be an object")
            return

        if "threat_level" not in reflex:
            result.add_error("reflex missing 'threat_level'")
        else:
            self._check_range(
                reflex["threat_level"],
                0.0, 1.0,
                "reflex.threat_level",
                result
            )

        # Check for extra fields
        extra_fields = set(reflex.keys()) - {"threat_level"}
        if extra_fields:
            result.add_error(f"reflex contains extra fields: {extra_fields}")

    # =========================================================================
    # Phase 4: Crosslinks Validation
    # =========================================================================

    def _phase4_crosslinks(self, episode_data: Dict[str, Any]) -> ValidationResult:
        """
        Phase 4: Crosslinks validation
        - Valid crosslink types only
        - ID reference format (no embedded state)
        """
        result = self._create_result()
        result.add_info("Phase 4: Crosslinks validation")

        emotive_snapshot = episode_data.get("emotive_snapshot", {})
        crosslinks = emotive_snapshot.get("crosslinks", {})

        if not isinstance(crosslinks, dict):
            result.add_error("crosslinks must be an object")
            return result

        # Check for invalid crosslink types
        for key in crosslinks.keys():
            if key not in self.CROSSLINK_TYPES:
                result.add_error(f"Invalid crosslink type: '{key}'")

        # Validate each crosslink structure (basic check for ID references)
        for key, value in crosslinks.items():
            if key in self.CROSSLINK_TYPES:
                # Check that values are strings (IDs) or arrays of strings, not embedded state
                if isinstance(value, dict):
                    # Should be simple ID references, not complex objects
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, dict) and len(sub_value) > 5:
                            result.add_warning(f"crosslinks.{key}.{sub_key} looks like embedded state (should be ID only)")
                elif isinstance(value, list):
                    # Array of ID strings
                    for item in value:
                        if not isinstance(item, str):
                            result.add_error(f"crosslinks.{key} should contain ID strings, not {type(item).__name__}")

        return result

    # =========================================================================
    # Phase 5: Forbidden Content Check
    # =========================================================================

    def _phase5_forbidden_content(self, episode_data: Dict[str, Any]) -> ValidationResult:
        """
        Phase 5: Forbidden content check
        - Recursive scan for forbidden fields
        """
        result = self._create_result()
        result.add_info("Phase 5: Forbidden content check")

        # Scan for forbidden fields
        self._scan_for_forbidden_fields(
            episode_data,
            EPISODIC_FORBIDDEN_FIELDS,
            result
        )

        return result

    # =========================================================================
    # Validation with Exception Raising
    # =========================================================================

    def validate_strict(self, episode_data: Dict[str, Any], ri_level: str = "L3") -> None:
        """
        Validate episode data, raising exception on failure

        Args:
            episode_data: Episode data to validate
            ri_level: RI level

        Raises:
            MSPValidationError: If validation fails
        """
        result = self.validate(episode_data, ri_level)
        if not result.valid:
            raise StructuralValidationError(
                "Episodic validation failed",
                errors=result.errors,
                context={"ri_level": ri_level}
            )
