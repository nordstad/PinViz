"""Predefined Raspberry Pi board templates."""

import json
from pathlib import Path

from .model import Board, HeaderPin, PinRole, Point
from .schemas import BoardConfigSchema, validate_board_config


def _get_asset_path(filename: str) -> str:
    """
    Get the absolute path to an asset file.

    Resolves the path to an SVG asset file in the package assets directory.
    Used internally by board factory functions to locate board SVG images.

    Args:
        filename: Name of the asset file (e.g., "pi_5_mod.svg")

    Returns:
        Absolute path to the asset file as a string

    Note:
        This is an internal function. Users typically don't need to call this directly.
    """
    module_dir = Path(__file__).parent
    asset_path = module_dir / "assets" / filename
    return str(asset_path)


def _get_board_config_path(config_name: str) -> Path:
    """
    Get the path to a board configuration file.

    Args:
        config_name: Name of the board configuration (e.g., "raspberry_pi_5")

    Returns:
        Path to the board configuration JSON file

    Note:
        This is an internal function. Users typically don't need to call this directly.
    """
    module_dir = Path(__file__).parent
    config_path = module_dir / "board_configs" / f"{config_name}.json"
    return config_path


def _calculate_dual_header_positions(layout_dict: dict, pins: list) -> dict[int, Point]:
    """
    Calculate pin positions for dual-header boards (e.g., Raspberry Pi Pico).

    Dual-header boards have horizontal pin layouts with pins arranged along
    top and bottom edges. The top header typically has reversed pin numbering
    (e.g., pin 20 on left, pin 1 on right) while the bottom header has normal
    ordering (e.g., pin 21 on left, pin 40 on right).

    Args:
        layout_dict: Layout configuration containing top_header and bottom_header
                    specifications with start_x, pin_spacing, and y coordinates
        pins: List of pin configuration objects with physical_pin and header attributes

    Returns:
        Dictionary mapping physical pin numbers to Point positions

    Raises:
        ValueError: If a pin has an invalid header side (not 'top' or 'bottom')

    Note:
        This is an internal function used by load_board_from_config().
    """
    pin_positions = {}

    for pin_config in pins:
        header_side = getattr(pin_config, "header", None)

        if header_side == "top":
            # Top header: pins in a single horizontal row
            # Note: Pins are in REVERSE order (higher pin numbers on left)
            header_layout = layout_dict["top_header"]
            pin_num = pin_config.physical_pin

            # Calculate X position: reversed order
            x_pos = header_layout["start_x"] + ((20 - pin_num) * header_layout["pin_spacing"])
            # Fixed Y position for all top header pins
            y_pos = header_layout["y"]

        elif header_side == "bottom":
            # Bottom header: pins in a single horizontal row
            header_layout = layout_dict["bottom_header"]
            pin_num = pin_config.physical_pin

            # Calculate X position: each pin increments horizontally
            x_pos = header_layout["start_x"] + ((pin_num - 21) * header_layout["pin_spacing"])
            # Fixed Y position for all bottom header pins
            y_pos = header_layout["y"]
        else:
            raise ValueError(
                f"Pin {pin_config.physical_pin} has invalid header side: {header_side}. "
                f"Expected 'top' or 'bottom'."
            )

        pin_positions[pin_config.physical_pin] = Point(x_pos, y_pos)

    return pin_positions


def _calculate_single_header_positions(layout_dict: dict, pins: list) -> dict[int, Point]:
    """
    Calculate pin positions for single-header boards (e.g., Raspberry Pi 4/5).

    Single-header boards have the standard Raspberry Pi GPIO layout with two
    vertical columns:
    - Left column (odd pins): 1, 3, 5, ..., N-1 (top to bottom)
    - Right column (even pins): 2, 4, 6, ..., N (top to bottom)

    Args:
        layout_dict: Layout configuration containing left_col_x, right_col_x,
                    start_y, and row_spacing values
        pins: List of pin configuration objects (used to determine number of rows)

    Returns:
        Dictionary mapping physical pin numbers to Point positions

    Note:
        This is an internal function used by load_board_from_config().
    """
    pin_positions = {}
    num_rows = len(pins) // 2  # 20 rows for 40-pin header

    for row in range(num_rows):
        y_pos = layout_dict["start_y"] + (row * layout_dict["row_spacing"])
        odd_pin = (row * 2) + 1  # Physical pins 1, 3, 5, ...
        even_pin = (row * 2) + 2  # Physical pins 2, 4, 6, ...

        pin_positions[odd_pin] = Point(layout_dict["left_col_x"], y_pos)  # Left column
        pin_positions[even_pin] = Point(layout_dict["right_col_x"], y_pos)  # Right column

    return pin_positions


