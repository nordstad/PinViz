"""Validate command implementation."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from ...config_loader import load_diagram
from ...device_validator import validate_devices
from ...validation import DiagramValidator, ValidationLevel
from ..config import load_config
from ..context import AppContext
from ..output import print_error, print_success, print_validation_issues, print_warning

console = Console()


def validate_command(
    config_file: Annotated[
        Path,
        typer.Argument(
            help="Path to YAML or JSON configuration file",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Treat warnings as errors (exit with error code if warnings found)",
        ),
    ] = False,
) -> None:
    """
    Validate a diagram configuration.

    Check for wiring mistakes, pin conflicts, and compatibility issues.

    [bold]Examples:[/bold]

      pinviz validate diagram.yaml

      pinviz validate diagram.yaml --strict
    """
    ctx = AppContext(config=load_config())
    log = ctx.logger

    try:
        log.info("validation_started", config_path=str(config_file), strict_mode=strict)
        console.print(f"Validating configuration: [cyan]{config_file}[/cyan]")

        diagram = load_diagram(config_file)

        log.debug(
            "config_loaded",
            device_count=len(diagram.devices),
            connection_count=len(diagram.connections),
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        if not issues:
            log.info("validation_passed", config_path=str(config_file))
            console.print()
            print_success("Validation passed! No issues found.", console)
            print_success("Current limits OK", console)
            return

        # Categorize issues
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        warnings = [i for i in issues if i.level == ValidationLevel.WARNING]

        log.info(
            "validation_issues_found",
            total_issues=len(issues),
            errors=len(errors),
            warnings=len(warnings),
        )

        # Display all issues
        print_validation_issues(issues, console)

        # Summary
        console.print()
        error_count = len(errors)
        warning_count = len(warnings)

        if error_count > 0 or warning_count > 0:
            console.print(
                f"Found [red]{error_count}[/red] error(s), "
                f"[yellow]{warning_count}[/yellow] warning(s)"
            )

        # Return appropriate exit code
        if errors:
            log.error("validation_failed", error_count=error_count)
            raise typer.Exit(code=1)  # noqa: B904  # noqa: B904

        if warnings and strict:
            log.warning("strict_mode_warnings_as_errors", warning_count=warning_count)
            print_error("Treating warnings as errors (--strict mode)", console)
            raise typer.Exit(code=1)  # noqa: B904  # noqa: B904

        log.info("validation_completed_with_warnings", warning_count=warning_count)

    except typer.Exit:
        raise
    except Exception as e:
        log.exception(
            "validation_error",
            config_path=str(config_file),
            error_type=type(e).__name__,
            error_message=str(e),
        )
        print_error(str(e), console)
        raise typer.Exit(code=1)  # noqa: B904


def validate_devices_command(
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Treat warnings as errors (exit with error code if warnings found)",
        ),
    ] = False,
) -> None:
    """
    Validate all device configuration files.

    Check all device JSON files for errors and common issues.

    [bold]Examples:[/bold]

      pinviz validate-devices

      pinviz validate-devices --strict
    """
    ctx = AppContext(config=load_config())
    log = ctx.logger

    log.info("device_validation_started", strict_mode=strict)
    console.print("Validating device configurations...")
    console.print()

    try:
        result = validate_devices()

        log.debug(
            "validation_completed",
            total_files=result.total_files,
            valid_files=result.valid_files,
            errors=result.error_count,
            warnings=result.warning_count,
        )

        # Display errors
        if result.errors:
            console.print("[bold red]Errors:[/bold red]")
            for error in result.errors:
                console.print(f"  [red]•[/red] {error}")
            console.print()

        # Display warnings
        if result.warnings:
            console.print("[bold yellow]Warnings:[/bold yellow]")
            for warning in result.warnings:
                console.print(f"  [yellow]•[/yellow] {warning}")
            console.print()

        # Summary
        console.print(f"Scanned [cyan]{result.total_files}[/cyan] device configuration files")
        console.print(f"Valid: [green]{result.valid_files}[/green]")

        if result.error_count > 0:
            console.print(f"Errors: [red]{result.error_count}[/red]")
        if result.warning_count > 0:
            console.print(f"Warnings: [yellow]{result.warning_count}[/yellow]")

        console.print()

        # Exit codes
        if result.has_errors:
            log.error("validation_failed", error_count=result.error_count)
            print_error("Validation failed with errors", console)
            raise typer.Exit(code=1)  # noqa: B904  # noqa: B904

        if result.has_warnings and strict:
            log.warning("strict_mode_warnings_as_errors", warning_count=result.warning_count)
            print_error("Validation failed: warnings in strict mode", console)
            raise typer.Exit(code=1)  # noqa: B904  # noqa: B904

        if result.has_warnings:
            log.info("validation_completed_with_warnings", warning_count=result.warning_count)
            print_warning("Validation completed with warnings", console)
            return

        log.info("validation_passed")
        print_success("All device configurations are valid!", console)

    except typer.Exit:
        raise
    except Exception as e:
        log.exception(
            "validation_error",
            error_type=type(e).__name__,
            error_message=str(e),
        )
        print_error(f"Error during validation: {e}", console)
        raise typer.Exit(code=1)  # noqa: B904
