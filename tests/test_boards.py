"""Tests for board factory functions."""

import pytest

from pinviz import boards
from pinviz.model import PinRole


def test_raspberry_pi_5_board_creation():
    """Test creating a Raspberry Pi 5 board."""
    board = boards.raspberry_pi_5()
    assert board is not None
    assert board.name == "Raspberry Pi 5"


def test_raspberry_pi_5_has_40_pins():
    """Test that Raspberry Pi 5 has 40 GPIO pins."""
    board = boards.raspberry_pi_5()
    assert len(board.pins) == 40


def test_raspberry_pi_5_pin_numbers():
    """Test that all pin numbers 1-40 are present."""
    board = boards.raspberry_pi_5()
    pin_numbers = {pin.number for pin in board.pins}
    assert pin_numbers == set(range(1, 41))


def test_raspberry_pi_5_power_pins():
    """Test power pin roles."""
    board = boards.raspberry_pi_5()
    # Check 3V3 pins (1, 17)
    pin1 = board.get_pin_by_number(1)
    pin17 = board.get_pin_by_number(17)
    assert pin1.role == PinRole.POWER_3V3
    assert pin17.role == PinRole.POWER_3V3

    # Check 5V pins (2, 4)
    pin2 = board.get_pin_by_number(2)
    pin4 = board.get_pin_by_number(4)
    assert pin2.role == PinRole.POWER_5V
    assert pin4.role == PinRole.POWER_5V


def test_raspberry_pi_5_ground_pins():
    """Test ground pin roles."""
    board = boards.raspberry_pi_5()
    ground_pins = [6, 9, 14, 20, 25, 30, 34, 39]
    for pin_num in ground_pins:
        pin = board.get_pin_by_number(pin_num)
        assert pin.role == PinRole.GROUND, f"Pin {pin_num} should be GROUND"
        assert pin.gpio_bcm is None


def test_raspberry_pi_5_i2c_pins():
    """Test I2C pin roles and BCM numbers."""
    board = boards.raspberry_pi_5()
    # SDA on GPIO2 (pin 3)
    sda_pin = board.get_pin_by_number(3)
    assert sda_pin.role == PinRole.I2C_SDA
    assert sda_pin.gpio_bcm == 2
    assert sda_pin.name == "GPIO2"

    # SCL on GPIO3 (pin 5)
    scl_pin = board.get_pin_by_number(5)
    assert scl_pin.role == PinRole.I2C_SCL
    assert scl_pin.gpio_bcm == 3
    assert scl_pin.name == "GPIO3"


def test_raspberry_pi_5_spi_pins():
    """Test SPI pin roles and BCM numbers."""
    board = boards.raspberry_pi_5()
    # MOSI on GPIO10 (pin 19)
    mosi_pin = board.get_pin_by_number(19)
    assert mosi_pin.role == PinRole.SPI_MOSI
    assert mosi_pin.gpio_bcm == 10

    # MISO on GPIO9 (pin 21)
    miso_pin = board.get_pin_by_number(21)
    assert miso_pin.role == PinRole.SPI_MISO
    assert miso_pin.gpio_bcm == 9

    # SCLK on GPIO11 (pin 23)
    sclk_pin = board.get_pin_by_number(23)
    assert sclk_pin.role == PinRole.SPI_SCLK
    assert sclk_pin.gpio_bcm == 11

    # CE0 on GPIO8 (pin 24)
    ce0_pin = board.get_pin_by_number(24)
    assert ce0_pin.role == PinRole.SPI_CE0
    assert ce0_pin.gpio_bcm == 8

    # CE1 on GPIO7 (pin 26)
    ce1_pin = board.get_pin_by_number(26)
    assert ce1_pin.role == PinRole.SPI_CE1
    assert ce1_pin.gpio_bcm == 7


def test_raspberry_pi_5_uart_pins():
    """Test UART pin roles and BCM numbers."""
    board = boards.raspberry_pi_5()
    # TX on GPIO14 (pin 8)
    tx_pin = board.get_pin_by_number(8)
    assert tx_pin.role == PinRole.UART_TX
    assert tx_pin.gpio_bcm == 14

    # RX on GPIO15 (pin 10)
    rx_pin = board.get_pin_by_number(10)
    assert rx_pin.role == PinRole.UART_RX
    assert rx_pin.gpio_bcm == 15


