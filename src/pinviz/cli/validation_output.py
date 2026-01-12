"""Validation output handling for CLI commands."""

from dataclasses import dataclass
from enum import Enum

from rich.console import Console

from ..validation import ValidationIssue, ValidationLevel
from .output import (
    ValidateOutputJson,
    format_validation_issues_json,
    get_validation_summary,
    output_json,
    print_error,
    print_success,
    print_validation_issues,
)


class ValidationStatus(Enum):
    """Validation result status."""

    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationResult:
    """Encapsulates validation result and output logic.

    This class simplifies validation command implementations by centralizing
    the logic for determining validation status, categorizing issues, and
    outputting results in both console and JSON formats.

    Attributes:
        issues: List of validation issues found
        strict: Whether to treat warnings as errors
        config_path: Optional path to config file (for error reporting)

    Example:
        >>> validator = DiagramValidator()
        >>> issues = validator.validate(diagram)
        >>> result = ValidationResult(issues=issues, strict=True)
        >>>
        >>> if result.json_output:
        >>>     result.output_json(console)
        >>> else:
        >>>     result.output_console(console)
        >>>
        >>> if result.exit_code != 0:
        >>>     raise typer.Exit(code=result.exit_code)
    """

    issues: list[ValidationIssue]
    strict: bool
    config_path: str | None = None

    @property
    def status(self) -> ValidationStatus:
        """Determine validation status based on issues and strict mode.

        Returns:
            ValidationStatus: SUCCESS if no issues, ERROR if errors found or
                             warnings in strict mode, WARNING if warnings found
        """
        if self.errors:
            return ValidationStatus.ERROR
        if self.warnings and self.strict:
            return ValidationStatus.ERROR
        if self.warnings:
            return ValidationStatus.WARNING
        return ValidationStatus.SUCCESS

    @property
    def errors(self) -> list[ValidationIssue]:
        """Get only error-level issues.

        Returns:
            List of validation issues with ERROR level
        """
        return [i for i in self.issues if i.level == ValidationLevel.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Get only warning-level issues.

        Returns:
            List of validation issues with WARNING level
        """
        return [i for i in self.issues if i.level == ValidationLevel.WARNING]

    @property
    def exit_code(self) -> int:
        """Get appropriate exit code based on validation status.

        Returns:
            0 for success/warning (non-strict), 1 for errors or warnings (strict)
        """
        return 1 if self.status in (ValidationStatus.ERROR,) else 0

    def output_json(self, console: Console) -> None:
        """Output validation result as JSON.

        Args:
            console: Rich console for output
        """
        result = ValidateOutputJson(
            status=self.status.value,
            validation=get_validation_summary(self.issues),
            issues=format_validation_issues_json(self.issues) if self.issues else None,
        )
        output_json(result, console)

    def output_console(self, console: Console) -> None:
        """Output validation result to console with Rich formatting.

        Args:
            console: Rich console for output
        """
        if not self.issues:
            console.print()
            print_success("Validation passed! No issues found.", console)
            print_success("Current limits OK", console)
            return

        # Display all issues
        print_validation_issues(self.issues, console)

        # Summary
        console.print()
        error_count = len(self.errors)
        warning_count = len(self.warnings)

        if error_count > 0 or warning_count > 0:
            console.print(
                f"Found [red]{error_count}[/red] error(s), "
                f"[yellow]{warning_count}[/yellow] warning(s)"
            )

        # Strict mode message
        if self.warnings and self.strict and not self.errors:
            print_error("Treating warnings as errors (--strict mode)", console)
