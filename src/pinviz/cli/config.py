"""CLI configuration using pydantic-settings."""

import sys
import tomllib
from pathlib import Path
from typing import Any, Literal

from platformdirs import user_config_dir
from pydantic import Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


def get_config_file_path() -> Path:
    """Get the path to the config file.

    Returns:
        Path to config.toml file

    Example:
        >>> config_path = get_config_file_path()
        >>> print(config_path)
        /Users/username/.config/pinviz/config.toml
    """
    config_dir = Path(user_config_dir("pinviz", appauthor=False))
    return config_dir / "config.toml"


class TomlConfigSource(PydanticBaseSettingsSource):
    """Custom settings source for loading from TOML config file."""

    def get_field_value(self, _field: Any, field_name: str) -> tuple[Any, str, bool]:
        """Get field value from TOML config file."""
        # Load TOML config
        config_path = get_config_file_path()
        if not config_path.exists():
            return None, field_name, False

        try:
            with open(config_path, "rb") as f:
                toml_data = tomllib.load(f)
            if field_name in toml_data:
                return toml_data[field_name], field_name, False
        except Exception:
            pass

        return None, field_name, False

    def prepare_field_value(
        self, _field_name: str, _field: Any, value: Any, _value_is_complex: bool
    ) -> Any:
        """Prepare the field value (convert if needed)."""
        return value

    def __call__(self) -> dict[str, Any]:
        """Load all config from TOML file."""
        config_path = get_config_file_path()
        if not config_path.exists():
            return {}

        try:
            with open(config_path, "rb") as f:
                return tomllib.load(f)
        except Exception:
            return {}


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

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,  # noqa: ARG003
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Customize settings sources with proper precedence.

        Precedence (highest to lowest):
        1. init_settings (programmatic initialization, e.g., CLI args)
        2. env_settings (environment variables)
        3. toml_settings (config file)
        4. file_secret_settings
        5. Default values
        """
        return (
            init_settings,
            env_settings,
            TomlConfigSource(settings_cls),
            file_secret_settings,
        )


# Default TOML configuration template
DEFAULT_CONFIG_TEMPLATE = """# PinViz CLI Configuration
# This file is automatically created by `pinviz config init`
#
# Configuration precedence (highest to lowest):
# 1. CLI arguments (e.g., --log-level DEBUG)
# 2. Environment variables (e.g., PINVIZ_LOG_LEVEL=DEBUG)
# 3. This config file (~/.config/pinviz/config.toml)
# 4. Built-in defaults

# Logging verbosity: DEBUG, INFO, WARNING, ERROR
log_level = "WARNING"

# Log output format: console (human-readable) or json (machine-readable)
log_format = "console"

# Default output directory for generated diagrams
output_dir = "./out"
"""


def get_config_dir() -> Path:
    """Get the platform-specific config directory for pinviz.

    Returns:
        Path to config directory (e.g., ~/.config/pinviz on Linux/macOS,
        %APPDATA%/pinviz on Windows)

    Example:
        >>> config_dir = get_config_dir()
        >>> print(config_dir)
        /Users/username/.config/pinviz
    """
    return Path(user_config_dir("pinviz", appauthor=False))


def create_default_config() -> Path:
    """Create a default config file if it doesn't exist.

    Returns:
        Path to the created (or existing) config file

    Example:
        >>> config_path = create_default_config()
        >>> print(f"Config created at: {config_path}")
        Config created at: /Users/username/.config/pinviz/config.toml
    """
    config_path = get_config_file_path()
    config_dir = config_path.parent

    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create default config file if it doesn't exist
    if not config_path.exists():
        config_path.write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")

    return config_path


def load_toml_config() -> dict:
    """Load configuration from TOML file if it exists.

    Returns:
        Dictionary of config values from TOML file, or empty dict if file doesn't exist

    Example:
        >>> config_dict = load_toml_config()
        >>> print(config_dict.get('log_level', 'WARNING'))
        WARNING
    """
    config_path = get_config_file_path()

    if not config_path.exists():
        return {}

    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        # Print warning but don't fail - just return empty dict
        print(f"Warning: Failed to load config from {config_path}: {e}", file=sys.stderr)
        return {}


def load_config() -> CliConfig:
    """Load CLI configuration with proper precedence.

    Configuration precedence (highest to lowest):
    1. CLI arguments (handled by Typer, not here)
    2. Environment variables (PINVIZ_* prefix)
    3. Config file (~/.config/pinviz/config.toml)
    4. Defaults (defined in CliConfig)

    The precedence is handled automatically by pydantic-settings using
    the custom TomlConfigSource settings source.

    Returns:
        Configured CliConfig instance with values from all sources

    Example:
        >>> config = load_config()
        >>> print(f"Log level: {config.log_level}")
        Log level: WARNING
    """
    return CliConfig()