def load_board_from_config(config_name: str) -> Board:
    """
    Load a board definition from a JSON configuration file.

    This function reads a board configuration from the board_configs directory,
    validates it against the BoardConfigSchema, calculates pin positions based
    on layout parameters, and returns a fully configured Board object.

    The configuration file must specify:
    - Board metadata (name, SVG asset, dimensions)
    - GPIO header layout parameters (column positions, spacing)
    - Pin definitions (physical pin number, name, role, BCM GPIO number)

    Pin positions are calculated automatically based on the layout parameters
    to align with the board's SVG asset.

    Args:
        config_name: Name of the board configuration file (without .json extension)
                    For example, "raspberry_pi_5" will load "raspberry_pi_5.json"

    Returns:
        Board: Configured board with all pins positioned

    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        ValueError: If the configuration is invalid or fails validation
        json.JSONDecodeError: If the JSON file is malformed

    Examples:
        >>> board = load_board_from_config("raspberry_pi_5")
        >>> print(board.name)
        Raspberry Pi 5
        >>> print(len(board.pins))
        40

    Note:
        This is the recommended way to add new board types. Simply create a new
        JSON configuration file in the board_configs directory following the
        schema defined in BoardConfigSchema.
    """
    config_path = _get_board_config_path(config_name)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Board configuration file not found: {config_path}. "
            f"Available configurations should be placed in the board_configs directory."
        )

    try:
        with open(config_path) as f:
            config_dict = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in board configuration file {config_path}: {e}") from e

    # Validate configuration against schema
    try:
        config: BoardConfigSchema = validate_board_config(config_dict)
    except Exception as e:
        raise ValueError(f"Invalid board configuration in {config_path}: {e}") from e

    # Calculate pin positions based on layout parameters
    # Check if this is a dual-header board (like Pico) or single-header (like Pi 5)
    layout_dict = config.layout if isinstance(config.layout, dict) else config.layout.__dict__
    is_dual_header = (
        layout_dict.get("top_header") is not None and layout_dict.get("bottom_header") is not None
    )

    # Use appropriate position calculation method based on board type
    if is_dual_header:
        pin_positions = _calculate_dual_header_positions(layout_dict, config.pins)
    else:
        pin_positions = _calculate_single_header_positions(layout_dict, config.pins)

    # Create HeaderPin objects from configuration
    pins = []
    for pin_config in config.pins:
        pin_role = PinRole(pin_config.role)  # Convert string to PinRole enum
        position = pin_positions.get(pin_config.physical_pin)

        if position is None:
            raise ValueError(
                f"Could not calculate position for pin {pin_config.physical_pin}. "
                f"Pin number may be out of range for the configured layout."
            )

        header_pin = HeaderPin(
            number=pin_config.physical_pin,
            name=pin_config.name,
            role=pin_role,
            gpio_bcm=pin_config.gpio_bcm,
            position=position,
        )
        pins.append(header_pin)

    # Sort pins by physical pin number for consistency
    pins.sort(key=lambda p: p.number)

    return Board(
        name=config.name,
        pins=pins,
        svg_asset_path=_get_asset_path(config.svg_asset),
        width=config.width,
        height=config.height,
        header_offset=Point(config.header_offset.x, config.header_offset.y),
        layout=None,  # Using SVG asset instead of programmatic rendering
    )


def raspberry_pi_5() -> Board:
    """
    Create a Raspberry Pi 5 board with 40-pin GPIO header.

    This function loads the board definition from a JSON configuration file
    (raspberry_pi_5.json) which specifies pin layout, positions, and metadata.
    Pin positions are calculated automatically to align with the board's SVG asset.

    Pin layout (physical pin numbers):
    Standard 2x20 header layout:
    - Left column (odd pins): 1, 3, 5, ..., 39 (top to bottom)
    - Right column (even pins): 2, 4, 6, ..., 40 (top to bottom)

    Returns:
        Board: Configured Raspberry Pi 5 board with all pins positioned

    Examples:
        >>> board = raspberry_pi_5()
        >>> print(board.name)
        Raspberry Pi 5
        >>> print(len(board.pins))
        40
        >>> # Get a specific pin by physical number
        >>> pin_1 = board.get_pin(1)
        >>> print(pin_1.name, pin_1.role)
        3V3 PinRole.POWER_3V3
    """
    return load_board_from_config("raspberry_pi_5")


