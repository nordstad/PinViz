"""Validate command implementation."""

from pathlib import Path
from typing import Annotated

import typer

from ...config_loader import load_diagram
from ...device_validator import validate_devices
from ...validation import DiagramValidator, ValidationLevel
from ..config import load_config
from ..context import AppContext
from ..output import (
    ValidateDevicesOutputJson,
    ValidateOutputJson,
    format_validation_issues_json,
    get_validation_summary,
    output_json,
    print_error,
    print_success,
    print_validation_issues,
    print_warning,
)


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
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output machine-readable JSON status",
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

        if not json_output:
            ctx.console.print(f"Validating configuration: [cyan]{config_file}[/cyan]")

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

            if json_output:
                result = ValidateOutputJson(
                    status="success",
                    validation=get_validation_summary([]),
                    issues=None,
                )
                output_json(result, ctx.console)
            else:
                ctx.console.print()
                print_success("Validation passed! No issues found.", ctx.console)
                print_success("Current limits OK", ctx.console)
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

        error_count = len(errors)
        warning_count = len(warnings)

        # Output results
        if json_output:
            status = "error" if errors else ("warning" if warnings else "success")
            result = ValidateOutputJson(
                status=status,
                validation=get_validation_summary(issues),
                issues=format_validation_issues_json(issues),
            )
            output_json(result, ctx.console)
        else:
            # Display all issues
            print_validation_issues(issues, ctx.console)

            # Summary
            ctx.console.print()
            if error_count > 0 or warning_count > 0:
                ctx.console.print(
                    f"Found [red]{error_count}[/red] error(s), "
                    f"[yellow]{warning_count}[/yellow] warning(s)"
                )

        # Return appropriate exit code
        if errors:
            log.error("validation_failed", error_count=error_count)
            raise typer.Exit(code=1)

        if warnings and strict:
            log.warning("strict_mode_warnings_as_errors", warning_count=warning_count)
            if not json_output:
                print_error("Treating warnings as errors (--strict mode)", ctx.console)
            raise typer.Exit(code=1)

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

        if json_output:
            result = ValidateOutputJson(
                status="error",
                validation=get_validation_summary([]),
                issues=None,
                errors=[str(e)],
            )
            output_json(result, ctx.console)
        else:
            print_error(str(e), ctx.console)

        raise typer.Exit(code=1) from None


def validate_devices_command(
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            help="Treat warnings as errors (exit with error code if warnings found)",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output machine-readable JSON status",
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

    if not json_output:
        ctx.console.print("Validating device configurations...")
        ctx.console.print()

    try:
        result = validate_devices()

        log.debug(
            "validation_completed",
            total_files=result.total_files,
            valid_files=result.valid_files,
            errors=result.error_count,
            warnings=result.warning_count,
        )

        # Output results
        if json_output:
            status = (
                "error" if result.has_errors else ("warning" if result.has_warnings else "success")
            )
            json_result = ValidateDevicesOutputJson(
                status=status,
                total_files=result.total_files,
                valid_files=result.valid_files,
                error_count=result.error_count,
                warning_count=result.warning_count,
                errors=[str(e) for e in result.errors] if result.errors else None,
                warnings=[str(w) for w in result.warnings] if result.warnings else None,
            )
            output_json(json_result, ctx.console)
        else:
            # Display errors
            if result.errors:
                ctx.console.print("[bold red]Errors:[/bold red]")
                for error in result.errors:
                    ctx.console.print(f"  [red]•[/red] {error}")
                ctx.console.print()

            # Display warnings
            if result.warnings:
                ctx.console.print("[bold yellow]Warnings:[/bold yellow]")
                for warning in result.warnings:
                    ctx.console.print(f"  [yellow]•[/yellow] {warning}")
                ctx.console.print()

            # Summary
            ctx.console.print(
                f"Scanned [cyan]{result.total_files}[/cyan] device configuration files"
            )
            ctx.console.print(f"Valid: [green]{result.valid_files}[/green]")

            if result.error_count > 0:
                ctx.console.print(f"Errors: [red]{result.error_count}[/red]")
            if result.warning_count > 0:
                ctx.console.print(f"Warnings: [yellow]{result.warning_count}[/yellow]")

            ctx.console.print()

        # Exit codes
        if result.has_errors:
            log.error("validation_failed", error_count=result.error_count)
            if not json_output:
                print_error("Validation failed with errors", ctx.console)
            raise typer.Exit(code=1)

        if result.has_warnings and strict:
            log.warning("strict_mode_warnings_as_errors", warning_count=result.warning_count)
            if not json_output:
                print_error("Validation failed: warnings in strict mode", ctx.console)
            raise typer.Exit(code=1)

        if result.has_warnings:
            log.info("validation_completed_with_warnings", warning_count=result.warning_count)
            if not json_output:
                print_warning("Validation completed with warnings", ctx.console)
            return

        log.info("validation_passed")
        if not json_output:
            print_success("All device configurations are valid!", ctx.console)

    except typer.Exit:
        raise
    except Exception as e:
        log.exception(
            "validation_error",
            error_type=type(e).__name__,
            error_message=str(e),
        )

        if json_output:
            json_result = ValidateDevicesOutputJson(
                status="error",
                total_files=0,
                valid_files=0,
                error_count=1,
                warning_count=0,
                errors=[str(e)],
            )
            output_json(json_result, ctx.console)
        else:
            print_error(f"Error during validation: {e}", ctx.console)

        raise typer.Exit(code=1) from None
