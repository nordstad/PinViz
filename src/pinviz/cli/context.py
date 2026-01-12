"""Application context for CLI commands."""

from dataclasses import dataclass, field

import structlog
from rich.console import Console

from ..devices import DeviceRegistry, get_registry
from .config import CliConfig, load_config


@dataclass
class AppContext:
    """Shared application context for CLI commands.

    Provides centralized access to configuration, logging, console output,
    and device registry for all CLI commands. This enables dependency injection
    and consistent behavior across the CLI.

    Attributes:
        config: CLI configuration loaded from environment/files
        console: Rich console for formatted output
        logger: Structured logger instance
        registry: Device registry for template access

    Example:
        >>> from pinviz.cli.config import load_config
        >>> ctx = AppContext(config=load_config())
        >>> ctx.logger.info("command_started", command="render")
        >>> ctx.console.print("[green]Success![/green]")
    """

    config: CliConfig
    console: Console = field(default_factory=Console)
    logger: structlog.stdlib.BoundLogger = field(init=False)
    registry: DeviceRegistry = field(default_factory=get_registry)

    def __post_init__(self):
        """Initialize logger after dataclass construction."""
        self.logger = structlog.get_logger(__name__)


def get_app_context() -> AppContext:
    """Factory function for creating AppContext instances.

    Creates and returns a new AppContext instance with loaded configuration.
    This is called as a default factory for commands to reduce boilerplate.

    Returns:
        AppContext: Configured application context

    Example:
        >>> def my_command(
        ...     ctx: AppContextDep = None,
        ... ) -> None:
        ...     # ctx is automatically created via get_app_context()
        ...     ctx.logger.info("command_started")
    """
    return AppContext(config=load_config())


# For now, we'll just use manual context creation in commands
# Future enhancement: could explore custom Typer callback for DI
# AppContextDep is kept as a type alias for consistency
AppContextDep = AppContext
