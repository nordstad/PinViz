"""Standardized board rendering system for consistent visual appearance."""

from dataclasses import dataclass, field

import drawsvg as draw

from .model import Point


@dataclass
class BoardStyle:
    """
    Standardized board visual styling.

    Defines the visual appearance of PCB boards including colors, dimensions,
    and the critical scale factor for size consistency.

    Attributes:
        pcb_color: PCB substrate color (standard green)
        pcb_border_color: PCB edge/border color
        header_color: GPIO header connector color (black plastic)
        pad_color: Contact pad color (gold)
        silkscreen_color: Silkscreen text color (white)
        mounting_hole_color: Mounting hole color
        corner_radius: Board corner radius in pixels
        border_width: Board border width in pixels
        scale_factor: CRITICAL - converts mm to pixels (3.0 = 3px per mm)
    """

    pcb_color: str = "#006B32"  # Standard PCB green
    pcb_border_color: str = "#004D24"  # Darker green border
    header_color: str = "#1A1A1A"  # Black plastic connector
    pad_color: str = "#FFD700"  # Gold pads
    silkscreen_color: str = "#FFFFFF"  # White silkscreen
    mounting_hole_color: str = "#C0C0C0"  # Silver/gray
    corner_radius: float = 8.0
    border_width: float = 2.0
    scale_factor: float = 3.0  # px/mm - CRITICAL for consistent sizing


# Standard color palette for different PCB types
STANDARD_COLORS = {
    "pcb_green": "#006B32",  # Standard PCB green
    "pcb_blue": "#000080",  # Alternative PCB blue
    "pcb_black": "#1A1A1A",  # Black PCB
    "pcb_red": "#8B0000",  # Red PCB
    "header_black": "#1A1A1A",  # Plastic connector housing
    "pad_gold": "#FFD700",  # Gold contact pads
    "pad_silver": "#C0C0C0",  # Silver contact pads
    "silkscreen": "#FFFFFF",  # White silkscreen text
    "copper": "#B87333",  # Exposed copper
}


@dataclass
class BoardLayout:
    """
    Physical board dimensions and features in millimeters.

    All dimensions are in millimeters and will be converted to pixels
    using the BoardStyle.scale_factor during rendering.

    Attributes:
        width_mm: Physical board width in millimeters
        height_mm: Physical board height in millimeters
        header_x_mm: GPIO header X position in mm (from top-left)
        header_y_mm: GPIO header Y position in mm (from top-left)
        header_width_mm: Header width (default 5.08mm for 2-row header)
        header_height_mm: Header height (default 50.8mm for 20-pin rows)
        mounting_holes: List of mounting hole positions in mm
        decorative_elements: Optional decorative elements (chips, connectors)
    """

    width_mm: float
    height_mm: float
    header_x_mm: float
    header_y_mm: float
    header_width_mm: float = 5.08  # Standard 2-row header (2 * 2.54mm)
    header_height_mm: float = 50.8  # 20 pins * 2.54mm spacing
    mounting_holes: list[Point] = field(default_factory=list)
    decorative_elements: list[dict] = field(default_factory=list)

    def to_pixels(self, scale_factor: float) -> tuple[float, float]:
        """
        Convert board dimensions to pixels.

        Args:
            scale_factor: Pixels per millimeter

        Returns:
            Tuple of (width_px, height_px)
        """
        return (self.width_mm * scale_factor, self.height_mm * scale_factor)


