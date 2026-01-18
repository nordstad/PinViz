"""Utility functions for pinviz."""


def is_output_pin(pin_name: str) -> bool:
    """Detect if a pin should be positioned on the right (output) side.

    Args:
        pin_name: The name of the pin to check

    Returns:
        True if the pin should be positioned on the right side (output),
        False otherwise (input or power pins go on the left side)
    """
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
