"""Theme system for pinviz diagrams.

Provides centralized color management for light and dark modes.
"""

from dataclasses import dataclass
from enum import Enum


class Theme(str, Enum):
    """Diagram theme options."""

    LIGHT = "light"
    DARK = "dark"


@dataclass
class ColorScheme:
    """Centralizes all theme-dependent colors.

    Wire colors and pin role colors remain theme-independent
    as they follow electrical conventions and functional identification.
    """

    # Backgrounds
    canvas_background: str
    table_background: str
    table_header_background: str
    table_separator: str
    legend_background: str

    # Text
    text_primary: str  # titles, labels, device names
    text_secondary: str  # descriptions, secondary content

    # Pin labels
    pin_label_background: str
    pin_label_text: str

    # Strokes
    pin_circle_stroke: str
    device_stroke: str
    legend_stroke: str
    legend_text: str


LIGHT_SCHEME = ColorScheme(
    canvas_background="white",
    table_background="#F8F9FA",
    table_header_background="#E9ECEF",
    table_separator="#DEE2E6",
    legend_background="white",
    text_primary="#333",
    text_secondary="#666",
    pin_label_background="#000000",
    pin_label_text="#FFFFFF",
    pin_circle_stroke="#333",
    device_stroke="#333",
    legend_stroke="#333",
    legend_text="#333",
)

DARK_SCHEME = ColorScheme(
    canvas_background="#1E1E1E",  # VS Code dark theme
    table_background="#2D2D2D",
    table_header_background="#3A3A3A",
    table_separator="#4A4A4A",
    legend_background="#2D2D2D",
    text_primary="#E0E0E0",  # High contrast light gray
    text_secondary="#B0B0B0",
    pin_label_background="#FFFFFF",  # Inverted for contrast
    pin_label_text="#000000",
    pin_circle_stroke="#E0E0E0",
    device_stroke="#E0E0E0",
    legend_stroke="#E0E0E0",
    legend_text="#E0E0E0",
)


def get_color_scheme(theme: Theme) -> ColorScheme:
    """Get the color scheme for a given theme.

    Args:
        theme: The theme to get colors for

    Returns:
        ColorScheme with colors appropriate for the theme
    """
    return DARK_SCHEME if theme == Theme.DARK else LIGHT_SCHEME
