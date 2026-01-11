# Adding a New Board to PinViz

This guide walks you through adding support for a new board type to PinViz. The process takes approximately 15-30 minutes for Raspberry Pi boards (which share the same GPIO pinout), or 1-2 hours for completely new board types.

## Prerequisites

- SVG asset file of the board
- Board pinout documentation (pin numbers, roles, BCM GPIO numbers if applicable)
- Basic understanding of the board's physical dimensions

## Quick Start (Raspberry Pi Boards)

**All modern Raspberry Pi boards (Pi 2, 3, 4, 5) share the identical 40-pin GPIO pinout.** This means you can copy the pin configuration from an existing board and only update the board name and SVG asset.

### Example: Adding Raspberry Pi 4

```bash
# 1. Place SVG asset
cp path/to/pi_4_mod.svg src/pinviz/assets/

# 2. Copy and modify board config
cp src/pinviz/board_configs/raspberry_pi_5.json \
   src/pinviz/board_configs/raspberry_pi_4.json

# Edit raspberry_pi_4.json:
#   - Change "name" to "Raspberry Pi 4 Model B"
#   - Change "svg_asset" to "pi_4_mod.svg"
#   - Keep everything else the same (identical GPIO pinout)
```

Then follow the detailed steps below to update code files and add tests.

## Detailed Step-by-Step Guide

### Step 1: Prepare SVG Asset

#### Option A: Using Existing SVG

1. Obtain or create an SVG file of the board
2. Ensure the SVG shows the GPIO header clearly
3. **Critical:** The SVG viewBox dimensions should match existing boards for pin alignment
   ```bash
   # Check existing board dimensions
   head -5 src/pinviz/assets/pi_5_mod.svg | grep viewBox
   # Output: viewBox="0 0 206 308"
   ```

4. Place the SVG file in `src/pinviz/assets/`:
   ```bash
   cp path/to/your_board.svg src/pinviz/assets/board_name_mod.svg
   ```

#### Option B: Creating SVG from Scratch

If creating a new SVG:
- Use the same viewBox dimensions as existing boards for consistency
- Position the GPIO header in a similar location
- Keep the design simple and clear

### Step 2: Create Board Configuration JSON

Create a new JSON file in `src/pinviz/board_configs/`:

```bash
touch src/pinviz/board_configs/raspberry_pi_4.json
```

#### For Raspberry Pi Boards (Identical GPIO Pinout)

Copy an existing Raspberry Pi board configuration:

```bash
cp src/pinviz/board_configs/raspberry_pi_5.json \
   src/pinviz/board_configs/raspberry_pi_4.json
```

Edit the new file and **only** change:
```json
{
  "name": "Raspberry Pi 4 Model B",    // Change this
  "svg_asset": "pi_4_mod.svg",         // Change this
  "width": 205.42,                     // Keep same for pin alignment
  "height": 307.46,                    // Keep same for pin alignment
  "header_offset": {                   // Keep same
    "x": 23.715,
    "y": 5.156
  },
  "layout": {                          // Keep same
    "left_col_x": 187.1,
    "right_col_x": 199.1,
    "start_y": 16.2,
    "row_spacing": 12.0
  },
  "pins": [                            // Keep same - identical GPIO
    {"physical_pin": 1, "name": "3V3", "role": "3V3", "gpio_bcm": null},
    {"physical_pin": 2, "name": "5V", "role": "5V", "gpio_bcm": null},
    // ... all 40 pins identical
  ]
}
```

#### For Non-Raspberry Pi Boards

You'll need to define all pins manually. Use this template:

```json
{
  "name": "Your Board Name",
  "svg_asset": "your_board.svg",
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
    {"physical_pin": 1, "name": "PIN_NAME", "role": "ROLE", "gpio_bcm": null_or_number},
    // Define all pins...
  ]
}
```

