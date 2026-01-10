# Adding New Boards to PinViz

This guide walks you through adding support for new boards to PinViz. The process takes approximately 15-30 minutes for Raspberry Pi boards with 40-pin GPIO headers.

## Overview

PinViz uses a JSON-based board configuration system that makes it easy to add new board types without modifying Python code. Board definitions are stored in `src/pinviz/board_configs/` directory.

## Quick Summary

For Raspberry Pi boards with 40-pin GPIO headers, you can copy an existing board's pin configuration since they all share the same GPIO pinout. This significantly simplifies the process.

## Board Configuration Structure

A board configuration JSON file contains:

```json
{
  "name": "Raspberry Pi 5",
  "svg_asset": "pi_5_mod.svg",
  "width": 205.42,
  "height": 307.46,
  "header_offset": {"x": 23.715, "y": 5.156},
  "layout": {
    "left_col_x": 187.1,
    "right_col_x": 199.1,
    "start_y": 16.2,
    "row_spacing": 12.0
  },
  "pins": [
    {"physical_pin": 1, "name": "3V3", "role": "3V3", "gpio_bcm": null},
    {"physical_pin": 2, "name": "5V", "role": "5V", "gpio_bcm": null},
    ...
  ]
}
```

## Step-by-Step Guide

### Step 1: Create or Obtain SVG Asset

1. Place your SVG file in `src/pinviz/assets/` (e.g., `raspberry_pi_4.svg`)
2. **Important:** For pin alignment, use similar viewBox dimensions to existing boards
   - Check existing SVG: `head -5 src/pinviz/assets/pi_5_mod.svg | grep viewBox`
   - Pi 5 uses: `viewBox="0 0 206 308"` - use same dimensions for consistent pin spacing

### Step 2: Create Board Configuration JSON

1. Create `src/pinviz/board_configs/raspberry_pi_4.json`
2. **For Raspberry Pi boards:** Copy from `raspberry_pi_5.json` and update:
   - `name`: "Raspberry Pi 4 Model B"
   - `svg_asset`: "pi_4_mod.svg"
   - Keep `width`, `height`, `layout`, and `pins` identical (they share the same GPIO pinout)
3. **For non-Raspberry Pi boards:** Define all pins manually with proper layout parameters

### Step 3: Add Factory Function

In `src/pinviz/boards.py`, add a factory function:

```python
def raspberry_pi_4() -> Board:
    """
    Create a Raspberry Pi 4 Model B board with 40-pin GPIO header.

    Uses standard 40-pin GPIO pinout (same as Pi 2, 3, 5, Zero 2 W).
    All GPIO pins operate at 3.3V logic levels and are NOT 5V tolerant.

    Returns:
        Board: Configured Raspberry Pi 4 Model B board with all pins positioned
    """
    return load_board_from_config("raspberry_pi_4")
```

### Step 4: Add Board Name Aliases

In `src/pinviz/config_loader.py`, update `_load_board_by_name()`:

```python
board_loaders = {
    # Raspberry Pi 5
    "raspberry_pi_5": boards.raspberry_pi_5,
    "rpi5": boards.raspberry_pi_5,
    # Raspberry Pi 4 - ADD THESE LINES
    "raspberry_pi_4": boards.raspberry_pi_4,
    "rpi4": boards.raspberry_pi_4,
    "pi4": boards.raspberry_pi_4,
    # Aliases
    "raspberry_pi": boards.raspberry_pi,
    "rpi": boards.raspberry_pi,
}
```

Also update the docstring to document the supported board names.

### Step 5: Update Schema Validation

In `src/pinviz/schemas.py`, update `VALID_BOARD_NAMES`:

```python
VALID_BOARD_NAMES = {
    "raspberry_pi_5",
    "raspberry_pi_4",  # ADD THIS LINE
    "raspberry_pi",
    "rpi5",
    "rpi4",            # ADD THIS LINE
    "pi4",             # ADD THIS LINE
    "rpi",
}
```

### Step 6: Add Tests

In `tests/test_boards.py`, add comprehensive tests:

```python
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

    for pin_num in range(1, 41):
        pi4_pin = pi4.get_pin_by_number(pin_num)
        pi5_pin = pi5.get_pin_by_number(pin_num)

        assert pi4_pin.role == pi5_pin.role
        assert pi4_pin.gpio_bcm == pi5_pin.gpio_bcm
        assert pi4_pin.name == pi5_pin.name
```

