"""Layout engine for positioning components and routing wires."""

import math
from dataclasses import dataclass

from .model import Connection, Device, Diagram, Point, WireStyle


@dataclass
class LayoutConfig:
    """
    Configuration parameters for diagram layout.

    Controls spacing, margins, and visual parameters for the diagram layout engine.
    All measurements are in SVG units (typically pixels).

    Attributes:
        board_margin_left: Left margin before board (default: 40.0)
        board_margin_top: Top margin before board (default: 40.0)
        device_area_left: X position where devices start (default: 450.0)
        device_spacing_vertical: Vertical space between stacked devices (default: 20.0)
        device_margin_top: Top margin for first device (default: 60.0)
        rail_offset: Horizontal distance from board to wire routing rail (default: 40.0)
        wire_offset_increment: Spacing between parallel wires from same pin (default: 3.0)
        corner_radius: Radius for wire corner rounding (default: 5.0)
        legend_margin: Margin around legend box (default: 20.0)
        legend_width: Width of legend box (default: 150.0)
        legend_height: Height of legend box (default: 120.0)
        pin_number_y_offset: Vertical offset for pin number circles (default: 12.0)
        gpio_diagram_width: Width of GPIO reference diagram (default: 125.0)
        gpio_diagram_margin: Margin around GPIO reference diagram (default: 40.0)
    """

    board_margin_left: float = 40.0
    board_margin_top: float = 40.0
    device_area_left: float = 450.0  # Start of device area
    device_spacing_vertical: float = 20.0  # Space between devices
    device_margin_top: float = 60.0
    rail_offset: float = 40.0  # Distance from board to wire rail
    wire_offset_increment: float = 3.0  # Offset for parallel wires
    corner_radius: float = 5.0  # Radius for rounded corners
    legend_margin: float = 20.0
    legend_width: float = 150.0
    legend_height: float = 120.0
    pin_number_y_offset: float = 12.0  # Y offset for pin number circles
    gpio_diagram_width: float = 125.0  # Width of GPIO pin diagram
    gpio_diagram_margin: float = 40.0  # Margin around GPIO diagram


@dataclass
class RoutedWire:
    """
    A wire connection with calculated routing path.

    Contains the complete routing information for a wire, including all waypoints
    along its path. This is the result of the layout engine's wire routing algorithm.

    Attributes:
        connection: The original connection specification
        path_points: List of points defining the wire path (min 2 points)
        color: Wire color as hex code (from connection or auto-assigned)
        from_pin_pos: Absolute position of source pin on board
        to_pin_pos: Absolute position of destination pin on device
    """

    connection: Connection
    path_points: list[Point]
    color: str
    from_pin_pos: Point
    to_pin_pos: Point


