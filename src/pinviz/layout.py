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
        board_margin_top_base: Base top margin before board (default: 80.0)
        title_height: Height reserved for title text (default: 40.0)
        title_margin: Margin below title before wires can start (default: 50.0)
        device_area_left: X position where devices start (default: 450.0)
        device_spacing_vertical: Vertical space between stacked devices (default: 20.0)
        device_margin_top: Top margin for first device (default: 60.0)
        rail_offset: Horizontal distance from board to wire routing rail (default: 40.0)
        wire_spacing: Minimum vertical spacing between parallel wires (default: 8.0)
        bundle_spacing: Spacing between wire bundles (default: 4.0)
        corner_radius: Radius for wire corner rounding (default: 5.0)
        canvas_padding: Uniform padding around all content (default: 40.0)
        legend_margin: Margin around legend box (default: 20.0)
        legend_width: Width of legend box (default: 150.0)
        legend_height: Height of legend box (default: 120.0)
        pin_number_y_offset: Vertical offset for pin number circles (default: 12.0)
        gpio_diagram_width: Width of GPIO reference diagram (default: 125.0)
        gpio_diagram_margin: Margin around GPIO reference diagram (default: 40.0)
        specs_table_top_margin: Margin above specs table from bottom element (default: 30.0)
    """

    board_margin_left: float = 40.0
    board_margin_top_base: float = 40.0  # Base margin (used when no title)
    title_height: float = 40.0  # Space reserved for title
    title_margin: float = 50.0  # Margin below title (prevents wire overlap)
    device_area_left: float = 450.0  # Start of device area
    device_spacing_vertical: float = 20.0  # Space between devices
    device_margin_top: float = 60.0
    rail_offset: float = 40.0  # Distance from board to wire rail
    wire_spacing: float = 8.0  # Minimum spacing between parallel wires
    bundle_spacing: float = 4.0  # Spacing within a bundle
    corner_radius: float = 5.0  # Radius for rounded corners
    canvas_padding: float = 40.0  # Uniform padding around all content
    legend_margin: float = 20.0
    legend_width: float = 150.0
    legend_height: float = 120.0
    pin_number_y_offset: float = 12.0  # Y offset for pin number circles
    gpio_diagram_width: float = 125.0  # Width of GPIO pin diagram
    gpio_diagram_margin: float = 40.0  # Margin around GPIO diagram
    specs_table_top_margin: float = 30.0  # Margin above specs table

    def get_board_margin_top(self, show_title: bool) -> float:
        """Calculate actual board top margin based on whether title is shown."""
        if show_title:
            return self.board_margin_top_base + self.title_height + self.title_margin
        return self.board_margin_top_base


@dataclass
class LayoutConstants:
    """
    Algorithm constants for wire routing and path calculation.

    These constants control the behavior of the wire routing algorithm,
    including grouping, spacing, and curve generation. They are separate
    from LayoutConfig as they represent algorithmic tuning parameters
    rather than user-configurable layout settings.
    """

    # Wire grouping constants
    Y_POSITION_TOLERANCE: float = 50.0  # Pixels - wires within this Y range are grouped together
    FROM_Y_POSITION_TOLERANCE: float = (
        100.0  # Pixels - tolerance for conflict detection between wires
    )

    # Rail positioning constants
    RAIL_SPACING_MULTIPLIER: float = (
        3.0  # Multiplier for device rail spacing (multiplied by wire_spacing)
    )

    # Vertical spacing constants
    VERTICAL_SPACING_MULTIPLIER: float = (
        4.5  # Multiplier for vertical wire separation (multiplied by wire_spacing)
    )
    MIN_SEPARATION_MULTIPLIER: float = (
        1.5  # Multiplier for minimum wire separation in conflict detection
    )

    # Path sampling constants for conflict detection
    SAMPLE_POSITIONS: tuple[float, ...] = (
        0.0,
        0.25,
        0.5,
        0.75,
        1.0,
    )  # Positions along path to sample for overlap detection

    # Conflict resolution constants
    CONFLICT_ADJUSTMENT_DIVISOR: float = 2.0  # Divisor for adjusting conflicting wires

    # Wire path calculation constants
    STRAIGHT_SEGMENT_LENGTH: float = 15.0  # Length of straight segment at device pin end
    WIRE_PIN_EXTENSION: float = 2.0  # Extension beyond pin center for visual connection
    SIMILAR_Y_THRESHOLD: float = 50.0  # Threshold for determining if wires are at similar Y

    # Bezier curve control point ratios for gentle horizontal arc (similar Y)
    GENTLE_ARC_CTRL1_RAIL_RATIO: float = 0.3  # Rail influence on control point 1
    GENTLE_ARC_CTRL1_START_RATIO: float = 0.7  # Start position influence on control point 1
    GENTLE_ARC_CTRL1_OFFSET_RATIO: float = 0.8  # Y offset influence on control point 1

    GENTLE_ARC_CTRL2_RAIL_RATIO: float = 0.7  # Rail influence on control point 2
    GENTLE_ARC_CTRL2_END_RATIO: float = 0.3  # End position influence on control point 2
    GENTLE_ARC_CTRL2_OFFSET_RATIO: float = 0.3  # Y offset influence on control point 2

    # Bezier curve control point ratios for S-curve (different Y)
    S_CURVE_CTRL1_RATIO: float = 0.4  # Ratio for control point 1 position
    S_CURVE_CTRL1_OFFSET_RATIO: float = 0.9  # Y offset influence on control point 1

    S_CURVE_CTRL2_RATIO: float = 0.4  # Ratio for control point 2 position
    S_CURVE_CTRL2_OFFSET_RATIO: float = 0.3  # Y offset influence on control point 2


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


@dataclass
class WireData:
    """
    Intermediate wire data collected during routing.

    Stores all information needed to route a single wire before path calculation.
    Used internally by the layout engine during the wire routing algorithm.

    Attributes:
        connection: The original connection specification
        from_pos: Absolute position of source pin on board
        to_pos: Absolute position of destination pin on device
        color: Wire color as hex code (from connection or auto-assigned)
        device: The target device for this wire
    """

    connection: Connection
    from_pos: Point
    to_pos: Point
    color: str
    device: Device


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
        self.constants = LayoutConstants()

    def layout_diagram(self, diagram: Diagram) -> tuple[float, float, list[RoutedWire]]:
        """
        Calculate layout for a complete diagram.

        Args:
            diagram: The diagram to layout

        Returns:
            Tuple of (canvas_width, canvas_height, routed_wires)
        """
        # Calculate actual board margin based on whether title is shown
        self._board_margin_top = self.config.get_board_margin_top(diagram.show_title)

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

    def _collect_wire_data(self, diagram: Diagram) -> list[WireData]:
        """
        Collect wire connection data from the diagram.

        First pass: Gathers information about each connection including pin positions,
        device references, and wire colors. This prepares all the data needed for
        the wire routing algorithm.

        Args:
            diagram: The diagram containing connections, board, and devices

        Returns:
            List of WireData objects with resolved positions and colors
        """
        wire_data: list[WireData] = []

        # Build device lookup dictionary for O(1) access (performance optimization)
        device_by_name = {device.name: device for device in diagram.devices}

        for conn in diagram.connections:
            # Find board pin by physical pin number
            board_pin = diagram.board.get_pin_by_number(conn.board_pin)
            if not board_pin or not board_pin.position:
                continue

            # Find the target device by name (using O(1) dictionary lookup)
            device = device_by_name.get(conn.device_name)
            if not device:
                continue

            # Find the specific device pin by name
            device_pin = device.get_pin_by_name(conn.device_pin_name)
            if not device_pin:
                continue

            # Calculate absolute position of board pin
            # (board position is offset by margins)
            from_pos = Point(
                self.config.board_margin_left + board_pin.position.x,
                self._board_margin_top + board_pin.position.y,
            )

            # Calculate absolute position of device pin
            # (device pins are relative to device position)
            to_pos = Point(
                device.position.x + device_pin.position.x,
                device.position.y + device_pin.position.y,
            )

            # Determine wire color: use connection color if specified,
            # otherwise use default color based on pin role
            from .model import DEFAULT_COLORS

            if conn.color:
                color = conn.color.value if hasattr(conn.color, "value") else conn.color
            else:
                color = DEFAULT_COLORS.get(board_pin.role, "#808080")

            wire_data.append(WireData(conn, from_pos, to_pos, color, device))

        return wire_data

    def _group_wires_by_position(self, wire_data: list[WireData]) -> dict[int, list[int]]:
        """
        Group wires by their starting Y position for vertical offset calculation.

        Wires that start from pins at similar Y coordinates need vertical offsets
        on their horizontal segments to prevent visual overlap. This method groups
        wire indices by Y position so offsets can be calculated per group.

        Args:
            wire_data: List of WireData objects to group

        Returns:
            Dictionary mapping group_id to list of wire indices in that group
        """
        # Tolerance in pixels - pins within this range are considered at same Y level
        y_tolerance = self.constants.Y_POSITION_TOLERANCE
        y_groups: dict[int, list[int]] = {}

        for idx, wire in enumerate(wire_data):
            # Find existing group with similar starting Y position
            group_id = None
            for gid, wire_indices in y_groups.items():
                # Compare with the first wire in the group
                first_wire_y = wire_data[wire_indices[0]].from_pos.y
                if abs(wire.from_pos.y - first_wire_y) < y_tolerance:
                    group_id = gid
                    break

            # Create new group if no matching group found
            if group_id is None:
                group_id = len(y_groups)
                y_groups[group_id] = []

            y_groups[group_id].append(idx)

        return y_groups

    def _assign_rail_positions(
        self, wire_data: list[WireData], board_width: float
    ) -> tuple[dict[str, float], dict[str, int]]:
        """
        Assign rail X positions for each device to prevent wire crossings.

        Each device gets its own vertical "rail" for routing wires. Wires to the
        same device share a rail, while wires to different devices use different
        rails. This prevents crossing and maintains visual clarity.

        Args:
            wire_data: List of WireData objects to assign rails for
            board_width: Width of the board for calculating base rail position

        Returns:
            Tuple of (device_to_base_rail, wire_count_per_device):
            - device_to_base_rail: Maps device name to its base rail X position
            - wire_count_per_device: Maps device name to count of wires going to it
        """
        # Calculate base rail X position (to the right of the board)
        board_right_edge = self.config.board_margin_left + board_width
        base_rail_x = board_right_edge + self.config.rail_offset

        # Collect unique devices in order of appearance
        # This maintains visual flow from top to bottom
        unique_devices = []
        seen_devices = set()
        for wire in wire_data:
            if wire.device.name not in seen_devices:
                unique_devices.append(wire.device)
                seen_devices.add(wire.device.name)

        # Assign each device a base rail position
        # Devices lower on the page get rails further to the right
        device_to_base_rail: dict[str, float] = {}
        for idx, device in enumerate(unique_devices):
            # Each device gets progressively more rail offset
            device_to_base_rail[device.name] = base_rail_x + (
                idx * self.config.wire_spacing * self.constants.RAIL_SPACING_MULTIPLIER
            )

        # Count wires per device for sub-offset calculations
        wire_count_per_device: dict[str, int] = {}
        for wire in wire_data:
            wire_count_per_device[wire.device.name] = (
                wire_count_per_device.get(wire.device.name, 0) + 1
            )

        return device_to_base_rail, wire_count_per_device

    def _route_wires(self, diagram: Diagram) -> list[RoutedWire]:
        """
        Route all wires using device-based routing lanes to prevent crossings.

        This is the main wire routing orchestration method. It coordinates the
        multi-step routing algorithm:
        1. Collect wire data (pins, positions, colors)
        2. Sort wires for optimal visual flow
        3. Group wires by starting position for offset calculation
        4. Assign routing rails to each device
        5. Calculate initial wire paths with offsets
        6. Detect and resolve any remaining conflicts
        7. Generate final routed wires

        Strategy:
        - Assign each device a vertical routing zone based on its Y position
        - Wires to the same device route through that device's zone
        - Wires to different devices use different zones, preventing crossings
        - Similar to Fritzing's approach where wires don't cross

        Args:
            diagram: The diagram containing all connections, board, and devices

        Returns:
            List of RoutedWire objects with calculated paths
        """
        # Step 1: Collect wire data from all connections
        wire_data = self._collect_wire_data(diagram)

        # Sort wires by starting Y position first, then by target device
        # This groups wires from nearby pins together for better visual flow
        wire_data.sort(key=lambda w: (w.from_pos.y, w.device.position.y, w.to_pos.y))

        # Step 2: Group wires by starting Y position for vertical offset calculation
        y_groups = self._group_wires_by_position(wire_data)

        # Step 3: Assign rail positions for each device
        device_to_base_rail, wire_count_per_device = self._assign_rail_positions(
            wire_data, diagram.board.width
        )

        # Step 4: Calculate initial wire paths with offsets
        initial_wires = self._calculate_initial_wire_paths(
            wire_data, y_groups, device_to_base_rail, wire_count_per_device
        )

        # Step 5: Detect and resolve any overlapping wire paths
        y_offset_adjustments = self._detect_and_resolve_overlaps(initial_wires)

        # Step 6: Generate final routed wires with all adjustments applied
        routed_wires = self._generate_final_routed_wires(initial_wires, y_offset_adjustments)

        return routed_wires

    def _calculate_initial_wire_paths(
        self,
        wire_data: list[WireData],
        y_groups: dict[int, list[int]],
        device_to_base_rail: dict[str, float],
        wire_count_per_device: dict[str, int],
    ) -> list[dict]:
        """
        Calculate initial wire paths with rail positions and vertical offsets.

        For each wire, calculates:
        - The rail X position (based on device assignment with sub-offsets)
        - The vertical Y offset (based on position within Y group)

        Args:
            wire_data: List of WireData objects to route
            y_groups: Mapping of group_id to list of wire indices
            device_to_base_rail: Base rail X position for each device
            wire_count_per_device: Number of wires going to each device

        Returns:
            List of wire info dictionaries with routing parameters
        """
        # Track wire index per device for sub-offset calculation
        wire_index_per_device: dict[str, int] = {}
        initial_wires = []

        for wire_idx, wire in enumerate(wire_data):
            # Get the base rail X for this device
            base_rail = device_to_base_rail[wire.device.name]

            # Get and increment wire index for this device
            dev_wire_idx = wire_index_per_device.get(wire.device.name, 0)
            wire_index_per_device[wire.device.name] = dev_wire_idx + 1

            # Calculate sub-offset for multiple wires to same device
            # Center the wires around the base rail position
            num_wires = wire_count_per_device[wire.device.name]
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
                        vertical_spacing = (
                            self.config.wire_spacing * self.constants.VERTICAL_SPACING_MULTIPLIER
                        )
                        spread = (num_in_group - 1) * vertical_spacing / 2
                        y_offset = pos_in_group * vertical_spacing - spread
                    break

            initial_wires.append(
                {
                    "conn": wire.connection,
                    "from_pos": wire.from_pos,
                    "to_pos": wire.to_pos,
                    "color": wire.color,
                    "device": wire.device,
                    "rail_x": rail_x,
                    "y_offset": y_offset,
                    "wire_idx": wire_idx,
                }
            )

        return initial_wires

    def _generate_final_routed_wires(
        self, initial_wires: list[dict], y_offset_adjustments: dict[int, float]
    ) -> list[RoutedWire]:
        """
        Generate final routed wires with all adjustments applied.

        Takes the initial wire paths and applies conflict resolution adjustments
        to create the final RoutedWire objects with complete path information.

        Args:
            initial_wires: List of initial wire info dictionaries
            y_offset_adjustments: Adjustments to y_offset for each wire

        Returns:
            List of RoutedWire objects with calculated paths
        """
        routed_wires: list[RoutedWire] = []

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
        min_separation = (
            self.config.wire_spacing * self.constants.MIN_SEPARATION_MULTIPLIER
        )  # Minimum desired separation

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
                # Sample points between each pair
                for t in self.constants.SAMPLE_POSITIONS:
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
                if (
                    abs(wire_a["from_y"] - wire_b["from_y"])
                    > self.constants.FROM_Y_POSITION_TOLERANCE
                ):
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
            adjustment_amount = conflict["severity"] / self.constants.CONFLICT_ADJUSTMENT_DIVISOR

            # Push wire_a up, wire_b down
            wire_a_idx = conflict["wire_a"]
            wire_b_idx = conflict["wire_b"]
            adjustments[wire_a_idx] = adjustments.get(wire_a_idx, 0.0) - adjustment_amount
            adjustments[wire_b_idx] = adjustments.get(wire_b_idx, 0.0) + adjustment_amount

        return adjustments

    def _calculate_connection_points(self, to_pos: Point) -> tuple[Point, Point]:
        """
        Calculate connection and extended end points for wire routing.

        Args:
            to_pos: Target position (device pin)

        Returns:
            Tuple of (connection_point, extended_end)
        """
        # Create a point slightly before the device pin for the curve to end
        connection_point = Point(to_pos.x - self.constants.STRAIGHT_SEGMENT_LENGTH, to_pos.y)

        # Extend the final point slightly beyond pin center so wire visually penetrates the pin
        extended_end = Point(to_pos.x + self.constants.WIRE_PIN_EXTENSION, to_pos.y)

        return connection_point, extended_end

    def _calculate_gentle_arc_path(
        self,
        from_pos: Point,
        rail_x: float,
        y_offset: float,
        connection_point: Point,
        extended_end: Point,
    ) -> list[Point]:
        """
        Calculate gentle horizontal arc path for wires with similar Y positions.

        Args:
            from_pos: Starting position (board pin)
            rail_x: X position for the vertical routing rail
            y_offset: Vertical offset for the curve path
            connection_point: Point where curve ends
            extended_end: Final point with pin extension

        Returns:
            List of points defining the gentle arc path
        """
        # Control point 1 - strong fan out
        ctrl1 = Point(
            rail_x * self.constants.GENTLE_ARC_CTRL1_RAIL_RATIO
            + from_pos.x * self.constants.GENTLE_ARC_CTRL1_START_RATIO,
            from_pos.y + y_offset * self.constants.GENTLE_ARC_CTRL1_OFFSET_RATIO,
        )
        # Control point 2 - converge to connection point
        ctrl2_x = (
            rail_x * self.constants.GENTLE_ARC_CTRL2_RAIL_RATIO
            + connection_point.x * self.constants.GENTLE_ARC_CTRL2_END_RATIO
        )
        ctrl2_y = connection_point.y + y_offset * self.constants.GENTLE_ARC_CTRL2_OFFSET_RATIO
        ctrl2 = Point(ctrl2_x, ctrl2_y)
        return [from_pos, ctrl1, ctrl2, connection_point, extended_end]

    def _calculate_s_curve_path(
        self,
        from_pos: Point,
        rail_x: float,
        y_offset: float,
        connection_point: Point,
        extended_end: Point,
    ) -> list[Point]:
        """
        Calculate smooth S-curve path for wires with vertical separation.

        Args:
            from_pos: Starting position (board pin)
            rail_x: X position for the vertical routing rail
            y_offset: Vertical offset for the curve path
            connection_point: Point where curve ends
            extended_end: Final point with pin extension

        Returns:
            List of points defining the S-curve path
        """
        # Control point 1: starts from board, curves toward rail with dramatic fan out
        ctrl1_x = from_pos.x + (rail_x - from_pos.x) * self.constants.S_CURVE_CTRL1_RATIO
        ctrl1_y = from_pos.y + y_offset * self.constants.S_CURVE_CTRL1_OFFSET_RATIO

        # Control point 2: approaches connection point from rail with gentle convergence
        ctrl2_x = (
            connection_point.x + (rail_x - connection_point.x) * self.constants.S_CURVE_CTRL2_RATIO
        )
        ctrl2_y = connection_point.y + y_offset * self.constants.S_CURVE_CTRL2_OFFSET_RATIO

        return [
            from_pos,
            Point(ctrl1_x, ctrl1_y),  # Control point 1
            Point(ctrl2_x, ctrl2_y),  # Control point 2
            connection_point,  # End of curve
            extended_end,  # Straight segment penetrating into pin
        ]

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
        # Calculate connection points
        connection_point, extended_end = self._calculate_connection_points(to_pos)

        # Choose curve type based on vertical distance
        dy = to_pos.y - from_pos.y

        if abs(dy) < self.constants.SIMILAR_Y_THRESHOLD:
            # Wires at similar Y - use gentle horizontal arc
            return self._calculate_gentle_arc_path(
                from_pos, rail_x, y_offset, connection_point, extended_end
            )
        else:
            # Wires with vertical separation - use smooth S-curve
            return self._calculate_s_curve_path(
                from_pos, rail_x, y_offset, connection_point, extended_end
            )

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
        max_y = self._board_margin_top + diagram.board.height

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

        # Add uniform padding around all content
        canvas_width = max_x + self.config.canvas_padding
        canvas_height = max_y + self.config.canvas_padding

        # Add extra space for device specifications table if needed
        # Table is positioned below the bottommost element (device or board)
        if diagram.show_legend:
            devices_with_specs = [d for d in diagram.devices if d.description]
            if devices_with_specs:
                # Find the bottommost element
                board_bottom = self._board_margin_top + diagram.board.height
                device_bottom = max_y  # Already calculated above from devices
                max_bottom = max(board_bottom, device_bottom)

                # Table position: below bottommost element + margin
                table_y = max_bottom + self.config.specs_table_top_margin

                # Table height: header (35px) + rows (varies with multiline descriptions)
                # Use realistic estimate matching render_svg.py base row height
                header_height = 35
                base_row_height = 30  # Base height per row (single line)
                table_height = header_height + (len(devices_with_specs) * base_row_height)
                table_bottom = table_y + table_height

                # Ensure canvas is tall enough for the table
                canvas_height = max(canvas_height, table_bottom + self.config.canvas_padding)

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
        # Cubic Bezier curve followed by straight line into pin
        # This ensures the wire visually connects directly into the device pin
        # points[0] = start, points[1] = ctrl1, points[2] = ctrl2
        # points[3] = connection point, points[4] = pin center

        # Smooth cubic Bezier using middle two points as control points
        path_parts.append(
            f"C {points[1].x:.2f},{points[1].y:.2f} "
            f"{points[2].x:.2f},{points[2].y:.2f} "
            f"{points[3].x:.2f},{points[3].y:.2f}"
        )

        # Straight line segment into the pin for clear visual connection
        path_parts.append(f"L {points[4].x:.2f},{points[4].y:.2f}")
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
