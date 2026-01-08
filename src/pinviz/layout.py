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
        wire_spacing: Minimum vertical spacing between parallel wires (default: 8.0)
        bundle_spacing: Spacing between wire bundles (default: 4.0)
        corner_radius: Radius for wire corner rounding (default: 5.0)
        legend_margin: Margin around legend box (default: 20.0)
        legend_width: Width of legend box (default: 150.0)
        legend_height: Height of legend box (default: 120.0)
        pin_number_y_offset: Vertical offset for pin number circles (default: 12.0)
        gpio_diagram_width: Width of GPIO reference diagram (default: 125.0)
        gpio_diagram_margin: Margin around GPIO reference diagram (default: 40.0)
    """

    board_margin_left: float = 40.0
    board_margin_top: float = 80.0  # Increased to prevent wire overlap with title
    device_area_left: float = 450.0  # Start of device area
    device_spacing_vertical: float = 20.0  # Space between devices
    device_margin_top: float = 60.0
    rail_offset: float = 40.0  # Distance from board to wire rail
    wire_spacing: float = 8.0  # Minimum spacing between parallel wires
    bundle_spacing: float = 4.0  # Spacing within a bundle
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
        Route all wires using device-based routing lanes to prevent crossings.

        Strategy:
        - Assign each device a vertical routing zone based on its Y position
        - Wires to the same device route through that device's zone
        - Wires to different devices use different zones, preventing crossings
        - Similar to Fritzing's approach where wires don't cross
        """
        routed_wires: list[RoutedWire] = []

        # First pass: collect all connection data
        wire_data: list[tuple[Connection, Point, Point, str, Device]] = []

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
            from_pos = Point(
                self.config.board_margin_left + board_pin.position.x,
                self.config.board_margin_top + board_pin.position.y,
            )

            to_pos = Point(
                device.position.x + device_pin.position.x,
                device.position.y + device_pin.position.y,
            )

            # Determine wire color
            from .model import DEFAULT_COLORS

            if conn.color:
                color = conn.color.value if hasattr(conn.color, "value") else conn.color
            else:
                color = DEFAULT_COLORS.get(board_pin.role, "#808080")

            wire_data.append((conn, from_pos, to_pos, color, device))

        # Sort wires by starting Y position first, then by target device
        # This groups wires from nearby pins together for better visual flow
        wire_data.sort(key=lambda x: (x[1].y, x[4].position.y, x[2].y))

        # Group wires by starting Y position to add vertical offsets for horizontal segments
        # This prevents horizontal overlap when multiple wires start from nearby pins
        y_tolerance = 50.0  # Pixels - pins within this range are considered at same Y level
        y_groups: dict[int, list[int]] = {}  # Maps group_id to list of wire indices

        for idx, (_, from_pos, _, _, _) in enumerate(wire_data):
            # Find existing group with similar Y, or create new group
            group_id = None
            for gid, wire_indices in y_groups.items():
                # Check first wire in group to see if Y positions are close
                first_wire_y = wire_data[wire_indices[0]][1].y
                if abs(from_pos.y - first_wire_y) < y_tolerance:
                    group_id = gid
                    break

            if group_id is None:
                group_id = len(y_groups)
                y_groups[group_id] = []

            y_groups[group_id].append(idx)

        # Calculate base rail X position
        board_right_edge = self.config.board_margin_left + diagram.board.width
        base_rail_x = board_right_edge + self.config.rail_offset

        # Assign each unique device a base rail X position
        # Devices lower on the page get rails further to the right
        unique_devices = []
        seen_devices = set()
        for _, _, _, _, device in wire_data:
            if device.name not in seen_devices:
                unique_devices.append(device)
                seen_devices.add(device.name)

        # Create rail mapping: each device gets a base rail position
        device_to_base_rail: dict[str, float] = {}
        for idx, device in enumerate(unique_devices):
            # Each device gets a base rail offset
            device_to_base_rail[device.name] = base_rail_x + (idx * self.config.wire_spacing * 3)

        # Count wires per device to add sub-offsets
        wire_count_per_device: dict[str, int] = {}
        for _, _, _, _, device in wire_data:
            wire_count_per_device[device.name] = wire_count_per_device.get(device.name, 0) + 1

        # Track wire index per device
        wire_index_per_device: dict[str, int] = {}

        # Initial routing pass - calculate all wire paths
        initial_wires = []
        for wire_idx, (conn, from_pos, to_pos, color, device) in enumerate(wire_data):
            # Get the base rail X for this device
            base_rail = device_to_base_rail[device.name]

            # Get wire index for this device
            dev_wire_idx = wire_index_per_device.get(device.name, 0)
            wire_index_per_device[device.name] = dev_wire_idx + 1

            # Add sub-offset for multiple wires to same device
            # Center the wires around the base rail position
            num_wires = wire_count_per_device[device.name]
            if num_wires > 1:
                # Spread wires evenly around the base rail
                spread = (num_wires - 1) * self.config.wire_spacing / 2
                offset = dev_wire_idx * self.config.wire_spacing - spread
            else:
                offset = 0

            rail_x = base_rail + offset

            # Calculate vertical offset for horizontal segment to prevent overlap
            y_offset = 0.0
            for _group_id, group_indices in y_groups.items():
                if wire_idx in group_indices:
                    # Find position within group
                    pos_in_group = group_indices.index(wire_idx)
                    num_in_group = len(group_indices)
                    if num_in_group > 1:
                        # Spread wires vertically with dramatic spacing for clear separation
                        vertical_spacing = self.config.wire_spacing * 4.5
                        spread = (num_in_group - 1) * vertical_spacing / 2
                        y_offset = pos_in_group * vertical_spacing - spread
                    break

            initial_wires.append(
                {
                    "conn": conn,
                    "from_pos": from_pos,
                    "to_pos": to_pos,
                    "color": color,
                    "device": device,
                    "rail_x": rail_x,
                    "y_offset": y_offset,
                    "wire_idx": wire_idx,
                }
            )

        # Conflict detection and resolution pass
        y_offset_adjustments = self._detect_and_resolve_overlaps(initial_wires)

        # Final routing with adjusted offsets
        for wire_info in initial_wires:
            # Apply any adjustments from conflict resolution
            adjustment = y_offset_adjustments.get(wire_info["wire_idx"], 0.0)
            final_y_offset = wire_info["y_offset"] + adjustment

            # Create path points routing through the device's rail
            path_points = self._calculate_wire_path_device_zone(
                wire_info["from_pos"],
                wire_info["to_pos"],
                wire_info["rail_x"],
                final_y_offset,
                wire_info["conn"].style,
            )

            routed_wires.append(
                RoutedWire(
                    connection=wire_info["conn"],
                    path_points=path_points,
                    color=wire_info["color"],
                    from_pin_pos=wire_info["from_pos"],
                    to_pin_pos=wire_info["to_pos"],
                )
            )

        return routed_wires

    def _detect_and_resolve_overlaps(self, wires: list[dict]) -> dict[int, float]:
        """
        Detect overlapping wire paths and calculate offset adjustments.

        Samples points along each wire path and checks for overlaps.
        Returns adjustments to y_offset for each wire to minimize overlaps.

        Args:
            wires: List of wire info dicts with positions and initial offsets

        Returns:
            Dictionary mapping wire_idx to y_offset adjustment
        """
        adjustments = {}
        min_separation = self.config.wire_spacing * 1.5  # Minimum desired separation

        # Sample points along each wire's potential path
        wire_samples = []
        for wire in wires:
            # Create initial path to analyze
            path_points = self._calculate_wire_path_device_zone(
                wire["from_pos"],
                wire["to_pos"],
                wire["rail_x"],
                wire["y_offset"],
                wire["conn"].style,
            )

            # Sample points along the path (simplified - use path points directly)
            samples = []
            for i in range(len(path_points) - 1):
                p1, p2 = path_points[i], path_points[i + 1]
                # Sample 5 points between each pair
                for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
                    x = p1.x + (p2.x - p1.x) * t
                    y = p1.y + (p2.y - p1.y) * t
                    samples.append((x, y))

            wire_samples.append(
                {
                    "wire_idx": wire["wire_idx"],
                    "samples": samples,
                    "from_y": wire["from_pos"].y,
                }
            )

        # Detect conflicts between wire pairs
        conflicts = []
        for i in range(len(wire_samples)):
            for j in range(i + 1, len(wire_samples)):
                wire_a = wire_samples[i]
                wire_b = wire_samples[j]

                # Check if wires have similar starting Y (potential overlap)
                if abs(wire_a["from_y"] - wire_b["from_y"]) > 100:
                    continue  # Wires start far apart, unlikely to conflict

                # Check minimum distance between sampled points
                min_dist = float("inf")
                for pa in wire_a["samples"]:
                    for pb in wire_b["samples"]:
                        dist = math.sqrt((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2)
                        min_dist = min(min_dist, dist)

                if min_dist < min_separation:
                    conflicts.append(
                        {
                            "wire_a": wire_a["wire_idx"],
                            "wire_b": wire_b["wire_idx"],
                            "severity": min_separation - min_dist,
                        }
                    )

        # Apply adjustments to resolve conflicts
        # Push conflicting wires further apart
        for conflict in sorted(conflicts, key=lambda c: c["severity"], reverse=True):
            adjustment_amount = conflict["severity"] / 2

            # Push wire_a up, wire_b down
            wire_a_idx = conflict["wire_a"]
            wire_b_idx = conflict["wire_b"]
            adjustments[wire_a_idx] = adjustments.get(wire_a_idx, 0.0) - adjustment_amount
            adjustments[wire_b_idx] = adjustments.get(wire_b_idx, 0.0) + adjustment_amount

        return adjustments

    def _calculate_wire_path_device_zone(
        self,
        from_pos: Point,
        to_pos: Point,
        rail_x: float,
        y_offset: float,
        style: WireStyle,
    ) -> list[Point]:
        """
        Calculate wire path with organic Bezier curves.

        Creates smooth, flowing curves similar to Fritzing's style rather than
        hard orthogonal lines. Uses device-specific rail positions and vertical
        offsets to prevent overlap and crossings.

        Args:
            from_pos: Starting position (board pin)
            to_pos: Ending position (device pin)
            rail_x: X position for the vertical routing rail (device-specific)
            y_offset: Vertical offset for the curve path
            style: Wire routing style (always uses curved style now)

        Returns:
            List of points defining the wire path with Bezier control points
        """
        # Calculate smooth curve path with gentle arcs
        # Use intermediate points to create natural-looking Bezier curves

        dy = to_pos.y - from_pos.y

        # Create a smooth S-curve or gentle arc path using rail_x for routing
        # Apply stronger y_offset at the beginning to fan out wires dramatically
        if abs(dy) < 50:  # Wires at similar Y - gentle horizontal arc through rail
            # Control point 1 - strong fan out
            ctrl1 = Point(rail_x * 0.3 + from_pos.x * 0.7, from_pos.y + y_offset * 0.8)
            # Control point 2 - converge
            ctrl2 = Point(rail_x * 0.7 + to_pos.x * 0.3, to_pos.y + y_offset * 0.3)
            return [from_pos, ctrl1, ctrl2, to_pos]
        else:  # Wires with vertical separation - smooth S-curve
            # Use 4 control points for a single smooth cubic Bezier
            # Control point 1: starts from board, curves toward rail with dramatic fan out
            ctrl1_x = from_pos.x + (rail_x - from_pos.x) * 0.4
            ctrl1_y = from_pos.y + y_offset * 0.9

            # Control point 2: approaches device from rail with gentle convergence
            ctrl2_x = to_pos.x + (rail_x - to_pos.x) * 0.4
            ctrl2_y = to_pos.y + y_offset * 0.3

            return [
                from_pos,
                Point(ctrl1_x, ctrl1_y),  # Control point 1
                Point(ctrl2_x, ctrl2_y),  # Control point 2
                to_pos,
            ]

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

        return canvas_width, canvas_height


def create_bezier_path(points: list[Point], corner_radius: float = 5.0) -> str:
    """
    Create an SVG path string with smooth Bezier curves.

    Creates organic, flowing curves through the points using cubic Bezier curves,
    similar to the classic Fritzing diagram style.

    Args:
        points: List of points defining the path (including control points)
        corner_radius: Not used, kept for API compatibility

    Returns:
        SVG path d attribute string with smooth curves
    """
    if len(points) < 2:
        return ""

    # Start at first point
    path_parts = [f"M {points[0].x:.2f},{points[0].y:.2f}"]

    if len(points) == 2:
        # Simple line
        path_parts.append(f"L {points[1].x:.2f},{points[1].y:.2f}")
    elif len(points) == 3:
        # Quadratic Bezier through middle point
        path_parts.append(
            f"Q {points[1].x:.2f},{points[1].y:.2f} {points[2].x:.2f},{points[2].y:.2f}"
        )
    elif len(points) == 4:
        # Smooth cubic Bezier using middle two points as control points
        path_parts.append(
            f"C {points[1].x:.2f},{points[1].y:.2f} "
            f"{points[2].x:.2f},{points[2].y:.2f} "
            f"{points[3].x:.2f},{points[3].y:.2f}"
        )
    elif len(points) == 5:
        # Two connected smooth cubic Bezier curves for S-shape
        # Calculate smooth control points for the transition at middle point
        mid_point = points[2]

        # First curve: points[0] -> points[2]
        # Control point 1: points[1]
        # Control point 2: approach mid_point smoothly from points[1] direction
        ctrl2_x = mid_point.x - (mid_point.x - points[1].x) * 0.3
        ctrl2_y = mid_point.y - (mid_point.y - points[1].y) * 0.3

        path_parts.append(
            f"C {points[1].x:.2f},{points[1].y:.2f} "
            f"{ctrl2_x:.2f},{ctrl2_y:.2f} "
            f"{mid_point.x:.2f},{mid_point.y:.2f}"
        )

        # Second curve: points[2] -> points[4]
        # Control point 1: leave mid_point smoothly toward points[3]
        # Control point 2: points[3]
        ctrl1_x = mid_point.x + (points[3].x - mid_point.x) * 0.3
        ctrl1_y = mid_point.y + (points[3].y - mid_point.y) * 0.3

        path_parts.append(
            f"C {ctrl1_x:.2f},{ctrl1_y:.2f} "
            f"{points[3].x:.2f},{points[3].y:.2f} "
            f"{points[4].x:.2f},{points[4].y:.2f}"
        )
    else:
        # Many points - create smooth curve through all
        for i in range(1, len(points)):
            if i == len(points) - 1:
                # Last segment - simple curve
                prev = points[i - 1]
                curr = points[i]
                # Create smooth approach to final point
                cx = prev.x + (curr.x - prev.x) * 0.5
                path_parts.append(f"Q {cx:.2f},{curr.y:.2f} {curr.x:.2f},{curr.y:.2f}")
            else:
                # Use current point as control, next as target
                curr = points[i]
                next_pt = points[i + 1]
                path_parts.append(f"Q {curr.x:.2f},{curr.y:.2f} {next_pt.x:.2f},{next_pt.y:.2f}")
                i += 1  # Skip next point since we used it

    return " ".join(path_parts)