class LayoutEngine:
    """
    Calculate positions and wire routing for diagram components.

    The layout engine handles the algorithmic placement of devices and routing
    of wires between board pins and device pins. It uses a "rail" system where
    wires route horizontally to a vertical rail, then along the rail, then
    horizontally to the device.

    Wire routing features:
        - Automatic offset for parallel wires from the same pin
        - Rounded corners for professional appearance
        - Multiple routing styles (orthogonal, curved, mixed)
        - Optimized path calculation to minimize overlaps
    """

    def __init__(self, config: LayoutConfig | None = None):
        """
        Initialize layout engine with optional configuration.

        Args:
            config: Layout configuration parameters. If None, uses default LayoutConfig.
        """
        self.config = config or LayoutConfig()

    def layout_diagram(self, diagram: Diagram) -> tuple[float, float, list[RoutedWire]]:
        """
        Calculate layout for a complete diagram.

        Args:
            diagram: The diagram to layout

        Returns:
            Tuple of (canvas_width, canvas_height, routed_wires)
        """
        # Position devices vertically on the right side
        self._position_devices(diagram.devices)

        # Route all wires
        routed_wires = self._route_wires(diagram)

        # Calculate canvas size
        canvas_width, canvas_height = self._calculate_canvas_size(diagram, routed_wires)

        return canvas_width, canvas_height, routed_wires

    def _position_devices(self, devices: list[Device]) -> None:
        """
        Position devices vertically in the device area.

        Stacks devices vertically on the right side of the board, starting at
        device_area_left. Devices are positioned top-to-bottom with consistent
        spacing between them.

        Args:
            devices: List of devices to position (positions are modified in-place)

        Note:
            This method mutates the position attribute of each device.
        """
        y_offset = self.config.device_margin_top

        for device in devices:
            device.position = Point(
                self.config.device_area_left,
                y_offset,
            )
            y_offset += device.height + self.config.device_spacing_vertical

    def _route_wires(self, diagram: Diagram) -> list[RoutedWire]:
        """
        Route all wires in the diagram.

        Uses orthogonal routing with rounded corners and automatic wire offsetting
        to prevent overlap.
        """
        routed_wires: list[RoutedWire] = []

        # Group connections by rail position to calculate offsets
        rail_groups: dict[int, list[tuple[Connection, Point, Point, str]]] = {}

        for conn in diagram.connections:
            # Find board pin
            board_pin = diagram.board.get_pin_by_number(conn.board_pin)
            if not board_pin or not board_pin.position:
                continue

            # Find device and device pin
            device = next((d for d in diagram.devices if d.name == conn.device_name), None)
            if not device:
                continue

            device_pin = device.get_pin_by_name(conn.device_pin_name)
            if not device_pin:
                continue

            # Calculate absolute positions
            # Add pin_number_y_offset to match where pin circles are actually drawn
            from_pos = Point(
                self.config.board_margin_left + board_pin.position.x,
                self.config.board_margin_top
                + board_pin.position.y
                + self.config.pin_number_y_offset,
            )

            to_pos = Point(
                device.position.x + device_pin.position.x,
                device.position.y + device_pin.position.y,
            )

            # Determine wire color
            from .model import DEFAULT_COLORS

            # Handle both WireColor enum and plain hex string
            if conn.color:
                color = conn.color.value if hasattr(conn.color, "value") else conn.color
            else:
                color = DEFAULT_COLORS.get(board_pin.role, "#808080")

            # Group by source pin for offset calculation
            pin_key = conn.board_pin
            if pin_key not in rail_groups:
                rail_groups[pin_key] = []
            rail_groups[pin_key].append((conn, from_pos, to_pos, color))

        # Now create routed wires with proper offsets
        for _pin_key, connections in rail_groups.items():
            for idx, (conn, from_pos, to_pos, color) in enumerate(connections):
                # Calculate wire offset for parallel wires
                offset = idx * self.config.wire_offset_increment

                path_points = self._calculate_wire_path(from_pos, to_pos, offset, conn.style)

                routed_wires.append(
                    RoutedWire(
                        connection=conn,
                        path_points=path_points,
                        color=color,
                        from_pin_pos=from_pos,
                        to_pin_pos=to_pos,
                    )
                )

        return routed_wires

    def _calculate_wire_path(
        self, from_pos: Point, to_pos: Point, offset: float, style: WireStyle
    ) -> list[Point]:
        """
        Calculate the path for a wire.

        For MIXED style (orthogonal with rounded corners):
        1. Start at from_pos
        2. Move horizontally to rail
        3. Move vertically along rail
        4. Move horizontally to to_pos

        Args:
            from_pos: Starting position (board pin)
            to_pos: Ending position (device pin)
            offset: Vertical offset for parallel wires
            style: Wire routing style

        Returns:
            List of points defining the wire path
        """
        rail_x = from_pos.x + self.config.rail_offset + offset

        if style == WireStyle.MIXED or style == WireStyle.ORTHOGONAL:
            # Orthogonal routing: horizontal -> vertical -> horizontal
            return [
                from_pos,
                Point(rail_x, from_pos.y),  # Move right to rail
                Point(rail_x, to_pos.y),  # Move along rail to target y
                to_pos,  # Move right to target
            ]
        elif style == WireStyle.CURVED:
            # For curved, we'll use the same waypoints but render as bezier
            return [
                from_pos,
                Point(rail_x, from_pos.y),
                Point(rail_x, to_pos.y),
                to_pos,
            ]
        else:
            # Straight line
            return [from_pos, to_pos]

    def _calculate_canvas_size(
        self, diagram: Diagram, routed_wires: list[RoutedWire]
    ) -> tuple[float, float]:
        """
        Calculate required canvas size to fit all components.

        Determines the minimum canvas dimensions needed to display the board,
        all devices, all wire paths, and optional legend/GPIO diagram without
        clipping or overlap.

        Args:
            diagram: The diagram containing board, devices, and configuration
            routed_wires: List of wires with calculated routing paths

        Returns:
            Tuple of (canvas_width, canvas_height) in SVG units

        Note:
            Adds extra margin for the legend and GPIO reference diagram if enabled.
        """
        # Find the rightmost and bottommost elements
        max_x = self.config.board_margin_left + diagram.board.width
        max_y = self.config.board_margin_top + diagram.board.height

        # Check devices
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

        # Add margin and space for legend
        canvas_width = max_x + 200  # Extra space for legend
        canvas_height = max_y + 40

        if diagram.show_legend:
            # Reserve space for legend in bottom right
            legend_y = canvas_height - self.config.legend_height - self.config.legend_margin
            # Ensure legend doesn't overlap with content
            canvas_height = max(
                canvas_height, legend_y + self.config.legend_height + self.config.legend_margin
            )

        # Add space for GPIO diagram on the right if enabled
        if diagram.show_gpio_diagram:
            canvas_width += self.config.gpio_diagram_width + self.config.gpio_diagram_margin

            # Ensure canvas height accommodates the GPIO diagram
            # GPIO diagram viewBox is 500x1600, when scaled to target width
            gpio_original_width = 500.0
            gpio_original_height = 1600.0
            gpio_scale = self.config.gpio_diagram_width / gpio_original_width
            gpio_height = gpio_original_height * gpio_scale

            # Minimum canvas height to fit GPIO diagram with margins
            min_height_for_gpio = gpio_height + (2 * self.config.board_margin_top)
            canvas_height = max(canvas_height, min_height_for_gpio)

        return canvas_width, canvas_height


