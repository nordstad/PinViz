# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`pinviz` is a Python package that programmatically generates Raspberry Pi GPIO connection diagrams in SVG format. It supports both declarative YAML/JSON configuration and programmatic Python API for creating wiring diagrams.

## Development Environment

This project uses `uv` as the package manager and build tool.

### Setup and Build
```bash
# Install dependencies (including dev dependencies)
uv sync --dev

# Run the CLI tool
uv run pinviz <command>
```

### Code Quality
```bash
# Lint and format with ruff
uv run ruff check .
uv run ruff format .

# Run tests
uv run pytest
```

## CLI Commands

The main CLI entry point is `pinviz`:

```bash
# Generate diagram from YAML config
pinviz render examples/bh1750.yaml -o output.svg

# Generate built-in examples
pinviz example bh1750 -o images/bh1750.svg
pinviz example ir_led -o images/ir_led.svg
pinviz example i2c_spi -o images/i2c_spi.svg

# List available templates
pinviz list

# Create new device interactively
pinviz add-device
```

## Architecture

### Core Data Model (`model.py`)
- **Immutable entities**: Uses dataclasses for `Board`, `Device`, `HeaderPin`, `DevicePin`, `Connection`, `Diagram`
- **PinRole enum**: Defines pin functions (GPIO, I2C, SPI, UART, PWM, power, ground)
- **DEFAULT_COLORS dict**: Maps pin roles to wire colors for automatic color assignment
- **WireStyle enum**: Defines wire routing styles (orthogonal, curved, mixed)

### Component Factory Modules
- **`boards.py`**: Board templates loaded from JSON configs in `board_configs/`
  - Pin positions are pre-calculated based on physical GPIO header layout
  - Pins have physical pin numbers (1-40), BCM GPIO numbers, names, and roles
- **`devices/registry.py`**: Device template registry with dual-path support:
  - **Primary**: JSON configs from `device_configs/` (recommended)
  - **Fallback**: Python factory functions (backward compatibility, deprecated)
- **`devices/loader.py`**: JSON device loader with smart defaults system
  - Auto-calculates pin positions (vertical/horizontal layouts)
  - Auto-calculates device dimensions based on pin count
  - Category-based color defaults (sensors=turquoise, LEDs=red, etc.)
  - Parameter substitution support (e.g., LED colors, device names)

### Configuration Loading (`config_loader.py`)
- **ConfigLoader class**: Parses YAML/JSON files into diagram objects
- Supports both predefined device types (by name) and custom device definitions
- Board selection by name alias (e.g., "raspberry_pi_5", "rpi5", "rpi")
- Auto-assigns wire colors based on pin roles if not specified

### Layout Engine (`layout.py`)
- **LayoutEngine class**: Positions devices and routes wires algorithmically
- **Device positioning**: Stacks devices vertically on the right side of the board
- **Wire routing**: Orthogonal routing with rounded corners
  - Wires routed through a "rail" to the right of the GPIO header
  - Parallel wires from the same pin get automatic offset to prevent overlap
  - Path calculation handles three routing styles: orthogonal, curved, mixed
- **LayoutConfig**: Configurable spacing, margins, corner radius

### SVG Rendering (`render_svg.py`)
- **SVGRenderer class**: Converts diagram objects to SVG files using `drawsvg`
- Embeds external board SVG assets by parsing and inlining elements
- Draws devices as colored rounded rectangles with pin markers
- Draws wires as paths with rounded corners using bezier curves
- Auto-generates legend showing wire colors and their meanings
- Fallback rendering if board SVG asset is missing

## Key Design Patterns

1. **Separation of concerns**: Model → Layout → Rendering pipeline
2. **Registry pattern**: `boards.py` loads from JSON configs; `devices/registry.py` provides device templates from JSON
3. **Position calculation**: Absolute positions calculated during layout phase; devices/pins use relative positions
4. **Two-phase wire routing**: Group connections by source pin to calculate offsets, then route each wire
5. **Color assignment**: Automatic based on pin role, can be overridden per connection
6. **Configuration-based**: Board and device definitions loaded from JSON files with smart defaults

## Board Configuration System

Board definitions are stored in JSON files in `src/pinviz/board_configs/` directory. This makes it easy to add new board types without modifying Python code.

### Board Configuration Structure

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

### Adding a New Board

**Quick Summary:** For Raspberry Pi boards with 40-pin GPIO headers, you can copy an existing board's pin configuration since they all share the same GPIO pinout. This takes ~15-30 minutes.

#### Step 1: Create or Obtain SVG Asset

1. Place SVG file in `src/pinviz/assets/` (e.g., `raspberry_pi_4.svg`)
2. **Important:** For pin alignment, the SVG should have similar viewBox dimensions to existing boards
   - Check existing SVG: `head -5 src/pinviz/assets/pi_5_mod.svg | grep viewBox`
   - Pi 5 uses: `viewBox="0 0 206 308"` - use same dimensions for consistent pin spacing

#### Step 2: Create Board Configuration JSON

1. Create `src/pinviz/board_configs/raspberry_pi_4.json`
2. **For Raspberry Pi boards:** Copy from `raspberry_pi_5.json` and update:
   - `name`: "Raspberry Pi 4 Model B"
   - `svg_asset`: "pi_4_mod.svg"
   - Keep `width`, `height`, `layout`, and `pins` identical (they share the same GPIO pinout)
3. **For non-Raspberry Pi boards:** Define all pins manually with proper layout parameters

