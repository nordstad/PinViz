"""Predefined Raspberry Pi board templates."""

from pathlib import Path

from .model import Board, HeaderPin, PinRole, Point


def _get_asset_path(filename: str) -> str:
    """
    Get the absolute path to an asset file.

    Resolves the path to an SVG asset file in the package assets directory.
    Used internally by board factory functions to locate board SVG images.

    Args:
        filename: Name of the asset file (e.g., "pi2.svg")

    Returns:
        Absolute path to the asset file as a string

    Note:
        This is an internal function. Users typically don't need to call this directly.
    """
    module_dir = Path(__file__).parent
    asset_path = module_dir / "assets" / filename
    return str(asset_path)


def raspberry_pi_5() -> Board:
    """
    Create a Raspberry Pi 5 board with 40-pin GPIO header.

    Pin layout (physical pin numbers):
    Standard 2x20 header layout:
    - Top row (odd pins): 1, 3, 5, ..., 39 (left to right)
    - Bottom row (even pins): 2, 4, 6, ..., 40 (left to right)

    Returns:
        Board: Configured Raspberry Pi 5 board
    """
    # GPIO header positions for standard vertical column layout
    # Standard Raspberry Pi GPIO has 2 vertical columns with 20 rows:
    # - Left column (odd pins): 1, 3, 5, ..., 39 (top to bottom)
    # - Right column (even pins): 2, 4, 6, ..., 40 (top to bottom)
    #
    # Fine-tuned values to align with pi2.svg yellow circles (GPIO pins)
    left_col_x = 174.5  # X position for left column (odd pins)
    right_col_x = 186.5  # X position for right column (even pins)
    start_y = 6.0  # Starting Y position (top)
    row_spacing = 12.0  # Vertical spacing between rows

    _pin_positions = {}

    # Generate positions for all 40 pins in vertical columns
    for row in range(20):  # 20 rows
        y_pos = start_y + (row * row_spacing)
        odd_pin = (row * 2) + 1  # Physical pins 1, 3, 5, ..., 39
        even_pin = (row * 2) + 2  # Physical pins 2, 4, 6, ..., 40

        _pin_positions[odd_pin] = Point(left_col_x, y_pos)  # Left column (odd)
        _pin_positions[even_pin] = Point(right_col_x, y_pos)  # Right column (even)

    pins = [
        # Pin 1-2
        HeaderPin(1, "3V3", PinRole.POWER_3V3, gpio_bcm=None, position=_pin_positions[1]),
        HeaderPin(2, "5V", PinRole.POWER_5V, gpio_bcm=None, position=_pin_positions[2]),
        # Pin 3-4
        HeaderPin(3, "GPIO2", PinRole.I2C_SDA, gpio_bcm=2, position=_pin_positions[3]),
        HeaderPin(4, "5V", PinRole.POWER_5V, gpio_bcm=None, position=_pin_positions[4]),
        # Pin 5-6
        HeaderPin(5, "GPIO3", PinRole.I2C_SCL, gpio_bcm=3, position=_pin_positions[5]),
        HeaderPin(6, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[6]),
        # Pin 7-8
        HeaderPin(7, "GPIO4", PinRole.GPIO, gpio_bcm=4, position=_pin_positions[7]),
        HeaderPin(8, "GPIO14", PinRole.UART_TX, gpio_bcm=14, position=_pin_positions[8]),
        # Pin 9-10
        HeaderPin(9, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[9]),
        HeaderPin(10, "GPIO15", PinRole.UART_RX, gpio_bcm=15, position=_pin_positions[10]),
        # Pin 11-12
        HeaderPin(11, "GPIO17", PinRole.GPIO, gpio_bcm=17, position=_pin_positions[11]),
        HeaderPin(12, "GPIO18", PinRole.PWM, gpio_bcm=18, position=_pin_positions[12]),
        # Pin 13-14
        HeaderPin(13, "GPIO27", PinRole.GPIO, gpio_bcm=27, position=_pin_positions[13]),
        HeaderPin(14, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[14]),
        # Pin 15-16
        HeaderPin(15, "GPIO22", PinRole.GPIO, gpio_bcm=22, position=_pin_positions[15]),
        HeaderPin(16, "GPIO23", PinRole.GPIO, gpio_bcm=23, position=_pin_positions[16]),
        # Pin 17-18
        HeaderPin(17, "3V3", PinRole.POWER_3V3, gpio_bcm=None, position=_pin_positions[17]),
        HeaderPin(18, "GPIO24", PinRole.GPIO, gpio_bcm=24, position=_pin_positions[18]),
        # Pin 19-20
        HeaderPin(19, "GPIO10", PinRole.SPI_MOSI, gpio_bcm=10, position=_pin_positions[19]),
        HeaderPin(20, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[20]),
        # Pin 21-22
        HeaderPin(21, "GPIO9", PinRole.SPI_MISO, gpio_bcm=9, position=_pin_positions[21]),
        HeaderPin(22, "GPIO25", PinRole.GPIO, gpio_bcm=25, position=_pin_positions[22]),
        # Pin 23-24
        HeaderPin(23, "GPIO11", PinRole.SPI_SCLK, gpio_bcm=11, position=_pin_positions[23]),
        HeaderPin(24, "GPIO8", PinRole.SPI_CE0, gpio_bcm=8, position=_pin_positions[24]),
        # Pin 25-26
        HeaderPin(25, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[25]),
        HeaderPin(26, "GPIO7", PinRole.SPI_CE1, gpio_bcm=7, position=_pin_positions[26]),
        # Pin 27-28
        HeaderPin(27, "GPIO0", PinRole.I2C_EEPROM, gpio_bcm=0, position=_pin_positions[27]),
        HeaderPin(28, "GPIO1", PinRole.I2C_EEPROM, gpio_bcm=1, position=_pin_positions[28]),
        # Pin 29-30
        HeaderPin(29, "GPIO5", PinRole.GPIO, gpio_bcm=5, position=_pin_positions[29]),
        HeaderPin(30, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[30]),
        # Pin 31-32
        HeaderPin(31, "GPIO6", PinRole.GPIO, gpio_bcm=6, position=_pin_positions[31]),
        HeaderPin(32, "GPIO12", PinRole.PWM, gpio_bcm=12, position=_pin_positions[32]),
        # Pin 33-34
        HeaderPin(33, "GPIO13", PinRole.PWM, gpio_bcm=13, position=_pin_positions[33]),
        HeaderPin(34, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[34]),
        # Pin 35-36
        HeaderPin(35, "GPIO19", PinRole.PCM_FS, gpio_bcm=19, position=_pin_positions[35]),
        HeaderPin(36, "GPIO16", PinRole.GPIO, gpio_bcm=16, position=_pin_positions[36]),
        # Pin 37-38
        HeaderPin(37, "GPIO26", PinRole.GPIO, gpio_bcm=26, position=_pin_positions[37]),
        HeaderPin(38, "GPIO20", PinRole.PCM_DIN, gpio_bcm=20, position=_pin_positions[38]),
        # Pin 39-40
        HeaderPin(39, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[39]),
        HeaderPin(40, "GPIO21", PinRole.PCM_DOUT, gpio_bcm=21, position=_pin_positions[40]),
    ]

    return Board(
        name="Raspberry Pi",
        pins=pins,
        svg_asset_path=_get_asset_path("pi2.svg"),
        width=205.42,
        height=307.46,
        header_offset=Point(23.715, 5.156),
    )