class BoardRenderer:
    """
    Programmatic board rendering with consistent styling using drawsvg.

    Renders PCB boards with standardized appearance including:
    - PCB body with rounded corners
    - Mounting holes
    - GPIO header connector
    - Optional decorative elements

    All boards are rendered at the same scale factor (3.0 px/mm) to ensure
    visual consistency regardless of physical board size.
    """

    def __init__(self, style: BoardStyle):
        """
        Initialize board renderer with styling.

        Args:
            style: BoardStyle configuration
        """
        self.style = style

    def render_board(self, layout: BoardLayout, x: float, y: float) -> draw.Group:
        """
        Render a complete board at the specified position.

        Args:
            layout: Board layout with physical dimensions
            x: X position in SVG canvas
            y: Y position in SVG canvas

        Returns:
            SVG Group containing the board rendering
        """
        group = draw.Group(transform=f"translate({x}, {y})")

        # Convert mm to pixels using standard scale
        w_px = layout.width_mm * self.style.scale_factor
        h_px = layout.height_mm * self.style.scale_factor

        # 1. PCB body with rounded corners
        pcb = draw.Rectangle(
            0,
            0,
            w_px,
            h_px,
            rx=self.style.corner_radius,
            ry=self.style.corner_radius,
            fill=self.style.pcb_color,
            stroke=self.style.pcb_border_color,
            stroke_width=self.style.border_width,
        )
        group.append(pcb)

        # 2. Mounting holes
        for hole_mm in layout.mounting_holes:
            hole_px = Point(
                hole_mm.x * self.style.scale_factor, hole_mm.y * self.style.scale_factor
            )
            group.append(self._render_mounting_hole(hole_px))

        # 3. GPIO header area
        group.append(self._render_header(layout))

        # 4. Optional decorative elements (chips, connectors, etc.)
        for element in layout.decorative_elements:
            group.append(self._render_decorative_element(element))

        return group

    def _render_header(self, layout: BoardLayout) -> draw.Group:
        """
        Render the GPIO header connector.

        Args:
            layout: Board layout with header dimensions

        Returns:
            SVG Group containing the header rendering
        """
        group = draw.Group()

        # Convert to pixels
        x = layout.header_x_mm * self.style.scale_factor
        y = layout.header_y_mm * self.style.scale_factor
        w = layout.header_width_mm * self.style.scale_factor
        h = layout.header_height_mm * self.style.scale_factor

        # Black plastic connector housing
        header_rect = draw.Rectangle(
            x - 2,
            y - 2,
            w + 4,
            h + 4,
            rx=2,
            ry=2,
            fill=self.style.header_color,
            stroke="#000",
            stroke_width=1,
        )
        group.append(header_rect)

        return group

    def _render_mounting_hole(self, pos: Point) -> draw.Group:
        """
        Render a mounting hole with realistic appearance.

        Args:
            pos: Hole position in pixels

        Returns:
            SVG Group containing the mounting hole
        """
        group = draw.Group()

        # Outer circle (drill hole) - 3.2mm diameter
        outer_radius = (3.2 / 2.0) * self.style.scale_factor
        group.append(
            draw.Circle(
                pos.x,
                pos.y,
                outer_radius,
                fill=self.style.mounting_hole_color,
                stroke="#999",
                stroke_width=0.5,
            )
        )

        # Inner circle (through-hole lighter center)
        inner_radius = (1.6 / 2.0) * self.style.scale_factor
        group.append(draw.Circle(pos.x, pos.y, inner_radius, fill="white", opacity=0.3))

        return group

    def _render_decorative_element(self, element: dict) -> draw.Group:
        """
        Render optional decorative elements like chips, connectors.

        Args:
            element: Element definition dict with type, position, size

        Returns:
            SVG Group containing the decorative element
        """
        group = draw.Group()

        elem_type = element.get("type", "chip")
        x_mm = element.get("x", 0)
        y_mm = element.get("y", 0)
        w_mm = element.get("width", 10)
        h_mm = element.get("height", 10)
        label = element.get("label", "")

        # Convert to pixels
        x = x_mm * self.style.scale_factor
        y = y_mm * self.style.scale_factor
        w = w_mm * self.style.scale_factor
        h = h_mm * self.style.scale_factor

        if elem_type == "chip":
            # Draw a simple chip representation
            chip = draw.Rectangle(
                x,
                y,
                w,
                h,
                rx=2,
                ry=2,
                fill="#1A1A1A",
                stroke="#333",
                stroke_width=1,
            )
            group.append(chip)

            # Add label if provided
            if label:
                text = draw.Text(
                    label,
                    8,
                    x + w / 2,
                    y + h / 2 + 3,
                    text_anchor="middle",
                    font_family="Arial, sans-serif",
                    fill=self.style.silkscreen_color,
                    font_size="8px",
                )
                group.append(text)

        return group
