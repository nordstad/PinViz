"""Unit tests for the pin assignment module."""

import pytest
from pinviz.model import PinRole
from pinviz_mcp.pin_assignment import PinAllocationState, PinAssigner, PinAssignment


class TestPinAllocationState:
    """Test suite for PinAllocationState class."""

    def test_initialization(self):
        """Test that state initializes with correct defaults."""
        state = PinAllocationState()

        assert len(state.used_pins) == 0
        assert state.i2c_sda_pin is None
        assert state.i2c_scl_pin is None
        assert len(state.i2c_devices) == 0
        assert state.spi_mosi_pin is None
        assert state.spi_ce0_assigned is False
        assert state.power_3v3_count == 0
        assert len(state.available_gpio) > 0


class TestPinAssigner:
    """Test suite for PinAssigner class."""

    def test_initialization(self):
        """Test that assigner initializes correctly."""
        assigner = PinAssigner()

        assert isinstance(assigner.state, PinAllocationState)
        assert len(assigner.assignments) == 0

    def test_single_i2c_device(self):
        """Test assigning pins for a single I2C device."""
        assigner = PinAssigner()

        device = {
            "name": "BME280 Sensor",
            "protocols": ["I2C"],
            "pins": [
                {"name": "VCC", "role": "3V3"},
                {"name": "GND", "role": "GND"},
                {"name": "SCL", "role": "I2C_SCL"},
                {"name": "SDA", "role": "I2C_SDA"},
            ],
        }

        assignments, warnings = assigner.assign_pins([device])

        assert len(assignments) == 4
        assert len(warnings) == 0

        # Check I2C pins are assigned correctly
        sda_assignment = next(a for a in assignments if a.pin_role == PinRole.I2C_SDA)
        scl_assignment = next(a for a in assignments if a.pin_role == PinRole.I2C_SCL)

        assert sda_assignment.board_pin_number == 3
        assert scl_assignment.board_pin_number == 5

    def test_multiple_i2c_devices_share_bus(self):
        """Test that multiple I2C devices share the same I2C bus."""
        assigner = PinAssigner()

        devices = [
            {
                "name": "BME280 Sensor",
                "protocols": ["I2C"],
                "i2c_address": "0x76",
                "pins": [
                    {"name": "VCC", "role": "3V3"},
                    {"name": "GND", "role": "GND"},
                    {"name": "SCL", "role": "I2C_SCL"},
                    {"name": "SDA", "role": "I2C_SDA"},
                ],
            },
            {
                "name": "SSD1306 Display",
                "protocols": ["I2C"],
                "i2c_address": "0x3C",
                "pins": [
                    {"name": "VCC", "role": "3V3"},
                    {"name": "GND", "role": "GND"},
                    {"name": "SCL", "role": "I2C_SCL"},
                    {"name": "SDA", "role": "I2C_SDA"},
                ],
            },
        ]

        assignments, warnings = assigner.assign_pins(devices)

        # Both devices should use the same I2C pins
        sda_assignments = [a for a in assignments if a.pin_role == PinRole.I2C_SDA]
        scl_assignments = [a for a in assignments if a.pin_role == PinRole.I2C_SCL]

        assert len(sda_assignments) == 2
        assert len(scl_assignments) == 2
        assert all(a.board_pin_number == 3 for a in sda_assignments)
        assert all(a.board_pin_number == 5 for a in scl_assignments)

        # Should have warnings about I2C addresses
        assert len(warnings) > 0
        assert any("I2C address" in w for w in warnings)

    def test_single_spi_device(self):
        """Test assigning pins for a single SPI device."""
        assigner = PinAssigner()

        device = {
            "name": "ST7735 TFT",
            "protocols": ["SPI"],
            "pins": [
                {"name": "VCC", "role": "3V3"},
                {"name": "GND", "role": "GND"},
                {"name": "MOSI", "role": "SPI_MOSI"},
                {"name": "MISO", "role": "SPI_MISO"},
                {"name": "SCLK", "role": "SPI_SCLK"},
                {"name": "CS", "role": "SPI_CE0"},
            ],
        }

        assignments, warnings = assigner.assign_pins([device])

        assert len(assignments) == 6
        assert len(warnings) == 0

        # Check SPI pins
        mosi = next(a for a in assignments if a.pin_role == PinRole.SPI_MOSI)
        miso = next(a for a in assignments if a.pin_role == PinRole.SPI_MISO)
        sclk = next(a for a in assignments if a.pin_role == PinRole.SPI_SCLK)

        assert mosi.board_pin_number == 19
        assert miso.board_pin_number == 21
        assert sclk.board_pin_number == 23

    def test_two_spi_devices_different_chip_selects(self):
        """Test that two SPI devices get different chip select pins."""
        assigner = PinAssigner()

        devices = [
            {
                "name": "Display 1",
                "protocols": ["SPI"],
                "pins": [
                    {"name": "VCC", "role": "3V3"},
                    {"name": "GND", "role": "GND"},
                    {"name": "MOSI", "role": "SPI_MOSI"},
                    {"name": "SCLK", "role": "SPI_SCLK"},
                    {"name": "CS", "role": "SPI_CE0"},
                ],
            },
            {
                "name": "Display 2",
                "protocols": ["SPI"],
                "pins": [
                    {"name": "VCC", "role": "3V3"},
                    {"name": "GND", "role": "GND"},
                    {"name": "MOSI", "role": "SPI_MOSI"},
                    {"name": "SCLK", "role": "SPI_SCLK"},
                    {"name": "CS", "role": "SPI_CE1"},
                ],
            },
        ]

        assignments, warnings = assigner.assign_pins(devices)

        # Both should share MOSI and SCLK
        mosi_assignments = [a for a in assignments if a.pin_role == PinRole.SPI_MOSI]
        assert len(mosi_assignments) == 2
        assert all(a.board_pin_number == 19 for a in mosi_assignments)

        # But should have different CS pins
        ce0_assignments = [a for a in assignments if a.pin_role == PinRole.SPI_CE0]
        ce1_assignments = [a for a in assignments if a.pin_role == PinRole.SPI_CE1]

        assert len(ce0_assignments) == 1
        assert len(ce1_assignments) == 1
        assert ce0_assignments[0].board_pin_number == 24
        assert ce1_assignments[0].board_pin_number == 26

    def test_three_spi_devices_warning(self):
        """Test that more than 2 SPI devices generates a warning."""
        assigner = PinAssigner()

        devices = [
            {
                "name": f"SPI Device {i}",
                "protocols": ["SPI"],
                "pins": [
                    {"name": "VCC", "role": "3V3"},
                    {"name": "CS", "role": "SPI_CE0"},
                ],
            }
            for i in range(3)
        ]

        assignments, warnings = assigner.assign_pins(devices)

        assert len(warnings) > 0
        assert any("chip select" in w.lower() for w in warnings)

    def test_gpio_device(self):
        """Test assigning pins for a GPIO device."""
        assigner = PinAssigner()

        device = {
            "name": "LED",
            "protocols": [],
            "pins": [
                {"name": "VCC", "role": "3V3"},
                {"name": "GND", "role": "GND"},
                {"name": "SIG", "role": "GPIO"},
            ],
        }

        assignments, warnings = assigner.assign_pins([device])

        assert len(assignments) == 3
        assert len(warnings) == 0

        # Check that a GPIO pin was assigned
        gpio_assignment = next(a for a in assignments if a.pin_role == PinRole.GPIO)
        assert gpio_assignment.board_pin_number in PinAssigner.GPIO_BCM_TO_PHYSICAL.values()

    def test_power_distribution(self):
        """Test that power pins are distributed correctly."""
        assigner = PinAssigner()

        # Create 3 devices that need 3.3V
        devices = [
            {
                "name": f"Device {i}",
                "protocols": [],
                "pins": [
                    {"name": "VCC", "role": "3V3"},
                    {"name": "GND", "role": "GND"},
                ],
            }
            for i in range(3)
        ]

        assignments, warnings = assigner.assign_pins(devices)

        # All should have power assignments
        power_assignments = [a for a in assignments if a.pin_role == PinRole.POWER_3V3]
        assert len(power_assignments) == 3

        # Power pins should cycle between available pins
        assert all(a.board_pin_number in [1, 17] for a in power_assignments)

    def test_ground_distribution(self):
        """Test that ground pins are distributed correctly."""
        assigner = PinAssigner()

        devices = [
            {
                "name": f"Device {i}",
                "protocols": [],
                "pins": [{"name": "GND", "role": "GND"}],
            }
            for i in range(5)
        ]

        assignments, warnings = assigner.assign_pins(devices)

        # All should have ground assignments
        assert len(assignments) == 5
        assert all(a.pin_role == PinRole.GROUND for a in assignments)

        # Ground pins should be from the available list
        assert all(a.board_pin_number in PinAssigner.GROUND_PINS for a in assignments)

    def test_power_overload_warning(self):
        """Test warning when too many devices use power."""
        assigner = PinAssigner()

        devices = [
            {
                "name": f"Device {i}",
                "protocols": [],
                "pins": [{"name": "VCC", "role": "3V3"}],
            }
            for i in range(6)
        ]

        assignments, warnings = assigner.assign_pins(devices)

        assert len(warnings) > 0
        assert any("current" in w.lower() for w in warnings)

    def test_mixed_devices(self):
        """Test complex scenario with mixed I2C, SPI, and GPIO devices."""
        assigner = PinAssigner()

        devices = [
            {
                "name": "BME280 Sensor",
                "protocols": ["I2C"],
                "pins": [
                    {"name": "VCC", "role": "3V3"},
                    {"name": "GND", "role": "GND"},
                    {"name": "SCL", "role": "I2C_SCL"},
                    {"name": "SDA", "role": "I2C_SDA"},
                ],
            },
            {
                "name": "ST7735 Display",
                "protocols": ["SPI"],
                "pins": [
                    {"name": "VCC", "role": "3V3"},
                    {"name": "GND", "role": "GND"},
                    {"name": "MOSI", "role": "SPI_MOSI"},
                    {"name": "SCLK", "role": "SPI_SCLK"},
                    {"name": "CS", "role": "SPI_CE0"},
                ],
            },
            {
                "name": "LED",
                "protocols": [],
                "pins": [
                    {"name": "VCC", "role": "3V3"},
                    {"name": "SIG", "role": "GPIO"},
                ],
            },
        ]

        assignments, warnings = assigner.assign_pins(devices)

        # Should have assignments for all pins
        assert len(assignments) == 11

        # Check I2C device has correct pins
        bme_assignments = [a for a in assignments if a.device_name == "BME280 Sensor"]
        assert len(bme_assignments) == 4

        # Check SPI device has correct pins
        display_assignments = [
            a for a in assignments if a.device_name == "ST7735 Display"
        ]
        assert len(display_assignments) == 5

        # Check GPIO device has correct pins
        led_assignments = [a for a in assignments if a.device_name == "LED"]
        assert len(led_assignments) == 2

    def test_assignment_dataclass(self):
        """Test PinAssignment dataclass."""
        assignment = PinAssignment(
            board_pin_number=3,
            device_name="Test Device",
            device_pin_name="SDA",
            pin_role=PinRole.I2C_SDA,
        )

        assert assignment.board_pin_number == 3
        assert assignment.device_name == "Test Device"
        assert assignment.device_pin_name == "SDA"
        assert assignment.pin_role == PinRole.I2C_SDA


