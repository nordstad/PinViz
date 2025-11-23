"""
Device Entry Validation for PinViz MCP Server.

Simple validation logic for device entries - no LLM calls required.
"""

import re
from typing import Any


def validate_device_entry(device_entry: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate a device entry against the schema.

    Args:
        device_entry: Device entry dictionary to validate

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Validate required fields
    required_fields = ["id", "name", "category", "description", "pins", "protocols", "voltage"]
    for field_name in required_fields:
        if field_name not in device_entry:
            errors.append(f"Missing required field: {field_name}")

    # Validate ID format (lowercase, hyphenated)
    if "id" in device_entry:
        device_id = device_entry["id"]
        if not re.match(r"^[a-z0-9-]+$", device_id):
            errors.append(f"Invalid ID format: {device_id} (must be lowercase, hyphenated)")

    # Validate category
    valid_categories = ["display", "sensor", "hat", "component", "actuator", "breakout"]
    if "category" in device_entry and device_entry["category"] not in valid_categories:
        errors.append(
            f"Invalid category: {device_entry['category']} "
            f"(must be one of {', '.join(valid_categories)})"
        )

    # Validate pins
    if "pins" in device_entry:
        pins = device_entry["pins"]
        if not isinstance(pins, list):
            errors.append("Pins must be an array")
        else:
            valid_roles = [
                "3V3",
                "5V",
                "GND",
                "I2C_SDA",
                "I2C_SCL",
                "SPI_MOSI",
                "SPI_MISO",
                "SPI_SCLK",
                "SPI_CS",
                "UART_TX",
                "UART_RX",
                "GPIO",
                "PWM",
                "1-Wire",
            ]
            for i, pin in enumerate(pins):
                if not isinstance(pin, dict):
                    errors.append(f"Pin {i} must be an object")
                    continue

                # Validate required pin fields
                if "name" not in pin:
                    errors.append(f"Pin {i} missing 'name' field")
                if "role" not in pin:
                    errors.append(f"Pin {i} missing 'role' field")
                elif pin["role"] not in valid_roles:
                    errors.append(
                        f"Pin {i} has invalid role: {pin['role']} "
                        f"(must be one of {', '.join(valid_roles)})"
                    )
                if "position" not in pin:
                    errors.append(f"Pin {i} missing 'position' field")

    # Validate protocols
    if "protocols" in device_entry:
        protocols = device_entry["protocols"]
        if not isinstance(protocols, list):
            errors.append("Protocols must be an array")
        else:
            valid_protocols = ["I2C", "SPI", "UART", "GPIO", "1-Wire", "PWM"]
            for protocol in protocols:
                if protocol not in valid_protocols:
                    errors.append(
                        f"Invalid protocol: {protocol} "
                        f"(must be one of {', '.join(valid_protocols)})"
                    )

    # Validate voltage
    if "voltage" in device_entry:
        voltage = device_entry["voltage"]
        if not isinstance(voltage, str) or not voltage:
            errors.append("Voltage must be a non-empty string")

    return (len(errors) == 0, errors)
