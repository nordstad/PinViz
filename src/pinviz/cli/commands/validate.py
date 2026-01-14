"""Validate command implementation."""

import typer

from ...config_loader import load_diagram
from ...device_validator import validate_devices
from ...validation import DiagramValidator, ValidationLevel
from ..context import AppContext
from ..decorators import handle_command_exception
from ..output import (
    ValidateDevicesOutputJson,
    ValidateOutputJson,
    get_validation_summary,
    output_json,
    print_error,
    print_success,
    print_warning,
)
from ..types import ConfigFileArg, JsonOption, StrictOption
from ..validation_output import ValidationResult


def validate_command(
    config_file: ConfigFileArg,
    strict: StrictOption = False,
    json_output: JsonOption = False,
) -> None:
    """
    Validate a diagram configuration.

    Check for wiring mistakes, pin conflicts, and compatibility issues.

    [bold]Examples:[/bold]

      pinviz validate diagram.yaml

      pinviz validate diagram.yaml --strict
    """
    ctx = AppContext()
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

        # Log validation results
        if not issues:
            log.info("validation_passed", config_path=str(config_file))
        else:
            errors = [i for i in issues if i.level == ValidationLevel.ERROR]
            warnings = [i for i in issues if i.level == ValidationLevel.WARNING]
            log.info(
                "validation_issues_found",
                total_issues=len(issues),
                errors=len(errors),
                warnings=len(warnings),
            )

        # Use ValidationResult for output and exit handling
        result = ValidationResult(issues=issues, strict=strict, config_path=str(config_file))

        if json_output:
            result.output_json(ctx.console)
        else:
            result.output_console(ctx.console)

        if result.exit_code != 0:
            if result.errors:
                log.error("validation_failed", error_count=len(result.errors))
            elif result.warnings and strict:
                log.warning("strict_mode_warnings_as_errors", warning_count=len(result.warnings))
            raise typer.Exit(code=result.exit_code)

        if result.warnings:
            log.info("validation_completed_with_warnings", warning_count=len(result.warnings))

    except typer.Exit:
        raise
    except Exception as e:
        handle_command_exception(
            e,
            "validation",
            ctx.console,
            log,
            json_output,
            lambda msg: ValidateOutputJson(
                status="error",
                validation=get_validation_summary([]),
                issues=None,
                errors=[msg],
            ),
        )


def validate_devices_command(
    strict: StrictOption = False,
    json_output: JsonOption = False,
) -> None:
    """
    Validate all device configuration files.

    Check all device JSON files for errors and common issues.

    [bold]Examples:[/bold]

      pinviz validate-devices

      pinviz validate-devices --strict
    """
    ctx = AppContext()
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
        handle_command_exception(
            e,
            "device_validation",
            ctx.console,
            log,
            json_output,
            lambda msg: ValidateDevicesOutputJson(
                status="error",
                total_files=0,
                valid_files=0,
                error_count=1,
                warning_count=0,
                errors=[msg],
            ),
        )