def raspberry_pi_zero_2w() -> Board:
    """
    Create a Raspberry Pi Zero 2 W board with 40-pin GPIO header.

    The Pi Zero 2 W has the same 40-pin GPIO header pinout as the Pi 5,
    but in a much smaller form factor (65mm × 30mm). The GPIO pins have
    tighter spacing (7.40 vs 12.0 row spacing) due to the compact design.

    Electrical differences (for reference, don't affect pinout):
    - Lower GPIO drive current (~8mA vs Pi 5's higher current with better ESD)
    - Fewer peripheral controllers (2 SPI vs 6, 2 I2C vs 4 on Pi 5)
    - Simpler power architecture (single PMIC vs Pi 5's multiple rails)
    - Direct BCM SoC GPIO vs Pi 5's RP1 I/O controller

    Pin layout matches Pi 5:
    - Top row (odd pins): 1, 3, 5, ..., 39 (left to right)
    - Bottom row (even pins): 2, 4, 6, ..., 40 (left to right)

    Returns:
        Board: Configured Raspberry Pi Zero 2 W board

    Examples:
        >>> from pinviz import boards
        >>> board = boards.raspberry_pi_zero_2w()
        >>> print(board.name)
        Raspberry Pi Zero 2 W
        >>> print(len(board.pins))
        40
    """
    # GPIO header positions for Pi Zero layout
    # Native SVG coordinates: left=134.10, right=142.20, start=34.00, spacing=7.50
    # Scaled by 1.6x to match Pi 5 pin spacing (12.0) for better visibility
    # This makes GPIO pins the same size as Pi 5 while maintaining aspect ratio
    left_col_x = 230.00  # X position for left column (odd pins)
    right_col_x = 253.00  # X position for right column (even pins)
    start_y = 75  # Starting Y position (top)
    row_spacing = 21.13  # Vertical spacing between rows (matches Pi 5)

    _pin_positions = {}

    # Generate positions for all 40 pins in vertical columns
    for row in range(20):  # 20 rows
        y_pos = start_y + (row * row_spacing)
        odd_pin = (row * 2) + 1  # Physical pins 1, 3, 5, ..., 39
        even_pin = (row * 2) + 2  # Physical pins 2, 4, 6, ..., 40

        _pin_positions[odd_pin] = Point(left_col_x, y_pos)  # Left column (odd)
        _pin_positions[even_pin] = Point(right_col_x, y_pos)  # Right column (even)

    # Pin definitions - IDENTICAL to Pi 5 (same 40-pin header pinout)
    pins = [
        # Pin 1-2
        HeaderPin(1, "3V3", PinRole.POWER_3V3, gpio_bcm=None, position=_pin_positions[1]),
        HeaderPin(2, "5V", PinRole.POWER_5V, gpio_bcm=None, position=_pin_positions[2]),
        # Pin 3-4
        HeaderPin(3, "GPIO2", PinRole.I2C_SDA, gpio_bcm=2, position=_pin_positions[3]),
        HeaderPin(4, "5V", PinRole.POWER_5V, gpio_bcm=None, position=_pin_positions[4]),
        # Pin 5-6
        HeaderPin(5, "GPIO3", PinRole.I2C_SCL, gpio_bcm=3, position=_pin_positions[5]),
        HeaderPin(6, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[6]),
        # Pin 7-8
        HeaderPin(7, "GPIO4", PinRole.GPIO, gpio_bcm=4, position=_pin_positions[7]),
        HeaderPin(8, "GPIO14", PinRole.UART_TX, gpio_bcm=14, position=_pin_positions[8]),
        # Pin 9-10
        HeaderPin(9, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[9]),
        HeaderPin(10, "GPIO15", PinRole.UART_RX, gpio_bcm=15, position=_pin_positions[10]),
        # Pin 11-12
        HeaderPin(11, "GPIO17", PinRole.GPIO, gpio_bcm=17, position=_pin_positions[11]),
        HeaderPin(12, "GPIO18", PinRole.PWM, gpio_bcm=18, position=_pin_positions[12]),
        # Pin 13-14
        HeaderPin(13, "GPIO27", PinRole.GPIO, gpio_bcm=27, position=_pin_positions[13]),
        HeaderPin(14, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[14]),
        # Pin 15-16
        HeaderPin(15, "GPIO22", PinRole.GPIO, gpio_bcm=22, position=_pin_positions[15]),
        HeaderPin(16, "GPIO23", PinRole.GPIO, gpio_bcm=23, position=_pin_positions[16]),
        # Pin 17-18
        HeaderPin(17, "3V3", PinRole.POWER_3V3, gpio_bcm=None, position=_pin_positions[17]),
        HeaderPin(18, "GPIO24", PinRole.GPIO, gpio_bcm=24, position=_pin_positions[18]),
        # Pin 19-20
        HeaderPin(19, "GPIO10", PinRole.SPI_MOSI, gpio_bcm=10, position=_pin_positions[19]),
        HeaderPin(20, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[20]),
        # Pin 21-22
        HeaderPin(21, "GPIO9", PinRole.SPI_MISO, gpio_bcm=9, position=_pin_positions[21]),
        HeaderPin(22, "GPIO25", PinRole.GPIO, gpio_bcm=25, position=_pin_positions[22]),
        # Pin 23-24
        HeaderPin(23, "GPIO11", PinRole.SPI_SCLK, gpio_bcm=11, position=_pin_positions[23]),
        HeaderPin(24, "GPIO8", PinRole.SPI_CE0, gpio_bcm=8, position=_pin_positions[24]),
        # Pin 25-26
        HeaderPin(25, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[25]),
        HeaderPin(26, "GPIO7", PinRole.SPI_CE1, gpio_bcm=7, position=_pin_positions[26]),
        # Pin 27-28
        HeaderPin(27, "GPIO0", PinRole.I2C_EEPROM, gpio_bcm=0, position=_pin_positions[27]),
        HeaderPin(28, "GPIO1", PinRole.I2C_EEPROM, gpio_bcm=1, position=_pin_positions[28]),
        # Pin 29-30
        HeaderPin(29, "GPIO5", PinRole.GPIO, gpio_bcm=5, position=_pin_positions[29]),
        HeaderPin(30, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[30]),
        # Pin 31-32
        HeaderPin(31, "GPIO6", PinRole.GPIO, gpio_bcm=6, position=_pin_positions[31]),
        HeaderPin(32, "GPIO12", PinRole.PWM, gpio_bcm=12, position=_pin_positions[32]),
        # Pin 33-34
        HeaderPin(33, "GPIO13", PinRole.PWM, gpio_bcm=13, position=_pin_positions[33]),
        HeaderPin(34, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[34]),
        # Pin 35-36
        HeaderPin(35, "GPIO19", PinRole.PCM_FS, gpio_bcm=19, position=_pin_positions[35]),
        HeaderPin(36, "GPIO16", PinRole.GPIO, gpio_bcm=16, position=_pin_positions[36]),
        # Pin 37-38
        HeaderPin(37, "GPIO26", PinRole.GPIO, gpio_bcm=26, position=_pin_positions[37]),
        HeaderPin(38, "GPIO20", PinRole.PCM_DIN, gpio_bcm=20, position=_pin_positions[38]),
        # Pin 39-40
        HeaderPin(39, "GND", PinRole.GROUND, gpio_bcm=None, position=_pin_positions[39]),
        HeaderPin(40, "GPIO21", PinRole.PCM_DOUT, gpio_bcm=21, position=_pin_positions[40]),
    ]

    return Board(
        name="Raspberry Pi Zero 2 W",
        pins=pins,
        svg_asset_path=_get_asset_path("pi_zero.svg"),
        width=465.60,  # SVG viewBox 291.0 scaled by 1.6x for better pin visibility
        height=931.20,  # SVG viewBox 582.0 scaled by 1.6x (matches Pi 5 pin spacing)
        header_offset=Point(0, 0),  # No offset needed - pins aligned to scaled SVG coordinates
    )


# Alias for convenience
def raspberry_pi() -> Board:
    """
    Create a Raspberry Pi board (alias for raspberry_pi_5()).

    Convenience function that returns the latest Raspberry Pi board.
    Currently points to Raspberry Pi 5.

    Returns:
        Board: Configured Raspberry Pi board

    Examples:
        >>> from pinviz import boards
        >>> board = boards.raspberry_pi()
        >>> print(board.name)
        Raspberry Pi
    """
    return raspberry_pi_5()
