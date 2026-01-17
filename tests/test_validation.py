"""Tests for validation module."""

from pinviz import boards
from pinviz.devices import get_registry
from pinviz.model import Connection, Device, DevicePin, Diagram, PinRole, Point
from pinviz.validation import DiagramValidator, ValidationLevel, check_pin_compatibility


class TestDuplicatePinDetection:
    """Tests for duplicate GPIO pin detection."""

    def test_duplicate_gpio_pins(self):
        """Test detection of duplicate GPIO pin usage."""
        board = boards.raspberry_pi_5()
        led1 = get_registry().create("led", color_name="LED1")
        led2 = get_registry().create("led", color_name="LED2")

        # Both LEDs connected to same GPIO pin
        connections = [
            Connection(11, "LED1 LED", "+"),  # GPIO17
            Connection(11, "LED2 LED", "+"),  # GPIO17 - duplicate!
            Connection(6, "LED1 LED", "-"),
            Connection(9, "LED2 LED", "-"),
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[led1, led2],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) == 1
        assert "Pin 11" in errors[0].message
        assert "multiple devices" in errors[0].message.lower()

    def test_shared_power_pins_allowed(self):
        """Test that multiple devices can share power/ground pins."""
        board = boards.raspberry_pi_5()
        sensor1 = get_registry().create("bh1750")
        sensor2 = get_registry().create("i2c_device", name="Sensor2")

        connections = [
            # Both sensors share power and ground - this is OK
            Connection(1, "BH1750 Light Sensor", "VCC"),
            Connection(1, "Sensor2", "VCC"),
            Connection(6, "BH1750 Light Sensor", "GND"),
            Connection(6, "Sensor2", "GND"),
            # Different I2C connections
            Connection(3, "BH1750 Light Sensor", "SDA"),
            Connection(5, "BH1750 Light Sensor", "SCL"),
            Connection(27, "Sensor2", "SDA"),
            Connection(28, "Sensor2", "SCL"),
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[sensor1, sensor2],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        # Should have no errors (power/ground sharing is OK)
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) == 0

    def test_shared_i2c_pins_noted(self):
        """Test that shared I2C pins are noted (not an error)."""
        board = boards.raspberry_pi_5()
        sensor1 = get_registry().create("bh1750")
        sensor2 = get_registry().create("i2c_device", name="Sensor2")

        connections = [
            Connection(1, "BH1750 Light Sensor", "VCC"),
            Connection(1, "Sensor2", "VCC"),
            Connection(6, "BH1750 Light Sensor", "GND"),
            Connection(6, "Sensor2", "GND"),
            # Both share the same I2C bus (pins 3 and 5)
            Connection(3, "BH1750 Light Sensor", "SDA"),
            Connection(3, "Sensor2", "SDA"),
            Connection(5, "BH1750 Light Sensor", "SCL"),
            Connection(5, "Sensor2", "SCL"),
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[sensor1, sensor2],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        # Should have info notes about I2C sharing
        infos = [i for i in issues if i.level == ValidationLevel.INFO]
        assert len(infos) == 2  # One for SDA, one for SCL
        assert any("I2C" in i.message for i in infos)


class TestVoltageCompatibility:
    """Tests for voltage compatibility validation."""

    def test_5v_to_3v3_device_error(self):
        """Test detection of 5V board pin to 3.3V device pin."""
        board = boards.raspberry_pi_5()

        # Create a 3.3V device
        device_3v3 = Device(
            name="3V3 Sensor",
            pins=[
                DevicePin("VCC", PinRole.POWER_3V3, Point(5, 10)),
                DevicePin("GND", PinRole.GROUND, Point(5, 20)),
            ],
        )

        # Connect 5V pin to 3.3V device - this is dangerous!
        connections = [
            Connection(2, "3V3 Sensor", "VCC"),  # Pin 2 is 5V
            Connection(6, "3V3 Sensor", "GND"),
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[device_3v3],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) >= 1
        assert any("5V" in e.message and "3.3V" in e.message for e in errors)

    def test_3v3_to_5v_device_warning(self):
        """Test detection of 3.3V board pin to 5V device pin."""
        board = boards.raspberry_pi_5()

        # Create a 5V device
        device_5v = Device(
            name="5V Device",
            pins=[
                DevicePin("VCC", PinRole.POWER_5V, Point(5, 10)),
                DevicePin("GND", PinRole.GROUND, Point(5, 20)),
            ],
        )

        # Connect 3.3V pin to 5V device - might not work properly
        connections = [
            Connection(1, "5V Device", "VCC"),  # Pin 1 is 3.3V
            Connection(6, "5V Device", "GND"),
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[device_5v],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        warnings = [i for i in issues if i.level == ValidationLevel.WARNING]
        assert len(warnings) >= 1
        assert any("3.3V" in w.message and "5V" in w.message for w in warnings)


class TestI2CAddressConflicts:
    """Tests for I2C address conflict detection."""

    def test_duplicate_bh1750_warning(self):
        """Test detection of multiple BH1750 sensors (same default address)."""
        board = boards.raspberry_pi_5()
        sensor1 = get_registry().create("bh1750")
        sensor1.type_id = "bh1750"  # Set type_id for registry lookup
        sensor2 = get_registry().create("bh1750")
        sensor2.name = "BH1750-2"  # Rename to distinguish from first sensor
        sensor2.type_id = "bh1750"  # Set type_id for registry lookup

        connections = [
            # First sensor
            Connection(1, "BH1750 Light Sensor", "VCC"),
            Connection(6, "BH1750 Light Sensor", "GND"),
            Connection(3, "BH1750 Light Sensor", "SDA"),
            Connection(5, "BH1750 Light Sensor", "SCL"),
            # Second sensor on same bus
            Connection(1, "BH1750-2", "VCC"),
            Connection(6, "BH1750-2", "GND"),
            Connection(3, "BH1750-2", "SDA"),
            Connection(5, "BH1750-2", "SCL"),
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[sensor1, sensor2],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        warnings = [i for i in issues if i.level == ValidationLevel.WARNING]
        # Should warn about I2C address conflict
        assert any("I2C address conflict" in w.message for w in warnings)
        assert any("0x23" in w.message for w in warnings)  # BH1750 default address


class TestConnectionValidity:
    """Tests for connection validity checks."""

    def test_invalid_board_pin_number(self):
        """Test detection of invalid board pin number."""
        board = boards.raspberry_pi_5()
        led = get_registry().create("led", color_name="LED")

        connections = [
            Connection(99, "LED", "+"),  # Invalid pin number!
            Connection(6, "LED", "-"),
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[led],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) >= 1
        assert any("Invalid board pin" in e.message for e in errors)

    def test_nonexistent_device(self):
        """Test detection of connection to non-existent device."""
        board = boards.raspberry_pi_5()
        led = get_registry().create("led", color_name="LED")

        connections = [
            Connection(11, "LED", "+"),
            Connection(6, "NonExistentDevice", "-"),  # Device doesn't exist!
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[led],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) >= 1
        assert any("not found" in e.message.lower() for e in errors)

    def test_nonexistent_device_pin(self):
        """Test detection of connection to non-existent device pin."""
        board = boards.raspberry_pi_5()
        led = get_registry().create("led", color_name="LED")

        connections = [
            Connection(11, "LED LED", "+"),
            Connection(6, "LED LED", "InvalidPin"),  # Pin doesn't exist on LED!
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[led],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) >= 1
        # Check for the pin not found error message
        assert any("InvalidPin" in e.message and "not found" in e.message for e in errors)


class TestCurrentLimits:
    """Tests for GPIO current limit checks."""

    def test_multiple_loads_on_gpio_warning(self):
        """Test warning when multiple devices connected to one GPIO."""
        board = boards.raspberry_pi_5()

        # Create multiple devices on same GPIO (likely current issue)
        led1 = get_registry().create("led", color_name="LED1")
        led2 = get_registry().create("led", color_name="LED2")

        connections = [
            Connection(11, "LED1", "+"),  # GPIO17
            Connection(11, "LED2", "+"),  # GPIO17 - same pin!
            Connection(6, "LED1", "-"),
            Connection(9, "LED2", "-"),
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[led1, led2],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        # This should generate both a pin conflict error and might mention current
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) >= 1


class TestValidDiagrams:
    """Tests for diagrams that should pass validation."""

    def test_simple_valid_diagram(self):
        """Test that a simple valid diagram passes validation."""
        board = boards.raspberry_pi_5()
        sensor = get_registry().create("bh1750")

        connections = [
            Connection(1, "BH1750 Light Sensor", "VCC"),
            Connection(6, "BH1750 Light Sensor", "GND"),
            Connection(3, "BH1750 Light Sensor", "SDA"),
            Connection(5, "BH1750 Light Sensor", "SCL"),
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[sensor],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        # Should have no errors
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) == 0

    def test_multiple_devices_valid(self):
        """Test that multiple properly connected devices pass validation."""
        board = boards.raspberry_pi_5()
        sensor = get_registry().create("bh1750")
        led = get_registry().create("led", color_name="Status")

        connections = [
            # Sensor on I2C
            Connection(1, "BH1750 Light Sensor", "VCC"),
            Connection(6, "BH1750 Light Sensor", "GND"),
            Connection(3, "BH1750 Light Sensor", "SDA"),
            Connection(5, "BH1750 Light Sensor", "SCL"),
            # LED on GPIO
            Connection(11, "Status LED", "+"),  # GPIO17
            Connection(9, "Status LED", "-"),
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[sensor, led],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        # Should have no errors
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) == 0


class TestPinCompatibilityMatrix:
    """Tests for the pin compatibility matrix function."""

    def test_compatible_power_connections(self):
        """Test that same voltage power connections are compatible."""
        is_compat, severity = check_pin_compatibility(PinRole.POWER_3V3, PinRole.POWER_3V3)
        assert is_compat is True
        assert severity is None

        is_compat, severity = check_pin_compatibility(PinRole.POWER_5V, PinRole.POWER_5V)
        assert is_compat is True
        assert severity is None

    def test_power_to_ground_dangerous(self):
        """Test that power to ground connections are detected as dangerous."""
        is_compat, severity = check_pin_compatibility(PinRole.POWER_3V3, PinRole.GROUND)
        assert is_compat is False
        assert severity == "error"

        is_compat, severity = check_pin_compatibility(PinRole.POWER_5V, PinRole.GROUND)
        assert is_compat is False
        assert severity == "error"

    def test_cross_voltage_power_connections(self):
        """Test that cross-voltage power connections are detected."""
        # 5V to 3.3V device - dangerous
        is_compat, severity = check_pin_compatibility(PinRole.POWER_5V, PinRole.POWER_3V3)
        assert is_compat is False
        assert severity == "error"

        # 3.3V to 5V device - warning (may not work)
        is_compat, severity = check_pin_compatibility(PinRole.POWER_3V3, PinRole.POWER_5V)
        assert is_compat is False
        assert severity == "warning"

    def test_i2c_pin_compatibility(self):
        """Test I2C pin role compatibility."""
        # SDA to SDA is OK
        is_compat, severity = check_pin_compatibility(PinRole.I2C_SDA, PinRole.I2C_SDA)
        assert is_compat is True
        assert severity is None

        # SCL to SCL is OK
        is_compat, severity = check_pin_compatibility(PinRole.I2C_SCL, PinRole.I2C_SCL)
        assert is_compat is True
        assert severity is None

        # SDA to SCL is swapped - error
        is_compat, severity = check_pin_compatibility(PinRole.I2C_SDA, PinRole.I2C_SCL)
        assert is_compat is False
        assert severity == "error"

        # SCL to SDA is swapped - error
        is_compat, severity = check_pin_compatibility(PinRole.I2C_SCL, PinRole.I2C_SDA)
        assert is_compat is False
        assert severity == "error"

    def test_spi_pin_compatibility(self):
        """Test SPI pin role compatibility."""
        # MOSI to MOSI is OK
        is_compat, severity = check_pin_compatibility(PinRole.SPI_MOSI, PinRole.SPI_MOSI)
        assert is_compat is True
        assert severity is None

        # MISO to MISO is OK
        is_compat, severity = check_pin_compatibility(PinRole.SPI_MISO, PinRole.SPI_MISO)
        assert is_compat is True
        assert severity is None

        # MOSI to MISO is swapped - error
        is_compat, severity = check_pin_compatibility(PinRole.SPI_MOSI, PinRole.SPI_MISO)
        assert is_compat is False
        assert severity == "error"

    def test_uart_pin_compatibility(self):
        """Test UART pin role compatibility."""
        # TX to RX is correct
        is_compat, severity = check_pin_compatibility(PinRole.UART_TX, PinRole.UART_RX)
        assert is_compat is True
        assert severity is None

        # RX to TX is correct
        is_compat, severity = check_pin_compatibility(PinRole.UART_RX, PinRole.UART_TX)
        assert is_compat is True
        assert severity is None

        # TX to TX won't work
        is_compat, severity = check_pin_compatibility(PinRole.UART_TX, PinRole.UART_TX)
        assert is_compat is False
        assert severity == "error"

        # RX to RX won't work
        is_compat, severity = check_pin_compatibility(PinRole.UART_RX, PinRole.UART_RX)
        assert is_compat is False
        assert severity == "error"

    def test_gpio_compatibility(self):
        """Test GPIO pin compatibility with various roles."""
        # GPIO to GPIO is OK
        is_compat, severity = check_pin_compatibility(PinRole.GPIO, PinRole.GPIO)
        assert is_compat is True
        assert severity is None

        # GPIO to PWM is OK
        is_compat, severity = check_pin_compatibility(PinRole.GPIO, PinRole.PWM)
        assert is_compat is True
        assert severity is None

        # GPIO to protocol pins - warning (might be bit-banging)
        is_compat, severity = check_pin_compatibility(PinRole.GPIO, PinRole.I2C_SDA)
        assert is_compat is True
        assert severity == "warning"

    def test_ground_compatibility(self):
        """Test ground pin compatibility."""
        # Ground to ground is always OK
        is_compat, severity = check_pin_compatibility(PinRole.GROUND, PinRole.GROUND)
        assert is_compat is True
        assert severity is None


class TestPinRoleCompatibilityValidation:
    """Tests for pin role compatibility validation in diagrams."""

    def test_swapped_i2c_lines_detected(self):
        """Test detection of swapped I2C SDA/SCL lines."""
        board = boards.raspberry_pi_5()

        # Create device with I2C pins
        device = Device(
            name="I2C Sensor",
            pins=[
                DevicePin("VCC", PinRole.POWER_3V3, Point(5, 10)),
                DevicePin("GND", PinRole.GROUND, Point(5, 20)),
                DevicePin("SDA", PinRole.I2C_SDA, Point(5, 30)),
                DevicePin("SCL", PinRole.I2C_SCL, Point(5, 40)),
            ],
        )

        # Swap SDA and SCL connections - this is wrong!
        connections = [
            Connection(1, "I2C Sensor", "VCC"),
            Connection(6, "I2C Sensor", "GND"),
            Connection(3, "I2C Sensor", "SCL"),  # Pin 3 is I2C_SDA, should connect to SDA
            Connection(5, "I2C Sensor", "SDA"),  # Pin 5 is I2C_SCL, should connect to SCL
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[device],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) >= 2  # Two swapped connections
        assert any("I2C_SDA" in e.message and "I2C_SCL" in e.message for e in errors)

    def test_power_to_ground_short_detected(self):
        """Test detection of dangerous power-to-ground short circuit."""
        board = boards.raspberry_pi_5()

        # Create device with ground pin
        device = Device(
            name="Device",
            pins=[DevicePin("GND", PinRole.GROUND, Point(5, 10))],
        )

        # Connect power pin to ground - DANGEROUS!
        connections = [
            Connection(1, "Device", "GND"),  # Pin 1 is 3.3V power
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[device],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) >= 1
        assert any("3V3" in e.message and "GND" in e.message for e in errors)

    def test_swapped_spi_lines_detected(self):
        """Test detection of swapped SPI MOSI/MISO lines."""
        board = boards.raspberry_pi_5()

        # Create SPI device
        device = Device(
            name="SPI Device",
            pins=[
                DevicePin("MOSI", PinRole.SPI_MOSI, Point(5, 10)),
                DevicePin("MISO", PinRole.SPI_MISO, Point(5, 20)),
                DevicePin("SCLK", PinRole.SPI_SCLK, Point(5, 30)),
            ],
        )

        # Swap MOSI and MISO - this is wrong!
        connections = [
            Connection(19, "SPI Device", "MISO"),  # Pin 19 is SPI_MOSI
            Connection(21, "SPI Device", "MOSI"),  # Pin 21 is SPI_MISO
            Connection(23, "SPI Device", "SCLK"),
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[device],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) >= 2
        assert any("SPI_MOSI" in e.message and "SPI_MISO" in e.message for e in errors)

    def test_uart_tx_to_tx_error(self):
        """Test detection of UART TX connected to TX (won't work)."""
        board = boards.raspberry_pi_5()

        # Create UART device
        device = Device(
            name="UART Device",
            pins=[
                DevicePin("TX", PinRole.UART_TX, Point(5, 10)),
                DevicePin("RX", PinRole.UART_RX, Point(5, 20)),
            ],
        )

        # Connect TX to TX - this won't work!
        connections = [
            Connection(8, "UART Device", "TX"),  # Pin 8 is UART_TX
            Connection(10, "UART Device", "RX"),
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[device],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) >= 1
        assert any("UART_TX" in e.message for e in errors)

    def test_device_to_device_pin_compatibility(self):
        """Test pin compatibility validation for device-to-device connections."""
        board = boards.raspberry_pi_5()

        # Create two devices
        power_module = Device(
            name="Power Module",
            pins=[
                DevicePin("VIN", PinRole.POWER_5V, Point(5, 10)),
                DevicePin("VOUT", PinRole.POWER_3V3, Point(5, 20)),
                DevicePin("GND", PinRole.GROUND, Point(5, 30)),
            ],
        )

        sensor = Device(
            name="Sensor",
            pins=[
                DevicePin("VCC", PinRole.POWER_3V3, Point(5, 10)),
                DevicePin("GND", PinRole.GROUND, Point(5, 20)),
            ],
        )

        # Connections:
        # - Board 5V to power module input (OK)
        # - Power module 3.3V output to sensor VCC (OK)
        # - Shared ground (OK)
        connections = [
            Connection(board_pin=2, device_name="Power Module", device_pin_name="VIN"),
            Connection(board_pin=6, device_name="Power Module", device_pin_name="GND"),
            Connection(
                source_device="Power Module",
                source_pin="VOUT",
                device_name="Sensor",
                device_pin_name="VCC",
            ),
            Connection(board_pin=6, device_name="Sensor", device_pin_name="GND"),
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[power_module, sensor],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        # Should have no errors - this is a valid power distribution setup
        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) == 0

    def test_device_to_device_incompatible_pins(self):
        """Test detection of incompatible pins in device-to-device connections."""
        board = boards.raspberry_pi_5()

        # Create two devices with incompatible pin connection
        device1 = Device(
            name="Device1",
            pins=[
                DevicePin("OUT", PinRole.POWER_5V, Point(5, 10)),
                DevicePin("GND", PinRole.GROUND, Point(5, 20)),
            ],
        )

        device2 = Device(
            name="Device2",
            pins=[
                DevicePin("IN", PinRole.POWER_3V3, Point(5, 10)),
                DevicePin("GND", PinRole.GROUND, Point(5, 20)),
            ],
        )

        # Connect 5V output to 3.3V input - dangerous!
        connections = [
            Connection(board_pin=2, device_name="Device1", device_pin_name="OUT"),
            Connection(board_pin=6, device_name="Device1", device_pin_name="GND"),
            Connection(board_pin=6, device_name="Device2", device_pin_name="GND"),
            Connection(
                source_device="Device1",
                source_pin="OUT",
                device_name="Device2",
                device_pin_name="IN",
            ),
        ]

        diagram = Diagram(
            title="Test",
            board=board,
            devices=[device1, device2],
            connections=connections,
        )

        validator = DiagramValidator()
        issues = validator.validate(diagram)

        errors = [i for i in issues if i.level == ValidationLevel.ERROR]
        assert len(errors) >= 1
        assert any("5V" in e.message and "3V3" in e.message for e in errors)