def raspberry_pi_4() -> Board:
    """
    Create a Raspberry Pi 4 Model B board with 40-pin GPIO header.

    Uses standard 40-pin GPIO pinout (same as Pi 2, 3, 5, Zero 2 W).
    All GPIO pins operate at 3.3V logic levels and are NOT 5V tolerant.

    This function loads the board definition from a JSON configuration file
    (raspberry_pi_4.json) which specifies pin layout, positions, and metadata.
    Pin positions are calculated automatically to align with the board's SVG asset.

    Pin layout (physical pin numbers):
    Standard 2x20 header layout:
    - Left column (odd pins): 1, 3, 5, ..., 39 (top to bottom)
    - Right column (even pins): 2, 4, 6, ..., 40 (top to bottom)

    Returns:
        Board: Configured Raspberry Pi 4 Model B board with all pins positioned

    Examples:
        >>> board = raspberry_pi_4()
        >>> print(board.name)
        Raspberry Pi 4 Model B
        >>> print(len(board.pins))
        40

    Note:
        WARNING: All Raspberry Pi GPIO pins operate at 3.3V logic levels.
        GPIO pins are NOT 5V tolerant. Applying 5V to any GPIO pin may
        permanently damage the board. Use level shifters for 5V devices.
    """
    return load_board_from_config("raspberry_pi_4")


def raspberry_pi_pico() -> Board:
    """
    Create a Raspberry Pi Pico board with dual 20-pin GPIO headers.

    The Pico has a unique dual-sided layout with 40 pins total:
    - Top header: pins 1-20 (single row along top edge)
    - Bottom header: pins 21-40 (single row along bottom edge)

    Unlike the standard Raspberry Pi, the Pico uses RP2040 microcontroller
    with GP0-GP28 GPIO pins instead of BCM numbering.

    This function loads the board definition from a JSON configuration file
    (raspberry_pi_pico.json) which specifies the dual-header layout.

    Pin layout (physical pin numbers):
    - Top header: pins 1-20 (pin 20 on left, pin 1 on right - reversed order)
    - Bottom header: pins 21-40 (pin 21 on left, pin 40 on right - normal order)

    Returns:
        Board: Configured Raspberry Pi Pico board with all pins positioned

    Examples:
        >>> board = raspberry_pi_pico()
        >>> print(board.name)
        Raspberry Pi Pico
        >>> print(len(board.pins))
        40

    Note:
        The Pico operates at 3.3V logic levels. Some pins support 5V input
        with appropriate voltage dividers. Check the Pico datasheet for
        specific pin capabilities.
    """
    return load_board_from_config("raspberry_pi_pico")


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


def get_available_boards() -> list[dict[str, str | list[str]]]:
    """
    Get a list of all available board configurations.

    Scans the board_configs directory and returns metadata for each board
    including its canonical name and aliases.

    Returns:
        List of dictionaries with board information:
        - name: Canonical board configuration name (e.g., "raspberry_pi_5")
        - display_name: Human-readable board name (e.g., "Raspberry Pi 5")
        - aliases: List of alternative names for the board

    Examples:
        >>> boards_info = get_available_boards()
        >>> for board in boards_info:
        ...     print(f"{board['name']}: {board['aliases']}")
        raspberry_pi_5: ['rpi5', 'rpi']
        raspberry_pi_4: ['rpi4', 'pi4']
        raspberry_pi_pico: ['pico']

    Note:
        This function dynamically discovers boards from the board_configs
        directory, so it will automatically include any newly added boards.
    """
    # Map of board config names to their aliases
    # This could be extracted to a separate config file if needed
    board_aliases = {
        "raspberry_pi_5": ["rpi5", "rpi"],
        "raspberry_pi_4": ["rpi4", "pi4"],
        "raspberry_pi_pico": ["pico"],
    }

    boards_list = []
    module_dir = Path(__file__).parent
    config_dir = module_dir / "board_configs"

    if config_dir.exists():
        for config_file in sorted(config_dir.glob("*.json")):
            board_name = config_file.stem  # e.g., "raspberry_pi_5"

            # Load the config to get the display name
            try:
                with open(config_file) as f:
                    config_dict = json.load(f)
                display_name = config_dict.get("name", board_name)
            except (json.JSONDecodeError, OSError):
                display_name = board_name

            boards_list.append(
                {
                    "name": board_name,
                    "display_name": display_name,
                    "aliases": board_aliases.get(board_name, []),
                }
            )

    return boards_list
