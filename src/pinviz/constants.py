"""Centralized constants for layout and rendering parameters."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceLayoutConstants:
    """
    Constants for device layout and pin positioning.

    These parameters control how custom device pins are positioned
    and spaced within device boundaries.

    Attributes:
        PIN_SPACING: Vertical spacing between consecutive pins (pixels)
        PIN_MARGIN_TOP: Top margin before first pin (pixels)
        PIN_MARGIN_BOTTOM: Bottom margin after last pin (pixels)
        PIN_X_LEFT: X position for left-side pins from device edge (pixels)
        DEFAULT_DEVICE_WIDTH: Default width for custom devices (pixels)
        RIGHT_PIN_OFFSET_RATIO: Stagger ratio for right-side pins (fraction of pin spacing)
        DEFAULT_DEVICE_COLOR: Default color for custom devices (hex color code)
    """

    PIN_SPACING: float = 14.0  # Increased from 8.0 to prevent label overlap
    PIN_MARGIN_TOP: float = 10.0
    PIN_MARGIN_BOTTOM: float = 10.0
    PIN_X_LEFT: float = 5.0
    DEFAULT_DEVICE_WIDTH: float = 80.0
    RIGHT_PIN_OFFSET_RATIO: float = 0.5  # Half of pin spacing
    DEFAULT_DEVICE_COLOR: str = "#4A90E2"  # Blue


@dataclass(frozen=True)
class LayoutAdjustmentConstants:
    """
    Constants for layout adjustments and positioning fine-tuning.

    These parameters handle edge cases and special layout adjustments
    for different board types and positioning scenarios.

    Attributes:
        DEVICE_ABOVE_PIN_ALLOWANCE: Pixels allowed for device to extend above connected pin (pixels)
        HORIZONTAL_BOARD_EXTRA_MARGIN: Extra margin for horizontal layout boards like Pico (pixels)
    """

    DEVICE_ABOVE_PIN_ALLOWANCE: float = 20.0  # Allow some device above pin
    HORIZONTAL_BOARD_EXTRA_MARGIN: float = 100.0  # Extra margin for Pico, ESP32, etc.


@dataclass(frozen=True)
class TableLayoutConstants:
    """
    Constants for device specifications table layout.

    These parameters control the appearance and spacing of the optional
    device specifications table rendered at the bottom of diagrams.

    Attributes:
        BASE_ROW_HEIGHT: Base height for table rows (pixels)
        LINE_SPACING: Vertical spacing between wrapped text lines (pixels)
        HEADER_HEIGHT: Height of table header row (pixels)
        PADDING_LEFT: Left padding inside table cells (pixels)
        PADDING_RIGHT: Right padding inside table cells (pixels)
        NAME_COLUMN_WIDTH: Width of device name column (pixels)
    """

    BASE_ROW_HEIGHT: float = 30.0  # Base height per row (single line)
    LINE_SPACING: float = 12.0  # Spacing between wrapped text lines
    HEADER_HEIGHT: float = 35.0  # Table header row height
    PADDING_LEFT: float = 10.0  # Left cell padding
    PADDING_RIGHT: float = 10.0  # Right cell padding
    NAME_COLUMN_WIDTH: float = 110.0  # Reduced from ~140-180 for better proportions


# Module-level constants instances for easy access
DEVICE_LAYOUT = DeviceLayoutConstants()
LAYOUT_ADJUSTMENTS = LayoutAdjustmentConstants()
TABLE_LAYOUT = TableLayoutConstants()