In `tests/test_config_loader.py`, add alias tests:

```python
@pytest.mark.parametrize(
    "board_name",
    ["raspberry_pi_4", "rpi4", "pi4", "RPI4", "PI4"],
)
def test_load_raspberry_pi_4_by_name(board_name):
    """Test loading Raspberry Pi 4 board by various name aliases."""
    config = {
        "title": "Test",
        "board": board_name,
        "devices": [],
        "connections": [],
    }
    loader = ConfigLoader()
    diagram = loader.load_from_dict(config)

    assert diagram.board is not None
    assert diagram.board.name == "Raspberry Pi 4 Model B"
```

### Step 7: Verify and Test

```bash
# Test the new board
uv run python -c "from pinviz import boards; print(boards.raspberry_pi_4().name)"

# Run specific tests
uv run pytest tests/test_boards.py::test_raspberry_pi_4_board_creation -v
uv run pytest tests/test_config_loader.py::test_load_raspberry_pi_4_by_name -v

# Run full test suite
uv run pytest

# Format and lint
uv run ruff format .
uv run ruff check .
```

## Implementation Checklist

Use this checklist to ensure you've completed all steps:

- [ ] SVG asset created/obtained in `src/pinviz/assets/`
- [ ] Board configuration JSON created in `src/pinviz/board_configs/`
- [ ] Factory function added to `src/pinviz/boards.py`
- [ ] Board aliases added to `src/pinviz/config_loader.py`
- [ ] Schema validation updated in `src/pinviz/schemas.py`
- [ ] Tests added to `tests/test_boards.py`
- [ ] Alias tests added to `tests/test_config_loader.py`
- [ ] All tests passing (477+ tests)
- [ ] Code formatted with ruff
- [ ] Example diagrams generated in `out/` directory

## Board Configuration Validation

All board configurations are validated against `BoardConfigSchema` in `schemas.py`:

- Pin numbers must be sequential (1, 2, 3, ...)
- Pin roles must be valid (GPIO, I2C_SDA, PWM, etc.)
- Layout parameters must be positive numbers
- Right column X must be greater than left column X

## Configuration Reference

### Pin Roles

Supported pin roles for automatic color assignment:

- `3V3`, `5V` - Power rails
- `GND` - Ground
- `GPIO` - General purpose I/O
- `I2C_SDA`, `I2C_SCL` - I2C bus
- `SPI_MOSI`, `SPI_MISO`, `SPI_SCLK`, `SPI_CE0`, `SPI_CE1` - SPI bus
- `UART_TX`, `UART_RX` - UART serial
- `PWM` - PWM output

### Layout Parameters

- `left_col_x`, `right_col_x`: X coordinates for left and right pin columns
- `start_y`: Y coordinate for the first pin
- `row_spacing`: Vertical spacing between pins

## Troubleshooting

### Issue: Pin Alignment is Off

**Solution:** Ensure your SVG viewBox dimensions match existing boards (typically `0 0 206 308`). Different viewBox dimensions will cause misalignment.

### Issue: Tests Fail with Pin Role Mismatch

**Solution:** Verify that your pin configuration matches the physical board. For Raspberry Pi boards, copy the exact pin configuration from an existing 40-pin board.

### Issue: Schema Validation Errors

**Solution:** Run `uv run pytest tests/test_schemas.py -v` to see specific validation errors. Common issues:

- Non-sequential pin numbers
- Invalid pin roles
- Negative layout parameters

## Need Help?

- Check existing board configurations in `src/pinviz/board_configs/` for examples
- Review the full architecture documentation in `CLAUDE.md`
- Open an issue on GitHub: <https://github.com/nordstad/PinViz/issues>
- Refer to the API documentation: <https://nordstad.github.io/PinViz/api/>

## Contributing Your Board

Once you've successfully added a new board:

1. Test it thoroughly with multiple example configurations
2. Generate example diagrams and save them to `out/` directory
3. Submit a pull request with:
   - Board configuration JSON
   - Factory function and tests
   - Example diagrams
   - Updated documentation

See [Contributing Guide](https://nordstad.github.io/PinViz/development/contributing/) for full details.