#### Step 3: Add Factory Function

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

#### Step 4: Add Board Name Aliases

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

#### Step 5: Update Schema Validation

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

#### Step 6: Add Tests

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

#### Step 7: Verify and Test

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

#### Checklist

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

### Board Configuration Validation

All board configurations are validated against `BoardConfigSchema` in `schemas.py`:
- Pin numbers must be sequential (1, 2, 3, ...)
- Pin roles must be valid (GPIO, I2C_SDA, PWM, etc.)
- Layout parameters must be positive numbers
- Right column X must be greater than left column X

## Device Configuration System

Device definitions are stored in JSON files in `src/pinviz/device_configs/` directory, organized by category (sensors/, leds/, displays/, io/, etc.). This makes it easy to add new devices without writing Python code.

### Device Configuration Structure

**Minimal example** (smart defaults handle everything else):
```json
{
  "id": "bh1750",
  "name": "BH1750 Light Sensor",
  "category": "sensors",
  "pins": [
    {"name": "VCC", "role": "3V3"},
    {"name": "GND", "role": "GND"},
    {"name": "SCL", "role": "I2C_SCL"},
    {"name": "SDA", "role": "I2C_SDA"}
  ]
}
```

**With optional metadata**:
```json
{
  "id": "ds18b20",
  "name": "DS18B20 Temperature Sensor",
  "category": "sensors",
  "description": "DS18B20 waterproof 1-Wire temperature sensor",
  "pins": [
    {"name": "VCC", "role": "3V3"},
    {"name": "DATA", "role": "GPIO"},
    {"name": "GND", "role": "GND"}
  ],
  "layout": {
    "pin_spacing": 10.0,
    "start_y": 12.0
  },
  "display": {
    "width": 75.0,
    "height": 45.0
  },
  "datasheet_url": "https://www.analog.com/media/en/technical-documentation/data-sheets/DS18B20.pdf",
  "notes": "Requires a 4.7kΩ pull-up resistor between DATA and VCC."
}
```

**With parameters** (for device variants):
```json
{
  "id": "led",
  "name": "{color_name} LED",
  "category": "leds",
  "pins": [
    {"name": "+", "role": "GPIO"},
    {"name": "-", "role": "GND"}
  ],
  "parameters": {
    "color_name": {
      "type": "string",
      "default": "Red",
      "description": "LED color for display name"
    }
  }
}
```

### Smart Defaults

The device loader automatically provides:
- **Pin positions**: Vertical layout (top to bottom) or horizontal layout (left to right)
- **Device dimensions**: Auto-sized to fit all pins with padding
- **Colors**: Category-based defaults (sensors=turquoise, LEDs=red, displays=blue, io=gray)
- **Wire colors**: Based on pin roles (I2C=yellow, SPI=cyan, power=red, ground=black)

### Using Devices from JSON Configs

```python
from pinviz.devices import get_registry

# Load device from JSON config (automatic)
registry = get_registry()
sensor = registry.create('bh1750')  # Loads from device_configs/sensors/bh1750.json

# With parameters
led = registry.create('led', color_name='Blue')  # Creates "Blue LED"
ir_ring = registry.create('ir_led_ring', num_leds=24)  # Creates "IR LED Ring (24)"

# Custom device name
i2c_dev = registry.create('i2c_device', name='BME280')  # Creates "BME280"
```

### Adding a New Device

**68% less configuration** compared to Python factory functions:

1. Create JSON file in appropriate category folder (e.g., `src/pinviz/device_configs/sensors/bme280.json`)
2. Define minimal required fields (id, name, category, pins)
3. Let smart defaults handle positions, dimensions, and colors
4. Done! Use with `registry.create('bme280')`

**Note:** All devices now use JSON configs exclusively. Legacy Python factory functions have been removed as of Phase 5 cleanup.

## Diagram Configuration File Structure

YAML/JSON format:
```yaml
title: "Diagram Title"
board: "raspberry_pi_5"  # or "rpi5", "rpi"
devices:
  - type: "bh1750"  # Predefined device type
    name: "Optional Override Name"
  - name: "Custom Device"  # Custom device definition
    pins:
      - name: "VCC"
        role: "3V3"
connections:
  - board_pin: 1  # Physical pin number (1-40)
    device: "Device Name"
    device_pin: "Pin Name"
    color: "#FF0000"  # Optional override
    style: "mixed"  # Optional: orthogonal, curved, mixed
show_legend: true
```

## Python API Structure

Programmatic API example:
```python
from pinviz import boards, devices, Connection, Diagram, SVGRenderer

board = boards.raspberry_pi_5()
sensor = devices.bh1750_light_sensor()
connections = [Connection(1, "BH1750", "VCC"), ...]
diagram = Diagram(title="...", board=board, devices=[sensor], connections=connections)

renderer = SVGRenderer()
renderer.render(diagram, "output.svg")
```

## Important Implementation Notes

- Pin numbers in connections are physical pin numbers (1-40), not BCM GPIO numbers
- Wire routing uses a "rail" system: horizontal from pin → vertical along rail → horizontal to device
- The layout engine mutates device positions but connections reference devices by name
- Board SVG assets are packaged in `src/pinviz/assets/` directory with the module
- All measurements are in SVG units (typically pixels)
- Always run ruff format and check before committing Python code.
- Make sure that the mkdocs are updated after doing changes ("docs" dir)
- Save dev plans to "plans" dir not commited to git
- Keep the project root dir clean, just essential files should be stored here
