"""Integration tests for Phase 1: Data Model, ConnectionGraph, and Validation.

This module tests the integration of Phase 1 components:
- Board configuration and pin definitions
- Device models with pin roles
- ConnectionGraph topology analysis (levels, cycles, dependencies)
- Validation (pin compatibility, voltage checks, conflicts)
- End-to-end flow from config to validated diagram
"""

from pinviz import boards
from pinviz.connection_graph import ConnectionGraph
from pinviz.devices import get_registry
from pinviz.model import Connection, Device, DevicePin, Diagram, PinRole
from pinviz.validation import DiagramValidator, ValidationLevel


class TestPhase1CoreIntegration:
    """Test integration of core Phase 1 components."""

    def test_simple_board_device_connection_flow(self):
        """Test basic flow: board -> device -> connection -> validation."""
        # Step 1: Get a board
        board = boards.raspberry_pi_5()
        assert board is not None
        assert len(board.pins) == 40

        # Step 2: Create a device
        sensor = get_registry().create("bh1750")
        assert sensor is not None
        assert len(sensor.pins) == 5  # VCC, GND, SCL, SDA, ADDR

        # Step 3: Create connections
        connections = [
            Connection(board_pin=1, device_name="BH1750 Light Sensor", device_pin_name="VCC"),
            Connection(board_pin=6, device_name="BH1750 Light Sensor", device_pin_name="GND"),
            Connection(board_pin=3, device_name="BH1750 Light Sensor", device_pin_name="SDA"),
            Connection(board_pin=5, device_name="BH1750 Light Sensor", device_pin_name="SCL"),
        ]

        # Step 4: Create diagram
        diagram = Diagram(
            title="Test Diagram",
            board=board,
            devices=[sensor],
            connections=connections,
        )

        # Step 5: Validate
        validator = DiagramValidator()
        issues = validator.validate(diagram)

        # Should have no errors
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) == 0

    def test_multi_device_shared_bus_integration(self):
        """Test multiple devices sharing I2C bus with validation."""
        board = boards.raspberry_pi_5()

        # Create two I2C devices
        device1 = get_registry().create("bh1750")
        device2 = Device(
            name="BME280",
            pins=[
                DevicePin(name="VCC", role=PinRole.POWER_3V3, position=(0, 0)),
                DevicePin(name="GND", role=PinRole.GROUND, position=(0, 10)),
                DevicePin(name="SDA", role=PinRole.I2C_SDA, position=(0, 20)),
                DevicePin(name="SCL", role=PinRole.I2C_SCL, position=(0, 30)),
            ],
        )

        # Connect both devices to same I2C bus
        connections = [
            # BH1750 connections
            Connection(board_pin=1, device_name="BH1750 Light Sensor", device_pin_name="VCC"),
            Connection(board_pin=6, device_name="BH1750 Light Sensor", device_pin_name="GND"),
            Connection(board_pin=3, device_name="BH1750 Light Sensor", device_pin_name="SDA"),
            Connection(board_pin=5, device_name="BH1750 Light Sensor", device_pin_name="SCL"),
            # BME280 connections (shared I2C)
            Connection(board_pin=1, device_name="BME280", device_pin_name="VCC"),
            Connection(board_pin=6, device_name="BME280", device_pin_name="GND"),
            Connection(board_pin=3, device_name="BME280", device_pin_name="SDA"),
            Connection(board_pin=5, device_name="BME280", device_pin_name="SCL"),
        ]

        diagram = Diagram(
            title="Multi-Device I2C",
            board=board,
            devices=[device1, device2],
            connections=connections,
        )

        # Validate
        validator = DiagramValidator()
        issues = validator.validate(diagram)

        # Should have INFO notes about shared I2C pins (which is OK)
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        infos = [i for i in issues if i.level == ValidationLevel.INFO]

        assert len(errors) == 0
        assert len(infos) >= 2  # Shared SDA and SCL noted


class TestConnectionGraphIntegration:
    """Test ConnectionGraph integration with board/device models."""

    def test_connection_graph_with_real_devices(self):
        """Test ConnectionGraph topology analysis with real device models."""
        # Create devices
        sensor = get_registry().create("bh1750")
        led = get_registry().create("ir_led_ring")

        # Create connections: board -> sensor -> led
        connections = [
            # Board to sensor
            Connection(board_pin=1, device_name="BH1750 Light Sensor", device_pin_name="VCC"),
            # Sensor to LED (device-to-device)
            Connection(
                source_device="BH1750 Light Sensor",
                source_pin="VCC",
                device_name="IR LED Ring (12)",
                device_pin_name="VCC",
            ),
        ]

        # Build graph
        graph = ConnectionGraph([sensor, led], connections)

        # Test level calculation
        levels = graph.calculate_device_levels()
        assert levels["BH1750 Light Sensor"] == 0  # Connected to board
        assert levels["IR LED Ring (12)"] == 1  # Connected to sensor

        # Test dependencies
        deps = graph.get_device_dependencies("IR LED Ring (12)")
        assert "BH1750 Light Sensor" in deps

        # Test root devices
        roots = graph.get_root_devices()
        assert "BH1750 Light Sensor" in roots
        assert "IR LED Ring (12)" not in roots

    def test_connection_graph_cycle_detection(self):
        """Test cycle detection in connection graph."""
        # Create devices
        device1 = Device(
            name="Device1",
            pins=[DevicePin(name="OUT", role=PinRole.GPIO, position=(0, 0))],
        )
        device2 = Device(
            name="Device2",
            pins=[DevicePin(name="OUT", role=PinRole.GPIO, position=(0, 0))],
        )

        # Create circular connections
        connections = [
            Connection(board_pin=1, device_name="Device1", device_pin_name="OUT"),
            Connection(
                source_device="Device1",
                source_pin="OUT",
                device_name="Device2",
                device_pin_name="OUT",
            ),
            Connection(
                source_device="Device2",
                source_pin="OUT",
                device_name="Device1",
                device_pin_name="OUT",
            ),
        ]

        graph = ConnectionGraph([device1, device2], connections)

        # Should detect cycle
        assert not graph.is_acyclic()
        cycles = graph.detect_cycles()
        assert len(cycles) > 0


