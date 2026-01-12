"""Modern CLI for pinviz using Typer + Rich."""

import sys
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.traceback import install as install_rich_traceback

from ..logging_config import configure_logging

# Install rich tracebacks for better error messages
install_rich_traceback(show_locals=False)

# Create Typer app
app = typer.Typer(
    name="pinviz",
    help="Generate Raspberry Pi GPIO connection diagrams",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=True,
    pretty_exceptions_enable=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        from importlib.metadata import version as get_version

        try:
            __version__ = get_version("pinviz")
        except Exception:
            __version__ = "unknown"
        rprint(f"pinviz version {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = None,
    log_level: Annotated[
        str,
        typer.Option(
            "--log-level",
            "-l",
            help="Set logging verbosity",
            case_sensitive=False,
        ),
    ] = "WARNING",
    log_format: Annotated[
        str,
        typer.Option(
            "--log-format",
            help="Log output format: json (machine-readable) or console (human-readable)",
            case_sensitive=False,
        ),
    ] = "console",
) -> None:
    """
    Generate Raspberry Pi GPIO connection diagrams.

    [bold]Examples:[/bold]

      pinviz render diagram.yaml
      pinviz render diagram.yaml -o out/wiring.svg --show-legend
      pinviz example bh1750
      pinviz validate diagram.yaml --strict
      pinviz list

    For more information, visit: [link]https://github.com/nordstad/PinViz[/link]
    """
    # Configure logging globally
    configure_logging(level=log_level.upper(), format=log_format)


# Register commands (import after app callback is defined)
from .commands import completion as completion_cmd  # noqa: E402
from .commands import config as config_cmd  # noqa: E402
from .commands import device, example, render, validate  # noqa: E402
from .commands import list as list_cmd  # noqa: E402

app.command(name="render")(render.render_command)
app.command(name="validate")(validate.validate_command)
app.command(name="validate-devices")(validate.validate_devices_command)
app.command(name="example")(example.example_command)
app.command(name="list")(list_cmd.list_command)
app.command(name="add-device")(device.add_device_command)

# Config command group
config_app = typer.Typer(
    name="config",
    help="Manage configuration settings",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
config_app.command(name="show")(config_cmd.config_show_command)
config_app.command(name="path")(config_cmd.config_path_command)
config_app.command(name="init")(config_cmd.config_init_command)
config_app.command(name="edit")(config_cmd.config_edit_command)
app.add_typer(config_app, name="config")

# Completion command group
completion_app = typer.Typer(
    name="completion",
    help="Manage shell completion",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)
completion_app.command(name="install")(completion_cmd.completion_install_command)
completion_app.command(name="show")(completion_cmd.completion_show_command)
completion_app.command(name="uninstall")(completion_cmd.completion_uninstall_command)
app.add_typer(completion_app, name="completion")


def main() -> int:
    """Entry point for CLI (called from pyproject.toml).

    Returns:
        Exit code: 0 for success, non-zero for errors
    """
    try:
        app()
        return 0
    except typer.Exit as e:
        return e.exit_code if e.exit_code is not None else 0
    except KeyboardInterrupt:
        Console().print("\n[yellow]Cancelled by user[/yellow]")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        Console().print(f"[red]Error:[/red] {e}", style="bold")
        if "--debug" in sys.argv or "-d" in sys.argv:
            raise
        return 1


if __name__ == "__main__":
    sys.exit(main())
