"""Decorators and helpers for CLI commands.

This module provides utilities to reduce boilerplate in CLI command implementations,
particularly around error handling and output formatting.
"""

from collections.abc import Callable
from contextlib import contextmanager
from typing import TypeVar

import structlog
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .output import output_json, print_error

T = TypeVar("T")


def handle_command_exception(
    e: Exception,
    command_name: str,
    console: Console,
    logger: structlog.stdlib.BoundLogger,
    json_output: bool = False,
    json_error_factory: Callable[[str], object] | None = None,
) -> None:
    """Handle exceptions in CLI commands consistently.

    This function centralizes the error handling logic that's common across
    all CLI commands. It logs the exception, outputs the error message,
    and exits with code 1.

    Args:
        e: The exception that was raised
        command_name: Name of the command (for logging)
        console: Rich console for output
        logger: Structured logger instance
        json_output: Whether to output JSON format
        json_error_factory: Optional function to create JSON error object.
                           Should accept error message string and return a
                           Pydantic model or dict.

    Example:
        >>> try:
        ...     # Command logic
        ...     pass
        ... except typer.Exit:
        ...     raise
        ... except Exception as e:
        ...     handle_command_exception(
        ...         e, "render", ctx.console, ctx.logger, json_output,
        ...         lambda msg: RenderOutputJson(status="error", errors=[msg])
        ...     )
    """
    logger.exception(
        f"{command_name}_error",
        error_type=type(e).__name__,
        error_message=str(e),
    )

    if json_output and json_error_factory:
        error_obj = json_error_factory(str(e))
        output_json(error_obj, console)
    else:
        print_error(str(e), console)

    raise typer.Exit(code=1) from None


@contextmanager
def progress_indicator(console: Console, description: str, *, transient: bool = True):
    """Context manager for displaying progress indicators.

    Provides a simple, consistent way to show progress spinners during
    long-running operations. The progress indicator can be stopped and
    restarted as needed within the context.

    Args:
        console: Rich console for output
        description: Initial description text for the progress indicator
        transient: If True, the progress indicator disappears when done (default: True)

    Yields:
        Progress: Rich Progress instance that can be used to update tasks

    Example:
        >>> with progress_indicator(console, "Loading configuration...") as progress:
        ...     task = progress.add_task("Loading...", total=None)
        ...     # Do work
        ...     progress.update(task, completed=True)
        ...
        ...     # Can add more tasks
        ...     task2 = progress.add_task("Validating...", total=None)
        ...     # Do more work
        ...     progress.update(task2, completed=True)
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=transient,
    ) as progress:
        yield progress