class TestPinMappings:
    """Test suite for pin mapping constants."""

    def test_i2c_pins(self):
        """Test that I2C pins are correctly defined."""
        assert PinAssigner.I2C_SDA_PIN == 3
        assert PinAssigner.I2C_SCL_PIN == 5

    def test_spi_pins(self):
        """Test that SPI pins are correctly defined."""
        assert PinAssigner.SPI_MOSI_PIN == 19
        assert PinAssigner.SPI_MISO_PIN == 21
        assert PinAssigner.SPI_SCLK_PIN == 23
        assert PinAssigner.SPI_CE0_PIN == 24
        assert PinAssigner.SPI_CE1_PIN == 26

    def test_power_pins(self):
        """Test that power pins are correctly defined."""
        assert PinAssigner.POWER_3V3_PINS == [1, 17]
        assert PinAssigner.POWER_5V_PINS == [2, 4]

    def test_ground_pins(self):
        """Test that ground pins are correctly defined."""
        assert len(PinAssigner.GROUND_PINS) == 8
        assert 6 in PinAssigner.GROUND_PINS
        assert 9 in PinAssigner.GROUND_PINS

    def test_gpio_bcm_mapping(self):
        """Test that GPIO BCM to physical mapping is correct."""
        # Test a few known mappings
        assert PinAssigner.GPIO_BCM_TO_PHYSICAL[2] == 3
        assert PinAssigner.GPIO_BCM_TO_PHYSICAL[3] == 5
        assert PinAssigner.GPIO_BCM_TO_PHYSICAL[4] == 7
        assert PinAssigner.GPIO_BCM_TO_PHYSICAL[17] == 11