def create_bezier_path(points: list[Point], corner_radius: float = 5.0) -> str:
    """
    Create an SVG path string with rounded corners.

    Args:
        points: List of points defining the path
        corner_radius: Radius for rounded corners

    Returns:
        SVG path d attribute string
    """
    if len(points) < 2:
        return ""

    # Start at first point
    path_parts = [f"M {points[0].x:.2f},{points[0].y:.2f}"]

    for i in range(1, len(points) - 1):
        prev = points[i - 1]
        curr = points[i]
        next_pt = points[i + 1]

        # Calculate direction vectors
        dx1 = curr.x - prev.x
        dy1 = curr.y - prev.y
        dx2 = next_pt.x - curr.x
        dy2 = next_pt.y - curr.y

        # Distance from corner point
        len1 = math.sqrt(dx1 * dx1 + dy1 * dy1)
        len2 = math.sqrt(dx2 * dx2 + dy2 * dy2)

        if len1 == 0 or len2 == 0:
            # Degenerate case, skip rounding
            path_parts.append(f"L {curr.x:.2f},{curr.y:.2f}")
            continue

        # Use smaller of corner_radius or half the segment length
        radius = min(corner_radius, len1 / 2, len2 / 2)

        # Calculate the points before and after the corner
        ratio1 = radius / len1
        ratio2 = radius / len2

        before = Point(curr.x - dx1 * ratio1, curr.y - dy1 * ratio1)
        after = Point(curr.x + dx2 * ratio2, curr.y + dy2 * ratio2)

        # Line to before corner, arc around corner
        path_parts.append(f"L {before.x:.2f},{before.y:.2f}")
        path_parts.append(f"Q {curr.x:.2f},{curr.y:.2f} {after.x:.2f},{after.y:.2f}")

    # Line to final point
    final = points[-1]
    path_parts.append(f"L {final.x:.2f},{final.y:.2f}")

    return " ".join(path_parts)