def test_raspberry_pi_5_pwm_pins():
    """Test PWM pin roles."""
    board = boards.raspberry_pi_5()
    pwm_pins = {12: 18, 32: 12, 33: 13}  # pin_number: bcm_number
    for pin_num, bcm_num in pwm_pins.items():
        pin = board.get_pin_by_number(pin_num)
        assert pin.role == PinRole.PWM
        assert pin.gpio_bcm == bcm_num


def test_raspberry_pi_5_gpio_pins():
    """Test generic GPIO pins."""
    board = boards.raspberry_pi_5()
    gpio_pins = [7, 11, 13, 15, 16, 18, 22, 29, 31, 36, 37]
    for pin_num in gpio_pins:
        pin = board.get_pin_by_number(pin_num)
        assert pin.role == PinRole.GPIO
        assert pin.gpio_bcm is not None


def test_raspberry_pi_5_all_pins_have_positions():
    """Test that all pins have position information."""
    board = boards.raspberry_pi_5()
    for pin in board.pins:
        assert pin.position is not None
        assert pin.position.x > 0
        assert pin.position.y >= 0


def test_raspberry_pi_5_pin_positions_alternating_columns():
    """Test that odd pins are in left column, even pins in right column."""
    board = boards.raspberry_pi_5()
    left_col_x = 187.0
    right_col_x = 199.0

    for pin in board.pins:
        if pin.number % 2 == 1:  # Odd pins (left column)
            assert pin.position.x == pytest.approx(left_col_x, abs=0.1)
        else:  # Even pins (right column)
            assert pin.position.x == pytest.approx(right_col_x, abs=0.1)


def test_raspberry_pi_5_board_dimensions():
    """Test board dimensions."""
    board = boards.raspberry_pi_5()
    assert board.width == pytest.approx(205.42, abs=0.1)
    assert board.height == pytest.approx(307.46, abs=0.1)


def test_raspberry_pi_5_svg_asset_path():
    """Test that SVG asset path is set."""
    board = boards.raspberry_pi_5()
    assert board.svg_asset_path is not None
    assert "pi_5_mod.svg" in board.svg_asset_path


def test_raspberry_pi_5_get_pin_by_bcm():
    """Test retrieving pins by BCM number."""
    board = boards.raspberry_pi_5()
    gpio2 = board.get_pin_by_bcm(2)
    assert gpio2 is not None
    assert gpio2.number == 3
    assert gpio2.role == PinRole.I2C_SDA


def test_raspberry_pi_alias():
    """Test that raspberry_pi() is an alias for raspberry_pi_5()."""
    board1 = boards.raspberry_pi()
    board2 = boards.raspberry_pi_5()
    assert board1.name == board2.name
    assert len(board1.pins) == len(board2.pins)
    assert board1.width == board2.width
    assert board1.height == board2.height


def test_load_board_from_config():
    """Test loading board configuration from JSON file."""
    board = boards.load_board_from_config("raspberry_pi_5")
    assert board.name == "Raspberry Pi 5"
    assert len(board.pins) == 40
    assert board.svg_asset_path.endswith("pi_5_mod.svg")