**Valid pin roles:**
- `"3V3"` - 3.3V power
- `"5V"` - 5V power
- `"GND"` - Ground
- `"GPIO"` - General purpose I/O
- `"I2C_SDA"` - I2C data line
- `"I2C_SCL"` - I2C clock line
- `"SPI_MOSI"` - SPI master out slave in
- `"SPI_MISO"` - SPI master in slave out
- `"SPI_SCLK"` - SPI clock
- `"SPI_CE0"`, `"SPI_CE1"` - SPI chip enable
- `"UART_TX"`, `"UART_RX"` - UART transmit/receive
- `"PWM"` - Pulse width modulation
- `"I2C_EEPROM"` - HAT ID EEPROM (reserved)
- `"PCM_FS"`, `"PCM_DIN"`, `"PCM_DOUT"` - PCM audio

### Step 3: Add Factory Function

Open `src/pinviz/boards.py` and add a new factory function at the end (before the aliases):

```python
def raspberry_pi_4() -> Board:
    """
    Create a Raspberry Pi 4 Model B board with 40-pin GPIO header.

    Uses standard 40-pin GPIO pinout (same as Pi 2, 3, 5).
    All GPIO pins operate at 3.3V logic levels and are NOT 5V tolerant.

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
```

**Key points:**
- Function name should be lowercase with underscores (e.g., `raspberry_pi_4`)
- Include comprehensive docstring with warnings if applicable
- Use `load_board_from_config()` with the config file name (without `.json`)

### Step 4: Add Board Name Aliases

Open `src/pinviz/config_loader.py` and find the `_load_board_by_name()` method (around line 194).

1. **Update the `board_loaders` dictionary:**
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

2. **Update the docstring** (around line 209):
   ```python
   Supported names:
       - "raspberry_pi_5", "rpi5": Raspberry Pi 5
       - "raspberry_pi_4", "rpi4", "pi4": Raspberry Pi 4 Model B
       - "raspberry_pi", "rpi": Latest Raspberry Pi (currently Pi 5)
   ```

**Alias naming conventions:**
- Full name: `"raspberry_pi_4"`
- Short name: `"rpi4"`
- Very short: `"pi4"` (optional)
- All aliases are case-insensitive

### Step 5: Update Schema Validation

Open `src/pinviz/schemas.py` and find `VALID_BOARD_NAMES` (around line 36).

Add your board aliases:
```python
VALID_BOARD_NAMES = {
    "raspberry_pi_5",
    "raspberry_pi_4",  # ADD THIS
    "raspberry_pi",
    "rpi5",
    "rpi4",            # ADD THIS
    "pi4",             # ADD THIS
    "rpi",
}
```

**Important:** Add all aliases you defined in Step 4, otherwise schema validation will fail.

### Step 6: Add Tests

#### Basic Board Tests

Open `tests/test_boards.py` and add these tests at the end:

```python
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
```

#### Alias Tests

Open `tests/test_config_loader.py` and add:

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

### Step 7: Test and Verify

Run through this verification checklist:

```bash
# 1. Test board loads correctly
uv run python -c "from pinviz import boards; print(boards.raspberry_pi_4().name)"
# Expected: Raspberry Pi 4 Model B

# 2. Test pin count
uv run python -c "from pinviz import boards; print(len(boards.raspberry_pi_4().pins))"
# Expected: 40

# 3. Run new board tests
uv run pytest tests/test_boards.py::test_raspberry_pi_4_board_creation -v
uv run pytest tests/test_boards.py::test_raspberry_pi_4_has_40_pins -v
uv run pytest tests/test_boards.py::test_raspberry_pi_4_identical_pinout_to_pi5 -v

# 4. Run alias tests
uv run pytest tests/test_config_loader.py::test_load_raspberry_pi_4_by_name -v

# 5. Run full test suite (should all pass)
uv run pytest
# Expected: 477+ tests passed

# 6. Format and lint code
uv run ruff format .
uv run ruff check .
```

### Step 8: Create Example Diagrams

Generate a few example diagrams to verify the board works correctly:

```bash
# Create test YAML
cat > /tmp/test_pi4.yaml << 'EOF'
title: "Raspberry Pi 4 Test - BH1750 Light Sensor"
board: "rpi4"
devices:
  - type: "bh1750"
    name: "Light Sensor"
connections:
  - board_pin: 1
    device: "Light Sensor"
    device_pin: "VCC"
  - board_pin: 3
    device: "Light Sensor"
    device_pin: "SDA"
  - board_pin: 5
    device: "Light Sensor"
    device_pin: "SCL"
  - board_pin: 6
    device: "Light Sensor"
    device_pin: "GND"
show_legend: true
EOF

# Generate diagram
uv run pinviz render /tmp/test_pi4.yaml -o out/pi4_test.svg

# Verify SVG was created
ls -lh out/pi4_test.svg
```

