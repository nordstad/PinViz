"""Device configuration validator for pinviz.

This module provides validation for all device JSON configuration files.
It scans the device_configs directory and validates each file against
the DeviceConfigSchema.
"""

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import ValidationError

from .schemas import validate_device_config


class ValidationSeverity(StrEnum):
    """Severity level for validation issues."""

    ERROR = "error"
    WARNING = "warning"


@dataclass
class ValidationIssue:
    """Represents a validation issue found in a device configuration.

    Attributes:
        file_path: Path to the device config file
        severity: Issue severity (error or warning)
        message: Human-readable error message
        details: Additional error details
    """

    file_path: Path
    severity: ValidationSeverity
    message: str
    details: str = ""

    def __str__(self) -> str:
        """Format validation issue for display."""
        severity_symbol = "❌" if self.severity == ValidationSeverity.ERROR else "⚠️ "
        result = f"{severity_symbol} {self.file_path.name}: {self.message}"
        if self.details:
            result += f"\n   {self.details}"
        return result


@dataclass
class ValidationResult:
    """Results from validating device configurations.

    Attributes:
        total_files: Total number of device files scanned
        valid_files: Number of valid device files
        errors: List of error issues
        warnings: List of warning issues
        checked_ids: Set of device IDs that were found
    """

    total_files: int
    valid_files: int
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
    checked_ids: set[str]

    @property
    def error_count(self) -> int:
        """Number of error issues."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Number of warning issues."""
        return len(self.warnings)

    @property
    def has_errors(self) -> bool:
        """Whether there are any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Whether there are any warnings."""
        return len(self.warnings) > 0

    @property
    def is_valid(self) -> bool:
        """Whether all files are valid (no errors)."""
        return not self.has_errors


class DeviceConfigValidator:
    """Validator for device configuration files."""

    def __init__(self):
        """Initialize the device config validator."""
        self.issues: list[ValidationIssue] = []
        self.device_ids: set[str] = set()
        self.id_to_files: dict[str, list[Path]] = {}

    def validate_all_devices(self, device_configs_dir: Path | None = None) -> ValidationResult:
        """Validate all device configuration files.

        Args:
            device_configs_dir: Path to device_configs directory.
                               If None, uses default location.

        Returns:
            ValidationResult with summary and all issues found
        """
        if device_configs_dir is None:
            # Default to src/pinviz/device_configs
            module_dir = Path(__file__).parent
            device_configs_dir = module_dir / "device_configs"

        if not device_configs_dir.exists():
            return ValidationResult(
                total_files=0,
                valid_files=0,
                errors=[
                    ValidationIssue(
                        file_path=device_configs_dir,
                        severity=ValidationSeverity.ERROR,
                        message=f"Device configs directory not found: {device_configs_dir}",
                    )
                ],
                warnings=[],
                checked_ids=set(),
            )

        # Scan all JSON files recursively
        json_files = list(device_configs_dir.rglob("*.json"))

        if not json_files:
            return ValidationResult(
                total_files=0,
                valid_files=0,
                errors=[],
                warnings=[
                    ValidationIssue(
                        file_path=device_configs_dir,
                        severity=ValidationSeverity.WARNING,
                        message="No device configuration files found",
                    )
                ],
                checked_ids=set(),
            )

        # Reset state
        self.issues = []
        self.device_ids = set()
        self.id_to_files = {}

        # Validate each file
        valid_count = 0
        for json_file in json_files:
            if self._validate_device_file(json_file):
                valid_count += 1

        # Check for duplicate IDs
        self._check_duplicate_ids()

        # Separate errors and warnings
        errors = [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]
        warnings = [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]

        return ValidationResult(
            total_files=len(json_files),
            valid_files=valid_count,
            errors=errors,
            warnings=warnings,
            checked_ids=self.device_ids.copy(),
        )

    def _validate_device_file(self, file_path: Path) -> bool:
        """Validate a single device configuration file.

        Args:
            file_path: Path to the device JSON file

        Returns:
            True if file is valid, False otherwise
        """
        try:
            # Read JSON file
            with open(file_path) as f:
                try:
                    config_data = json.load(f)
                except json.JSONDecodeError as e:
                    self.issues.append(
                        ValidationIssue(
                            file_path=file_path,
                            severity=ValidationSeverity.ERROR,
                            message="Invalid JSON syntax",
                            details=str(e),
                        )
                    )
                    return False

            # Validate against schema
            try:
                validated_config = validate_device_config(config_data)

                # Track device ID for duplicate checking
                device_id = validated_config.id
                self.device_ids.add(device_id)

                # Track which file this ID came from
                if device_id not in self.id_to_files:
                    self.id_to_files[device_id] = []
                self.id_to_files[device_id].append(file_path)

                # Check for common issues
                self._check_common_issues(file_path, validated_config)

                return True

            except ValidationError as e:
                # Format pydantic validation errors
                error_messages = []
                for error in e.errors():
                    loc = " → ".join(str(x) for x in error["loc"])
                    error_messages.append(f"{loc}: {error['msg']}")

                self.issues.append(
                    ValidationIssue(
                        file_path=file_path,
                        severity=ValidationSeverity.ERROR,
                        message="Schema validation failed",
                        details="\n   ".join(error_messages),
                    )
                )
                return False

        except Exception as e:
            self.issues.append(
                ValidationIssue(
                    file_path=file_path,
                    severity=ValidationSeverity.ERROR,
                    message=f"Failed to process file: {e}",
                )
            )
            return False

    def _check_common_issues(self, file_path: Path, config) -> None:
        """Check for common issues that aren't schema violations.

        Args:
            file_path: Path to the device file
            config: Validated device config
        """
        # Warning: Missing description
        if not config.description:
            self.issues.append(
                ValidationIssue(
                    file_path=file_path,
                    severity=ValidationSeverity.WARNING,
                    message="Missing description field",
                    details="Add a brief description of what the device does",
                )
            )

        # Warning: Missing datasheet URL
        if not config.datasheet_url:
            self.issues.append(
                ValidationIssue(
                    file_path=file_path,
                    severity=ValidationSeverity.WARNING,
                    message="Missing datasheet_url",
                    details="Add a link to the device datasheet for reference",
                )
            )

        # Warning: I2C device without address
        pin_roles = [pin.role for pin in config.pins]
        has_i2c = "I2C_SDA" in pin_roles or "I2C_SCL" in pin_roles
        if has_i2c and not config.i2c_address:
            self.issues.append(
                ValidationIssue(
                    file_path=file_path,
                    severity=ValidationSeverity.WARNING,
                    message="I2C device without i2c_address",
                    details="Add the default I2C address for this device",
                )
            )

    def _check_duplicate_ids(self) -> None:
        """Check for duplicate device IDs across all files."""
        for device_id, files in self.id_to_files.items():
            if len(files) > 1:
                # Found duplicate ID in multiple files
                file_list = ", ".join(f.name for f in files)
                self.issues.append(
                    ValidationIssue(
                        file_path=files[0],
                        severity=ValidationSeverity.ERROR,
                        message=f"Duplicate device ID '{device_id}'",
                        details=f"Found in {len(files)} files: {file_list}",
                    )
                )


def validate_devices(device_configs_dir: Path | None = None) -> ValidationResult:
    """Validate all device configuration files.

    Args:
        device_configs_dir: Optional path to device_configs directory

    Returns:
        ValidationResult with summary and all issues
    """
    validator = DeviceConfigValidator()
    return validator.validate_all_devices(device_configs_dir)