class TestValidationIntegration:
    """Test validation integration with ConnectionGraph and models."""

    def test_dangerous_connection_detected(self):
        """Test that dangerous connections are caught by validation."""
        board = boards.raspberry_pi_5()

        # Create device with intentional mismatch
        device = Device(
            name="Sensor",
            pins=[
                DevicePin(name="VCC", role=PinRole.POWER_3V3, position=(0, 0)),
                DevicePin(name="GND", role=PinRole.GROUND, position=(0, 10)),
            ],
        )

        # Dangerous: Connect 5V board pin to 3.3V device pin
        connections = [
            Connection(board_pin=2, device_name="Sensor", device_pin_name="VCC"),  # Pin 2 is 5V
            Connection(board_pin=6, device_name="Sensor", device_pin_name="GND"),
        ]

        diagram = Diagram(
            title="Test Dangerous",
            board=board,
            devices=[device],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        # Should have ERROR for 5V to 3.3V connection
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) > 0
        assert any("5V" in str(e) and "3.3V" in str(e) for e in errors)

    def test_pin_role_incompatibility_detected(self):
        """Test that incompatible pin roles are detected."""
        board = boards.raspberry_pi_5()

        device = Device(
            name="Test",
            pins=[
                DevicePin(name="SDA", role=PinRole.I2C_SDA, position=(0, 0)),
                DevicePin(name="SCL", role=PinRole.I2C_SCL, position=(0, 10)),
            ],
        )

        # Swapped I2C lines (SDA to SCL, SCL to SDA)
        connections = [
            Connection(board_pin=3, device_name="Test", device_pin_name="SCL"),  # Pin 3 is SDA
            Connection(board_pin=5, device_name="Test", device_pin_name="SDA"),  # Pin 5 is SCL
        ]

        diagram = Diagram(
            title="Test Swapped",
            board=board,
            devices=[device],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        # Should have ERROR for swapped I2C lines
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) >= 2  # Both swapped connections

    def test_device_to_device_validation(self):
        """Test validation of device-to-device connections."""
        device1 = Device(
            name="Source",
            pins=[
                DevicePin(name="OUT", role=PinRole.GPIO, position=(0, 0)),
                DevicePin(name="GND", role=PinRole.GROUND, position=(0, 10)),
            ],
        )

        device2 = Device(
            name="Target",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO, position=(0, 0)),
                DevicePin(name="VCC", role=PinRole.POWER_3V3, position=(0, 10)),
            ],
        )

        # Create connections including device-to-device
        connections = [
            Connection(board_pin=6, device_name="Source", device_pin_name="GND"),  # Pin 6 is GND
            Connection(board_pin=1, device_name="Target", device_pin_name="VCC"),  # Pin 1 is 3.3V
            # Device-to-device: GPIO to GPIO (OK)
            Connection(
                source_device="Source",
                source_pin="OUT",
                device_name="Target",
                device_pin_name="IN",
            ),
        ]

        board = boards.raspberry_pi_5()
        diagram = Diagram(
            title="Device-to-Device",
            board=board,
            devices=[device1, device2],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        # GPIO to GPIO should be compatible (no errors)
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) == 0


