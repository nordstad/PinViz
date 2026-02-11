"""Load diagram configurations from YAML/JSON files."""

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from . import boards
from .color_utils import resolve_color
from .connection_graph import ConnectionGraph
from .constants import DEVICE_LAYOUT
from .devices import get_registry
from .logging_config import get_logger
from .model import (
    Connection,
    Device,
    DevicePin,
    Diagram,
    PinRole,
    Point,
)
from .schemas import ConnectionSchema, validate_config
from .theme import Theme
from .utils import is_output_pin
from .validation import ValidationIssue, ValidationLevel

log = get_logger(__name__)

# Maximum config file size in bytes (10MB)
MAX_CONFIG_FILE_SIZE = 10 * 1024 * 1024


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

        log.debug("loading_config_file", config_path=str(path), format=path.suffix)

        if not path.exists():
            log.error("config_file_not_found", config_path=str(path))
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        # Validate file size to prevent memory issues
        file_size = path.stat().st_size
        if file_size > MAX_CONFIG_FILE_SIZE:
            log.error(
                "config_file_too_large",
                config_path=str(path),
                size_bytes=file_size,
                max_bytes=MAX_CONFIG_FILE_SIZE,
            )
            max_mb = MAX_CONFIG_FILE_SIZE // (1024 * 1024)
            raise ValueError(
                f"Config file too large: {file_size} bytes "
                f"(maximum: {MAX_CONFIG_FILE_SIZE} bytes / {max_mb}MB)"
            )

        # Load file based on extension
        if path.suffix in [".yaml", ".yml"]:
            with open(path) as f:
                config = yaml.safe_load(f)
            log.debug("yaml_config_parsed", config_path=str(path))
        elif path.suffix == ".json":
            with open(path) as f:
                config = json.load(f)
            log.debug("json_config_parsed", config_path=str(path))
        else:
            log.error("unsupported_file_format", format=path.suffix, config_path=str(path))
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

        Raises:
            ValueError: If configuration fails schema validation
        """
        # Check for None or non-dict config
        if config is None or not isinstance(config, dict):
            log.error("invalid_config_type", config_type=type(config).__name__)
            raise ValueError(
                "Configuration validation failed:\n"
                "  • Config must be a dictionary with required fields "
                "(title, board, devices, connections)"
            )

        # Validate configuration against schema
        try:
            validated_config = validate_config(config)
            log.debug(
                "config_schema_validated",
                title=validated_config.title,
                device_count=len(validated_config.devices),
                connection_count=len(validated_config.connections),
            )
        except ValidationError as e:
            # Format validation errors for better readability
            error_messages = []
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                error_messages.append(f"  • {field_path}: {error['msg']}")

            log.error(
                "config_schema_validation_failed",
                error_count=len(error_messages),
                errors=error_messages,
            )
            raise ValueError(
                "Configuration validation failed:\n" + "\n".join(error_messages)
            ) from e

        # Load board
        board_config = config.get("board", "raspberry_pi_5")
        if isinstance(board_config, str):
            board = self._load_board_by_name(board_config)
            log.debug("board_loaded", board_name=board.name)
        else:
            log.error("custom_board_not_supported")
            raise ValueError("Custom board definitions not yet supported")

        # Load devices
        device_configs = config.get("devices", [])
        diagram_devices = []

        log.debug("loading_devices", device_count=len(device_configs))
        for dev_config in device_configs:
            device = self._load_device(dev_config)
            diagram_devices.append(device)
            log.debug(
                "device_loaded",
                device_name=device.name,
                pin_count=len(device.pins),
                device_type=dev_config.get("type", "custom"),
            )

        # Load connections
        connection_configs = config.get("connections", [])
        connections = []

        log.debug("loading_connections", connection_count=len(connection_configs))
        for conn_config in connection_configs:
            connection = self._load_connection(conn_config)
            connections.append(connection)

        # Validate graph structure
        log.debug("validating_graph_structure")
        graph = ConnectionGraph(diagram_devices, connections)
        validation_issues = self._validate_graph(graph, diagram_devices, connections)

        # Check for critical errors
        errors = [issue for issue in validation_issues if issue.level == ValidationLevel.ERROR]
        warnings = [issue for issue in validation_issues if issue.level == ValidationLevel.WARNING]

        if errors:
            self._report_validation_errors(errors)
            log.error("config_validation_failed", error_count=len(errors))
            raise ValueError("Configuration has critical errors")

        if warnings:
            self._report_validation_warnings(warnings)

        # Parse theme
        theme_str = config.get("theme", "light")
        try:
            theme = Theme(theme_str.lower())
        except ValueError:
            log.warning("invalid_theme", theme=theme_str, using_default="light")
            theme = Theme.LIGHT

        # Create diagram
        diagram = Diagram(
            title=config.get("title", "GPIO Diagram"),
            board=board,
            devices=diagram_devices,
            connections=connections,
            show_legend=config.get("show_legend", False),
            show_gpio_diagram=config.get("show_gpio_diagram", False),
            show_title=config.get("show_title", True),
            show_board_name=config.get("show_board_name", True),
            theme=theme,
        )

        log.info(
            "diagram_config_loaded",
            title=diagram.title,
            board=board.name,
            device_count=len(diagram_devices),
            connection_count=len(connections),
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
            - "raspberry_pi_4", "rpi4", "pi4": Raspberry Pi 4 Model B
            - "raspberry_pi_pico", "pico": Raspberry Pi Pico
            - "raspberry_pi", "rpi": Latest Raspberry Pi (currently Pi 5)
        """
        board_loaders = {
            # Raspberry Pi 5
            "raspberry_pi_5": boards.raspberry_pi_5,
            "rpi5": boards.raspberry_pi_5,
            # Raspberry Pi 4
            "raspberry_pi_4": boards.raspberry_pi_4,
            "rpi4": boards.raspberry_pi_4,
            "pi4": boards.raspberry_pi_4,
            # Raspberry Pi Pico
            "raspberry_pi_pico": boards.raspberry_pi_pico,
            "pico": boards.raspberry_pi_pico,
            # Aliases
            "raspberry_pi": boards.raspberry_pi,
            "rpi": boards.raspberry_pi,
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

                # Set type_id to enable registry lookups (e.g., for I2C address validation)
                device.type_id = device_type

                # Override device name if specified
                if device_name and device_type not in ("i2c_device", "i2c", "spi_device", "spi"):
                    device.name = device_name

                # Override device description if specified
                if "description" in config:
                    device.description = config["description"]

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

        # Constants for pin positioning
        pin_spacing = DEVICE_LAYOUT.PIN_SPACING
        pin_margin_top = DEVICE_LAYOUT.PIN_MARGIN_TOP
        pin_margin_bottom = DEVICE_LAYOUT.PIN_MARGIN_BOTTOM
        pin_x_left = DEVICE_LAYOUT.PIN_X_LEFT
        default_width = DEVICE_LAYOUT.DEFAULT_DEVICE_WIDTH

        # Separate pins into left (input) and right (output) groups
        left_pins = []
        right_pins = []

        for _i, pin_config in enumerate(pin_configs):
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

            # Check if pin has explicit position
            if "position" in pin_config:
                pos = pin_config["position"]
                position = Point(pos["x"], pos["y"])
                pins_list = left_pins  # Default to left if explicit position
            else:
                position = None  # Will calculate later

                # Check for explicit side field
                if "side" in pin_config:
                    side_value = pin_config["side"].lower()
                    if side_value not in ("left", "right"):
                        raise ValueError(
                            f"Invalid 'side' value '{pin_config['side']}' for pin '{pin_name}'. "
                            f"Must be 'left' or 'right'."
                        )
                    pins_list = left_pins if side_value == "left" else right_pins
                elif is_output_pin(pin_name):
                    # Output pins go on the right (automatic detection)
                    pins_list = right_pins
                else:
                    # Input/power pins go on the left (default)
                    pins_list = left_pins

            pins_list.append({"name": pin_name, "role": role, "position": position})

        # Position right pins: align when equal counts, center when different
        if len(left_pins) != len(right_pins):
            # Center the side with fewer pins
            pin_count_diff = abs(len(left_pins) - len(right_pins))
            if len(right_pins) < len(left_pins):
                right_pin_offset = (pin_count_diff * pin_spacing) / 2
            else:
                right_pin_offset = 0
        else:
            # Equal counts: align pins (no offset)
            right_pin_offset = 0

        # Calculate dynamic height based on max number of pins on either side
        # Height = top margin + offset + (n-1) spacing between pins + bottom margin
        max_pins_per_side = max(len(left_pins), len(right_pins), 1)
        # Only include offset in height calculation if right side has fewer pins
        offset_for_height = right_pin_offset if len(right_pins) < len(left_pins) else 0
        calculated_height = (
            pin_margin_top
            + offset_for_height
            + ((max_pins_per_side - 1) * pin_spacing)
            + pin_margin_bottom
        )

        # Get final dimensions
        width = config.get("width", default_width)
        height = config.get("height", calculated_height)

        # Calculate actual pin positions
        pins = []
        pin_x_right = width - pin_x_left

        # Position left side pins
        for i, pin_data in enumerate(left_pins):
            if pin_data["position"] is None:
                pin_data["position"] = Point(pin_x_left, pin_margin_top + i * pin_spacing)
            pins.append(DevicePin(pin_data["name"], pin_data["role"], pin_data["position"]))

        # Position right side pins
        for i, pin_data in enumerate(right_pins):
            if pin_data["position"] is None:
                pin_data["position"] = Point(
                    pin_x_right, pin_margin_top + right_pin_offset + i * pin_spacing
                )
            pins.append(DevicePin(pin_data["name"], pin_data["role"], pin_data["position"]))

        return Device(
            name=name,
            pins=pins,
            width=width,
            height=height,
            color=resolve_color(config.get("color"), DEVICE_LAYOUT.DEFAULT_DEVICE_COLOR),
            description=config.get("description"),
        )

    def _validate_graph(
        self,
        graph: ConnectionGraph,
        devices: list[Device],
        connections: list[Connection],
    ) -> list[ValidationIssue]:
        """
        Validate connection graph structure.

        Performs structural validation on the device connection graph:
        - Detects cycles in device-to-device connections
        - Identifies orphaned devices (devices with no connections)
        - Validates pin compatibility between connected devices

        Args:
            graph: ConnectionGraph object representing the topology
            devices: List of devices in the diagram
            connections: List of connections in the diagram

        Returns:
            List of validation issues (errors, warnings, info)

        Examples:
            >>> issues = loader._validate_graph(graph, devices, connections)
            >>> errors = [i for i in issues if i.level == ValidationLevel.ERROR]
            >>> if errors:
            ...     print("Configuration has critical errors!")
        """
        issues: list[ValidationIssue] = []

        # Check for cycles
        cycles = graph.detect_cycles()
        for cycle in cycles:
            cycle_path = " → ".join(cycle)
            issues.append(
                ValidationIssue(
                    level=ValidationLevel.ERROR,
                    message=f"Cycle detected: {cycle_path}",
                    location="Device connections",
                )
            )
            log.error("cycle_detected_in_graph", cycle=cycle)

        # Check for orphaned devices (devices with no connections)
        connected_devices = set()
        for conn in connections:
            # Add target device
            connected_devices.add(conn.device_name)
            # Add source device if it's a device-to-device connection
            if conn.is_device_connection() and conn.source_device:
                connected_devices.add(conn.source_device)

        for device in devices:
            if device.name not in connected_devices:
                issues.append(
                    ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"Device '{device.name}' has no connections",
                        location=device.name,
                    )
                )
                log.warning("orphaned_device_detected", device_name=device.name)

        log.debug(
            "graph_validation_completed",
            cycle_count=len([i for i in issues if "Cycle detected" in i.message]),
            orphaned_count=len([i for i in issues if "has no connections" in i.message]),
        )

        return issues

    def _report_validation_errors(self, issues: list[ValidationIssue]) -> None:
        """
        Print formatted validation errors to console.

        Displays critical errors that prevent diagram generation,
        including helpful suggestions for fixing each issue.

        Args:
            issues: List of ERROR-level validation issues to report
        """
        print("\n❌ Configuration Errors:")
        for issue in issues:
            print(f"  • {issue.message}")
            if issue.location:
                print(f"    📍 Location: {issue.location}")

            # Add contextual suggestions based on error type
            if "Cycle detected" in issue.message:
                print("    💡 Suggestion: Remove one connection to break the cycle")
            elif "not found" in issue.message:
                print("    💡 Suggestion: Check device and pin names in your configuration")
        print()

    def _report_validation_warnings(self, issues: list[ValidationIssue]) -> None:
        """
        Print formatted validation warnings to console.

        Displays warnings about potential issues that don't prevent
        diagram generation but should be reviewed.

        Args:
            issues: List of WARNING-level validation issues to report
        """
        print("\n⚠️  Configuration Warnings:")
        for issue in issues:
            print(f"  • {issue.message}")
            if issue.location:
                print(f"    📍 Location: {issue.location}")

            # Add contextual suggestions based on warning type
            if "has no connections" in issue.message:
                print("    💡 Suggestion: Connect device to board or remove it from configuration")
        print()

    def _load_connection(self, config: dict[str, Any]) -> Connection:
        """
        Load a connection from configuration dictionary.

        Supports both legacy and new connection formats:

        Legacy format (board-to-device):
            {
                "board_pin": 1,
                "device": "LED",
                "device_pin": "VCC",
                "color": "#FF0000",  # optional
                "style": "mixed",  # optional
                "components": [...]  # optional
            }

        New format (board-to-device):
            {
                "from": {"board_pin": 1},
                "to": {"device": "LED", "device_pin": "VCC"},
                "color": "#FF0000",  # optional
                "style": "mixed",  # optional
                "components": [...]  # optional
            }

        New format (device-to-device):
            {
                "from": {"device": "Regulator", "device_pin": "VOUT"},
                "to": {"device": "LED", "device_pin": "VCC"},
                "color": "#FF0000",  # optional
                "style": "mixed",  # optional
                "components": [...]  # optional
            }

        Args:
            config: Connection configuration dictionary

        Returns:
            Connection object

        Examples:
            >>> # Legacy format
            >>> config = {"board_pin": 11, "device": "LED", "device_pin": "Anode"}
            >>> conn = loader._load_connection(config)
            >>>
            >>> # New format (board source)
            >>> config = {
            ...     "from": {"board_pin": 1},
            ...     "to": {"device": "LED", "device_pin": "VCC"}
            ... }
            >>> conn = loader._load_connection(config)
            >>>
            >>> # New format (device source)
            >>> config = {
            ...     "from": {"device": "Regulator", "device_pin": "VOUT"},
            ...     "to": {"device": "LED", "device_pin": "VCC"}
            ... }
            >>> conn = loader._load_connection(config)
        """
        # Use ConnectionSchema to parse and validate the connection
        # This automatically supports both legacy and new formats
        schema = ConnectionSchema(**config)
        return schema.to_connection()


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
