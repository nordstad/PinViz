"""Unit tests for the pin assignment module."""

import pytest

from pinviz import boards
from pinviz.mcp.pin_assignment import PinAllocationState, PinAssigner, PinAssignment
from pinviz.model import PinRole


@pytest.fixture()
def pi5_board():
    return boards.raspberry_pi_5()


@pytest.fixture()
def pico_board():
    return boards.load_board_from_config("raspberry_pi_pico")


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
        assert len(state.available_gpio) == 0


class TestPinAssigner:
    """Test suite for PinAssigner class."""

    def test_initialization(self, pi5_board):
        """Test that assigner initializes correctly."""
        assigner = PinAssigner(pi5_board)

        assert isinstance(assigner.state, PinAllocationState)
        assert len(assigner.assignments) == 0

    def test_single_i2c_device(self, pi5_board):
        """Test assigning pins for a single I2C device."""
        assigner = PinAssigner(pi5_board)

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

    def test_multiple_i2c_devices_share_bus(self, pi5_board):
        """Test that multiple I2C devices share the same I2C bus."""
        assigner = PinAssigner(pi5_board)

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

    def test_i2c_device_with_gpio_interrupt_pin(self, pi5_board):
        """I2C strategies should still allocate non-bus pins like INT."""
        assigner = PinAssigner(pi5_board)

        device = {
            "name": "MPU6050",
            "protocols": ["I2C"],
            "pins": [
                {"name": "VCC", "role": "3V3"},
                {"name": "GND", "role": "GND"},
                {"name": "SCL", "role": "I2C_SCL"},
                {"name": "SDA", "role": "I2C_SDA"},
                {"name": "INT", "role": "GPIO"},
            ],
        }

        assignments, warnings = assigner.assign_pins([device])

        assert len(assignments) == 5
        assert len(warnings) == 0
        int_assignment = next(a for a in assignments if a.device_pin_name == "INT")
        assert int_assignment.board_pin_number in pi5_board.pins_by_role()[PinRole.GPIO]

    def test_single_spi_device(self, pi5_board):
        """Test assigning pins for a single SPI device."""
        assigner = PinAssigner(pi5_board)

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

    def test_two_spi_devices_different_chip_selects(self, pi5_board):
        """Test that two SPI devices get different chip select pins."""
        assigner = PinAssigner(pi5_board)

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

    def test_three_spi_devices_warning(self, pi5_board):
        """Test that more than 2 SPI devices generates a warning."""
        assigner = PinAssigner(pi5_board)

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

    def test_gpio_device(self, pi5_board):
        """Test assigning pins for a GPIO device."""
        assigner = PinAssigner(pi5_board)

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
        assert gpio_assignment.board_pin_number in pi5_board.pins_by_role()[PinRole.GPIO]

    def test_power_distribution(self, pi5_board):
        """Test that power pins are distributed correctly."""
        assigner = PinAssigner(pi5_board)

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

    def test_ground_distribution(self, pi5_board):
        """Test that ground pins are distributed correctly."""
        assigner = PinAssigner(pi5_board)

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
        gnd_pins = pi5_board.pins_by_role()[PinRole.GROUND]
        assert all(a.board_pin_number in gnd_pins for a in assignments)

    def test_power_overload_warning(self, pi5_board):
        """Test warning when too many devices use power."""
        assigner = PinAssigner(pi5_board)

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

    def test_four_pwm_devices_use_all_pwm_pins(self, pi5_board):
        """PWM strategies should allocate all supported PWM-capable pins."""
        assigner = PinAssigner(pi5_board)
        pwm_pins = pi5_board.pins_by_role().get(PinRole.PWM, [])

        devices = [
            {
                "name": f"PWM Device {index}",
                "protocols": [],
                "pins": [{"name": "SIG", "role": "PWM"}],
            }
            for index in range(len(pwm_pins))
        ]

        assignments, warnings = assigner.assign_pins(devices)

        assert len(assignments) == len(pwm_pins)
        assert len(warnings) == 0
        assert {assignment.board_pin_number for assignment in assignments} == set(pwm_pins)

    def test_general_gpio_warning_when_gpio_pool_is_exhausted(self, pi5_board):
        """General GPIO assignment should warn when no GPIO pins remain."""
        assigner = PinAssigner(pi5_board)
        assigner.state.available_gpio = []

        warnings = assigner._assign_general_pin("Exhausted", "SIG", PinRole.GPIO)

        assert warnings == ["Error: No GPIO pins available for Exhausted/SIG"]

    def test_general_pwm_warning_when_pwm_candidates_are_exhausted(self, pi5_board):
        """PWM helper should warn when all PWM-capable pins are already used."""
        assigner = PinAssigner(pi5_board)
        assigner.state.used_pins.update(pi5_board.pins_by_role().get(PinRole.PWM, []))

        warnings = assigner._assign_general_pin("PWM Device", "SIG", PinRole.PWM)

        assert warnings == ["Warning: No PWM pins available for PWM Device/SIG"]

    def test_general_fixed_role_assignment_uses_fixed_pin(self, pi5_board):
        """Fixed-role pins should be assigned from the fixed mapping."""
        assigner = PinAssigner(pi5_board)

        warnings = assigner._assign_general_pin("UART Device", "TX", PinRole.UART_TX)

        assert warnings == []
        uart_tx_pin = pi5_board.pins_by_role()[PinRole.UART_TX][0]
        assert assigner.assignments[0].board_pin_number == uart_tx_pin

    def test_general_fixed_role_assignment_warns_when_pin_is_unavailable(self, pi5_board):
        """Fixed-role assignment should warn when the mapped board pin is already used."""
        assigner = PinAssigner(pi5_board)
        uart_tx_pin = pi5_board.pins_by_role()[PinRole.UART_TX][0]
        assigner.state.used_pins.add(uart_tx_pin)

        warnings = assigner._assign_general_pin("UART Device", "TX", PinRole.UART_TX)

        assert warnings == ["Warning: Fixed UART_TX pin unavailable for UART Device/TX"]
        assert assigner.assignments == []

    def test_general_pin_warns_for_unsupported_role_objects(self, pi5_board):
        """Unsupported role-like objects should produce a warning instead of crashing."""
        assigner = PinAssigner(pi5_board)

        class UnsupportedRole:
            value = "UNSUPPORTED"

        warnings = assigner._assign_general_pin("Mystery Device", "X", UnsupportedRole())

        assert warnings == ["Warning: Unsupported pin role UNSUPPORTED for Mystery Device/X"]

    def test_mixed_devices(self, pi5_board):
        """Test complex scenario with mixed I2C, SPI, and GPIO devices."""
        assigner = PinAssigner(pi5_board)

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
        display_assignments = [a for a in assignments if a.device_name == "ST7735 Display"]
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