class TestEndToEndPhase1:
    """End-to-end integration tests for complete Phase 1 flow."""

    def test_complete_valid_diagram_flow(self):
        """Test complete flow with valid configuration."""
        # 1. Get board and devices
        board = boards.raspberry_pi_5()
        sensor = get_registry().create("bh1750")

        # 2. Create connections
        connections = [
            Connection(board_pin=1, device_name="BH1750 Light Sensor", device_pin_name="VCC"),
            Connection(board_pin=6, device_name="BH1750 Light Sensor", device_pin_name="GND"),
            Connection(board_pin=3, device_name="BH1750 Light Sensor", device_pin_name="SDA"),
            Connection(board_pin=5, device_name="BH1750 Light Sensor", device_pin_name="SCL"),
        ]

        # 3. Build diagram
        diagram = Diagram(
            title="BH1750 Sensor",
            board=board,
            devices=[sensor],
            connections=connections,
        )

        # 4. Analyze topology
        graph = ConnectionGraph(diagram.devices, diagram.connections)
        assert graph.is_acyclic()
        levels = graph.calculate_device_levels()
        assert levels["BH1750 Light Sensor"] == 0

        # 5. Validate
        validator = DiagramValidator()
        issues = validator.validate(diagram)
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) == 0

    def test_complete_invalid_diagram_flow(self):
        """Test complete flow with invalid configuration (caught by validation)."""
        board = boards.raspberry_pi_5()

        # Create device
        device = Device(
            name="BadDevice",
            pins=[
                DevicePin(name="VCC", role=PinRole.POWER_3V3, position=(0, 0)),
                DevicePin(name="GND", role=PinRole.GROUND, position=(0, 10)),
            ],
        )

        # Dangerous connection: power to ground (short circuit)
        connections = [
            Connection(board_pin=1, device_name="BadDevice", device_pin_name="GND"),  # 3.3V to GND
        ]

        diagram = Diagram(
            title="Bad Diagram",
            board=board,
            devices=[device],
            connections=connections,
        )

        # Validation should catch this
        validator = DiagramValidator()
        issues = validator.validate(diagram)
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) > 0
        assert any(
            "short circuit" in str(e).lower() or "incompatible" in str(e).lower() for e in errors
        )

    def test_complex_multi_level_topology(self):
        """Test complex topology with multiple device levels."""
        # Create chain: board -> A -> B -> C
        device_a = Device(
            name="DeviceA",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO, position=(0, 0)),
                DevicePin(name="OUT", role=PinRole.GPIO, position=(0, 10)),
            ],
        )

        device_b = Device(
            name="DeviceB",
            pins=[
                DevicePin(name="IN", role=PinRole.GPIO, position=(0, 0)),
                DevicePin(name="OUT", role=PinRole.GPIO, position=(0, 10)),
            ],
        )

        device_c = Device(
            name="DeviceC",
            pins=[DevicePin(name="IN", role=PinRole.GPIO, position=(0, 0))],
        )

        connections = [
            # Board to A
            Connection(board_pin=7, device_name="DeviceA", device_pin_name="IN"),
            # A to B
            Connection(
                source_device="DeviceA",
                source_pin="OUT",
                device_name="DeviceB",
                device_pin_name="IN",
            ),
            # B to C
            Connection(
                source_device="DeviceB",
                source_pin="OUT",
                device_name="DeviceC",
                device_pin_name="IN",
            ),
        ]

        board = boards.raspberry_pi_5()
        diagram = Diagram(
            title="Multi-Level",
            board=board,
            devices=[device_a, device_b, device_c],
            connections=connections,
        )

        # Test topology
        graph = ConnectionGraph(diagram.devices, diagram.connections)
        levels = graph.calculate_device_levels()

        assert levels["DeviceA"] == 0
        assert levels["DeviceB"] == 1
        assert levels["DeviceC"] == 2

        # Test validation (should pass)
        validator = DiagramValidator()
        issues = validator.validate(diagram)
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) == 0


class TestPhase1ErrorHandling:
    """Test error handling and edge cases in Phase 1 integration."""

    def test_nonexistent_device_pin_caught(self):
        """Test that connections to nonexistent device pins are caught."""
        board = boards.raspberry_pi_5()
        sensor = get_registry().create("bh1750")

        # Connection to non-existent pin
        connections = [
            Connection(board_pin=1, device_name="BH1750 Light Sensor", device_pin_name="BADPIN"),
        ]

        diagram = Diagram(
            title="Bad Pin",
            board=board,
            devices=[sensor],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) > 0
        assert any("not found" in str(e).lower() for e in errors)

    def test_nonexistent_board_pin_caught(self):
        """Test that connections to nonexistent board pins are caught."""
        board = boards.raspberry_pi_5()
        sensor = get_registry().create("bh1750")

        # Invalid board pin number
        connections = [
            Connection(board_pin=999, device_name="BH1750 Light Sensor", device_pin_name="VCC"),
        ]

        diagram = Diagram(
            title="Bad Board Pin",
            board=board,
            devices=[sensor],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) > 0
        assert any("invalid board pin" in str(e).lower() for e in errors)

    def test_duplicate_gpio_usage_caught(self):
        """Test that duplicate GPIO pin usage is caught."""
        board = boards.raspberry_pi_5()

        device1 = Device(
            name="LED1",
            pins=[DevicePin(name="IN", role=PinRole.GPIO, position=(0, 0))],
        )
        device2 = Device(
            name="LED2",
            pins=[DevicePin(name="IN", role=PinRole.GPIO, position=(0, 0))],
        )

        # Both devices use same GPIO pin
        connections = [
            Connection(board_pin=7, device_name="LED1", device_pin_name="IN"),
            Connection(board_pin=7, device_name="LED2", device_pin_name="IN"),
        ]

        diagram = Diagram(
            title="Duplicate GPIO",
            board=board,
            devices=[device1, device2],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) > 0
        assert any("multiple devices" in str(e).lower() for e in errors)
