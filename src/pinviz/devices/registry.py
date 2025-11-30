"""Device registry for managing predefined device templates."""

from collections.abc import Callable
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
    factory: Callable[..., Device]
    parameters: dict[str, Any] | None = None
    url: str | None = None


class DeviceRegistry:
    """Central registry for device templates."""

    def __init__(self):
        self._templates: dict[str, DeviceTemplate] = {}

    def register(
        self,
        type_id: str,
        name: str,
        description: str,
        category: str,
        factory: Callable[..., Device],
        parameters: dict[str, Any] | None = None,
        url: str | None = None,
    ) -> None:
        """
        Register a device template.

        Args:
            type_id: Unique identifier for the device type (used in YAML configs)
            name: Human-readable device name
            description: Brief description of the device
            category: Device category (sensors, displays, leds, io, etc.)
            factory: Factory function that creates the device
            parameters: Optional dict describing factory parameters
            url: Optional URL to device documentation or datasheet
        """
        template = DeviceTemplate(
            type_id=type_id,
            name=name,
            description=description,
            category=category,
            factory=factory,
            parameters=parameters,
            url=url,
        )
        self._templates[type_id.lower()] = template

    def get(self, type_id: str) -> DeviceTemplate | None:
        """Get a device template by type ID."""
        return self._templates.get(type_id.lower())

    def create(self, type_id: str, **kwargs: Any) -> Device:
        """
        Create a device instance from a template.

        Args:
            type_id: Device type identifier
            **kwargs: Parameters to pass to the factory function

        Returns:
            Device instance

        Raises:
            ValueError: If device type is not registered
        """
        template = self.get(type_id)
        if not template:
            raise ValueError(f"Unknown device type: {type_id}")

        return template.factory(**kwargs)

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
