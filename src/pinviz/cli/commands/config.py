"""Config management commands for pinviz CLI."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from ..config import (
    create_default_config,
    get_config_file_path,
    load_config,
    load_toml_config,
)

console = Console()


def config_show_command() -> None:
    """
    Display current configuration values with their sources.

    Shows all configuration values and indicates where each value comes from
    (defaults, config file, or environment variables).

    Example:
        pinviz config show
    """
    config = load_config()
    toml_config = load_toml_config()
    config_path = get_config_file_path()

    # Create table for config display
    table = Table(title="Current Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="yellow", no_wrap=True)
    table.add_column("Value", style="green")
    table.add_column("Source", style="dim")

    # Check each setting and its source
    import os

    def get_source(key: str, toml_key: str) -> str:
        """Determine the source of a config value."""
        env_var = f"PINVIZ_{key.upper()}"
        if env_var in os.environ:
            return f"env ({env_var})"
        elif toml_key in toml_config:
            return "config file"
        return "default"

    table.add_row("log_level", config.log_level, get_source("log_level", "log_level"))
    table.add_row("log_format", config.log_format, get_source("log_format", "log_format"))
    table.add_row("output_dir", str(config.output_dir), get_source("output_dir", "output_dir"))

    console.print()
    console.print(table)
    console.print()
    console.print(f"[dim]Config file: {config_path}[/dim]")
    if not config_path.exists():
        console.print(
            "[yellow]Config file does not exist. Run 'pinviz config init' to create it.[/yellow]"
        )
    console.print()


def config_path_command() -> None:
    """
    Show the path to the configuration file.

    Displays the location of the config file (whether it exists or not).

    Example:
        pinviz config path
    """
    config_path = get_config_file_path()
    console.print()
    console.print(
        Panel(
            f"[cyan]{config_path}[/cyan]",
            title="Config File Location",
            border_style="blue",
        )
    )

    if config_path.exists():
        console.print("[green]✓[/green] Config file exists")
    else:
        console.print("[yellow]⚠[/yellow] Config file does not exist")
        console.print("[dim]Run 'pinviz config init' to create it[/dim]")
    console.print()


def config_init_command(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing config file",
    ),
) -> None:
    """
    Create a default configuration file.

    Creates a default config.toml file in the platform-specific config directory.
    Will not overwrite an existing file unless --force is specified.

    Example:
        pinviz config init
        pinviz config init --force  # Overwrite existing config
    """
    config_path = get_config_file_path()

    if config_path.exists() and not force:
        console.print()
        console.print(f"[yellow]Config file already exists:[/yellow] {config_path}")
        console.print("[dim]Use --force to overwrite[/dim]")
        console.print()
        raise typer.Exit(1)

    # Create config file
    if config_path.exists():
        # Backup existing file
        backup_path = config_path.with_suffix(".toml.backup")
        config_path.rename(backup_path)
        console.print(f"[dim]Backed up existing config to: {backup_path}[/dim]")

    config_path = create_default_config()

    console.print()
    console.print(f"[green]✓[/green] Created config file: [cyan]{config_path}[/cyan]")
    console.print()

    # Display the created config
    with open(config_path) as f:
        config_content = f.read()

    syntax = Syntax(config_content, "toml", theme="monokai", line_numbers=True)
    console.print(
        Panel(
            syntax,
            title="Config File Contents",
            border_style="green",
        )
    )
    console.print()
    console.print("[dim]Edit this file to customize your configuration[/dim]")
    console.print()


def config_edit_command() -> None:
    """
    Open the configuration file in your default editor.

    Uses the EDITOR environment variable to open the config file.
    Falls back to common editors (nano, vim, vi) if EDITOR is not set.

    Example:
        pinviz config edit
    """
    import os
    import shutil
    import subprocess

    config_path = get_config_file_path()

    # Create config if it doesn't exist
    if not config_path.exists():
        console.print("[yellow]Config file doesn't exist. Creating default config...[/yellow]")
        create_default_config()

    # Find an editor
    editor = os.environ.get("EDITOR")
    if not editor:
        # Try common editors
        for cmd in ["nano", "vim", "vi"]:
            if shutil.which(cmd):
                editor = cmd
                break

    if not editor:
        console.print("[red]Error:[/red] No editor found")
        console.print("[dim]Set the EDITOR environment variable or install nano/vim[/dim]")
        console.print(f"\nConfig file location: [cyan]{config_path}[/cyan]")
        raise typer.Exit(1)

    console.print(f"[dim]Opening {config_path} with {editor}...[/dim]")
    try:
        subprocess.run([editor, str(config_path)], check=True)
        console.print("[green]✓[/green] Config file saved")
    except subprocess.CalledProcessError:
        console.print("[red]Error:[/red] Editor exited with error")
        raise typer.Exit(1) from None
