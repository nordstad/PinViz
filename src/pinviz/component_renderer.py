"""Component and device rendering functionality for GPIO diagrams."""

import drawsvg as draw

from .model import Board, Device
from .render_constants import RENDER_CONSTANTS, _parse_font_size
from .theme import ColorScheme


class ComponentRenderer:
    """Handles rendering of devices, components, and board elements."""

    def __init__(self, color_scheme: ColorScheme):
        """Initialize renderer with color scheme.

        Args:
            color_scheme: Theme color scheme for rendering
        """
        self.color_scheme = color_scheme

    def draw_device(self, dwg: draw.Drawing, device: Device) -> None:
        """
        Draw a device or module as a colored rectangle with labeled pins.

        Renders the device name above the box, draws a rounded rectangle for the
        device body, and adds labeled pin markers with black backgrounds for
        readability.

        Args:
            dwg: The SVG drawing object
            device: The device to render
        """
        self.draw_device_box(dwg, device)
        self.draw_device_pins(dwg, device)

    def draw_device_box(self, dwg: draw.Drawing, device: Device) -> None:
        """Draw just the device box and name, without pins."""
        x = device.position.x
        y = device.position.y

        # Use full device name (no truncation)
        display_name = device.name

        # Adjust font size based on name length for better fit
        name_length = len(display_name)
        if name_length <= 20:
            font_size = RENDER_CONSTANTS.LEGEND_TITLE_FONT_SIZE
        elif name_length <= 30:
            font_size = RENDER_CONSTANTS.LEGEND_ENTRY_FONT_SIZE
        else:
            font_size = "9px"

        # Device name above the box
        text_x = x + device.width / 2
        text_y = y - 5  # Position above the box

        dwg.append(
            draw.Text(
                display_name,
                _parse_font_size(font_size),
                text_x,
                text_y,
                text_anchor="middle",
                font_family="Arial, sans-serif",
                font_weight="bold",
                fill=self.color_scheme.text_primary,
            )
        )

        # Device box
        dwg.append(
            draw.Rectangle(
                x,
                y,
                device.width,
                device.height,
                rx=RENDER_CONSTANTS.DEVICE_BORDER_RADIUS,
                ry=RENDER_CONSTANTS.DEVICE_BORDER_RADIUS,
                fill=device.color,
                stroke=self.color_scheme.device_stroke,
                stroke_width=2,
                opacity=0.9,
            )
        )

    def draw_device_pins(self, dwg: draw.Drawing, device: Device) -> None:
        """Draw device pins and labels."""
        x = device.position.x
        y = device.position.y

        # Draw pins
        for pin in device.pins:
            pin_x = x + pin.position.x
            pin_y = y + pin.position.y

            # Pin circle - small and visible with white halo for connection visibility
            # Draw white halo first for better wire connection visibility
            dwg.append(
                draw.Circle(
                    pin_x,
                    pin_y,
                    RENDER_CONSTANTS.PIN_MARKER_OUTER_RADIUS,
                    fill="white",
                    opacity=0.8,
                )
            )
            # Draw main pin circle
            dwg.append(
                draw.Circle(
                    pin_x,
                    pin_y,
                    RENDER_CONSTANTS.PIN_MARKER_INNER_RADIUS,
                    fill="#FFD700",
                    stroke=self.color_scheme.device_stroke,
                    stroke_width=RENDER_CONSTANTS.DEVICE_STROKE_WIDTH,
                    opacity=RENDER_CONSTANTS.DEVICE_OPACITY,
                )
            )

            # Detect if pin is on the right side of device (pin x > 50% of device width)
            is_right_side = pin.position.x > (device.width / 2)

            # Pin label with black background inside device box
            label_padding = 4
            label_height = 10
            # ~4.5px per character at 7px font (increased for safety)
            label_width = len(pin.name) * 4.5

            if is_right_side:
                # Right-side pin: label to the LEFT of pin circle
                label_x = pin_x - 6 - label_width - label_padding * 2
                text_x = label_x + label_padding
                text_anchor = "start"

                # Ensure label doesn't go outside device boundary on the left
                device_left = x
                if label_x < device_left:
                    label_x = device_left + 2  # 2px margin from edge
                    text_x = label_x + label_padding
            else:
                # Left-side pin: label to the RIGHT of pin circle (original behavior)
                label_x = pin_x + 6
                text_x = label_x + label_padding
                text_anchor = "start"

                # Ensure label doesn't go outside device boundary on the right
                device_right = x + device.width
                label_right = label_x + label_width + label_padding * 2
                if label_right > device_right:
                    # 2px margin from edge
                    label_x = device_right - label_width - label_padding * 2 - 2
                    text_x = label_x + label_padding

            label_y = pin_y

            # Draw background for pin label
            dwg.append(
                draw.Rectangle(
                    label_x,
                    label_y - label_height / 2,
                    label_width + label_padding * 2,
                    label_height,
                    rx=2,
                    ry=2,
                    fill=self.color_scheme.pin_label_background,
                    opacity=0.8,
                )
            )

            # Draw pin label text
            dwg.append(
                draw.Text(
                    pin.name,
                    7,
                    text_x,
                    label_y + 2.5,
                    text_anchor=text_anchor,
                    font_family="Arial, sans-serif",
                    fill=self.color_scheme.pin_label_text,
                )
            )

    def draw_board_fallback(self, dwg: draw.Drawing, board: Board, x: float, y: float) -> None:
        """Draw a simple representation of the board when SVG asset is not available."""
        # Board rectangle
        dwg.append(
            draw.Rectangle(
                x,
                y,
                board.width,
                board.height,
                rx=8,
                ry=8,
                fill="#2d8e3a",
                stroke="#1a5a23",
                stroke_width=2,
            )
        )

        # GPIO header representation
        header_x = x + board.header_offset.x
        header_y = y + board.header_offset.y

        dwg.append(
            draw.Rectangle(
                header_x - 5,
                header_y - 5,
                35,
                100,
                rx=2,
                ry=2,
                fill="#1a1a1a",
                stroke="#000",
            )
        )
