"""Wire rendering functionality for GPIO diagrams."""

import math

import drawsvg as draw

from .layout import LayoutConfig, RoutedWire, create_bezier_path
from .model import DEFAULT_COLORS, ComponentType, PinRole, Point
from .render_constants import RENDER_CONSTANTS


class WireRenderer:
    """Handles rendering of wires, inline components, and wire legends."""

    def __init__(self, layout_config: LayoutConfig):
        """
        Initialize wire renderer.

        Args:
            layout_config: Layout configuration for corner radius and legend settings
        """
        self.layout_config = layout_config

    def draw_wire(
        self, dwg: draw.Drawing, wire: RoutedWire, draw_connection_segment: bool = True
    ) -> None:
        """
        Draw a wire connection with optional inline components.

        Renders wires with rounded corners and white halos for visibility. If the
        wire has inline components (resistors, capacitors, diodes), breaks the wire
        into segments and draws component symbols at specified positions.

        Args:
            dwg: The SVG drawing object
            wire: The routed wire with path and color information
            draw_connection_segment: If False, skips drawing the final segment into the device pin
        """
        if not wire.connection.components:
            self._draw_simple_wire(dwg, wire, draw_connection_segment)
        else:
            self._draw_wire_with_components(dwg, wire, draw_connection_segment)

        self._draw_wire_endpoints(dwg, wire)

    def draw_wire_connection_segment(self, dwg: draw.Drawing, wire: RoutedWire) -> None:
        """Draw just the final straight segment that connects to the device pin."""
        if len(wire.path_points) >= 5:
            # Draw the straight line from connection_point to pin
            connection_point = wire.path_points[-2]
            end_point = wire.path_points[-1]

            # Create a simple line path
            path_d = (
                f"M {connection_point.x:.2f},{connection_point.y:.2f} "
                f"L {end_point.x:.2f},{end_point.y:.2f}"
            )

            # Draw with halo and core
            self._draw_wire_halo(dwg, path_d)
            self._draw_wire_core(dwg, path_d, wire.color)

    def draw_legend(
        self,
        dwg: draw.Drawing,
        routed_wires: list[RoutedWire],
        canvas_width: float,
        canvas_height: float,
    ) -> None:
        """Draw the legend showing wire color meanings."""
        legend_x = canvas_width - self.layout_config.legend_width - self.layout_config.legend_margin
        legend_y = (
            canvas_height - self.layout_config.legend_height - self.layout_config.legend_margin
        )

        # Legend background
        dwg.add(
            dwg.rect(
                insert=(legend_x, legend_y),
                size=(self.layout_config.legend_width, self.layout_config.legend_height),
                rx=RENDER_CONSTANTS.DEVICE_BORDER_RADIUS,
                ry=RENDER_CONSTANTS.DEVICE_BORDER_RADIUS,
                fill="white",
                stroke="#333",
                stroke_width=RENDER_CONSTANTS.DEVICE_STROKE_WIDTH,
                opacity=RENDER_CONSTANTS.DEVICE_OPACITY,
            )
        )

        # Legend title
        dwg.add(
            dwg.text(
                "Wire Colors",
                insert=(
                    legend_x + self.layout_config.legend_width / 2,
                    legend_y + RENDER_CONSTANTS.LEGEND_TITLE_Y_OFFSET,
                ),
                text_anchor="middle",
                font_size=RENDER_CONSTANTS.LEGEND_TITLE_FONT_SIZE,
                font_family="Arial, sans-serif",
                font_weight="bold",
                fill="#333",
            )
        )

        # Collect unique colors and their roles
        color_roles: dict[str, set[PinRole]] = {}
        for wire in routed_wires:
            color = wire.color
            # Try to determine the role from the connection
            # This is a simplified version; in practice, you'd look up the actual pin role
            if color not in color_roles:
                color_roles[color] = set()

            # Find the role by reverse lookup in DEFAULT_COLORS
            for role, default_color in DEFAULT_COLORS.items():
                if default_color == color:
                    color_roles[color].add(role)
                    break

        # Draw legend entries
        entry_y = legend_y + RENDER_CONSTANTS.LEGEND_FIRST_ENTRY_Y
        line_height = RENDER_CONSTANTS.LEGEND_LINE_HEIGHT

        for color, roles in sorted(color_roles.items()):
            if (
                entry_y
                > legend_y
                + self.layout_config.legend_height
                - RENDER_CONSTANTS.LEGEND_BOTTOM_MARGIN
            ):
                break  # Don't overflow legend box

            # Color swatch
            dwg.add(
                dwg.line(
                    start=(legend_x + RENDER_CONSTANTS.LEGEND_LINE_START_X, entry_y),
                    end=(legend_x + RENDER_CONSTANTS.LEGEND_LINE_END_X, entry_y),
                    stroke=color,
                    stroke_width=4,
                    stroke_linecap="round",
                )
            )

            # Role label
            role_text = ", ".join(sorted(r.value for r in roles))
            if not role_text:
                role_text = "Signal"

            dwg.add(
                dwg.text(
                    role_text,
                    insert=(
                        legend_x + RENDER_CONSTANTS.LEGEND_TEXT_X,
                        entry_y + RENDER_CONSTANTS.LEGEND_TEXT_Y_OFFSET,
                    ),
                    font_size=RENDER_CONSTANTS.LEGEND_ENTRY_FONT_SIZE,
                    font_family="Arial, sans-serif",
                    fill="#333",
                )
            )

            entry_y += line_height

    def _draw_simple_wire(
        self, dwg: draw.Drawing, wire: RoutedWire, draw_connection_segment: bool = True
    ) -> None:
        """Draw a simple wire without components."""
        if draw_connection_segment or len(wire.path_points) < 5:
            # Draw the full wire path
            path_d = create_bezier_path(wire.path_points, self.layout_config.corner_radius)
            self._draw_wire_halo(dwg, path_d)
            self._draw_wire_core(dwg, path_d, wire.color)
        else:
            # Draw only up to the connection point (skip the final straight segment)
            path_d = create_bezier_path(wire.path_points[:-1], self.layout_config.corner_radius)
            self._draw_wire_halo(dwg, path_d)
            self._draw_wire_core(dwg, path_d, wire.color)

    def _draw_wire_with_components(
        self, dwg: draw.Drawing, wire: RoutedWire, draw_connection_segment: bool = True
    ) -> None:
        """Draw a wire broken into segments by inline components."""
        component_positions = sorted(
            [(comp, comp.position) for comp in wire.connection.components], key=lambda x: x[1]
        )

        prev_pos = RENDER_CONSTANTS.SEGMENT_START
        for comp, comp_pos in component_positions:
            # Draw wire segment from prev_pos to comp_pos
            if comp_pos > prev_pos + RENDER_CONSTANTS.SEGMENT_POSITION_EPSILON:
                self._draw_wire_segment(dwg, wire, prev_pos, comp_pos)

            # Draw component symbol
            comp_pt, angle = self._point_along_path(wire.path_points, comp_pos)
            if comp.type == ComponentType.RESISTOR:
                self._draw_resistor_symbol(dwg, comp_pt, angle, wire.color, comp.value)

            prev_pos = comp_pos

        # Draw final segment from last component to end
        if prev_pos < RENDER_CONSTANTS.SEGMENT_END_THRESHOLD:
            self._draw_wire_segment(dwg, wire, prev_pos, RENDER_CONSTANTS.FULL_SEGMENT_END)

    def _draw_wire_segment(
        self, dwg: draw.Drawing, wire: RoutedWire, start_pos: float, end_pos: float
    ) -> None:
        """Draw a segment of a wire between two positions (0.0-1.0)."""
        segment_points = self._get_path_segment(wire.path_points, start_pos, end_pos)
        if len(segment_points) >= 2:
            path_d = create_bezier_path(segment_points, self.layout_config.corner_radius)
            self._draw_wire_halo(dwg, path_d)
            self._draw_wire_core(dwg, path_d, wire.color)

    def _get_path_segment(
        self, path_points: list[Point], start_pos: float, end_pos: float
    ) -> list[Point]:
        """Extract points from path between start_pos and end_pos."""
        if start_pos >= end_pos:
            return []

        segment_points = []

        # Add start point
        if start_pos > RENDER_CONSTANTS.SEGMENT_START:
            start_pt, _ = self._point_along_path(path_points, start_pos)
            segment_points.append(start_pt)

        # Add all intermediate path points that fall within range
        total_length = RENDER_CONSTANTS.SEGMENT_START
        segment_lengths = []
        for i in range(len(path_points) - 1):
            dx = path_points[i + 1].x - path_points[i].x
            dy = path_points[i + 1].y - path_points[i].y
            seg_len = math.sqrt(dx * dx + dy * dy)
            segment_lengths.append(seg_len)
            total_length += seg_len

        cumulative = RENDER_CONSTANTS.SEGMENT_START
        for i, seg_len in enumerate(segment_lengths):
            pos_at_start = cumulative / total_length
            pos_at_end = (cumulative + seg_len) / total_length

            # Include point if it's within our range
            if start_pos <= pos_at_start <= end_pos:
                segment_points.append(path_points[i])
            if start_pos <= pos_at_end <= end_pos:
                segment_points.append(path_points[i + 1])

            cumulative += seg_len

        # Add end point
        if end_pos < RENDER_CONSTANTS.FULL_SEGMENT_END:
            end_pt, _ = self._point_along_path(path_points, end_pos)
            segment_points.append(end_pt)

        # Remove duplicates while preserving order
        seen = set()
        unique_points = []
        for pt in segment_points:
            key = (
                round(pt.x, RENDER_CONSTANTS.POINT_ROUNDING_DECIMALS),
                round(pt.y, RENDER_CONSTANTS.POINT_ROUNDING_DECIMALS),
            )
            if key not in seen:
                seen.add(key)
                unique_points.append(pt)

        return unique_points if len(unique_points) >= 2 else segment_points

    def _point_along_path(self, points: list[Point], position: float) -> tuple[Point, float]:
        """
        Calculate a point along a path at the given position (0.0-1.0).

        Returns:
            Tuple of (point, angle_degrees) where angle is the tangent direction
        """
        if position <= RENDER_CONSTANTS.SEGMENT_START:
            # Angle from first to second point
            dx = points[1].x - points[0].x
            dy = points[1].y - points[0].y
            angle = math.degrees(math.atan2(dy, dx))
            return points[0], angle
        if position >= RENDER_CONSTANTS.FULL_SEGMENT_END:
            # Angle from second-to-last to last point
            dx = points[-1].x - points[-2].x
            dy = points[-1].y - points[-2].y
            angle = math.degrees(math.atan2(dy, dx))
            return points[-1], angle

        # Calculate total path length
        segments = []
        total_length = RENDER_CONSTANTS.SEGMENT_START
        for i in range(len(points) - 1):
            dx = points[i + 1].x - points[i].x
            dy = points[i + 1].y - points[i].y
            seg_length = math.sqrt(dx * dx + dy * dy)
            segments.append(seg_length)
            total_length += seg_length

        # Find target distance along path
        target_dist = position * total_length
        current_dist = RENDER_CONSTANTS.SEGMENT_START

        # Find which segment contains the target point
        for i, seg_length in enumerate(segments):
            if current_dist + seg_length >= target_dist:
                # Interpolate within this segment
                segment_position = (target_dist - current_dist) / seg_length
                p1 = points[i]
                p2 = points[i + 1]

                x = p1.x + segment_position * (p2.x - p1.x)
                y = p1.y + segment_position * (p2.y - p1.y)

                # Calculate angle
                dx = p2.x - p1.x
                dy = p2.y - p1.y
                angle = math.degrees(math.atan2(dy, dx))

                return Point(x, y), angle

            current_dist += seg_length

        # Fallback (shouldn't reach here)
        return points[-1], RENDER_CONSTANTS.SEGMENT_START

    def _draw_resistor_symbol(
        self, dwg: draw.Drawing, center: Point, angle: float, color: str, value: str
    ) -> None:
        """Draw a resistor symbol at the given position and angle."""
        # Resistor dimensions
        width = 20.0
        height = 6.0

        # Create group for resistor with transform
        g = draw.Group(transform=f"translate({center.x}, {center.y}) rotate({angle})")

        # Draw rectangle for resistor body
        rect = draw.Rectangle(
            -width / 2,
            -height / 2,
            width,
            height,
            fill="white",
            stroke=color,
            stroke_width=2,
        )

        # Draw lead lines (extending from resistor body)
        lead_length = 8.0
        left_lead = draw.Line(
            -width / 2 - lead_length,
            0,
            -width / 2,
            0,
            stroke=color,
            stroke_width=2,
        )
        right_lead = draw.Line(
            width / 2, 0, width / 2 + lead_length, 0, stroke=color, stroke_width=2
        )

        g.append(rect)
        g.append(left_lead)
        g.append(right_lead)

        # Add value label
        text = draw.Text(
            value,
            10,
            0,
            -height / 2 - 5,
            text_anchor="middle",
            font_family="Arial, sans-serif",
            fill="#333",
            font_weight="bold",
        )
        g.append(text)

        dwg.append(g)

    def _draw_wire_halo(self, dwg: draw.Drawing, path_d: str) -> None:
        """Draw the white halo around a wire for visibility."""
        dwg.append(
            draw.Path(
                d=path_d,
                stroke="white",
                stroke_width=RENDER_CONSTANTS.WIRE_MAIN_STROKE_WIDTH,
                fill="none",
                stroke_linecap="round",
                stroke_linejoin="round",
                opacity=RENDER_CONSTANTS.WIRE_MAIN_OPACITY,
            )
        )

    def _draw_wire_core(self, dwg: draw.Drawing, path_d: str, color: str) -> None:
        """Draw the colored core of a wire."""
        dwg.append(
            draw.Path(
                d=path_d,
                stroke=color,
                stroke_width=RENDER_CONSTANTS.WIRE_CORE_STROKE_WIDTH,
                fill="none",
                stroke_linecap="round",
                stroke_linejoin="round",
                opacity=RENDER_CONSTANTS.WIRE_CORE_OPACITY,
            )
        )

    def _draw_wire_endpoints(self, dwg: draw.Drawing, wire: RoutedWire) -> None:
        """Draw the start connection dots (board side only - device pins drawn separately)."""
        # Only draw endpoint circle at board side (start point)
        # Device side endpoint is handled by the device pin circle drawn later
        dwg.append(
            draw.Circle(
                wire.from_pin_pos.x,
                wire.from_pin_pos.y,
                RENDER_CONSTANTS.PIN_MARKER_OUTER_RADIUS,
                fill="white",
            )
        )
        dwg.append(
            draw.Circle(
                wire.from_pin_pos.x,
                wire.from_pin_pos.y,
                RENDER_CONSTANTS.PIN_MARKER_INNER_RADIUS,
                fill=wire.color,
            )
        )
