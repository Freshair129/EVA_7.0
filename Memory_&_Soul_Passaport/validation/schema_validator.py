# =============================================================================
# Schema Validator
# JSON Schema validation wrapper using jsonschema library
# =============================================================================

import json
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from jsonschema import validate, ValidationError as JsonSchemaValidationError, Draft7Validator
    from jsonschema.exceptions import SchemaError
except ImportError:
    raise ImportError("jsonschema library required. Install with: pip install jsonschema")

from .base_validator import BaseValidator, ValidationResult
from .exceptions import SchemaViolationError


class SchemaValidator(BaseValidator):
    """
    JSON Schema validator with caching
    """

    def __init__(
        self,
        schema_path: Optional[Path] = None,
        schema_dict: Optional[Dict[str, Any]] = None,
        strict_mode: bool = True,
        audit_log_path: Optional[Path] = None
    ):
        """
        Initialize schema validator

        Args:
            schema_path: Path to JSON schema file
            schema_dict: Schema as dictionary (alternative to schema_path)
            strict_mode: If True, treat warnings as errors
            audit_log_path: Path to audit log file
        """
        super().__init__(strict_mode, audit_log_path)

        if schema_path is None and schema_dict is None:
            raise ValueError("Either schema_path or schema_dict must be provided")

        # Load schema
        if schema_path:
            self.schema_path = schema_path
            self.schema = self._load_schema(schema_path)
        else:
            self.schema_path = None
            self.schema = schema_dict

        # Create validator (cached)
        try:
            self.validator = Draft7Validator(self.schema)
        except SchemaError as e:
            raise ValueError(f"Invalid JSON schema: {e}")

        self._audit_log("INFO", f"Schema validator initialized", {
            "schema_path": str(schema_path) if schema_path else "inline",
            "strict_mode": strict_mode
        })

    def _load_schema(self, schema_path: Path) -> Dict[str, Any]:
        """Load JSON schema from file"""
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            return schema
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file {schema_path}: {e}")

    def validate(self, data: Dict[str, Any], **kwargs) -> ValidationResult:
        """
        Validate data against JSON schema

        Args:
            data: Data to validate
            **kwargs: Not used (for BaseValidator compatibility)

        Returns:
            ValidationResult
        """
        result = self._create_result()

        # Run jsonschema validation
        errors = list(self.validator.iter_errors(data))

        if errors:
            result.valid = False
            for error in errors:
                # Build path to error
                path = ".".join(str(p) for p in error.path) if error.path else "root"
                error_msg = f"Schema violation at '{path}': {error.message}"
                result.add_error(error_msg)

            self._audit_log("ERROR", "Schema validation failed", {
                "error_count": len(errors),
                "errors": result.errors
            })
        else:
            result.add_info("Schema validation passed")
            self._audit_log("INFO", "Schema validation passed")

        return result

    def validate_strict(self, data: Dict[str, Any]) -> None:
        """
        Validate data against schema, raising exception on failure

        Args:
            data: Data to validate

        Raises:
            SchemaViolationError: If validation fails
        """
        result = self.validate(data)
        if not result.valid:
            raise SchemaViolationError(
                "Schema validation failed",
                errors=result.errors,
                context={"schema_path": str(self.schema_path) if self.schema_path else "inline"}
            )
