"""Render command implementation."""

from pathlib import Path
from typing import Annotated

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...config_loader import load_diagram
from ...render_svg import SVGRenderer
from ...validation import DiagramValidator, ValidationLevel
from ..config import load_config
from ..context import AppContext
from ..output import (
    RenderOutputJson,
    get_validation_summary,
    output_json,
    print_error,
    print_success,
    print_validation_issues,
    print_warning,
)


def render_command(
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
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output SVG file path (default: <config>.svg)",
        ),
    ] = None,
    no_title: Annotated[
        bool,
        typer.Option(
            "--no-title",
            help="Hide the diagram title in the SVG output",
        ),
    ] = False,
    no_board_name: Annotated[
        bool,
        typer.Option(
            "--no-board-name",
            help="Hide the board name in the SVG output",
        ),
    ] = False,
    show_legend: Annotated[
        bool,
        typer.Option(
            "--show-legend",
            help="Show device specifications table below the diagram",
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
    Render a diagram from a configuration file.

    [bold]Examples:[/bold]

      pinviz render diagram.yaml

      pinviz render diagram.yaml -o out/wiring.svg --show-legend

      pinviz render diagram.yaml --no-title --json
    """
    ctx = AppContext(config=load_config())
    log = ctx.logger

    # Determine output path
    output_path = output or config_file.with_suffix(".svg")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=ctx.console,
            transient=True,
        ) as progress:
            # Load config
            task = progress.add_task("Loading configuration...", total=None)
            diagram = load_diagram(config_file)
            progress.update(task, completed=True)

            log.debug(
                "config_loaded",
                device_count=len(diagram.devices),
                connection_count=len(diagram.connections),
            )

            # Apply visibility flags
            if no_title:
                diagram.show_title = False
            if no_board_name:
                diagram.show_board_name = False
            if show_legend:
                diagram.show_legend = True

            # Validate
            task = progress.add_task("Validating diagram...", total=None)
            validator = DiagramValidator()
            issues = validator.validate(diagram)
            progress.update(task, completed=True)

            if issues:
                errors = [i for i in issues if i.level == ValidationLevel.ERROR]
                warnings = [i for i in issues if i.level == ValidationLevel.WARNING]

                if errors:
                    print_validation_issues(issues, ctx.console)
                    print_error(
                        f"Found {len(errors)} error(s). Cannot generate diagram.",
                        ctx.console,
                    )
                    raise typer.Exit(code=1)

                # Show warnings but continue
                if warnings:
                    print_validation_issues(issues, ctx.console)
                    print_warning(
                        f"Found {len(warnings)} warning(s). Review carefully.", ctx.console
                    )
                    ctx.console.print()

            # Render
            task = progress.add_task("Rendering SVG...", total=None)
            renderer = SVGRenderer()
            renderer.render(diagram, output_path)
            progress.update(task, completed=True)

        if not json_output:
            print_success(f"Diagram generated: {output_path}", ctx.console)
        else:
            result = RenderOutputJson(
                status="success",
                output_path=str(output_path),
                validation=get_validation_summary(issues),
            )
            output_json(result, ctx.console)

        log.info("diagram_generated", output_path=str(output_path))

    except typer.Exit:
        # Re-raise Typer exits (for error codes)
        raise
    except Exception as e:
        log.exception("render_failed", config_path=str(config_file), error=str(e))

        if json_output:
            result = RenderOutputJson(
                status="error",
                output_path=None,
                validation=get_validation_summary([]),
                errors=[str(e)],
            )
            output_json(result, ctx.console)
        else:
            print_error(str(e), ctx.console)

        raise typer.Exit(code=1) from None
