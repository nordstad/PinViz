"""Rich output helpers for consistent CLI UX."""

from rich.console import Console
from rich.table import Table

from ..validation import ValidationIssue, ValidationLevel


def print_validation_issues(issues: list[ValidationIssue], console: Console) -> None:
    """Print validation issues with rich formatting.

    Creates a formatted table showing validation issues categorized by severity
    level (ERROR, WARN, INFO) with appropriate color coding.

    Args:
        issues: List of validation issues to display
        console: Rich console instance for output

    Example:
        >>> from rich.console import Console
        >>> from pinviz.validation import ValidationIssue, ValidationLevel
        >>> issues = [
        ...     ValidationIssue(ValidationLevel.ERROR, "Pin conflict at GPIO17"),
        ...     ValidationIssue(ValidationLevel.WARNING, "Power supply may be insufficient"),
        ... ]
        >>> console = Console()
        >>> print_validation_issues(issues, console)
        # Displays formatted table with colored severity levels
    """
    if not issues:
        return

    # Categorize issues by level
    errors = [i for i in issues if i.level == ValidationLevel.ERROR]
    warnings = [i for i in issues if i.level == ValidationLevel.WARNING]
    infos = [i for i in issues if i.level == ValidationLevel.INFO]

    console.print("\n[bold]Validation Issues:[/bold]")

    # Create rich table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Level", style="dim", width=10)
    table.add_column("Issue", overflow="fold")

    # Add rows with color coding
    for issue in errors:
        table.add_row("[red]ERROR[/red]", str(issue))
    for issue in warnings:
        table.add_row("[yellow]WARN[/yellow]", str(issue))
    for issue in infos:
        table.add_row("[blue]INFO[/blue]", str(issue))

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