class TestBoardPinMappings:
    """Test that board pin roles are correctly derived for Pi5."""

    def test_i2c_pins(self, pi5_board):
        """Test that I2C pins are correctly derived from board."""
        pin_map = pi5_board.pins_by_role()
        assert pin_map[PinRole.I2C_SDA][0] == 3
        assert pin_map[PinRole.I2C_SCL][0] == 5

    def test_spi_pins(self, pi5_board):
        """Test that SPI pins are correctly derived from board."""
        pin_map = pi5_board.pins_by_role()
        assert pin_map[PinRole.SPI_MOSI][0] == 19
        assert pin_map[PinRole.SPI_MISO][0] == 21
        assert pin_map[PinRole.SPI_SCLK][0] == 23
        assert pin_map[PinRole.SPI_CE0][0] == 24
        assert pin_map[PinRole.SPI_CE1][0] == 26

    def test_power_pins(self, pi5_board):
        """Test that power pins are correctly derived from board."""
        pin_map = pi5_board.pins_by_role()
        assert pin_map[PinRole.POWER_3V3] == [1, 17]
        assert pin_map[PinRole.POWER_5V] == [2, 4]

    def test_ground_pins(self, pi5_board):
        """Test that ground pins are correctly derived from board."""
        pin_map = pi5_board.pins_by_role()
        assert len(pin_map[PinRole.GROUND]) == 8
        assert 6 in pin_map[PinRole.GROUND]
        assert 9 in pin_map[PinRole.GROUND]

    def test_gpio_pins(self, pi5_board):
        """Test that GPIO pins are present on the board."""
        pin_map = pi5_board.pins_by_role()
        gpio_pins = pin_map[PinRole.GPIO]
        assert len(gpio_pins) > 0
        # Verify a few known GPIO physical pins
        assert 7 in gpio_pins  # GPIO4
        assert 11 in gpio_pins  # GPIO17
        assert 13 in gpio_pins  # GPIO27


class TestPicoBoard:
    """Test that PinAssigner works with a Pico board (board-agnostic)."""

    def test_pico_gpio_device(self, pico_board):
        """GPIO assignment on Pico should use Pico's GPIO pins."""
        assigner = PinAssigner(pico_board)

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
        gpio_assignment = next(a for a in assignments if a.pin_role == PinRole.GPIO)
        # Verify the GPIO pin is from the Pico's pin set, not Pi5's
        pico_gpio_pins = pico_board.pins_by_role()[PinRole.GPIO]
        assert gpio_assignment.board_pin_number in pico_gpio_pins

    def test_pico_ground_distribution(self, pico_board):
        """Ground pins on Pico should come from Pico's GND pins."""
        assigner = PinAssigner(pico_board)

        devices = [
            {
                "name": f"Device {i}",
                "protocols": [],
                "pins": [{"name": "GND", "role": "GND"}],
            }
            for i in range(3)
        ]

        assignments, warnings = assigner.assign_pins(devices)

        pico_gnd_pins = pico_board.pins_by_role()[PinRole.GROUND]
        assert all(a.board_pin_number in pico_gnd_pins for a in assignments)
