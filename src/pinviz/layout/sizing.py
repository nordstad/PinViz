"""Canvas size calculation for diagrams."""

import logging

from ..constants import TABLE_LAYOUT
from ..model import Diagram
from .types import LayoutConfig, RoutedWire

logger = logging.getLogger(__name__)


class CanvasSizer:
    """
    Calculates canvas dimensions to fit all diagram components.

    Determines the minimum canvas size needed to display the board,
    all devices, all wire paths, and optional legend/GPIO diagram
    without clipping or overlap.
    """

    def __init__(self, config: LayoutConfig, board_margin_top: float):
        """
        Initialize canvas sizer.

        Args:
            config: Layout configuration parameters
            board_margin_top: Top margin for the board
        """
        self.config = config
        self.board_margin_top = board_margin_top

    def calculate_canvas_size(
        self, diagram: Diagram, routed_wires: list[RoutedWire]
    ) -> tuple[float, float]:
        """
        Calculate required canvas size to fit all components.

        Determines the minimum canvas dimensions needed to display the board,
        all devices, all wire paths, and optional legend/GPIO diagram without
        clipping or overlap. Accounts for multi-tier device layouts.

        Args:
            diagram: The diagram containing board, devices, and configuration
            routed_wires: List of wires with calculated routing paths

        Returns:
            Tuple of (canvas_width, canvas_height) in SVG units

        Note:
            Adds extra margin for the legend and GPIO reference diagram if enabled.
        """
        # Start with board dimensions
        max_x = self.config.board_margin_left + diagram.board.width
        max_y = self.board_margin_top + diagram.board.height

        # Find rightmost device across all tiers
        for device in diagram.devices:
            device_right = device.position.x + device.width
            device_bottom = device.position.y + device.height
            max_x = max(max_x, device_right)
            max_y = max(max_y, device_bottom)

        # Check wire paths
        for wire in routed_wires:
            for point in wire.path_points:
                max_x = max(max_x, point.x)
                max_y = max(max_y, point.y)

        # Add uniform padding around all content
        canvas_width = max_x + self.config.canvas_padding
        canvas_height = max_y + self.config.canvas_padding

        # Add extra space for device specifications table if needed
        # Table is positioned below the bottommost element (device or board)
        if diagram.show_legend:
            devices_with_specs = [d for d in diagram.devices if d.description]
            if devices_with_specs:
                # Find the bottommost element
                board_bottom = self.board_margin_top + diagram.board.height
                device_bottom = max_y  # Already calculated above from devices
                max_bottom = max(board_bottom, device_bottom)

                # Table position: below bottommost element + margin
                table_y = max_bottom + self.config.specs_table_top_margin

                # Table height: header + rows (varies with multiline descriptions)
                # Use realistic estimate matching render_svg.py base row height
                header_height = TABLE_LAYOUT.HEADER_HEIGHT
                base_row_height = TABLE_LAYOUT.BASE_ROW_HEIGHT
                table_height = header_height + (len(devices_with_specs) * base_row_height)
                table_bottom = table_y + table_height

                # Ensure canvas is tall enough for the table
                canvas_height = max(canvas_height, table_bottom + self.config.canvas_padding)

        # Apply min/max bounds
        original_width = canvas_width
        original_height = canvas_height

        canvas_width = max(
            self.config.min_canvas_width, min(canvas_width, self.config.max_canvas_width)
        )
        canvas_height = max(
            self.config.min_canvas_height, min(canvas_height, self.config.max_canvas_height)
        )

        # Log warnings if clamped
        if (
            canvas_width == self.config.max_canvas_width
            and original_width > self.config.max_canvas_width
        ):
            logger.warning(
                f"Canvas width clamped to {canvas_width}px (requested: {original_width:.0f}px). "
                "Diagram may be too wide. Consider reducing device count or tier spacing."
            )

        if (
            canvas_height == self.config.max_canvas_height
            and original_height > self.config.max_canvas_height
        ):
            logger.warning(
                f"Canvas height clamped to {canvas_height}px (requested: {original_height:.0f}px). "
                "Diagram may be too tall. Consider reducing device count or vertical spacing."
            )

        return canvas_width, canvas_height