def test_load_board_config_missing_file():
    """Test that loading non-existent config raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError) as exc_info:
        boards.load_board_from_config("nonexistent_board")
    assert "Board configuration file not found" in str(exc_info.value)


def test_load_board_config_positions_calculated():
    """Test that pin positions are calculated from layout parameters."""
    board = boards.load_board_from_config("raspberry_pi_5")

    # Check that positions are calculated correctly
    # Layout parameters from config: left_col_x=187.1, right_col_x=199.1,
    # start_y=16.2, row_spacing=12.0
    pin1 = board.get_pin_by_number(1)  # Odd pin, left column, row 0
    pin2 = board.get_pin_by_number(2)  # Even pin, right column, row 0

    assert pin1.position.x == pytest.approx(187.1, abs=0.01)
    assert pin2.position.x == pytest.approx(199.1, abs=0.01)
    assert pin1.position.y == pytest.approx(16.2, abs=0.01)  # start_y
    assert pin2.position.y == pytest.approx(16.2, abs=0.01)  # start_y

    # Check row spacing
    pin3 = board.get_pin_by_number(3)  # Row 1
    assert pin3.position.y == pytest.approx(16.2 + 12.0, abs=0.01)


def test_load_board_config_pin_roles():
    """Test that pin roles are correctly loaded and converted."""
    board = boards.load_board_from_config("raspberry_pi_5")

    # Verify some pin roles
    assert board.get_pin_by_number(1).role == PinRole.POWER_3V3
    assert board.get_pin_by_number(3).role == PinRole.I2C_SDA
    assert board.get_pin_by_number(6).role == PinRole.GROUND
    assert board.get_pin_by_number(7).role == PinRole.GPIO


def test_load_board_config_bcm_numbers():
    """Test that BCM GPIO numbers are correctly loaded."""
    board = boards.load_board_from_config("raspberry_pi_5")

    # Verify BCM numbers
    assert board.get_pin_by_number(3).gpio_bcm == 2  # GPIO2
    assert board.get_pin_by_number(5).gpio_bcm == 3  # GPIO3
    assert board.get_pin_by_number(7).gpio_bcm == 4  # GPIO4

    # Power and ground pins should have None
    assert board.get_pin_by_number(1).gpio_bcm is None  # 3V3
    assert board.get_pin_by_number(6).gpio_bcm is None  # GND


# Raspberry Pi 4 Tests
def test_raspberry_pi_4_board_creation():
    """Test creating a Raspberry Pi 4 board."""
    board = boards.raspberry_pi_4()
    assert board is not None
    assert board.name == "Raspberry Pi 4 Model B"


def test_raspberry_pi_4_has_40_pins():
    """Test that Raspberry Pi 4 has 40 GPIO pins."""
    board = boards.raspberry_pi_4()
    assert len(board.pins) == 40


def test_raspberry_pi_4_identical_pinout_to_pi5():
    """Test that Raspberry Pi 4 has identical GPIO pinout to Pi 5."""
    pi4 = boards.raspberry_pi_4()
    pi5 = boards.raspberry_pi_5()

    # Both should have 40 pins
    assert len(pi4.pins) == len(pi5.pins)

    # Pin roles and BCM numbers should be identical
    for pin_num in range(1, 41):
        pi4_pin = pi4.get_pin_by_number(pin_num)
        pi5_pin = pi5.get_pin_by_number(pin_num)

        assert pi4_pin.role == pi5_pin.role, f"Pin {pin_num} role mismatch"
        assert pi4_pin.gpio_bcm == pi5_pin.gpio_bcm, f"Pin {pin_num} BCM mismatch"
        assert pi4_pin.name == pi5_pin.name, f"Pin {pin_num} name mismatch"


def test_raspberry_pi_4_svg_asset_path():
    """Test that SVG asset path is set correctly for Pi 4."""
    board = boards.raspberry_pi_4()
    assert board.svg_asset_path is not None
    assert "pi_4_mod.svg" in board.svg_asset_path


def test_raspberry_pi_4_board_dimensions():
    """Test that Pi 4 has same dimensions as Pi 5 (identical SVG size)."""
    pi4 = boards.raspberry_pi_4()
    pi5 = boards.raspberry_pi_5()

    # Should have identical dimensions for pin alignment
    assert pi4.width == pytest.approx(pi5.width, abs=0.1)
    assert pi4.height == pytest.approx(pi5.height, abs=0.1)


def test_raspberry_pi_4_i2c_pins():
    """Test I2C pin roles and BCM numbers on Pi 4."""
    board = boards.raspberry_pi_4()

    # SDA on GPIO2 (pin 3)
    sda_pin = board.get_pin_by_number(3)
    assert sda_pin.role == PinRole.I2C_SDA
    assert sda_pin.gpio_bcm == 2

    # SCL on GPIO3 (pin 5)
    scl_pin = board.get_pin_by_number(5)
    assert scl_pin.role == PinRole.I2C_SCL
    assert scl_pin.gpio_bcm == 3


def test_raspberry_pi_4_spi_pins():
    """Test SPI pin roles and BCM numbers on Pi 4."""
    board = boards.raspberry_pi_4()

    # MOSI on GPIO10 (pin 19)
    mosi_pin = board.get_pin_by_number(19)
    assert mosi_pin.role == PinRole.SPI_MOSI
    assert mosi_pin.gpio_bcm == 10

    # CE0 on GPIO8 (pin 24)
    ce0_pin = board.get_pin_by_number(24)
    assert ce0_pin.role == PinRole.SPI_CE0
    assert ce0_pin.gpio_bcm == 8


def test_load_board_from_config_pi4():
    """Test loading Raspberry Pi 4 configuration from JSON file."""
    board = boards.load_board_from_config("raspberry_pi_4")
    assert board.name == "Raspberry Pi 4 Model B"
    assert len(board.pins) == 40
    assert board.svg_asset_path.endswith("pi_4_mod.svg")


# Raspberry Pi Pico Tests
def test_raspberry_pi_pico_board_creation():
    """Test creating a Raspberry Pi Pico board."""
    board = boards.raspberry_pi_pico()
    assert board is not None
    assert board.name == "Raspberry Pi Pico"


def test_raspberry_pi_pico_has_40_pins():
    """Test that Raspberry Pi Pico has 40 GPIO pins."""
    board = boards.raspberry_pi_pico()
    assert len(board.pins) == 40


def test_raspberry_pi_pico_pin_numbers():
    """Test that all pin numbers 1-40 are present."""
    board = boards.raspberry_pi_pico()
    pin_numbers = {pin.number for pin in board.pins}
    assert pin_numbers == set(range(1, 41))


def test_raspberry_pi_pico_power_pins():
    """Test power pin roles on Pico."""
    board = boards.raspberry_pi_pico()

    # 3V3 pins (36, 37)
    pin36 = board.get_pin_by_number(36)
    pin37 = board.get_pin_by_number(37)
    assert pin36.role == PinRole.POWER_3V3
    assert pin37.role == PinRole.POWER_3V3
    assert pin36.name == "3V3"
    assert pin37.name == "3V3_EN"

    # 5V pins (VSYS=39, VBUS=40)
    pin39 = board.get_pin_by_number(39)
    pin40 = board.get_pin_by_number(40)
    assert pin39.role == PinRole.POWER_5V
    assert pin40.role == PinRole.POWER_5V
    assert pin39.name == "VSYS"
    assert pin40.name == "VBUS"


def test_raspberry_pi_pico_ground_pins():
    """Test ground pin roles on Pico."""
    board = boards.raspberry_pi_pico()
    # Ground pins: 3, 8, 13, 18, 23, 28, 33, 38
    ground_pins = [3, 8, 13, 18, 23, 28, 33, 38]
    for pin_num in ground_pins:
        pin = board.get_pin_by_number(pin_num)
        assert pin.role == PinRole.GROUND, f"Pin {pin_num} should be GROUND"
        assert pin.name == "GND"
        assert pin.gpio_bcm is None


def test_raspberry_pi_pico_gpio_pins():
    """Test GPIO pins on Pico (GP0-GP28)."""
    board = boards.raspberry_pi_pico()

    # Test a few GPIO pins
    # GP0 (pin 1)
    pin1 = board.get_pin_by_number(1)
    assert pin1.role == PinRole.GPIO
    assert pin1.name == "GP0"
    assert pin1.gpio_bcm == 0

    # GP15 (pin 20)
    pin20 = board.get_pin_by_number(20)
    assert pin20.role == PinRole.GPIO
    assert pin20.name == "GP15"
    assert pin20.gpio_bcm == 15

    # GP16 (pin 21)
    pin21 = board.get_pin_by_number(21)
    assert pin21.role == PinRole.GPIO
    assert pin21.name == "GP16"
    assert pin21.gpio_bcm == 16

    # GP28 (pin 34)
    pin34 = board.get_pin_by_number(34)
    assert pin34.role == PinRole.GPIO
    assert pin34.name == "GP28"
    assert pin34.gpio_bcm == 28


def test_raspberry_pi_pico_all_pins_have_positions():
    """Test that all Pico pins have position information."""
    board = boards.raspberry_pi_pico()
    for pin in board.pins:
        assert pin.position is not None
        assert pin.position.x >= 0
        assert pin.position.y >= 0


def test_raspberry_pi_pico_horizontal_layout():
    """Test that Pico has horizontal pin layout (single row per header)."""
    board = boards.raspberry_pi_pico()

    # Top header (pins 1-20) should all have same Y coordinate
    top_pins = [board.get_pin_by_number(i) for i in range(1, 21)]
    top_y_coords = {pin.position.y for pin in top_pins}
    assert len(top_y_coords) == 1, "Top header pins should all have same Y coordinate"
    assert list(top_y_coords)[0] == pytest.approx(6.5, abs=0.1)

    # Bottom header (pins 21-40) should all have same Y coordinate
    bottom_pins = [board.get_pin_by_number(i) for i in range(21, 41)]
    bottom_y_coords = {pin.position.y for pin in bottom_pins}
    assert len(bottom_y_coords) == 1, "Bottom header pins should all have same Y coordinate"
    assert list(bottom_y_coords)[0] == pytest.approx(94.0, abs=0.1)


def test_raspberry_pi_pico_top_header_reversed_order():
    """Test that top header pins are in reversed order (pin 20 on left, pin 1 on right)."""
    board = boards.raspberry_pi_pico()

    # Pin 20 should be leftmost (smallest X)
    pin20 = board.get_pin_by_number(20)
    pin1 = board.get_pin_by_number(1)

    assert pin20.position.x < pin1.position.x, "Pin 20 should be left of pin 1"

    # Pin positions should decrease as pin numbers increase (reversed)
    for i in range(1, 20):
        pin_lower = board.get_pin_by_number(i)
        pin_higher = board.get_pin_by_number(i + 1)
        assert pin_lower.position.x > pin_higher.position.x, (
            f"Pin {i} should be right of pin {i + 1} (reversed order)"
        )


def test_raspberry_pi_pico_bottom_header_normal_order():
    """Test that bottom header pins are in normal order (pin 21 on left, pin 40 on right)."""
    board = boards.raspberry_pi_pico()

    # Pin 21 should be leftmost (smallest X)
    pin21 = board.get_pin_by_number(21)
    pin40 = board.get_pin_by_number(40)

    assert pin21.position.x < pin40.position.x, "Pin 21 should be left of pin 40"

    # Pin positions should increase as pin numbers increase (normal order)
    for i in range(21, 40):
        pin_lower = board.get_pin_by_number(i)
        pin_higher = board.get_pin_by_number(i + 1)
        assert pin_lower.position.x < pin_higher.position.x, (
            f"Pin {i} should be left of pin {i + 1} (normal order)"
        )


def test_raspberry_pi_pico_pin_spacing():
    """Test that Pico pins have consistent spacing."""
    board = boards.raspberry_pi_pico()

    # Test top header spacing
    pin1 = board.get_pin_by_number(1)
    pin2 = board.get_pin_by_number(2)
    top_spacing = abs(pin1.position.x - pin2.position.x)
    assert top_spacing == pytest.approx(12.0, abs=0.1), "Pin spacing should be 12.0"

    # Test bottom header spacing
    pin21 = board.get_pin_by_number(21)
    pin22 = board.get_pin_by_number(22)
    bottom_spacing = abs(pin21.position.x - pin22.position.x)
    assert bottom_spacing == pytest.approx(12.0, abs=0.1), "Pin spacing should be 12.0"


def test_raspberry_pi_pico_board_dimensions():
    """Test Pico board dimensions."""
    board = boards.raspberry_pi_pico()
    assert board.width == pytest.approx(249.0, abs=0.1)
    assert board.height == pytest.approx(101.0, abs=0.1)


def test_raspberry_pi_pico_svg_asset_path():
    """Test that SVG asset path is set for Pico."""
    board = boards.raspberry_pi_pico()
    assert board.svg_asset_path is not None
    assert "pico_mod.svg" in board.svg_asset_path


def test_load_board_from_config_pico():
    """Test loading Raspberry Pi Pico configuration from JSON file."""
    board = boards.load_board_from_config("raspberry_pi_pico")
    assert board.name == "Raspberry Pi Pico"
    assert len(board.pins) == 40
    assert board.svg_asset_path.endswith("pico_mod.svg")


def test_raspberry_pi_pico_special_pins():
    """Test special pins on Pico (RUN, ADC_VREF)."""
    board = boards.raspberry_pi_pico()

    # RUN pin (pin 30)
    run_pin = board.get_pin_by_number(30)
    assert run_pin.name == "RUN"
    assert run_pin.role == PinRole.GPIO
    assert run_pin.gpio_bcm is None

    # ADC_VREF pin (pin 35)
    adc_pin = board.get_pin_by_number(35)
    assert adc_pin.name == "ADC_VREF"
    assert adc_pin.role == PinRole.GPIO
    assert adc_pin.gpio_bcm is None


# ESP32 DevKit V1 Tests
def test_esp32_devkit_v1_board_creation():
    """Test creating an ESP32 DevKit V1 board."""
    board = boards.load_board_from_config("esp32_devkit_v1")
    assert board is not None
    assert board.name == "ESP32 DevKit V1"


def test_esp32_devkit_v1_has_30_pins():
    """Test that ESP32 DevKit V1 has 30 GPIO pins."""
    board = boards.load_board_from_config("esp32_devkit_v1")
    assert len(board.pins) == 30


def test_esp32_devkit_v1_power_pins():
    """Test power pin roles on ESP32."""
    board = boards.load_board_from_config("esp32_devkit_v1")

    # 3V3 pin (1)
    pin1 = board.get_pin_by_number(1)
    assert pin1.role == PinRole.POWER_3V3

    # 5V pin (2)
    pin2 = board.get_pin_by_number(2)
    assert pin2.role == PinRole.POWER_5V


def test_esp32_devkit_v1_ground_pins():
    """Test ground pin roles on ESP32."""
    board = boards.load_board_from_config("esp32_devkit_v1")
    ground_pins = [3, 4]  # GND pins
    for pin_num in ground_pins:
        pin = board.get_pin_by_number(pin_num)
        assert pin.role == PinRole.GROUND, f"Pin {pin_num} should be GROUND"


def test_esp32_devkit_v1_i2c_pins():
    """Test I2C pin roles on ESP32."""
    board = boards.load_board_from_config("esp32_devkit_v1")

    # SDA on GPIO21 (pin 21)
    sda_pin = board.get_pin_by_number(21)
    assert sda_pin.role == PinRole.I2C_SDA
    assert sda_pin.gpio_bcm == 21

    # SCL on GPIO22 (pin 27)
    scl_pin = board.get_pin_by_number(27)
    assert scl_pin.role == PinRole.I2C_SCL
    assert scl_pin.gpio_bcm == 22


def test_esp32_devkit_v1_svg_asset_path():
    """Test that SVG asset path is set for ESP32."""
    board = boards.load_board_from_config("esp32_devkit_v1")
    assert board.svg_asset_path is not None
    assert "esp32_devkit_v1_mod.svg" in board.svg_asset_path


# ESP8266 NodeMCU Tests
def test_esp8266_nodemcu_board_creation():
    """Test creating an ESP8266 NodeMCU board."""
    board = boards.load_board_from_config("esp8266_nodemcu")
    assert board is not None
    assert board.name == "ESP8266 NodeMCU"


def test_esp8266_nodemcu_has_30_pins():
    """Test that ESP8266 NodeMCU has 30 GPIO pins."""
    board = boards.load_board_from_config("esp8266_nodemcu")
    assert len(board.pins) == 30


def test_esp8266_nodemcu_power_pins():
    """Test power pin roles on NodeMCU."""
    board = boards.load_board_from_config("esp8266_nodemcu")

    # 3V3 pins (12, 21, 30)
    pin12 = board.get_pin_by_number(12)
    pin21 = board.get_pin_by_number(21)
    pin30 = board.get_pin_by_number(30)
    assert pin12.role == PinRole.POWER_3V3
    assert pin21.role == PinRole.POWER_3V3
    assert pin30.role == PinRole.POWER_3V3

    # 5V pin (29)
    pin29 = board.get_pin_by_number(29)
    assert pin29.role == PinRole.POWER_5V


def test_esp8266_nodemcu_ground_pins():
    """Test ground pin roles on NodeMCU."""
    board = boards.load_board_from_config("esp8266_nodemcu")
    ground_pins = [14, 19, 27, 28]  # GND pins
    for pin_num in ground_pins:
        pin = board.get_pin_by_number(pin_num)
        assert pin.role == PinRole.GROUND, f"Pin {pin_num} should be GROUND"


def test_esp8266_nodemcu_i2c_pins():
    """Test I2C pin roles on NodeMCU."""
    board = boards.load_board_from_config("esp8266_nodemcu")

    # SCL on D1/GPIO5 (pin 4)
    scl_pin = board.get_pin_by_number(4)
    assert scl_pin.role == PinRole.I2C_SCL
    assert scl_pin.gpio_bcm == 5

    # SDA on D2/GPIO4 (pin 6)
    sda_pin = board.get_pin_by_number(6)
    assert sda_pin.role == PinRole.I2C_SDA
    assert sda_pin.gpio_bcm == 4


def test_esp8266_nodemcu_svg_asset_path():
    """Test that SVG asset path is set for NodeMCU."""
    board = boards.load_board_from_config("esp8266_nodemcu")
    assert board.svg_asset_path is not None
    assert "esp8266_nodemcu_mod.svg" in board.svg_asset_path


# Wemos D1 Mini Tests
def test_wemos_d1_mini_board_creation():
    """Test creating a Wemos D1 Mini board."""
    board = boards.load_board_from_config("wemos_d1_mini")
    assert board is not None
    assert board.name == "Wemos D1 Mini"


def test_wemos_d1_mini_has_16_pins():
    """Test that Wemos D1 Mini has 16 GPIO pins."""
    board = boards.load_board_from_config("wemos_d1_mini")
    assert len(board.pins) == 16


def test_wemos_d1_mini_power_pins():
    """Test power pin roles on D1 Mini."""
    board = boards.load_board_from_config("wemos_d1_mini")

    # 3V3 pin (15)
    pin15 = board.get_pin_by_number(15)
    assert pin15.role == PinRole.POWER_3V3

    # 5V pin (16)
    pin16 = board.get_pin_by_number(16)
    assert pin16.role == PinRole.POWER_5V


def test_wemos_d1_mini_ground_pins():
    """Test ground pin roles on D1 Mini."""
    board = boards.load_board_from_config("wemos_d1_mini")
    ground_pins = [14]  # GND pin
    for pin_num in ground_pins:
        pin = board.get_pin_by_number(pin_num)
        assert pin.role == PinRole.GROUND, f"Pin {pin_num} should be GROUND"


def test_wemos_d1_mini_i2c_pins():
    """Test I2C pin roles on D1 Mini."""
    board = boards.load_board_from_config("wemos_d1_mini")

    # SCL on D1/GPIO5 (pin 6)
    scl_pin = board.get_pin_by_number(6)
    assert scl_pin.role == PinRole.I2C_SCL
    assert scl_pin.gpio_bcm == 5

    # SDA on D2/GPIO4 (pin 8)
    sda_pin = board.get_pin_by_number(8)
    assert sda_pin.role == PinRole.I2C_SDA
    assert sda_pin.gpio_bcm == 4


def test_wemos_d1_mini_svg_asset_path():
    """Test that SVG asset path is set for D1 Mini."""
    board = boards.load_board_from_config("wemos_d1_mini")
    assert board.svg_asset_path is not None
    assert "wemos_d1_mini_mod.svg" in board.svg_asset_path
