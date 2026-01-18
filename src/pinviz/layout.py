"""Layout engine for positioning components and routing wires."""

import logging
import math
from dataclasses import dataclass

from .connection_graph import ConnectionGraph
from .constants import LAYOUT_ADJUSTMENTS, TABLE_LAYOUT
from .model import Connection, Device, Diagram, Point, WireStyle

logger = logging.getLogger(__name__)


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
        tier_spacing: Horizontal spacing between device tiers (default: 200.0)
        min_canvas_width: Minimum canvas width (default: 400.0)
        min_canvas_height: Minimum canvas height (default: 300.0)
        max_canvas_width: Maximum canvas width (default: 5000.0)
        max_canvas_height: Maximum canvas height (default: 3000.0)
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
    tier_spacing: float = 200.0  # Horizontal spacing between device tiers
    min_canvas_width: float = 400.0  # Minimum canvas width
    min_canvas_height: float = 300.0  # Minimum canvas height
    max_canvas_width: float = 5000.0  # Maximum canvas width
    max_canvas_height: float = 3000.0  # Maximum canvas height

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
    MAX_ADJUSTMENT: float = 50.0  # Maximum total adjustment per wire to prevent unbounded offsets

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
        source_device: The source device (None for board-to-device connections)
        is_source_right_side: True if source pin is on right side of device
        is_target_right_side: True if target pin is on right side of device
    """

    connection: Connection
    from_pos: Point
    to_pos: Point
    color: str
    device: Device
    source_device: Device | None = None
    is_source_right_side: bool = False
    is_target_right_side: bool = False


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

        # Position devices across multiple tiers based on connection depth
        self._position_devices_by_level(diagram)

        # Route all wires
        routed_wires = self._route_wires(diagram)

        # Calculate canvas size
        canvas_width, canvas_height = self._calculate_canvas_size(diagram, routed_wires)

        # Validate layout and log warnings
        validation_issues = self.validate_layout(diagram, canvas_width, canvas_height)
        wire_clearance_issues = self._validate_wire_clearance(diagram, routed_wires)
        all_issues = validation_issues + wire_clearance_issues
        for issue in all_issues:
            logger.warning(f"Layout validation: {issue}")

        return canvas_width, canvas_height, routed_wires

    def _calculate_device_levels(self, diagram: Diagram) -> dict[str, int]:
        """
        Calculate level for each device using connection graph.

        Returns:
            Dictionary mapping device names to their hierarchical levels.
        """
        graph = ConnectionGraph(diagram.devices, diagram.connections)
        return graph.calculate_device_levels()

    def _calculate_tier_positions(
        self, device_levels: dict[str, int], devices: list[Device]
    ) -> dict[int, float]:
        """
        Calculate X position for each device tier.

        Args:
            device_levels: Mapping of device names to their hierarchical levels
            devices: List of all devices in the diagram

        Returns:
            Mapping from level number to X coordinate.
        """
        tier_positions = {}
        current_x = self.config.device_area_left

        max_level = max(device_levels.values()) if device_levels else 0

        for level in range(max_level + 1):
            # Get devices at this level
            devices_at_level = [d for d in devices if device_levels.get(d.name, -1) == level]

            # Store tier X position
            tier_positions[level] = current_x

            # Calculate max device width at this level
            if devices_at_level:
                max_width = max(d.width for d in devices_at_level)
                current_x += max_width + self.config.tier_spacing
            else:
                # Empty level, skip but add minimal spacing
                current_x += self.config.tier_spacing

        return tier_positions

    def _is_horizontal_layout_board(self, diagram: Diagram) -> bool:
        """
        Detect if board has horizontal/dual-sided layout (like Pico, ESP32).

        Horizontal layout boards have pins on top and bottom edges,
        vs. vertical layout boards (Pi 4/5) with pins in columns on one side.

        Returns:
            True if board has horizontal layout (dual headers), False otherwise
        """
        # Check if any pin has a 'header' attribute (top/bottom)
        # This indicates a dual-header horizontal layout board
        if diagram.board.pins:
            # Sample first few pins to check for header attribute
            for pin in diagram.board.pins[:5]:
                if hasattr(pin, "header") and pin.header in ("top", "bottom"):
                    return True
        return False

    def _get_board_vertical_range(self, diagram: Diagram) -> tuple[float, float]:
        """
        Get the vertical range of the board in absolute coordinates.

        Works for all board types:
        - Pi 5/Pi 4: Uses full board height (220px)
        - Pico: Uses full board height (101px)

        Returns:
            (board_top_y, board_bottom_y) in absolute canvas coordinates
        """
        board_top = self._board_margin_top
        board_bottom = self._board_margin_top + diagram.board.height
        return board_top, board_bottom

    def _calculate_device_target_y(self, device: Device, diagram: Diagram) -> float:
        """
        Calculate the ideal Y position for a device based on its connections.

        Board-agnostic approach:
        - Collects Y positions of all connected pins (uses pin.position.y)
        - Returns centroid (average) of these Y positions
        - Works for vertical pin arrays (Pi) and horizontal rows (Pico)

        Examples:
        - Pi 5: Device connects to pins at y=16, y=28, y=40 → target_y = 28
        - Pico: Device connects to top row (y=6.5) → target_y = 6.5
        - Pico: Device connects to top and bottom → target_y ≈ 50 (middle)
        """
        y_positions = []

        for conn in diagram.connections:
            if conn.device_name != device.name:
                continue

            # Board-to-device connection
            if conn.board_pin is not None:
                board_pin = diagram.board.get_pin_by_number(conn.board_pin)
                if board_pin and board_pin.position:
                    # Use pin's Y position (works for all board layouts)
                    pin_y = self._board_margin_top + board_pin.position.y
                    y_positions.append(pin_y)

            # Device-to-device connection
            elif conn.source_device is not None:
                source_dev = next(
                    (d for d in diagram.devices if d.name == conn.source_device),
                    None,
                )
                if source_dev and source_dev.position.y > 0:
                    # Use source device's center Y
                    source_center_y = source_dev.position.y + source_dev.height / 2
                    y_positions.append(source_center_y)

        # Return centroid or fallback to middle of board
        if y_positions:
            return sum(y_positions) / len(y_positions)
        else:
            # Fallback: center of board
            board_top, board_bottom = self._get_board_vertical_range(diagram)
            return (board_top + board_bottom) / 2

    def _calculate_min_device_y(self, diagram: Diagram) -> float:
        """
        Calculate minimum Y position for devices to avoid title overlap.

        Works for all board types:
        - Finds the topmost connected pin (min Y value)
        - Ensures title + 50px clearance is maintained
        - Returns the safe minimum Y for device positioning
        """
        if not diagram.show_title:
            return self._board_margin_top

        # Find the topmost pin that has connections
        connected_pins = set()
        for conn in diagram.connections:
            if conn.board_pin is not None:
                connected_pins.add(conn.board_pin)

        if not connected_pins:
            return self._board_margin_top

        # Get Y positions of connected pins
        min_pin_y = float("inf")
        for pin_num in connected_pins:
            pin = diagram.board.get_pin_by_number(pin_num)
            if pin and pin.position:
                pin_y = self._board_margin_top + pin.position.y
                min_pin_y = min(min_pin_y, pin_y)

        # Title clearance: title bottom + 50px margin
        title_bottom = self.config.board_margin_top_base + self.config.title_height
        min_y_with_clearance = title_bottom + self.config.title_margin

        # Use the greater of: title clearance or topmost pin
        return max(
            min_y_with_clearance,
            min_pin_y - LAYOUT_ADJUSTMENTS.DEVICE_ABOVE_PIN_ALLOWANCE,
        )

    def _position_with_target_y(
        self,
        device_targets: list[tuple[Device, float]],
        min_y: float,
        max_y: float,
        min_spacing: float,
    ) -> None:
        """Position devices at their target Y with collision avoidance."""
        current_y = min_y

        for device, target_y in device_targets:
            # Try to honor target, but don't go below current_y (avoid overlap)
            adjusted_y = max(current_y, target_y)

            device.position = Point(device.position.x, adjusted_y)
            current_y = adjusted_y + device.height + min_spacing

    def _position_evenly_distributed(
        self,
        device_targets: list[tuple[Device, float]],
        min_y: float,
        max_y: float,
    ) -> None:
        """Distribute devices evenly when space is limited."""
        if len(device_targets) == 1:
            # Single device - center vertically
            device, _ = device_targets[0]
            center_y = (min_y + max_y) / 2
            device_y = center_y - device.height / 2
            device.position = Point(device.position.x, device_y)
        else:
            # Multiple devices - distribute with appropriate spacing
            total_device_height = sum(d.height for d, _ in device_targets)
            available_height = max_y - min_y
            num_gaps = len(device_targets) - 1

            # Calculate spacing
            if num_gaps > 0:
                if total_device_height <= available_height:
                    # Enough space - distribute evenly
                    spacing = (available_height - total_device_height) / num_gaps
                else:
                    # Not enough space - use minimum spacing and extend beyond max_y
                    spacing = self.config.device_spacing_vertical
            else:
                spacing = 0

            current_y = min_y
            for device, _ in device_targets:
                device.position = Point(device.position.x, current_y)
                current_y += device.height + spacing

    def _position_devices_vertically_smart(
        self,
        devices_at_level: list[Device],
        diagram: Diagram,
    ) -> None:
        """
        Position devices vertically based on their pin connections.

        Board-agnostic algorithm:
        1. Calculate target Y for each device (connection centroid)
        2. Sort devices by target Y
        3. Determine constraints (min Y from title, max Y from board bottom)
        4. Position devices respecting targets while maintaining spacing

        Handles all board types correctly because it uses pin.position.y values.
        """
        if not devices_at_level:
            return

        # Step 1: Calculate target Y for each device
        device_targets = []
        for device in devices_at_level:
            target_y = self._calculate_device_target_y(device, diagram)
            device_targets.append((device, target_y))

        # Step 2: Sort by target Y (top to bottom)
        device_targets.sort(key=lambda x: x[1])

        # Step 3: Get constraints
        board_top, board_bottom = self._get_board_vertical_range(diagram)
        min_device_y = self._calculate_min_device_y(diagram)

        # Step 4: Calculate space requirements
        total_device_height = sum(d.height for d, _ in device_targets)
        num_gaps = len(device_targets) - 1
        min_spacing = self.config.device_spacing_vertical
        total_min_spacing = num_gaps * min_spacing if num_gaps > 0 else 0
        total_height_needed = total_device_height + total_min_spacing

        # Step 5: Calculate max_device_y based on board layout type
        is_horizontal_layout = self._is_horizontal_layout_board(diagram)

        if is_horizontal_layout:
            # Horizontal layout boards (Pico, ESP32): Allow devices to extend beyond board
            # These boards are typically shorter and have pins on top/bottom
            max_device_y = (
                min_device_y
                + total_height_needed
                + LAYOUT_ADJUSTMENTS.HORIZONTAL_BOARD_EXTRA_MARGIN
            )
        else:
            # Vertical layout boards (Pi 4/5): Try to fit within board height
            available_height_at_board = board_bottom - min_device_y
            if total_height_needed <= available_height_at_board:
                # Devices fit - use board bottom as constraint
                max_device_y = board_bottom
            else:
                # Devices don't fit - allow extending beyond board
                max_device_y = min_device_y + total_height_needed

        available_height = max_device_y - min_device_y

        # Step 6: Position devices
        if total_height_needed <= available_height:
            # Enough space - position at target Y with adjustments
            self._position_with_target_y(device_targets, min_device_y, max_device_y, min_spacing)
        else:
            # Limited space - even distribution
            self._position_evenly_distributed(device_targets, min_device_y, max_device_y)

    def _position_devices_by_level(self, diagram: Diagram) -> None:
        """
        Position devices across horizontal tiers based on connection depth.

        Devices are positioned in tiers (columns) based on their hierarchical level
        in the connection graph. Within each tier, devices are stacked vertically.

        Args:
            diagram: The diagram containing devices and connections

        Note:
            This method mutates the position attribute of each device.
        """
        # Calculate device levels from connection graph
        device_levels = self._calculate_device_levels(diagram)

        # Calculate X position for each tier
        tier_positions = self._calculate_tier_positions(device_levels, diagram.devices)

        # Group devices by level
        devices_by_level: dict[int, list[Device]] = {}
        for device in diagram.devices:
            level = device_levels.get(device.name, 0)
            if level not in devices_by_level:
                devices_by_level[level] = []
            devices_by_level[level].append(device)

        # Position devices within each tier (NEW: smart vertical positioning)
        for level, devices_at_level in devices_by_level.items():
            tier_x = tier_positions[level]

            # Set X positions first
            for device in devices_at_level:
                device.position = Point(tier_x, 0)  # Y will be set below

            # Apply smart vertical positioning (works for all board types)
            self._position_devices_vertically_smart(devices_at_level, diagram)

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
                from .model import DEFAULT_COLORS

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
                    self.config.board_margin_left + board_pin.position.x,
                    self._board_margin_top + board_pin.position.y,
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
                from .model import DEFAULT_COLORS

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
                    "source_device": wire.source_device,
                    "is_source_right_side": wire.is_source_right_side,
                    "is_target_right_side": wire.is_target_right_side,
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
        import time

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

    def _calculate_canvas_size(
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
        max_y = self._board_margin_top + diagram.board.height

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
                board_bottom = self._board_margin_top + diagram.board.height
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

    def _rectangles_overlap(
        self, rect1: tuple[float, float, float, float], rect2: tuple[float, float, float, float]
    ) -> bool:
        """
        Check if two rectangles overlap.

        Args:
            rect1: Rectangle as (x1, y1, x2, y2) where x2 > x1 and y2 > y1
            rect2: Rectangle as (x1, y1, x2, y2) where x2 > x1 and y2 > y1

        Returns:
            True if rectangles overlap, False otherwise
        """
        x1_min, y1_min, x1_max, y1_max = rect1
        x2_min, y2_min, x2_max, y2_max = rect2

        # Rectangles overlap if they're not completely separated
        return not (x1_max <= x2_min or x2_max <= x1_min or y1_max <= y2_min or y2_max <= y1_min)

    def _validate_wire_clearance(
        self,
        diagram: Diagram,
        routed_wires: list[RoutedWire],
    ) -> list[str]:
        """Validate that wires maintain clearance from title."""
        issues = []

        if not diagram.show_title:
            return issues

        # Calculate title bottom
        title_bottom = self.config.board_margin_top_base + self.config.title_height
        required_clearance = self.config.title_margin  # 50px
        min_safe_y = title_bottom + required_clearance

        # Find the topmost wire point
        min_wire_y = float("inf")
        for wire in routed_wires:
            for point in wire.path_points:
                min_wire_y = min(min_wire_y, point.y)

        if min_wire_y < min_safe_y:
            clearance = min_wire_y - title_bottom
            issues.append(
                f"Wire clearance warning: Wires are {clearance:.1f}px from title "
                f"(recommended: {required_clearance}px). Consider adjusting layout."
            )

        return issues

    def validate_layout(
        self, diagram: Diagram, canvas_width: float, canvas_height: float
    ) -> list[str]:
        """
        Validate calculated layout for issues.

        Checks for:
        - Device overlaps
        - Devices positioned at negative coordinates
        - Devices extending beyond canvas bounds

        Args:
            diagram: The diagram with positioned devices
            canvas_width: Canvas width
            canvas_height: Canvas height

        Returns:
            List of validation warnings/errors (empty if no issues)
        """
        issues = []

        # Check for device overlaps
        for i, dev1 in enumerate(diagram.devices):
            pos1 = dev1.position
            rect1 = (pos1.x, pos1.y, pos1.x + dev1.width, pos1.y + dev1.height)

            for dev2 in diagram.devices[i + 1 :]:
                pos2 = dev2.position
                rect2 = (pos2.x, pos2.y, pos2.x + dev2.width, pos2.y + dev2.height)

                if self._rectangles_overlap(rect1, rect2):
                    issues.append(f"Devices '{dev1.name}' and '{dev2.name}' overlap")

        # Check for out-of-bounds devices
        for device in diagram.devices:
            pos = device.position
            if pos.x < 0 or pos.y < 0:
                issues.append(f"Device '{device.name}' positioned at negative coordinates")

            if pos.x + device.width > canvas_width:
                issues.append(f"Device '{device.name}' extends beyond canvas width")

            if pos.y + device.height > canvas_height:
                issues.append(f"Device '{device.name}' extends beyond canvas height")

        return issues


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
