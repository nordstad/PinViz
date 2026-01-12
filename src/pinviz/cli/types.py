"""Common type aliases for CLI commands.

This module provides reusable type annotations for common CLI options,
reducing boilerplate and ensuring consistency across commands.
"""

from pathlib import Path
from typing import Annotated

import typer

# Input/Output file types
ConfigFileArg = Annotated[
    Path,
    typer.Argument(
        help="Path to YAML or JSON configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
]

OutputOption = Annotated[
    Path | None,
    typer.Option(
        "--output",
        "-o",
        help="Output SVG file path",
    ),
]

# Boolean flag options
JsonOption = Annotated[
    bool,
    typer.Option(
        "--json",
        help="Output machine-readable JSON status",
    ),
]

StrictOption = Annotated[
    bool,
    typer.Option(
        "--strict",
        help="Treat warnings as errors (exit with error code if warnings found)",
    ),
]

NoTitleOption = Annotated[
    bool,
    typer.Option(
        "--no-title",
        help="Hide the diagram title in the SVG output",
    ),
]

NoBoardNameOption = Annotated[
    bool,
    typer.Option(
        "--no-board-name",
        help="Hide the board name in the SVG output",
    ),
]

ShowLegendOption = Annotated[
    bool,
    typer.Option(
        "--show-legend",
        help="Show device specifications table below the diagram",
    ),
]

ForceOption = Annotated[
    bool,
    typer.Option(
        "--force",
        "-f",
        help="Force operation (overwrite existing files)",
    ),
]

# Shell completion options
ShellOption = Annotated[
    str | None,
    typer.Option(
        "--shell",
        "-s",
        help="Shell to use (bash, zsh, fish). Auto-detected if not specified.",
    ),
]
