# Adding a New Board

Board definitions are stored in JSON files in `src/pinviz/board_configs/` directory.

**Quick Summary:** For Raspberry Pi boards with 40-pin GPIO headers, you can copy an existing board's pin configuration since they all share the same GPIO pinout. This takes ~15-30 minutes.

## Standard Board Configuration

### Board JSON Structure

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

## Dual-Sided Board Configuration (Pico-style)

Boards with GPIO pins on multiple edges (like Raspberry Pi Pico) use horizontal pin rows instead of vertical columns.

```json
{
  "name": "Raspberry Pi Pico",
  "svg_asset": "pico_mod.svg",
  "width": 249.0,
  "height": 101.0,
  "header_offset": {"x": 0, "y": 0},
  "layout": {
    "top_header": {
      "start_x": 8.0,
      "pin_spacing": 12.0,
      "y": 6.5
    },
    "bottom_header": {
      "start_x": 8.0,
      "pin_spacing": 12.0,
      "y": 94.0
    }
  },
  "pins": [
    {"physical_pin": 1, "name": "GP0", "role": "GPIO", "gpio_bcm": 0, "header": "top"},
    {"physical_pin": 2, "name": "GP1", "role": "GPIO", "gpio_bcm": 1, "header": "top"},
    ...
    {"physical_pin": 21, "name": "GP16", "role": "GPIO", "gpio_bcm": 16, "header": "bottom"},
    ...
  ]
}
```

**Key Differences:**

1. **Layout Structure**: Uses `top_header` and `bottom_header` instead of `left_col_x`/`right_col_x`
2. **Pin Positioning**: Horizontal rows (X increments, Y fixed per header) instead of vertical columns
3. **Header Field**: Each pin requires a `"header"` field indicating `"top"` or `"bottom"`
4. **Pin Numbering**:
   - Top header: pins 1-20 (pin 20 on left, pin 1 on right - **reversed order**)
   - Bottom header: pins 21-40 (pin 21 on left, pin 40 on right - normal order)

## Step-by-Step Guide

### Step 1: Create or Obtain SVG Asset

1. Place SVG file in `src/pinviz/assets/` (e.g., `raspberry_pi_4.svg`)
2. **Important:** For pin alignment, the SVG should have similar viewBox dimensions to existing boards
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

In `src/pinviz/boards.py`, add:

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

Also update the docstring with supported names.

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

In `tests/test_boards.py`, add:

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

In `tests/test_config_loader.py`, add:

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

# Run tests
uv run pytest tests/test_boards.py::test_raspberry_pi_4_board_creation -v
uv run pytest tests/test_config_loader.py::test_load_raspberry_pi_4_by_name -v

# Run full test suite
uv run pytest

# Format and lint
uv run ruff format .
uv run ruff check .
```

## Checklist

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
