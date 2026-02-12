"""Device positioning logic for multi-tier layouts."""

from ..connection_graph import ConnectionGraph
from ..constants import LAYOUT_ADJUSTMENTS
from ..model import Device, Diagram, Point
from .types import LayoutConfig


class DevicePositioner:
    """
    Positions devices across horizontal tiers based on connection depth.

    Handles multi-tier layout where devices are arranged in columns (tiers)
    based on their hierarchical level in the connection graph. Within each
    tier, devices are stacked vertically with smart positioning based on
    their pin connections.
    """

    def __init__(self, config: LayoutConfig, board_margin_top: float):
        """
        Initialize device positioner.

        Args:
            config: Layout configuration parameters
            board_margin_top: Top margin for the board
        """
        self.config = config
        self.board_margin_top = board_margin_top

    def position_devices(self, diagram: Diagram) -> None:
        """
        Position all devices in the diagram across horizontal tiers.

        Calculates device levels from connection graph, assigns X positions
        for each tier, then positions devices vertically within each tier.

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

        # Position devices within each tier
        for level, devices_at_level in devices_by_level.items():
            tier_x = tier_positions[level]

            # Set X positions first
            for device in devices_at_level:
                device.position = Point(tier_x, 0)  # Y will be set below

            # Apply smart vertical positioning (works for all board types)
            self._position_devices_vertically_smart(devices_at_level, diagram)

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
        board_top = self.board_margin_top
        board_bottom = self.board_margin_top + diagram.board.height
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
                    pin_y = self.board_margin_top + board_pin.position.y
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
            return self.board_margin_top

        # Find the topmost pin that has connections
        connected_pins = set()
        for conn in diagram.connections:
            if conn.board_pin is not None:
                connected_pins.add(conn.board_pin)

        if not connected_pins:
            return self.board_margin_top

        # Get Y positions of connected pins
        min_pin_y = float("inf")
        for pin_num in connected_pins:
            pin = diagram.board.get_pin_by_number(pin_num)
            if pin and pin.position:
                pin_y = self.board_margin_top + pin.position.y
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
