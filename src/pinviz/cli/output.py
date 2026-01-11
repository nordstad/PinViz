"""Rich output helpers for consistent CLI UX."""

from typing import Any, Literal

from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..validation import ValidationIssue, ValidationLevel


def print_validation_issues(
    issues: list[ValidationIssue], console: Console, use_panel: bool = True
) -> None:
    """Print validation issues with rich formatting.

    Creates a formatted table showing validation issues categorized by severity
    level (ERROR, WARN, INFO) with appropriate color coding, optionally wrapped
    in a panel for better visual organization.

    Args:
        issues: List of validation issues to display
        console: Rich console instance for output
        use_panel: Whether to wrap the output in a rich panel (default: True)

    Example:
        >>> from rich.console import Console
        >>> from pinviz.validation import ValidationIssue, ValidationLevel
        >>> issues = [
        ...     ValidationIssue(ValidationLevel.ERROR, "Pin conflict at GPIO17"),
        ...     ValidationIssue(ValidationLevel.WARNING, "Power supply may be insufficient"),
        ... ]
        >>> console = Console()
        >>> print_validation_issues(issues, console)
        # Displays formatted table with colored severity levels in a panel
    """
    if not issues:
        return

    # Categorize issues by level
    errors = [i for i in issues if i.level == ValidationLevel.ERROR]
    warnings = [i for i in issues if i.level == ValidationLevel.WARNING]
    infos = [i for i in issues if i.level == ValidationLevel.INFO]

    # Create rich table
    table = Table(show_header=True, header_style="bold", show_edge=False)
    table.add_column("Level", style="dim", width=10)
    table.add_column("Issue", overflow="fold")

    # Add rows with color coding
    for issue in errors:
        table.add_row("[red]ERROR[/red]", str(issue))
    for issue in warnings:
        table.add_row("[yellow]WARN[/yellow]", str(issue))
    for issue in infos:
        table.add_row("[blue]INFO[/blue]", str(issue))

    # Wrap in panel if requested
    if use_panel:
        panel_title = (
            "[bold red]Validation Issues" if errors else "[bold yellow]Validation Warnings"
        )
        panel = Panel(
            table,
            title=panel_title,
            border_style="red" if errors else "yellow",
            padding=(1, 2),
        )
        console.print(panel)
    else:
        console.print("\n[bold]Validation Issues:[/bold]")
        console.print(table)


def print_success(message: str, console: Console) -> None:
    """Print a success message with green checkmark.

    Args:
        message: Success message to display
        console: Rich console instance for output

    Example:
        >>> from rich.console import Console
        >>> console = Console()
        >>> print_success("Diagram generated: output.svg", console)
        ✓ Diagram generated: output.svg
    """
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str, console: Console) -> None:
    """Print an error message with red X.

    Args:
        message: Error message to display
        console: Rich console instance for output

    Example:
        >>> from rich.console import Console
        >>> console = Console()
        >>> print_error("Configuration file not found", console)
        ✗ Configuration file not found
    """
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str, console: Console) -> None:
    """Print a warning message with yellow warning symbol.

    Args:
        message: Warning message to display
        console: Rich console instance for output

    Example:
        >>> from rich.console import Console
        >>> console = Console()
        >>> print_warning("Found 3 warnings. Review carefully.", console)
        ⚠ Found 3 warnings. Review carefully.
    """
    console.print(f"[yellow]⚠[/yellow] {message}")


# JSON Output Schemas


class ValidationSummary(BaseModel):
    """Summary of validation results."""

    errors: int = 0
    warnings: int = 0
    infos: int = 0


class ValidationIssueJson(BaseModel):
    """JSON representation of a validation issue."""

    level: str
    message: str


class RenderOutputJson(BaseModel):
    """JSON output for render command."""

    status: Literal["success", "error"]
    output_path: str | None = None
    validation: ValidationSummary
    errors: list[str] | None = None


class ValidateOutputJson(BaseModel):
    """JSON output for validate command."""

    status: Literal["success", "error", "warning"]
    validation: ValidationSummary
    issues: list[ValidationIssueJson] | None = None
    errors: list[str] | None = None


class DeviceInfo(BaseModel):
    """Device information for JSON output."""

    id: str
    category: str
    description: str | None = None
    url: str | None = None


class BoardInfo(BaseModel):
    """Board information for JSON output."""

    name: str
    aliases: list[str]


class ListOutputJson(BaseModel):
    """JSON output for list command."""

    status: Literal["success"]
    boards: list[BoardInfo]
    devices: list[DeviceInfo]
    examples: list[dict[str, str]]


class ExampleOutputJson(BaseModel):
    """JSON output for example command."""

    status: Literal["success", "error"]
    example_name: str
    output_path: str | None = None
    errors: list[str] | None = None


class ValidateDevicesOutputJson(BaseModel):
    """JSON output for validate-devices command."""

    status: Literal["success", "error", "warning"]
    total_files: int
    valid_files: int
    error_count: int
    warning_count: int
    errors: list[str] | None = None
    warnings: list[str] | None = None


def output_json(data: BaseModel | dict[str, Any], console: Console) -> None:
    """Output JSON data to console with pretty formatting.

    Args:
        data: Pydantic model or dict to output as JSON
        console: Rich console instance for output

    Example:
        >>> from rich.console import Console
        >>> console = Console()
        >>> data = RenderOutputJson(
        ...     status="success",
        ...     output_path="output.svg",
        ...     validation=ValidationSummary(errors=0, warnings=1)
        ... )
        >>> output_json(data, console)
    """
    if isinstance(data, BaseModel):
        json_data = data.model_dump(mode="json", exclude_none=True)
    else:
        json_data = data

    # Use Rich's built-in JSON printing for syntax highlighting
    console.print_json(data=json_data)


def format_validation_issues_json(issues: list[ValidationIssue]) -> list[ValidationIssueJson]:
    """Convert validation issues to JSON-serializable format.

    Args:
        issues: List of validation issues

    Returns:
        List of JSON-serializable validation issues
    """
    return [ValidationIssueJson(level=issue.level.name, message=str(issue)) for issue in issues]


def get_validation_summary(issues: list[ValidationIssue]) -> ValidationSummary:
    """Get validation summary counts from issues list.

    Args:
        issues: List of validation issues

    Returns:
        ValidationSummary with counts by level
    """
    return ValidationSummary(
        errors=len([i for i in issues if i.level == ValidationLevel.ERROR]),
        warnings=len([i for i in issues if i.level == ValidationLevel.WARNING]),
        infos=len([i for i in issues if i.level == ValidationLevel.INFO]),
    )