Create multiple examples:
- Simple LED circuit
- I2C device connection
- SPI device connection
- Multi-device wiring

## Final Checklist

Before considering the board addition complete:

- [ ] SVG asset placed in `src/pinviz/assets/`
- [ ] Board configuration JSON created in `src/pinviz/board_configs/`
- [ ] Factory function added to `src/pinviz/boards.py` with comprehensive docstring
- [ ] Board aliases added to `src/pinviz/config_loader.py` (both dictionary and docstring)
- [ ] Schema validation updated in `src/pinviz/schemas.py` (all aliases)
- [ ] Basic tests added to `tests/test_boards.py` (at least 3-5 tests)
- [ ] Alias tests added to `tests/test_config_loader.py` (parameterized test)
- [ ] All tests passing: `uv run pytest` shows 477+ passed
- [ ] Code formatted: `uv run ruff format .`
- [ ] Code linted: `uv run ruff check .` passes
- [ ] Example diagrams generated successfully in `out/` directory
- [ ] Visual inspection of generated SVGs confirms proper pin alignment

## Files Modified Summary

For each new board, you'll modify exactly these files:

1. **New files created (2):**
   - `src/pinviz/assets/board_name_mod.svg`
   - `src/pinviz/board_configs/board_name.json`

2. **Code files modified (3):**
   - `src/pinviz/boards.py` - Add factory function
   - `src/pinviz/config_loader.py` - Add aliases
   - `src/pinviz/schemas.py` - Add to VALID_BOARD_NAMES

3. **Test files modified (2):**
   - `tests/test_boards.py` - Add board tests
   - `tests/test_config_loader.py` - Add alias tests

**Total: 2 new files + 5 modified files**

## Common Issues and Solutions

### Issue: Schema validation fails with "Invalid board name"

**Solution:** Make sure you added ALL aliases to `VALID_BOARD_NAMES` in `src/pinviz/schemas.py`.

### Issue: Pin positions don't align with SVG

**Solution:**
1. Check that SVG viewBox dimensions match existing boards
2. Verify `layout` parameters in JSON config match the SVG GPIO header position
3. Use `head -5 src/pinviz/assets/your_board.svg | grep viewBox` to check dimensions

### Issue: Tests fail with "Board not found"

**Solution:** Ensure the config file name matches what you pass to `load_board_from_config()` (without `.json` extension).

### Issue: Import error for boards.raspberry_pi_4

**Solution:** Make sure you added the factory function to `src/pinviz/boards.py` and it's properly indented at module level.

## Tips for Success

1. **Start with a working board:** Copy an existing Raspberry Pi config if you're adding another Raspberry Pi variant
2. **Test frequently:** Run tests after each step to catch issues early
3. **Check existing examples:** Look at how `raspberry_pi_5` is implemented as a reference
4. **Use descriptive names:** Board names should be clear and include the model (e.g., "Raspberry Pi 4 Model B")
5. **Document safety warnings:** Include voltage and safety information in docstrings
6. **Generate multiple examples:** Create 3-4 example diagrams to verify different scenarios work

## Time Estimates

- **Raspberry Pi board (shared GPIO):** 15-30 minutes
- **New board type (unique GPIO):** 1-2 hours
- **Adding tests:** 15-20 minutes
- **Creating example diagrams:** 10-15 minutes

**Total for Raspberry Pi board:** ~45-60 minutes
**Total for completely new board:** ~2-3 hours

## Getting Help

If you encounter issues:

1. Check this guide thoroughly
2. Review the implementation of `raspberry_pi_5` as a reference
3. Run `uv run pytest -v` to see detailed test failures
4. Check the logs when running `uv run pinviz render`
5. Verify all file modifications were made correctly

## Next Steps After Adding a Board

Consider:
- Updating README.md with the new board
- Adding board-specific examples to `examples/` directory
- Documenting any board-specific quirks or limitations
- Creating a pull request if contributing to the project
