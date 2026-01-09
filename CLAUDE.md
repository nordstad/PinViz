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
```

## Architecture

### Core Data Model (`model.py`)
- **Immutable entities**: Uses dataclasses for `Board`, `Device`, `HeaderPin`, `DevicePin`, `Connection`, `Diagram`
- **PinRole enum**: Defines pin functions (GPIO, I2C, SPI, UART, PWM, power, ground)
- **DEFAULT_COLORS dict**: Maps pin roles to wire colors for automatic color assignment
- **WireStyle enum**: Defines wire routing styles (orthogonal, curved, mixed)

### Component Factory Modules
- **`boards.py`**: Predefined board templates (currently Raspberry Pi 5 with 40-pin GPIO)
  - Pin positions are pre-calculated based on physical GPIO header layout
  - Pins have physical pin numbers (1-40), BCM GPIO numbers, names, and roles
- **`devices.py`**: Device/module templates (BH1750, IR LED ring, generic I2C/SPI, LED, button)
  - Each device has named pins with roles and relative positions

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
2. **Factory pattern**: `boards.py` and `devices.py` provide factory functions for predefined components
3. **Position calculation**: Absolute positions calculated during layout phase; devices/pins use relative positions
4. **Two-phase wire routing**: Group connections by source pin to calculate offsets, then route each wire
5. **Color assignment**: Automatic based on pin role, can be overridden per connection
6. **Configuration-based boards**: Board definitions loaded from JSON files in `src/pinviz/board_configs/`

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

1. Create SVG asset file in `src/pinviz/assets/` (e.g., `raspberry_pi_4.svg`)
2. Create board configuration JSON in `src/pinviz/board_configs/` (e.g., `raspberry_pi_4.json`)
3. Define layout parameters to align with SVG pin positions:
   - `left_col_x`, `right_col_x`: X coordinates for pin columns
   - `start_y`: Y coordinate for first pin row
   - `row_spacing`: Vertical spacing between rows
4. List all pins with physical number, name, role, and BCM GPIO number
5. Create factory function in `boards.py`:
   ```python
   def raspberry_pi_4() -> Board:
       return load_board_from_config("raspberry_pi_4")
   ```

### Board Configuration Validation

All board configurations are validated against `BoardConfigSchema` in `schemas.py`:
- Pin numbers must be sequential (1, 2, 3, ...)
- Pin roles must be valid (GPIO, I2C_SDA, PWM, etc.)
- Layout parameters must be positive numbers
- Right column X must be greater than left column X

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
