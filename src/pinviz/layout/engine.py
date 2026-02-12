"""Main layout engine orchestrator."""

from ..logging_config import get_logger
from ..model import Diagram, Point
from .positioning import DevicePositioner
from .routing import WireRouter
from .sizing import CanvasSizer
from .types import LayoutConfig, LayoutResult

log = get_logger(__name__)


class LayoutEngine:
    """
    Calculate positions and wire routing for diagram components.

    The layout engine orchestrates the algorithmic placement of devices and routing
    of wires between board pins and device pins. It coordinates three specialized
    components:
    - DevicePositioner: Handles device placement across tiers
    - WireRouter: Routes wires with smooth curves
    - CanvasSizer: Calculates canvas dimensions

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

    def _check_complexity(self, diagram: Diagram) -> None:
        """
        Check diagram complexity and log warnings or raise errors if limits exceeded.

        Args:
            diagram: The diagram to check

        Raises:
            ValueError: If diagram exceeds hard complexity limits (max_connections, max_devices)
        """
        connection_count = len(diagram.connections)
        device_count = len(diagram.devices)

        # Check hard limits first (errors)
        if (
            self.config.max_connections is not None
            and connection_count > self.config.max_connections
        ):
            log.error(
                "diagram_exceeds_max_connections",
                connection_count=connection_count,
                max_connections=self.config.max_connections,
            )
            raise ValueError(
                f"Diagram has {connection_count} connections, exceeding maximum of "
                f"{self.config.max_connections}. Split into multiple diagrams or "
                f"increase --max-complexity limit."
            )

        if self.config.max_devices is not None and device_count > self.config.max_devices:
            log.error(
                "diagram_exceeds_max_devices",
                device_count=device_count,
                max_devices=self.config.max_devices,
            )
            raise ValueError(
                f"Diagram has {device_count} devices, exceeding maximum of "
                f"{self.config.max_devices}. Split into multiple diagrams or "
                f"increase --max-complexity limit."
            )

        # Log warnings for complexity thresholds
        if connection_count > self.config.warn_connections:
            log.warning(
                "diagram_complexity_high",
                connection_count=connection_count,
                warn_threshold=self.config.warn_connections,
                message=(
                    f"Diagram has {connection_count} connections "
                    f"(>{self.config.warn_connections}). "
                    "Consider splitting into multiple diagrams for clarity and performance."
                ),
            )

        if device_count > self.config.warn_devices:
            log.warning(
                "device_count_high",
                device_count=device_count,
                warn_threshold=self.config.warn_devices,
                message=(
                    f"Diagram has {device_count} devices (>{self.config.warn_devices}). "
                    "Layout may be crowded."
                ),
            )

    def layout_diagram(self, diagram: Diagram) -> LayoutResult:
        """
        Calculate layout for a complete diagram.

        Returns a LayoutResult containing all layout information including
        canvas dimensions, device positions, and routed wires. This immutable
        result can be passed to the renderer without further diagram mutation.

        Args:
            diagram: The diagram to layout

        Returns:
            LayoutResult with complete layout information

        Note:
            For backward compatibility, this method still mutates device.position
            on the diagram's devices. Future versions will remove this mutation.
        """
        # Check complexity and log warnings/errors
        self._check_complexity(diagram)

        # Calculate actual board margin based on whether title is shown
        board_margin_top = self.config.get_board_margin_top(diagram.show_title)

        # Position devices across multiple tiers based on connection depth
        # NOTE: This still mutates diagram.devices[].position for backward compatibility
        positioner = DevicePositioner(self.config, board_margin_top)
        positioner.position_devices(diagram)

        # Route all wires
        router = WireRouter(self.config, self.config.board_margin_left, board_margin_top)
        routed_wires = router.route_wires(diagram)

        # Calculate canvas size
        sizer = CanvasSizer(self.config, board_margin_top)
        canvas_width, canvas_height = sizer.calculate_canvas_size(diagram, routed_wires)

        # Collect device positions into immutable mapping
        device_positions = {
            device.name: Point(device.position.x, device.position.y) for device in diagram.devices
        }

        # Calculate board position
        board_position = Point(self.config.board_margin_left, board_margin_top)

        # Validate layout and log warnings
        validation_issues = self.validate_layout(diagram, canvas_width, canvas_height)
        wire_clearance_issues = self._validate_wire_clearance(
            diagram, routed_wires, board_margin_top
        )
        all_issues = validation_issues + wire_clearance_issues
        for issue in all_issues:
            log.warning("layout_validation_issue", issue=issue)

        # Return immutable layout result
        return LayoutResult(
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            board_position=board_position,
            device_positions=device_positions,
            routed_wires=routed_wires,
            board_margin_top=board_margin_top,
        )

    def _validate_wire_clearance(
        self,
        diagram: Diagram,
        routed_wires: list,
        board_margin_top: float,
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
