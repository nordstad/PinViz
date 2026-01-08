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


