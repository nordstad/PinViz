"""Render command implementation."""

import typer

from ...config_loader import load_diagram
from ...render_svg import SVGRenderer
from ...theme import Theme
from ...validation import DiagramValidator, ValidationLevel
from ..context import AppContext
from ..decorators import handle_command_exception, progress_indicator
from ..output import (
    RenderOutputJson,
    get_validation_summary,
    output_json,
    print_error,
    print_success,
    print_validation_issues,
    print_warning,
)
from ..types import (
    ConfigFileArg,
    JsonOption,
    NoBoardNameOption,
    NoTitleOption,
    OutputOption,
    ShowLegendOption,
)


def render_command(
    config_file: ConfigFileArg,
    output: OutputOption = None,
    no_title: NoTitleOption = False,
    no_board_name: NoBoardNameOption = False,
    show_legend: ShowLegendOption = False,
    theme: str = typer.Option(None, help="Theme: light or dark (overrides config)"),
    json_output: JsonOption = False,
) -> None:
    """
    Render a diagram from a configuration file.

    [bold]Examples:[/bold]

      pinviz render diagram.yaml

      pinviz render diagram.yaml -o out/wiring.svg --show-legend

      pinviz render diagram.yaml --no-title --theme dark --json
    """
    ctx = AppContext()
    log = ctx.logger

    # Determine output path
    output_path = output or config_file.with_suffix(".svg")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with progress_indicator(ctx.console, "") as progress:
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

            # Apply theme if specified
            if theme:
                try:
                    diagram.theme = Theme(theme.lower())
                except ValueError as e:
                    print_error(f"Invalid theme '{theme}'. Must be 'light' or 'dark'.")
                    raise typer.Exit(1) from e

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
        handle_command_exception(
            e,
            "render",
            ctx.console,
            log,
            json_output,
            lambda msg: RenderOutputJson(
                status="error",
                output_path=None,
                validation=get_validation_summary([]),
                errors=[msg],
            ),
        )
