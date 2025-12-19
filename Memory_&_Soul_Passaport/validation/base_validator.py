# =============================================================================
# Base Validator
# Abstract base class for all MSP validators
# =============================================================================

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime, timezone

from .exceptions import MSPValidationError


# =============================================================================
# ValidationResult
# =============================================================================

@dataclass
class ValidationResult:
    """Result of validation operation"""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, message: str):
        """Add an error (makes result invalid)"""
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str):
        """Add a warning (doesn't affect validity)"""
        self.warnings.append(message)

    def add_info(self, message: str):
        """Add info message"""
        self.info.append(message)

    def merge(self, other: 'ValidationResult'):
        """Merge another ValidationResult into this one"""
        self.valid = self.valid and other.valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.info.extend(other.info)
        self.context.update(other.context)

    def __str__(self):
        parts = []
        parts.append(f"Valid: {self.valid}")

        if self.errors:
            parts.append(f"Errors ({len(self.errors)}):")
            for err in self.errors:
                parts.append(f"  - {err}")

        if self.warnings:
            parts.append(f"Warnings ({len(self.warnings)}):")
            for warn in self.warnings:
                parts.append(f"  - {warn}")

        if self.info:
            parts.append(f"Info ({len(self.info)}):")
            for inf in self.info:
                parts.append(f"  - {inf}")

        return "\n".join(parts)


# =============================================================================
# BaseValidator
# =============================================================================

class BaseValidator(ABC):
    """Abstract base class for all MSP validators"""

    def __init__(
        self,
        strict_mode: bool = True,
        audit_log_path: Optional[Path] = None
    ):
        """
        Initialize base validator

        Args:
            strict_mode: If True, treat warnings as errors
            audit_log_path: Path to audit log file (optional)
        """
        self.strict_mode = strict_mode
        self.audit_log_path = audit_log_path

        # Set up logging
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Set up audit logger"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING if self.strict_mode else logging.INFO)
        console_formatter = logging.Formatter('[%(name)s] %(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler (if audit log specified)
        if self.audit_log_path:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.audit_log_path)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        return logger

    @abstractmethod
    def validate(self, data: Dict[str, Any], **kwargs) -> ValidationResult:
        """
        Validate data

        Args:
            data: Data to validate
            **kwargs: Additional context-specific parameters

        Returns:
            ValidationResult with validation outcome
        """
        pass

    def _create_result(self, valid: bool = True) -> ValidationResult:
        """Create a new ValidationResult"""
        return ValidationResult(valid=valid)

    def _check_required_fields(
        self,
        data: Dict[str, Any],
        required_fields: List[str],
        result: ValidationResult,
        path: str = ""
    ):
        """
        Check for required fields

        Args:
            data: Data dictionary to check
            required_fields: List of required field names
            result: ValidationResult to update
            path: Current path in nested structure (for error messages)
        """
        for field in required_fields:
            if field not in data:
                result.add_error(
                    f"Missing required field: '{path}{field}'" if path else f"Missing required field: '{field}'"
                )

    def _check_enum_value(
        self,
        value: Any,
        valid_values: List[Any],
        field_name: str,
        result: ValidationResult
    ):
        """
        Check if value is in allowed enum values

        Args:
            value: Value to check
            valid_values: List of valid enum values
            field_name: Name of field (for error message)
            result: ValidationResult to update
        """
        if value not in valid_values:
            result.add_error(
                f"Invalid enum value for '{field_name}': '{value}' not in {valid_values}"
            )

    def _check_range(
        self,
        value: float,
        min_val: float,
        max_val: float,
        field_name: str,
        result: ValidationResult
    ):
        """
        Check if numeric value is in valid range

        Args:
            value: Value to check
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            field_name: Name of field (for error message)
            result: ValidationResult to update
        """
        if not isinstance(value, (int, float)):
            result.add_error(f"Field '{field_name}' must be numeric, got {type(value).__name__}")
            return

        if not (min_val <= value <= max_val):
            result.add_error(
                f"Field '{field_name}' value {value} out of range [{min_val}, {max_val}]"
            )

    def _scan_for_forbidden_fields(
        self,
        data: Dict[str, Any],
        forbidden_fields: List[str],
        result: ValidationResult,
        path: str = ""
    ):
        """
        Recursively scan for forbidden fields

        Args:
            data: Data dictionary to scan
            forbidden_fields: List of forbidden field names
            result: ValidationResult to update
            path: Current path in nested structure
        """
        if not isinstance(data, dict):
            return

        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key

            # Check if this key is forbidden
            if key in forbidden_fields:
                result.add_error(f"Forbidden field found: '{current_path}'")

            # Recurse into nested structures
            if isinstance(value, dict):
                self._scan_for_forbidden_fields(value, forbidden_fields, result, current_path)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        self._scan_for_forbidden_fields(
                            item, forbidden_fields, result, f"{current_path}[{i}]"
                        )

    def _audit_log(self, level: str, message: str, context: Dict[str, Any] = None):
        """
        Write to audit log

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            message: Log message
            context: Additional context to log
        """
        log_entry = message
        if context:
            log_entry += f" | Context: {context}"

        log_method = getattr(self.logger, level.lower())
        log_method(log_entry)
