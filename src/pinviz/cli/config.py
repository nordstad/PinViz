"""CLI configuration using pydantic-settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CliConfig(BaseSettings):
    """CLI configuration with environment variable support.

    Configuration precedence (highest to lowest):
    1. CLI arguments (handled by Typer)
    2. Environment variables (PINVIZ_* prefix)
    3. Config file (~/.config/pinviz/config.toml) - Phase 2
    4. Defaults (defined below)

    Example:
        >>> config = CliConfig()
        >>> config.log_level
        'WARNING'

        # Override with environment variable
        >>> import os
        >>> os.environ['PINVIZ_LOG_LEVEL'] = 'DEBUG'
        >>> config = CliConfig()
        >>> config.log_level
        'DEBUG'
    """

    model_config = SettingsConfigDict(
        env_prefix="PINVIZ_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="WARNING",
        description="Logging verbosity level",
    )

    log_format: Literal["json", "console"] = Field(
        default="console",
        description="Log output format: json (machine-readable) or console (human-readable)",
    )

    output_dir: Path = Field(
        default=Path("./out"),
        description="Default output directory for generated diagrams",
    )


def load_config() -> CliConfig:
    """Load CLI configuration from environment variables.

    Returns:
        Configured CliConfig instance with values from environment

    Example:
        >>> config = load_config()
        >>> print(f"Log level: {config.log_level}")
        Log level: WARNING
    """
    return CliConfig()
