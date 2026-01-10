"""Device registry for managing device templates loaded from JSON configurations."""

import json
from dataclasses import dataclass
from typing import Any

from ..model import Device


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
        self._scan_device_configs()

    def _scan_device_configs(self) -> None:
        """Scan device_configs directory and populate registry metadata."""
        from .loader import _get_device_config_path

        # Try to find device_configs directory
        try:
            # Get a path to any config to find the directory
            test_path = _get_device_config_path("bh1750")
            configs_dir = test_path.parent.parent
        except FileNotFoundError:
            # Can't find configs, skip scanning
            return

        # Scan all JSON files in all subdirectories
        for json_file in configs_dir.rglob("*.json"):
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
            except (json.JSONDecodeError, KeyError):
                # Skip invalid JSON files
                continue

    def get(self, type_id: str) -> DeviceTemplate | None:
        """Get device template metadata by type ID."""
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
        """Get all registered device templates."""
        return list(self._templates.values())

    def list_by_category(self, category: str) -> list[DeviceTemplate]:
        """Get all device templates in a specific category."""
        return [t for t in self._templates.values() if t.category == category]

    def get_categories(self) -> list[str]:
        """Get all unique device categories."""
        categories = {t.category for t in self._templates.values()}
        return sorted(categories)


# Global registry instance
_registry = DeviceRegistry()


def get_registry() -> DeviceRegistry:
    """Get the global device registry instance."""
    return _registry
