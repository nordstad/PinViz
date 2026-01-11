"""Shell completion commands for pinviz CLI."""

import os
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def detect_shell() -> str | None:
    """
    Detect the current shell from environment.

    Returns:
        Shell name (bash, zsh, fish) or None if not detected
    """
    shell_path = os.environ.get("SHELL", "")
    if "bash" in shell_path:
        return "bash"
    elif "zsh" in shell_path:
        return "zsh"
    elif "fish" in shell_path:
        return "fish"
    return None


def get_completion_script(shell: str) -> str:
    """
    Get the completion script for the given shell.

    Args:
        shell: Shell name (bash, zsh, fish)

    Returns:
        Completion script content
    """
    try:
        # Use subprocess to get completion script from Typer
        result = subprocess.run(
            [sys.executable, "-c", f"import typer; print(typer.get_completion('{shell}'))"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""


def completion_install_command(
    shell: str | None = typer.Option(
        None,
        "--shell",
        "-s",
        help="Shell to install completion for (bash, zsh, fish). Auto-detected if not specified.",
    ),
) -> None:
    """
    Install shell completion for pinviz.

    Adds completion script to your shell's configuration file.
    Supported shells: bash, zsh, fish.

    Example:
        pinviz completion install
        pinviz completion install --shell bash
    """
    # Detect shell if not specified
    if shell is None:
        shell = detect_shell()
        if shell is None:
            console.print("[red]Error:[/red] Could not detect shell")
            console.print("[dim]Specify shell manually with --shell (bash, zsh, or fish)[/dim]")
            raise typer.Exit(1)
        console.print(f"[dim]Detected shell: {shell}[/dim]")

    # Validate shell
    if shell not in ("bash", "zsh", "fish"):
        console.print(f"[red]Error:[/red] Unsupported shell: {shell}")
        console.print("[dim]Supported shells: bash, zsh, fish[/dim]")
        raise typer.Exit(1)

    console.print()
    console.print(f"[cyan]Installing completion for {shell}...[/cyan]")

    # Determine config file
    home = Path.home()
    if shell == "bash":
        config_file = home / ".bashrc"
        completion_line = 'eval "$(pinviz --show-completion bash)"'
    elif shell == "zsh":
        config_file = home / ".zshrc"
        completion_line = 'eval "$(pinviz --show-completion zsh)"'
    elif shell == "fish":
        config_dir = home / ".config" / "fish" / "completions"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "pinviz.fish"
        # For fish, we need to generate and save the completion script
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pinviz", "--show-completion", "fish"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                config_file.write_text(result.stdout, encoding="utf-8")
                console.print(
                    f"[green]✓[/green] Completion installed to: [cyan]{config_file}[/cyan]"
                )
                console.print(
                    "[dim]Restart your shell or run: source ~/.config/fish/config.fish[/dim]"
                )
                console.print()
                return
            else:
                console.print("[red]Error:[/red] Failed to generate fish completion script")
                raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None
        return

    # Check if already installed
    if config_file.exists():
        content = config_file.read_text(encoding="utf-8")
        if completion_line in content:
            console.print(f"[yellow]⚠[/yellow]  Completion already installed in {config_file}")
            console.print()
            return

    # Add completion line to config file
    try:
        with open(config_file, "a", encoding="utf-8") as f:
            f.write(f"\n# pinviz completion\n{completion_line}\n")

        console.print(f"[green]✓[/green] Completion installed to: [cyan]{config_file}[/cyan]")
        console.print(f"[dim]Restart your shell or run: source {config_file}[/dim]")
        console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to install completion: {e}")
        raise typer.Exit(1) from None


def completion_show_command(
    shell: str | None = typer.Option(
        None,
        "--shell",
        "-s",
        help="Shell to show completion for (bash, zsh, fish). Auto-detected if not specified.",
    ),
) -> None:
    """
    Display the completion script for your shell.

    Shows the completion script that would be installed.
    Useful for manual installation or debugging.

    Example:
        pinviz completion show
        pinviz completion show --shell bash
    """
    # Detect shell if not specified
    if shell is None:
        shell = detect_shell()
        if shell is None:
            console.print("[red]Error:[/red] Could not detect shell")
            console.print("[dim]Specify shell manually with --shell (bash, zsh, or fish)[/dim]")
            raise typer.Exit(1)

    # Validate shell
    if shell not in ("bash", "zsh", "fish"):
        console.print(f"[red]Error:[/red] Unsupported shell: {shell}")
        console.print("[dim]Supported shells: bash, zsh, fish[/dim]")
        raise typer.Exit(1)

    console.print()

    # Show completion script
    if shell in ("bash", "zsh"):
        script = f'eval "$(pinviz --show-completion {shell})"'
        console.print(
            Panel(
                Syntax(script, "bash", theme="monokai"),
                title=f"Completion Script for {shell}",
                border_style="cyan",
            )
        )
        console.print()
        console.print("[dim]Add this line to your shell config file:[/dim]")
        if shell == "bash":
            console.print(f"[cyan]  echo '{script}' >> ~/.bashrc[/cyan]")
        else:
            console.print(f"[cyan]  echo '{script}' >> ~/.zshrc[/cyan]")
    elif shell == "fish":
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pinviz", "--show-completion", "fish"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                console.print(
                    Panel(
                        Syntax(result.stdout, "fish", theme="monokai", line_numbers=True),
                        title="Completion Script for fish",
                        border_style="cyan",
                    )
                )
                console.print()
                console.print("[dim]Save this to: ~/.config/fish/completions/pinviz.fish[/dim]")
            else:
                console.print("[red]Error:[/red] Failed to generate fish completion script")
                raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from None

    console.print()


def completion_uninstall_command(
    shell: str | None = typer.Option(
        None,
        "--shell",
        "-s",
        help="Shell to uninstall completion from. Auto-detected if not specified.",
    ),
) -> None:
    """
    Uninstall shell completion for pinviz.

    Removes completion script from your shell's configuration file.

    Example:
        pinviz completion uninstall
        pinviz completion uninstall --shell bash
    """
    # Detect shell if not specified
    if shell is None:
        shell = detect_shell()
        if shell is None:
            console.print("[red]Error:[/red] Could not detect shell")
            console.print("[dim]Specify shell manually with --shell[/dim]")
            raise typer.Exit(1)

    # Validate shell
    if shell not in ("bash", "zsh", "fish"):
        console.print(f"[red]Error:[/red] Unsupported shell: {shell}")
        raise typer.Exit(1)

    console.print(f"[cyan]Uninstalling completion for {shell}...[/cyan]")

    home = Path.home()
    if shell == "bash":
        config_file = home / ".bashrc"
        completion_line = 'eval "$(pinviz --show-completion bash)"'
    elif shell == "zsh":
        config_file = home / ".zshrc"
        completion_line = 'eval "$(pinviz --show-completion zsh)"'
    elif shell == "fish":
        config_file = home / ".config" / "fish" / "completions" / "pinviz.fish"
        if config_file.exists():
            config_file.unlink()
            console.print(f"[green]✓[/green] Removed: [cyan]{config_file}[/cyan]")
        else:
            console.print("[yellow]⚠[/yellow]  Completion not installed")
        console.print()
        return

    # Remove completion line from config file
    if not config_file.exists():
        console.print(f"[yellow]⚠[/yellow]  Config file not found: {config_file}")
        console.print()
        return

    content = config_file.read_text(encoding="utf-8")
    if completion_line not in content:
        console.print("[yellow]⚠[/yellow]  Completion not installed")
        console.print()
        return

    # Remove the line and surrounding comments
    lines = content.splitlines()
    new_lines = []
    skip_next = False

    for line in lines:
        if completion_line in line:
            skip_next = False
            # Remove previous line if it's the comment
            if new_lines and "# pinviz completion" in new_lines[-1]:
                new_lines.pop()
            continue
        if not skip_next:
            new_lines.append(line)

    config_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    console.print(f"[green]✓[/green] Completion uninstalled from: [cyan]{config_file}[/cyan]")
    console.print()
