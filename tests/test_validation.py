"""Tests for validation module."""


from pinviz import boards
from pinviz.devices import bh1750_light_sensor, generic_i2c_device, simple_led
from pinviz.model import Connection, Device, DevicePin, Diagram, PinRole, Point
from pinviz.validation import DiagramValidator, ValidationLevel


class TestDuplicatePinDetection:
    """Tests for duplicate GPIO pin detection."""

    def test_duplicate_gpio_pins(self):
        """Test detection of duplicate GPIO pin usage."""
        board = boards.raspberry_pi_5()
        led1 = simple_led("LED1")
        led2 = simple_led("LED2")

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
        sensor1 = bh1750_light_sensor()
        sensor2 = generic_i2c_device("Sensor2")

        connections = [
            # Both sensors share power and ground - this is OK
            Connection(1, "BH1750", "VCC"),
            Connection(1, "Sensor2", "VCC"),
            Connection(6, "BH1750", "GND"),
            Connection(6, "Sensor2", "GND"),
            # Different I2C connections
            Connection(3, "BH1750", "SDA"),
            Connection(5, "BH1750", "SCL"),
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
        sensor1 = bh1750_light_sensor()
        sensor2 = generic_i2c_device("Sensor2")

        connections = [
            Connection(1, "BH1750", "VCC"),
            Connection(1, "Sensor2", "VCC"),
            Connection(6, "BH1750", "GND"),
            Connection(6, "Sensor2", "GND"),
            # Both share the same I2C bus (pins 3 and 5)
            Connection(3, "BH1750", "SDA"),
            Connection(3, "Sensor2", "SDA"),
            Connection(5, "BH1750", "SCL"),
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
        sensor1 = bh1750_light_sensor()
        sensor2 = Device(
            name="BH1750-2",
            pins=[
                DevicePin("VCC", PinRole.POWER_3V3, Point(5, 10)),
                DevicePin("GND", PinRole.GROUND, Point(5, 18)),
                DevicePin("SCL", PinRole.I2C_SCL, Point(5, 26)),
                DevicePin("SDA", PinRole.I2C_SDA, Point(5, 34)),
            ],
        )

        connections = [
            # First sensor
            Connection(1, "BH1750", "VCC"),
            Connection(6, "BH1750", "GND"),
            Connection(3, "BH1750", "SDA"),
            Connection(5, "BH1750", "SCL"),
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
        led = simple_led("LED")

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
        led = simple_led("LED")

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
        led = simple_led("LED")

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
        led1 = simple_led("LED1")
        led2 = simple_led("LED2")

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
        sensor = bh1750_light_sensor()

        connections = [
            Connection(1, "BH1750", "VCC"),
            Connection(6, "BH1750", "GND"),
            Connection(3, "BH1750", "SDA"),
            Connection(5, "BH1750", "SCL"),
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
        sensor = bh1750_light_sensor()
        led = simple_led("Status")

        connections = [
            # Sensor on I2C
            Connection(1, "BH1750", "VCC"),
            Connection(6, "BH1750", "GND"),
            Connection(3, "BH1750", "SDA"),
            Connection(5, "BH1750", "SCL"),
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
