"""Color utility functions for PinViz."""

from __future__ import annotations

import re

from .model import WireColor


def resolve_color(color_input: str | None, default: str = "#4A90E2") -> str:
    """
    Convert named color or hex code to hex format.

    Accepts both named colors (case-insensitive) and hex color codes.
    Named colors are matched against the WireColor enum. Invalid inputs
    fall back to the default color.

    Args:
        color_input: Named color (e.g., "red", "RED") or hex code (e.g., "#FF0000")
        default: Fallback color if input is None or invalid (default: "#4A90E2" - PinViz blue)

    Returns:
        Hex color code in #RRGGBB format

    Examples:
        >>> resolve_color("red")
        "#FF0000"
        >>> resolve_color("RED")
        "#FF0000"
        >>> resolve_color("#00FF00")
        "#00FF00"
        >>> resolve_color(None, "#123456")
        "#123456"
        >>> resolve_color("notacolor")
        "#4A90E2"
    """
    # Return default if color_input is None
    if color_input is None:
        return default

    # Strip whitespace and try matching against WireColor enum (case-insensitive)
    color_input = color_input.strip()
    color_upper = color_input.upper()
    try:
        # Try to get the color from WireColor enum
        wire_color = WireColor[color_upper]
        return wire_color.value
    except KeyError:
        pass

    # Check if it's a valid hex format
    if re.match(r"^#[0-9A-Fa-f]{6}$", color_input):
        return color_input

    # Invalid color - return default
    return default
