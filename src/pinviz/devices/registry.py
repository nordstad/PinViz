"""Device registry for managing device templates loaded from JSON configurations.

This module provides a central registry for all device templates defined in JSON
configuration files. The registry automatically scans the device_configs/ directory
and provides methods to create device instances with metadata enrichment.

The registry system enables:
- Automatic device discovery from JSON configs
- Metadata caching for fast lookups
- Device creation with parameter substitution
- Category-based device filtering
- Datasheet URL and I2C address management

The module supports both a global default registry (for convenience) and
independent registries (for testing and isolation).

Example (default registry):
    >>> from pinviz.devices import get_registry
    >>> registry = get_registry()
    >>> sensor = registry.create('bh1750')
    >>> print(sensor.name)
    BH1750 Light Sensor
    >>> print(sensor.url)
    https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf

Example (isolated registry for testing):
    >>> from pinviz.devices import create_registry
    >>> test_registry = create_registry()
    >>> # Use test_registry independently without affecting global state
"""

import json
from dataclasses import dataclass
from typing import Any

from ..logging_config import get_logger
from ..model import Device

log = get_logger(__name__)


@dataclass
class DeviceTemplate:
    """Metadata for a device template."""

    type_id: str
    name: str
    description: str
    category: str
    url: str | None = None
    i2c_address: int | None = None  # Default I2C address (7-bit)


class DeviceRegistry:
    """Central registry for device templates loaded from JSON configurations."""

    def __init__(self):
        self._templates: dict[str, DeviceTemplate] = {}
        self._failed_configs: list[str] = []
        self._scan_device_configs()

    def _scan_device_configs(self) -> None:
        """
        Scan device_configs directory and populate registry metadata.

        This method recursively scans all subdirectories in device_configs/ for JSON
        files, extracts metadata (id, name, description, category, datasheet URL,
        I2C address), and caches them in the registry for fast lookups.

        Malformed JSON files are logged as warnings. If zero devices load, raises
        RuntimeError to fail fast rather than failing later with cryptic errors.
        """
        from .loader import _get_device_config_path

        # Try to find device_configs directory
        try:
            # Get a path to any config to find the directory
            test_path = _get_device_config_path("bh1750")
            configs_dir = test_path.parent.parent
        except FileNotFoundError:
            # Can't find configs, skip scanning
            return

        # Track failed configs for fail-fast validation
        total_files = 0

        # Scan all JSON files in all subdirectories
        for json_file in configs_dir.rglob("*.json"):
            total_files += 1
            try:
                with open(json_file) as f:
                    config = json.load(f)

                # Extract metadata from JSON config
                type_id = config.get("id", json_file.stem)
                name = config.get("name", type_id)
                description = config.get("description", "")
                category = config.get("category", "generic")
                url = config.get("datasheet_url")

                # Parse I2C address if present
                i2c_address = None
                i2c_addr_str = config.get("i2c_address")
                if i2c_addr_str:
                    # Handle hex strings like "0x3C"
                    i2c_address = int(i2c_addr_str, 16 if i2c_addr_str.startswith("0x") else 10)

                # Store template metadata
                template = DeviceTemplate(
                    type_id=type_id,
                    name=name,
                    description=description,
                    category=category,
                    url=url,
                    i2c_address=i2c_address,
                )
                self._templates[type_id.lower()] = template
            except json.JSONDecodeError as e:
                # Skip invalid JSON files but log warning
                log.warning(
                    "invalid_device_config_json",
                    file=str(json_file),
                    error=str(e),
                    line=e.lineno if hasattr(e, "lineno") else None,
                )
                self._failed_configs.append(json_file.name)
                continue
            except KeyError as e:
                # Skip configs with missing required fields but log warning
                log.warning(
                    "invalid_device_config_schema",
                    file=str(json_file),
                    error=f"Missing required field: {e}",
                )
                self._failed_configs.append(json_file.name)
                continue

        # Fail-fast validation: Check if any devices loaded
        if total_files > 0 and len(self._templates) == 0:
            log.error(
                "device_registry_failed_to_load_any_devices",
                total_files=total_files,
                failed_devices=self._failed_configs,
            )
            raise RuntimeError(
                f"Device registry failed to load any devices. "
                f"Found {total_files} config file(s), all failed to load. "
                f"Failed configs: {', '.join(self._failed_configs)}\n"
                f"Check device_configs/ directory and JSON syntax."
            )

        # Log warning if some devices failed (but not all)
        if self._failed_configs:
            log.warning(
                "some_device_configs_failed",
                failed_count=len(self._failed_configs),
                loaded_count=len(self._templates),
                failed_files=self._failed_configs,
            )

        # Log registry health check
        if len(self._templates) > 0:
            log.info(
                "device_registry_loaded",
                loaded_count=len(self._templates),
                failed_count=len(self._failed_configs),
                total_files=total_files,
            )

    def get(self, type_id: str) -> DeviceTemplate | None:
        """
        Get device template metadata by type ID.

        Args:
            type_id: Device type identifier (case-insensitive)

        Returns:
            DeviceTemplate with metadata, or None if not found

        Example:
            >>> registry = get_registry()
            >>> template = registry.get('bh1750')
            >>> print(template.name)
            BH1750 Light Sensor
        """
        return self._templates.get(type_id.lower())

    def create(self, type_id: str, **kwargs: Any) -> Device:
        """
        Create a device instance from JSON configuration.

        Args:
            type_id: Device type identifier (matches JSON config filename)
            **kwargs: Parameters to pass to the config loader (e.g., color_name, num_leds)

        Returns:
            Device instance with metadata

        Raises:
            ValueError: If device config file not found
        """
        from .loader import load_device_from_config

        try:
            device = load_device_from_config(type_id, **kwargs)

            # Enrich device with metadata from registry
            template = self.get(type_id)
            if template:
                device.type_id = template.type_id
                device.description = template.description
                device.url = template.url
                device.category = template.category
                device.i2c_address = template.i2c_address

            return device
        except FileNotFoundError:
            raise ValueError(
                f"Unknown device type: {type_id}. No JSON configuration found in device_configs/."
            ) from None

    def list_all(self) -> list[DeviceTemplate]:
        """
        Get all registered device templates.

        Returns:
            List of all DeviceTemplate objects in the registry

        Example:
            >>> registry = get_registry()
            >>> all_devices = registry.list_all()
            >>> print(f"Found {len(all_devices)} devices")
            Found 8 devices
        """
        return list(self._templates.values())

    def get_failed_configs(self) -> list[str]:
        """
        Get list of config files that failed to load.

        Returns:
            List of filenames that failed during registry initialization

        Example:
            >>> registry = get_registry()
            >>> failed = registry.get_failed_configs()
            >>> if failed:
            ...     print(f"Warning: {len(failed)} configs failed to load")
        """
        return self._failed_configs.copy()

    def get_health_status(self) -> dict[str, int]:
        """
        Get registry health status.

        Returns:
            Dictionary with 'loaded', 'failed', and 'total' counts

        Example:
            >>> registry = get_registry()
            >>> status = registry.get_health_status()
            >>> print(f"Loaded: {status['loaded']}/{status['total']}")
        """
        return {
            "loaded": len(self._templates),
            "failed": len(self._failed_configs),
            "total": len(self._templates) + len(self._failed_configs),
        }

    def list_by_category(self, category: str) -> list[DeviceTemplate]:
        """
        Get all device templates in a specific category.

        Args:
            category: Device category (e.g., 'sensors', 'leds', 'displays')

        Returns:
            List of DeviceTemplate objects in the specified category

        Example:
            >>> registry = get_registry()
            >>> sensors = registry.list_by_category('sensors')
            >>> for sensor in sensors:
            ...     print(f"{sensor.name}: {sensor.description}")
        """
        return [t for t in self._templates.values() if t.category == category]

    def get_categories(self) -> list[str]:
        """
        Get all unique device categories.

        Returns:
            Sorted list of category names

        Example:
            >>> registry = get_registry()
            >>> categories = registry.get_categories()
            >>> print(categories)
            ['displays', 'generic', 'io', 'leds', 'sensors']
        """
        categories = {t.category for t in self._templates.values()}
        return sorted(categories)


