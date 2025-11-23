"""
Connection Builder for PinViz MCP Server.

This module converts pin assignments into PinViz Connection objects and generates
complete Diagram objects ready for rendering.
"""

from pinviz import boards
from pinviz.mcp.pin_assignment import PinAssignment
from pinviz.model import DEFAULT_COLORS, Connection, Device, DevicePin, Diagram, Point


class ConnectionBuilder:
    """
    Builds PinViz Diagram objects from pin assignments.

    Takes pin assignments and device data, then generates:
    - Device objects with positioned pins
    - Connection objects with auto-assigned wire colors
    - Complete Diagram object ready for rendering
    """

    def __init__(self):
        """Initialize the connection builder."""
        pass

    def build_diagram(
        self,
        assignments: list[PinAssignment],
        devices_data: list[dict],
        board_name: str = "raspberry_pi_5",
        title: str = "GPIO Wiring Diagram",
    ) -> Diagram:
        """
        Build a complete Diagram from pin assignments.

        Args:
            assignments: List of PinAssignment objects
            devices_data: List of device dictionaries from database
            board_name: Board type (default: "raspberry_pi_5")
            title: Diagram title

        Returns:
            Complete Diagram object ready for rendering
        """
        # Get board
        board = self._get_board(board_name)

        # Build Device objects
        devices = self._build_devices(devices_data)

        # Build Connection objects
        connections = self._build_connections(assignments)

        # Create diagram
        diagram = Diagram(
            title=title,
            board=board,
            devices=devices,
            connections=connections,
            show_legend=True,
        )

        return diagram

    def _get_board(self, board_name: str):
        """Get board object by name."""
        if board_name == "raspberry_pi_5":
            return boards.raspberry_pi_5()
        else:
            # Default to Raspberry Pi 5
            return boards.raspberry_pi_5()

    def _build_devices(self, devices_data: list[dict]) -> list[Device]:
        """Build Device objects from device data."""
        devices = []

        for device_data in devices_data:
            device_name = device_data["name"]
            device_pins_data = device_data["pins"]

            # Build DevicePin objects
            device_pins = []
            for i, pin_data in enumerate(device_pins_data):
                pin = DevicePin(
                    name=pin_data["name"],
                    role=pin_data["role"],
                    position=Point(0, i * 10),  # Simple vertical spacing
                )
                device_pins.append(pin)

            # Create Device
            device = Device(
                name=device_name,
                pins=device_pins,
                width=120.0,
                height=max(60.0, len(device_pins) * 10 + 20),
                position=Point(0, 0),  # Will be set by layout engine
                color=self._get_device_color(device_data),
            )
            devices.append(device)

        return devices

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
            )
            connections.append(connection)

        return connections

    def _get_device_color(self, device_data: dict) -> str:
        """Get device color based on category."""
        category = device_data.get("category", "")

        color_map = {
            "display": "#4A90E2",  # Blue
            "sensor": "#50E3C2",  # Turquoise
            "actuator": "#F5A623",  # Orange
            "hat": "#BD10E0",  # Purple
            "breakout": "#7ED321",  # Green
            "component": "#F8E71C",  # Yellow
        }

        return color_map.get(category, "#4A90E2")  # Default blue


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
