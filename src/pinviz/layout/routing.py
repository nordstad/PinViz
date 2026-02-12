"""Wire routing logic for diagram connections."""

import logging
import math
import time

from ..model import DEFAULT_COLORS, Diagram, Point, WireStyle
from .types import LayoutConfig, LayoutConstants, RoutedWire, WireData

logger = logging.getLogger(__name__)


class WireRouter:
    """
    Routes wires between board pins and device pins.

    Implements device-based routing lanes where each device gets its own
    vertical "rail" for routing wires. This prevents wire crossings and
    maintains visual clarity similar to Fritzing diagrams.

    Features:
    - Automatic offset for parallel wires from the same pin
    - Smooth Bezier curves for professional appearance
    - Conflict detection and resolution
    - Support for device-to-device connections
    """

    def __init__(self, config: LayoutConfig, board_margin_left: float, board_margin_top: float):
        """
        Initialize wire router.

        Args:
            config: Layout configuration parameters
            board_margin_left: Left margin for the board
            board_margin_top: Top margin for the board
        """
        self.config = config
        self.constants = LayoutConstants()
        self.board_margin_left = board_margin_left
        self.board_margin_top = board_margin_top

    def route_wires(self, diagram: Diagram) -> list[RoutedWire]:
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

    def _collect_wire_data(self, diagram: Diagram) -> list[WireData]:
        """
        Collect wire connection data from the diagram.

        First pass: Gathers information about each connection including pin positions,
        device references, and wire colors. This prepares all the data needed for
        the wire routing algorithm.

        Handles both board-to-device and device-to-device connections.

        Args:
            diagram: The diagram containing connections, board, and devices

        Returns:
            List of WireData objects with resolved positions and colors
        """
        wire_data: list[WireData] = []

        # Build device lookup dictionary for O(1) access (performance optimization)
        device_by_name = {device.name: device for device in diagram.devices}

        for conn in diagram.connections:
            # Determine connection type: board-to-device or device-to-device
            is_device_to_device = conn.source_device is not None

            # Find the target device by name (using O(1) dictionary lookup)
            target_device = device_by_name.get(conn.device_name)
            if not target_device:
                continue

            # Find the specific target device pin by name
            target_pin = target_device.get_pin_by_name(conn.device_pin_name)
            if not target_pin:
                continue

            if is_device_to_device:
                # Device-to-device connection
                source_device = device_by_name.get(conn.source_device)
                if not source_device:
                    continue

                source_pin = source_device.get_pin_by_name(conn.source_pin)
                if not source_pin:
                    continue

                # Calculate absolute positions for device-to-device connection
                from_pos = Point(
                    source_device.position.x + source_pin.position.x,
                    source_device.position.y + source_pin.position.y,
                )
                to_pos = Point(
                    target_device.position.x + target_pin.position.x,
                    target_device.position.y + target_pin.position.y,
                )

                # Detect if pins are on right side of their respective devices
                is_source_right_side = source_pin.position.x > (source_device.width / 2)
                is_target_right_side = target_pin.position.x > (target_device.width / 2)

                # Use source pin role for color if no explicit color
                if conn.color:
                    color = conn.color.value if hasattr(conn.color, "value") else conn.color
                else:
                    color = DEFAULT_COLORS.get(source_pin.role, "#808080")

                wire_data.append(
                    WireData(
                        conn,
                        from_pos,
                        to_pos,
                        color,
                        target_device,
                        source_device,
                        is_source_right_side,
                        is_target_right_side,
                    )
                )

            else:
                # Board-to-device connection
                board_pin = diagram.board.get_pin_by_number(conn.board_pin)
                if not board_pin or not board_pin.position:
                    continue

                # Calculate absolute position of board pin
                # (board position is offset by margins)
                from_pos = Point(
                    self.board_margin_left + board_pin.position.x,
                    self.board_margin_top + board_pin.position.y,
                )

                # Calculate absolute position of device pin
                # (device pins are relative to device position)
                to_pos = Point(
                    target_device.position.x + target_pin.position.x,
                    target_device.position.y + target_pin.position.y,
                )

                # Detect if target pin is on right side of device
                is_target_right_side = target_pin.position.x > (target_device.width / 2)

                # Determine wire color: use connection color if specified,
                # otherwise use default color based on pin role
                if conn.color:
                    color = conn.color.value if hasattr(conn.color, "value") else conn.color
                else:
                    color = DEFAULT_COLORS.get(board_pin.role, "#808080")

                wire_data.append(
                    WireData(
                        conn,
                        from_pos,
                        to_pos,
                        color,
                        target_device,
                        None,
                        False,
                        is_target_right_side,
                    )
                )

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
        board_right_edge = self.board_margin_left + board_width
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
                    "source_device": wire.source_device,
                    "is_source_right_side": wire.is_source_right_side,
                    "is_target_right_side": wire.is_target_right_side,
                }
            )

        return initial_wires

    def _detect_and_resolve_overlaps(self, wires: list[dict]) -> dict[int, float]:
        """
        Detect overlapping wire paths and calculate offset adjustments.

        Samples points along each wire path and checks for overlaps.
        Returns adjustments to y_offset for each wire to minimize overlaps.

        Performance: Uses bounding box quick rejection to filter out non-overlapping
        wire pairs before expensive distance calculations. Early exit optimization
        stops checking sample pairs once a conflict is found.

        Args:
            wires: List of wire info dicts with positions and initial offsets

        Returns:
            Dictionary mapping wire_idx to y_offset adjustment
        """
        start_time = time.perf_counter()
        adjustments = {}
        min_separation = (
            self.config.wire_spacing * self.constants.MIN_SEPARATION_MULTIPLIER
        )  # Minimum desired separation

        # Performance tracking
        total_wire_pairs = 0
        bbox_rejections = 0
        distance_checks = 0

        # Sample points along each wire's potential path and calculate bounding boxes
        wire_samples = []
        for wire in wires:
            # Create initial path to analyze
            path_points = self._calculate_wire_path_device_zone(
                wire["from_pos"],
                wire["to_pos"],
                wire["rail_x"],
                wire["y_offset"],
                wire["conn"].style,
                wire["is_source_right_side"],
                wire["is_target_right_side"],
            )

            # Sample points along the path (simplified - use path points directly)
            samples = []
            min_x = float("inf")
            max_x = float("-inf")
            min_y = float("inf")
            max_y = float("-inf")

            for i in range(len(path_points) - 1):
                p1, p2 = path_points[i], path_points[i + 1]
                # Sample points between each pair
                for t in self.constants.SAMPLE_POSITIONS:
                    x = p1.x + (p2.x - p1.x) * t
                    y = p1.y + (p2.y - p1.y) * t
                    samples.append((x, y))
                    # Update bounding box
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)

            wire_samples.append(
                {
                    "wire_idx": wire["wire_idx"],
                    "samples": samples,
                    "from_y": wire["from_pos"].y,
                    "bbox": (min_x, max_x, min_y, max_y),
                }
            )

        # Detect conflicts between wire pairs
        conflicts = []
        for i in range(len(wire_samples)):
            for j in range(i + 1, len(wire_samples)):
                total_wire_pairs += 1
                wire_a = wire_samples[i]
                wire_b = wire_samples[j]

                # Check if wires have similar starting Y (potential overlap)
                if (
                    abs(wire_a["from_y"] - wire_b["from_y"])
                    > self.constants.FROM_Y_POSITION_TOLERANCE
                ):
                    bbox_rejections += 1
                    continue  # Wires start far apart, unlikely to conflict

                # Quick rejection using bounding boxes (O(1) check)
                # If bounding boxes don't overlap (with margin), wires can't conflict
                bbox_a = wire_a["bbox"]
                bbox_b = wire_b["bbox"]
                bbox_margin = min_separation

                # Check if bounding boxes overlap (with margin)
                if (
                    bbox_a[1] + bbox_margin < bbox_b[0]  # a_max_x + margin < b_min_x
                    or bbox_b[1] + bbox_margin < bbox_a[0]  # b_max_x + margin < a_min_x
                    or bbox_a[3] + bbox_margin < bbox_b[2]  # a_max_y + margin < b_min_y
                    or bbox_b[3] + bbox_margin < bbox_a[2]  # b_max_y + margin < a_min_y
                ):
                    bbox_rejections += 1
                    continue  # Bounding boxes don't overlap, skip expensive check

                # Bounding boxes overlap - need to check distances
                distance_checks += 1

                # Check minimum distance between sampled points (only if bounding boxes overlap)
                # Early exit optimization: stop checking as soon as we find a conflict
                min_dist = float("inf")
                found_conflict = False
                for pa in wire_a["samples"]:
                    for pb in wire_b["samples"]:
                        dist = math.sqrt((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2)
                        if dist < min_separation:
                            # Found a conflict - no need to check remaining pairs
                            min_dist = dist
                            found_conflict = True
                            break
                        min_dist = min(min_dist, dist)
                    if found_conflict:
                        break

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

            # Clamp adjustments to prevent unbounded offsets
            current_a = adjustments.get(wire_a_idx, 0.0)
            current_b = adjustments.get(wire_b_idx, 0.0)

            adjustments[wire_a_idx] = max(
                -self.constants.MAX_ADJUSTMENT,
                min(self.constants.MAX_ADJUSTMENT, current_a - adjustment_amount),
            )
            adjustments[wire_b_idx] = max(
                -self.constants.MAX_ADJUSTMENT,
                min(self.constants.MAX_ADJUSTMENT, current_b + adjustment_amount),
            )

        # Performance logging
        elapsed_time = time.perf_counter() - start_time
        if total_wire_pairs > 0:
            rejection_rate = (bbox_rejections / total_wire_pairs) * 100
            logger.debug(
                f"Wire conflict detection: {len(wires)} wires, "
                f"{total_wire_pairs} pairs checked, "
                f"{bbox_rejections} rejected ({rejection_rate:.1f}%), "
                f"{distance_checks} distance checks, "
                f"{len(conflicts)} conflicts found in {elapsed_time * 1000:.1f}ms"
            )

        return adjustments

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
                wire_info["is_source_right_side"],
                wire_info["is_target_right_side"],
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

    def _calculate_connection_points(
        self, to_pos: Point, is_right_side: bool = False
    ) -> tuple[Point, Point]:
        """
        Calculate connection and extended end points for wire routing.

        Args:
            to_pos: Target position (device pin)
            is_right_side: True if target pin is on right side of device

        Returns:
            Tuple of (connection_point, extended_end)
        """
        if is_right_side:
            # For right-side pins, wire approaches from the right
            connection_point = Point(to_pos.x + self.constants.STRAIGHT_SEGMENT_LENGTH, to_pos.y)
            # Extend inward (to the left)
            extended_end = Point(to_pos.x - self.constants.WIRE_PIN_EXTENSION, to_pos.y)
        else:
            # For left-side pins, wire approaches from the left (original behavior)
            connection_point = Point(to_pos.x - self.constants.STRAIGHT_SEGMENT_LENGTH, to_pos.y)
            # Extend inward (to the right)
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

    def _calculate_right_to_right_path(
        self,
        from_pos: Point,
        connection_point: Point,
        extended_end: Point,
        y_offset: float,
    ) -> list[Point]:
        """
        Calculate wire path for right-side output to another device (horizontal routing).

        Routes wires horizontally from right-side output pins directly to target
        devices, avoiding the left-side rail system that would cause wires to go
        underneath the source device.

        Args:
            from_pos: Starting position (already extended from right-side pin)
            connection_point: Point where curve should end near target
            extended_end: Final point penetrating into target pin
            y_offset: Vertical offset for path separation

        Returns:
            List of points defining smooth horizontal path
        """
        dy = connection_point.y - from_pos.y
        dx = connection_point.x - from_pos.x

        if abs(dy) < self.constants.SIMILAR_Y_THRESHOLD:
            # Similar Y levels - gentle horizontal arc
            mid_x = from_pos.x + dx * 0.5
            ctrl1 = Point(mid_x, from_pos.y + y_offset * 0.3)
            ctrl2 = Point(mid_x, connection_point.y + y_offset * 0.3)
        else:
            # Different Y levels - smooth S-curve
            ctrl1_x = from_pos.x + dx * 0.3
            ctrl1_y = from_pos.y + y_offset * 0.5
            ctrl2_x = from_pos.x + dx * 0.7
            ctrl2_y = connection_point.y + y_offset * 0.5
            ctrl1 = Point(ctrl1_x, ctrl1_y)
            ctrl2 = Point(ctrl2_x, ctrl2_y)

        return [from_pos, ctrl1, ctrl2, connection_point, extended_end]

    def _calculate_wire_path_device_zone(
        self,
        from_pos: Point,
        to_pos: Point,
        rail_x: float,
        y_offset: float,
        style: WireStyle,
        is_source_right_side: bool = False,
        is_target_right_side: bool = False,
    ) -> list[Point]:
        """
        Calculate wire path with organic Bezier curves.

        Creates smooth, flowing curves similar to Fritzing's style rather than
        hard orthogonal lines. Uses device-specific rail positions and vertical
        offsets to prevent overlap and crossings.

        Args:
            from_pos: Starting position (board pin or device pin)
            to_pos: Ending position (device pin)
            rail_x: X position for the vertical routing rail (device-specific)
            y_offset: Vertical offset for the curve path
            style: Wire routing style (always uses curved style now)
            is_source_right_side: True if source pin is on right side (device-to-device)
            is_target_right_side: True if target pin is on right side

        Returns:
            List of points defining the wire path with Bezier control points
        """
        # Calculate connection points for target
        connection_point, extended_end = self._calculate_connection_points(
            to_pos, is_target_right_side
        )

        # Calculate start connection point for source (device-to-device)
        if is_source_right_side:
            # For right-side source pins, extend slightly to the right
            from_pos = Point(from_pos.x + self.constants.WIRE_PIN_EXTENSION, from_pos.y)

            # Check if target is to the RIGHT (device-to-device right-to-left routing)
            if to_pos.x > from_pos.x:
                # Route directly RIGHT to the target device
                return self._calculate_right_to_right_path(
                    from_pos, connection_point, extended_end, y_offset
                )

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
