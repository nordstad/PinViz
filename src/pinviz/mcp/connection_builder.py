"""Connection Builder for PinViz MCP Server."""

from pinviz.board_selection import AliasBoardSelectionStrategy, BoardSelectionStrategy
from pinviz.diagram_builder import DiagramBuilder
from pinviz.model import DEFAULT_COLORS, Board, Connection, Device, Diagram
from pinviz.pin_assignment import PinAssignment

from .adapters import McpDeviceAdapter


class ConnectionBuilder:
    """
    Builds PinViz Diagram objects from pin assignments.

    Takes pin assignments and device data, then generates:
    - Device objects with positioned pins
    - Connection objects with auto-assigned wire colors
    - Complete Diagram object ready for rendering
    """

    def __init__(
        self,
        board_selection_strategy: BoardSelectionStrategy | None = None,
        device_adapter: McpDeviceAdapter | None = None,
    ):
        """Initialize the connection builder."""
        self._board_selection_strategy = board_selection_strategy or AliasBoardSelectionStrategy(
            fallback_board_name="raspberry_pi_5"
        )
        self._device_adapter = device_adapter or McpDeviceAdapter()

    def build_diagram(
        self,
        assignments: list[PinAssignment],
        devices_data: list[dict],
        board_name: str = "raspberry_pi_5",
        title: str = "GPIO Wiring Diagram",
        board: Board | None = None,
    ) -> Diagram:
        """
        Build a complete Diagram from pin assignments.

        Args:
            assignments: List of PinAssignment objects
            devices_data: List of device dictionaries from database
            board_name: Board type (default: "raspberry_pi_5")
            title: Diagram title
            board: Pre-loaded Board object (avoids redundant lookup)

        Returns:
            Complete Diagram object ready for rendering
        """
        # Build Device objects
        devices = self._build_devices(devices_data)

        # Build Connection objects
        connections = self._build_connections(assignments)

        # Create diagram through the shared builder so MCP assembly matches
        # config-based assembly semantics.
        builder = (
            DiagramBuilder(self._board_selection_strategy)
            .with_title(title)
            .with_devices(devices)
            .with_connections(connections)
        )
        if board is not None:
            builder.with_board(board)
        else:
            builder.with_board_name(board_name)
        return builder.build()

    def _get_board(self, board_name: str):
        """Get board object by name."""
        return self._board_selection_strategy.select_board(board_name)

    def _build_devices(self, devices_data: list[dict]) -> list[Device]:
        """Build Device objects from device data.

        First tries to load from device registry (device_configs/ or Python factories),
        then falls back to manual construction from MCP database data.
        """
        return self._device_adapter.adapt_many(devices_data)

    def _build_connections(self, assignments: list[PinAssignment]) -> list[Connection]:
        """Build Connection objects from pin assignments."""
        connections = []

        for assignment in assignments:
            # Auto-assign wire color based on pin role
            color = DEFAULT_COLORS.get(assignment.pin_role, "#808080")

            connection = Connection(
                board_pin=assignment.board_pin_number,
                device_name=assignment.device_name,
                device_pin_name=assignment.device_pin_name,
                color=color,
                style="mixed",  # Use mixed style for nice routing
                components=assignment.components,  # Pass through inline components
            )
            connections.append(connection)

        return connections

    def _get_device_color(self, device_data: dict) -> str:
        """Get device color based on category."""
        return self._device_adapter.get_device_color(device_data.get("category"))


def build_diagram_from_assignments(
    assignments: list[PinAssignment],
    devices_data: list[dict],
    board_name: str = "raspberry_pi_5",
    title: str = "GPIO Wiring Diagram",
) -> Diagram:
    """
    Convenience function to build a diagram from assignments.

    Args:
        assignments: List of PinAssignment objects
        devices_data: List of device dictionaries
        board_name: Board type
        title: Diagram title

    Returns:
        Complete Diagram object
    """
    builder = ConnectionBuilder()
    return builder.build_diagram(assignments, devices_data, board_name, title)
