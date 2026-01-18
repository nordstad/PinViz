"""Device configuration loader.

This module provides functionality to load device definitions from JSON
configuration files, similar to how board configurations are loaded.
"""

import contextlib
import json
from pathlib import Path

from ..model import Device, DevicePin, PinRole, Point


def _get_device_config_path(config_name: str) -> Path:
    """
    Get the path to a device configuration file.

    Args:
        config_name: Device configuration name (without .json extension)

    Returns:
        Path to the configuration file
    """
    # Get the directory where this module is located
    module_dir = Path(__file__).parent.parent
    device_configs_dir = module_dir / "device_configs"

    # Search for the config file in subdirectories (sensors, leds, etc.)
    for category_dir in device_configs_dir.iterdir():
        if category_dir.is_dir():
            config_path = category_dir / f"{config_name}.json"
            if config_path.exists():
                return config_path

    # If not found in subdirectories, check root device_configs directory
    config_path = device_configs_dir / f"{config_name}.json"
    return config_path


def load_device_from_config(config_name: str, **parameters) -> Device:
    """
    Load a device definition from a JSON configuration file.

    This function reads a device configuration from the device_configs directory
    and returns a fully configured Device object with metadata.

    The configuration file must specify:
    - Device metadata (name, category, description, manufacturer, etc.)
    - Pin definitions with positions
    - Display properties (width, height, color)
    - Optional protocol and voltage information

    Args:
        config_name: Name of the device configuration file (without .json extension)
                    For example, "bh1750" will load "bh1750.json"
        **parameters: Optional parameters to customize the device (e.g., color_name for LEDs)

    Returns:
        Device: Configured device with all metadata and positioned pins

    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        ValueError: If the configuration is invalid
        json.JSONDecodeError: If the JSON file is malformed

    Examples:
        >>> device = load_device_from_config("bh1750")
        >>> print(device.name)
        BH1750 Light Sensor
        >>> print(device.url)
        https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf

        >>> led = load_device_from_config("led", color_name="Blue")
        >>> print(led.name)
        Blue LED
    """
    config_path = _get_device_config_path(config_name)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Device configuration file not found: {config_path}. "
            f"Available configurations should be placed in the device_configs directory."
        )

    try:
        with open(config_path) as f:
            config_dict = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in device configuration file {config_path}: {e}") from e

    # Apply parameters if any are defined in the config
    device_name = config_dict.get("name", "Unknown Device")
    if "parameters" in config_dict:
        # Handle parameterized device names (e.g., "{color_name} LED")
        for param_name, param_config in config_dict["parameters"].items():
            if param_name in parameters:
                # Use provided parameter value
                param_value = parameters[param_name]
            else:
                # Use default from config
                param_value = param_config.get("default")

            # Apply parameter to device name
            device_name = device_name.replace(f"{{{param_name}}}", str(param_value))

    # Get layout configuration or use defaults
    layout_config = config_dict.get("layout", {})
    layout_type = layout_config.get("type", "vertical")  # vertical, horizontal, custom
    # Default spacing (increased from 8.0 to prevent label overlap)
    pin_spacing = layout_config.get("pin_spacing", 14.0)
    pin_x_left = layout_config.get("pin_x", 5.0)  # Default x position for left pins
    start_y = layout_config.get("start_y", 10.0)  # Starting y position

    # Helper function to detect output pins
    def is_output_pin(pin_name: str) -> bool:
        """Detect if a pin should be positioned on the right (output) side."""
        name_upper = pin_name.upper()
        output_patterns = [
            "OUT",
            "TX",
            "MOSI",
            "DO",
            "DOUT",
            "VOUT",
            "COM",  # Relay common
            "NO",  # Relay normally open
            "NC",  # Relay normally closed
            "WIPER",  # Potentiometer output
        ]
        return any(pattern in name_upper for pattern in output_patterns)

    # Separate pins into left and right groups for smart positioning
    left_pins = []
    right_pins = []

    for index, pin_config in enumerate(config_dict.get("pins", [])):
        pin_name = pin_config["name"]
        pin_role = PinRole(pin_config["role"])  # Convert string to PinRole enum

        # Check if pin has explicit position
        if "position" in pin_config:
            # Use explicit position if provided
            position_data = pin_config["position"]
            position = Point(position_data["x"], position_data["y"])
            pin_side = "left"  # Default to left if explicit
        elif is_output_pin(pin_name):
            position = None  # Will calculate later
            pin_side = "right"
        else:
            position = None  # Will calculate later
            pin_side = "left"

        pin_data = {
            "name": pin_name,
            "role": pin_role,
            "position": position,
            "original_index": index,
        }

        if pin_side == "right":
            right_pins.append(pin_data)
        else:
            left_pins.append(pin_data)

    # Get display properties first (needed for pin positioning)
    display = config_dict.get("display", {})
    width = display.get("width", 80.0)

    # Calculate positions for left and right pins
    pins = []
    pin_x_right = width - pin_x_left

    # Position left side pins
    for i, pin_data in enumerate(left_pins):
        if pin_data["position"] is None:
            if layout_type == "vertical":
                pin_data["position"] = Point(pin_x_left, start_y + i * pin_spacing)
            elif layout_type == "horizontal":
                pin_data["position"] = Point(pin_x_left + i * pin_spacing, start_y)
            else:  # custom or fallback
                pin_data["position"] = Point(pin_x_left, start_y + i * pin_spacing)

        pins.append(
            DevicePin(
                name=pin_data["name"],
                role=pin_data["role"],
                position=pin_data["position"],
            )
        )

    # Position right side pins
    for i, pin_data in enumerate(right_pins):
        if pin_data["position"] is None:
            if layout_type == "vertical":
                pin_data["position"] = Point(pin_x_right, start_y + i * pin_spacing)
            elif layout_type == "horizontal":
                pin_data["position"] = Point(pin_x_right + i * pin_spacing, start_y)
            else:  # custom or fallback
                pin_data["position"] = Point(pin_x_right, start_y + i * pin_spacing)

        pins.append(
            DevicePin(
                name=pin_data["name"],
                role=pin_data["role"],
                position=pin_data["position"],
            )
        )

    # Auto-calculate height based on max pins per side if not specified
    # Height = start_y + (n-1) spacing between pins + bottom margin
    max_pins_per_side = max(len(left_pins), len(right_pins), 1)
    bottom_margin = 10.0
    default_height = max(40.0, start_y + ((max_pins_per_side - 1) * pin_spacing) + bottom_margin)
    height = display.get("height", default_height)

    # Use category-based color defaults if not specified
    category = config_dict.get("category", "")
    category_colors = {
        "sensors": "#50E3C2",  # Turquoise
        "displays": "#4A90E2",  # Blue
        "leds": "#E74C3C",  # Red
        "actuators": "#F5A623",  # Orange
        "io": "#95A5A6",  # Gray
    }
    default_color = category_colors.get(category, "#4A90E2")
    color = display.get("color", default_color)

    # Parse I2C address if present (convert hex string to int)
    i2c_address = None
    if "i2c_address" in config_dict and config_dict["i2c_address"]:
        with contextlib.suppress(ValueError, TypeError):
            i2c_address = int(config_dict["i2c_address"], 16)

    # Create Device object with all metadata
    # Use 'id' field as type_id (primary), fall back to 'type_id' for backward compat
    type_id = config_dict.get("id") or config_dict.get("type_id")

    device = Device(
        name=device_name,
        pins=pins,
        width=width,
        height=height,
        color=color,
        type_id=type_id,
        description=config_dict.get("description"),
        url=config_dict.get("datasheet_url"),
        category=config_dict.get("category"),
        i2c_address=i2c_address,
    )

    return device
