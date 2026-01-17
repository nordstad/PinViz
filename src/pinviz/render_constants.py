"""Rendering constants for SVG generation."""

from dataclasses import dataclass


@dataclass
class RenderConstants:
    """
    Rendering constants for SVG generation.

    These constants control visual aspects of the rendered SVG including
    font sizes, stroke widths, padding, and other styling parameters.
    """

    # Font sizes
    TITLE_FONT_SIZE: int = 20  # Main diagram title
    BOARD_LABEL_FONT_SIZE: int = 14  # Board name label
    LEGEND_TITLE_FONT_SIZE: str = "12px"  # Legend title
    LEGEND_ENTRY_FONT_SIZE: str = "10px"  # Legend entries
    PIN_FONT_SIZE: str = "4.5px"  # Pin number text

    # Pin rendering
    PIN_RADIUS: float = 4.5  # Radius of pin circles
    PIN_STROKE_WIDTH: float = 0.5  # Stroke width for pin circles
    PIN_OPACITY: float = 0.95  # Opacity of pin circles
    PIN_TEXT_Y_OFFSET: float = 1.5  # Vertical offset for pin number text
    PIN_MARKER_OUTER_RADIUS: float = 4.0  # Outer radius for wire endpoint marker
    PIN_MARKER_INNER_RADIUS: float = 3.0  # Inner radius for wire endpoint marker

    # Wire rendering
    WIRE_MAIN_STROKE_WIDTH: float = 4.5  # Stroke width for main wire highlight
    WIRE_CORE_STROKE_WIDTH: float = 3.0  # Stroke width for wire core
    WIRE_MAIN_OPACITY: float = 1.0  # Opacity for main wire
    WIRE_CORE_OPACITY: float = 0.8  # Opacity for wire core

    # Device rendering
    DEVICE_BORDER_RADIUS: int = 5  # Radius for device rectangle corners
    DEVICE_STROKE_WIDTH: int = 1  # Stroke width for device border
    # Opacity for device rectangles (fully opaque to hide wires underneath)
    DEVICE_OPACITY: float = 1.0

    # Title and label positioning
    TITLE_Y_OFFSET: int = 25  # Y position for title text
    BOARD_LABEL_Y_OFFSET: int = 20  # Y offset below board for label

    # Legend layout
    LEGEND_TITLE_Y_OFFSET: int = 20  # Y offset for legend title
    LEGEND_FIRST_ENTRY_Y: int = 35  # Y position for first legend entry
    LEGEND_LINE_HEIGHT: int = 18  # Vertical spacing between legend entries
    LEGEND_BOTTOM_MARGIN: int = 10  # Bottom margin for legend entries
    LEGEND_LINE_START_X: int = 10  # X start position for legend line sample
    LEGEND_LINE_END_X: int = 30  # X end position for legend line sample
    LEGEND_TEXT_X: int = 35  # X position for legend text
    LEGEND_TEXT_Y_OFFSET: int = 4  # Y offset for legend text alignment

    # Segment sampling
    SEGMENT_POSITION_EPSILON: float = 0.01  # Epsilon for segment position comparisons
    SEGMENT_END_THRESHOLD: float = 0.99  # Threshold for determining segment end
    FULL_SEGMENT_END: float = 1.0  # Value representing full segment (100%)
    SEGMENT_START: float = 0.0  # Value representing segment start (0%)
    POINT_ROUNDING_DECIMALS: int = 2  # Decimal places for point coordinate rounding


# Module-level constants instance
RENDER_CONSTANTS = RenderConstants()


def _parse_font_size(size_str: str) -> float:
    """Parse font size string like '20px' to float."""
    return float(size_str.rstrip("px"))


def _parse_numeric_value(value_str: str | float | int) -> float:
    """
    Parse numeric value, stripping common SVG unit suffixes.

    Handles values like '173.122px', '10em', '5%' by stripping the unit suffix.

    Args:
        value_str: String, float, or int value

    Returns:
        Parsed float value
    """
    if isinstance(value_str, (float, int)):
        return float(value_str)

    # Strip common SVG units
    str_value = str(value_str)
    for unit in ["px", "pt", "em", "rem", "%", "cm", "mm", "in"]:
        if str_value.endswith(unit):
            return float(str_value[: -len(unit)])

    return float(str_value)