# Optional default registry instance (lazy-loaded)
_default_registry: DeviceRegistry | None = None


def get_registry() -> DeviceRegistry:
    """
    Get the default device registry instance.

    This is a convenience function for common use cases. The registry is
    lazily initialized on first access and cached for subsequent calls.
    For testing or isolated contexts, use create_registry() instead.

    Returns:
        The default DeviceRegistry instance

    Example:
        >>> from pinviz.devices import get_registry
        >>> registry = get_registry()
        >>> device = registry.create('bh1750')
        >>> print(device.name)
        BH1750 Light Sensor
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = DeviceRegistry()
    return _default_registry


def create_registry() -> DeviceRegistry:
    """
    Create a new independent device registry.

    Useful for:
    - Unit testing with isolated state
    - Multiple concurrent contexts
    - Custom device configurations

    Each call creates a fresh registry that scans the device_configs/
    directory independently. Changes to this registry do not affect
    the default registry returned by get_registry().

    Returns:
        A new DeviceRegistry instance

    Example:
        >>> from pinviz.devices import create_registry
        >>> test_registry = create_registry()
        >>> # Use test_registry independently
        >>> # No pollution of global state
    """
    return DeviceRegistry()


def reset_default_registry() -> None:
    """
    Reset the default registry (mainly for testing).

    This clears the cached default registry, causing get_registry()
    to create a fresh instance on the next call. This is useful for
    resetting state between test runs.

    Example:
        >>> from pinviz.devices import reset_default_registry
        >>> reset_default_registry()
        >>> # Next call to get_registry() will create a new instance
    """
    global _default_registry
    _default_registry = None
