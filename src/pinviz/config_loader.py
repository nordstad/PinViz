"""Load diagram configurations from YAML/JSON files."""

import json
from pathlib import Path
from typing import Any

import yaml

from . import boards
from .devices import get_registry
from .model import (
    Component,
    ComponentType,
    Connection,
    Device,
    DevicePin,
    Diagram,
    PinRole,
    Point,
    WireStyle,
)


class ConfigLoader:
    """
    Load and parse diagram configurations from files.

    Supports loading diagrams from YAML and JSON configuration files.
    Handles predefined device types from the device registry and custom
    device definitions with automatic wire color assignment.

    Examples:
        >>> loader = ConfigLoader()
        >>> diagram = loader.load_from_file("config.yaml")
        >>> print(diagram.title)
        My GPIO Diagram
    """

    def load_from_file(self, config_path: str | Path) -> Diagram:
        """
        Load a diagram from a YAML or JSON configuration file.

        Args:
            config_path: Path to configuration file (.yaml, .yml, or .json)

        Returns:
            Diagram object

        Raises:
            ValueError: If file format is not supported or config is invalid
        """
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        # Load file based on extension
        if path.suffix in [".yaml", ".yml"]:
            with open(path) as f:
                config = yaml.safe_load(f)
        elif path.suffix == ".json":
            with open(path) as f:
                config = json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

        return self.load_from_dict(config)

    def load_from_dict(self, config: dict[str, Any]) -> Diagram:
        """
        Load a diagram from a configuration dictionary.

        Expected structure:
        {
            "title": "My Diagram",
            "board": "raspberry_pi_5" or {"name": "...", ...},
            "devices": [
                {"type": "bh1750", "name": "Light Sensor"},
                {"name": "Custom Device", "pins": [...], ...}
            ],
            "connections": [
                {"board_pin": 1, "device": "Light Sensor", "device_pin": "VCC"},
                ...
            ]
        }

        Args:
            config: Configuration dictionary

        Returns:
            Diagram object
        """
        # Load board
        board_config = config.get("board", "raspberry_pi_5")
        if isinstance(board_config, str):
            board = self._load_board_by_name(board_config)
        else:
            raise ValueError("Custom board definitions not yet supported")

        # Load devices
        device_configs = config.get("devices", [])
        diagram_devices = []

        for dev_config in device_configs:
            device = self._load_device(dev_config)
            diagram_devices.append(device)

        # Load connections
        connection_configs = config.get("connections", [])
        connections = []

        for conn_config in connection_configs:
            connection = self._load_connection(conn_config)
            connections.append(connection)

        # Create diagram
        diagram = Diagram(
            title=config.get("title", "GPIO Diagram"),
            board=board,
            devices=diagram_devices,
            connections=connections,
            show_legend=config.get("show_legend", True),
            show_gpio_diagram=config.get("show_gpio_diagram", False),
        )

        return diagram

    def _load_board_by_name(self, name: str):
        """
        Load a predefined board by name or alias.

        Supports multiple aliases for convenience (e.g., "rpi5", "raspberry_pi_5").

        Args:
            name: Board name or alias (case-insensitive)

        Returns:
            Board object

        Raises:
            ValueError: If board name is not recognized

        Supported names:
            - "raspberry_pi_5", "rpi5": Raspberry Pi 5
            - "raspberry_pi", "rpi": Latest Raspberry Pi (currently Pi 5)
            - "raspberry_pi_zero_2w", "raspberry_pi_zero", "raspberry pi zero",
              "raspberry pi zero 2", "raspberry pi zero 2w", "pizero", "pi zero",
              "zero2w", "zero 2w", "zero", "rpizero", "rpi zero": Raspberry Pi Zero/Zero 2 W
        """
        board_loaders = {
            # Raspberry Pi 5
            "raspberry_pi_5": boards.raspberry_pi_5,
            "raspberry_pi": boards.raspberry_pi,
            "rpi5": boards.raspberry_pi_5,
            "rpi": boards.raspberry_pi,
            # Raspberry Pi Zero / Zero 2 W (13 aliases total)
            "raspberry_pi_zero_2w": boards.raspberry_pi_zero_2w,
            "raspberry_pi_zero": boards.raspberry_pi_zero_2w,
            "raspberry pi zero": boards.raspberry_pi_zero_2w,
            "raspberry pi zero 2": boards.raspberry_pi_zero_2w,
            "raspberry pi zero 2w": boards.raspberry_pi_zero_2w,
            "pizero": boards.raspberry_pi_zero_2w,
            "pi zero": boards.raspberry_pi_zero_2w,
            "zero2w": boards.raspberry_pi_zero_2w,
            "zero 2w": boards.raspberry_pi_zero_2w,
            "zero": boards.raspberry_pi_zero_2w,
            "rpizero": boards.raspberry_pi_zero_2w,
            "rpi zero": boards.raspberry_pi_zero_2w,
        }

        loader = board_loaders.get(name.lower())
        if not loader:
            raise ValueError(f"Unknown board: {name}")

        return loader()

    def _load_device(self, config: dict[str, Any]) -> Device:
        """
        Load a device from configuration dictionary.

        Handles both predefined device types from the registry and custom
        device definitions with inline pin specifications.

        Args:
            config: Device configuration dictionary with either:
                - "type": Predefined device type (e.g., "bh1750", "led")
                - "name" + "pins": Custom device definition

        Returns:
            Device object

        Raises:
            ValueError: If device configuration is invalid or incomplete

        Examples:
            >>> # Predefined device
            >>> config = {"type": "bh1750", "name": "Light Sensor"}
            >>> device = loader._load_device(config)
            >>>
            >>> # Custom device
            >>> config = {
            ...     "name": "Custom Sensor",
            ...     "pins": [
            ...         {"name": "VCC", "role": "3V3"},
            ...         {"name": "GND", "role": "GND"}
            ...     ]
            ... }
            >>> device = loader._load_device(config)
        """
        device_type = config.get("type", "").lower()
        device_name = config.get("name")

        # Custom device (no type specified, but has pins)
        if not device_type and device_name and "pins" in config:
            return self._load_custom_device(config)

        # Try to load from device registry
        if device_type:
            registry = get_registry()
            template = registry.get(device_type)

            if template:
                # Extract factory parameters from config
                kwargs = {}

                # Handle device-specific parameters
                if device_type == "ir_led_ring":
                    kwargs["num_leds"] = config.get("num_leds", 12)
                elif device_type in ("i2c_device", "i2c"):
                    kwargs["name"] = device_name or "I2C Device"
                    kwargs["has_int_pin"] = config.get(
                        "has_interrupt", config.get("has_int_pin", False)
                    )
                elif device_type in ("spi_device", "spi"):
                    kwargs["name"] = device_name or "SPI Device"
                elif device_type == "led":
                    kwargs["color_name"] = config.get("color", "Red")
                elif device_type == "button":
                    kwargs["pull_up"] = config.get("pull_up", True)

                # Create device from template
                device = registry.create(device_type, **kwargs)

                # Override device name if specified
                if device_name and device_type not in ("i2c_device", "i2c", "spi_device", "spi"):
                    device.name = device_name

                return device

        raise ValueError(f"Unknown or incomplete device configuration: {config}")

    def _load_custom_device(self, config: dict[str, Any]) -> Device:
        """
        Load a custom device definition with inline pin specifications.

        Creates a device from a configuration that includes explicit pin definitions
        rather than referencing a predefined device type.

        Args:
            config: Device configuration with "name", "pins", and optional
                "width", "height", "color" fields

        Returns:
            Device object

        Examples:
            >>> config = {
            ...     "name": "Custom Module",
            ...     "width": 100.0,
            ...     "height": 50.0,
            ...     "color": "#FF5733",
            ...     "pins": [
            ...         {"name": "VCC", "role": "3V3", "position": {"x": 10, "y": 10}},
            ...         {"name": "GND", "role": "GND"}  # Position auto-calculated
            ...     ]
            ... }
            >>> device = loader._load_custom_device(config)
        """
        name = config["name"]
        pin_configs = config["pins"]

        pins = []
        for i, pin_config in enumerate(pin_configs):
            pin_name = pin_config["name"]
            role_str = pin_config.get("role", "GPIO")

            # Parse role
            try:
                role = PinRole(role_str)
            except ValueError:
                # Try uppercase
                try:
                    role = PinRole(role_str.upper())
                except ValueError:
                    role = PinRole.GPIO

            # Position (auto-calculate if not provided)
            if "position" in pin_config:
                pos = pin_config["position"]
                position = Point(pos["x"], pos["y"])
            else:
                # Auto-position vertically
                position = Point(5.0, 10.0 + i * 8.0)

            pins.append(DevicePin(pin_name, role, position))

        return Device(
            name=name,
            pins=pins,
            width=config.get("width", 80.0),
            height=config.get("height", 40.0),
            color=config.get("color", "#4A90E2"),
        )

    def _load_connection(self, config: dict[str, Any]) -> Connection:
        """
        Load a connection from configuration dictionary.

        Parses a connection specification including optional color, net name,
        wire style, and inline components.

        Args:
            config: Connection configuration with required fields:
                - "board_pin": Physical pin number (1-40)
                - "device": Device name
                - "device_pin": Pin name on device
                Optional fields:
                - "color": Wire color as hex code
                - "net": Logical net name
                - "style": Wire routing style ("orthogonal", "curved", "mixed")
                - "components": List of inline components

        Returns:
            Connection object

        Examples:
            >>> config = {
            ...     "board_pin": 11,
            ...     "device": "LED",
            ...     "device_pin": "Anode",
            ...     "color": "#FF0000",
            ...     "components": [
            ...         {"type": "resistor", "value": "220Ω", "position": 0.5}
            ...     ]
            ... }
            >>> conn = loader._load_connection(config)
        """
        board_pin = config["board_pin"]
        device_name = config["device"]
        device_pin_name = config["device_pin"]

        # Optional fields
        color = config.get("color")
        net_name = config.get("net")
        style_str = config.get("style", "mixed")

        # Parse style
        try:
            style = WireStyle(style_str.lower())
        except ValueError:
            style = WireStyle.MIXED

        # Parse components (resistors, capacitors, etc.)
        components = []
        if "components" in config:
            for comp_config in config["components"]:
                comp_type_str = comp_config.get("type", "resistor").lower()
                try:
                    comp_type = ComponentType(comp_type_str)
                except ValueError:
                    comp_type = ComponentType.RESISTOR

                components.append(
                    Component(
                        type=comp_type,
                        value=comp_config["value"],
                        position=comp_config.get("position", 0.55),
                    )
                )

        return Connection(
            board_pin=board_pin,
            device_name=device_name,
            device_pin_name=device_pin_name,
            color=color,
            net_name=net_name,
            style=style,
            components=components,
        )


def load_diagram(config_path: str | Path) -> Diagram:
    """
    Convenience function to load a diagram from a file.

    Args:
        config_path: Path to YAML or JSON configuration file

    Returns:
        Diagram object
    """
    loader = ConfigLoader()
    return loader.load_from_file(config_path)
