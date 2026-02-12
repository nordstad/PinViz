"""Layout data types and configuration."""

from dataclasses import dataclass

from ..model import Connection, Device, Point


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
        warn_connections: Threshold for connection count warning (default: 30)
        warn_devices: Threshold for device count warning (default: 20)
        max_connections: Hard limit for connection count, None = unlimited (default: None)
        max_devices: Hard limit for device count, None = unlimited (default: None)
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
    # Complexity thresholds
    warn_connections: int = 30  # Warn if connections exceed this
    warn_devices: int = 20  # Warn if devices exceed this
    max_connections: int | None = None  # Hard limit for connections (None = unlimited)
    max_devices: int | None = None  # Hard limit for devices (None = unlimited)

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
class LayoutResult:
    """
    Complete layout information for a diagram.

    Contains all calculated layout data including canvas dimensions, positioned
    devices, and routed wires. This is the immutable output of the layout engine
    that gets passed to the renderer.

    This decouples layout calculation from rendering, enabling:
    - Independent testing of layout logic
    - Alternative layout algorithms
    - Layout result caching
    - Thread-safe parallel rendering

    Attributes:
        canvas_width: Calculated canvas width in SVG units
        canvas_height: Calculated canvas height in SVG units
        board_position: Absolute position of the board on canvas
        device_positions: Mapping of device names to their absolute positions
        routed_wires: List of wires with calculated routing paths
        board_margin_top: Top margin of the board (needed for pin positioning)
    """

    canvas_width: float
    canvas_height: float
    board_position: Point
    device_positions: dict[str, Point]
    routed_wires: list[RoutedWire]
    board_margin_top: float


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
