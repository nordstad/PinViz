# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`pinviz` is a Python package that programmatically generates Raspberry Pi GPIO connection diagrams in SVG format. It supports both declarative YAML/JSON configuration and programmatic Python API for creating wiring diagrams.

## Development Environment

This project uses `uv` as the package manager and build tool.

```bash
# Install dependencies (including dev dependencies)
uv sync --dev

# Run the CLI tool
uv run pinviz <command>

# Lint and format with ruff
uv run ruff check .
uv run ruff format .

# Run tests
uv run pytest
```

## CLI Commands Reference

```bash
# Render diagrams
pinviz render config.yaml -o output.svg [--json]

# Validate configurations
pinviz validate config.yaml [--strict] [--json]
pinviz validate-devices [--json]

# Generate examples
pinviz example bh1750 -o out/bh1750.svg [--json]

# List available templates
pinviz list [--json]

# Add new device interactively
pinviz add-device
```

**Global options:** `--version`

## Architecture

### Core Components

1. **Data Model** (`model.py`): Immutable dataclasses for `Board`, `Device`, `Connection`, `Diagram`
2. **Board System** (`boards.py`, `board_configs/`): Board templates loaded from JSON configs
3. **Device System** (`devices/registry.py`, `device_configs/`): Device templates from JSON with smart defaults
4. **Config Loader** (`config_loader.py`): Parses YAML/JSON into diagram objects
5. **Layout Engine** (`layout.py`): Positions devices and routes wires algorithmically
6. **SVG Renderer** (`render_svg.py`): Converts diagrams to SVG using `drawsvg`
7. **CLI** (`cli/`): Modular Typer-based CLI with Rich output and JSON support
8. **Connection Graph** (`connection_graph.py`): Multi-level device connection validation and analysis

### Multi-Level Device Support (v0.11.0+)

#### Connection Model

`Connection` dataclass supports both board and device sources:

- `board_pin: int | None` - Board source (backward compatible)
- `source_device: str | None` - Device source (new)
- `source_pin: str | None` - Source pin on device (new)

#### Connection Graph

`ConnectionGraph` class (src/pinviz/connection_graph.py):

- Builds directed graph from connections
- Calculates device levels via BFS
- Detects cycles using DFS
- Validates pin compatibility

#### Layout Strategy

Multi-tier horizontal layout:

- Devices positioned in tiers based on connection depth
- Each tier gets its own X position
- Vertical stacking within each tier
- Dynamic spacing based on device widths

#### Wire Routing

Device-to-device routing:

- Each tier has routing zone on right side
- Wires flow horizontally through inter-tier zones
- Bezier curves for smooth appearance
- Backward connections (higher → lower level) supported

### Key Design Patterns

1. **Separation of concerns**: Model → Layout → Rendering pipeline
2. **Registry pattern**: JSON-based configs for boards and devices
3. **Position calculation**: Absolute positions in layout phase; devices/pins use relative
4. **Two-phase wire routing**: Group by source pin, calculate offsets, then route
5. **Color assignment**: Automatic based on pin role, overridable per connection
6. **Configuration-based**: Board/device definitions in JSON with smart defaults

### Configuration File Structure

```yaml
title: "Diagram Title"
board: "raspberry_pi_5"  # or "rpi5", "rpi4", "rpi"
devices:
  - type: "bh1750"  # Predefined device type
    name: "Optional Override Name"
  - name: "Custom Device"  # Inline custom device
    pins:
      - name: "VCC"
        role: "3V3"
connections:
  - board_pin: 1  # Physical pin number (1-40)
    device: "Device Name"
    device_pin: "Pin Name"
    color: "#FF0000"  # Optional
    style: "mixed"  # Optional: orthogonal, curved, mixed
show_legend: true
```

### Python API

```python
from pinviz import boards, devices, Connection, Diagram, SVGRenderer

board = boards.raspberry_pi_5()
sensor = devices.bh1750_light_sensor()
connections = [Connection(1, "BH1750", "VCC"), ...]
diagram = Diagram(title="...", board=board, devices=[sensor], connections=connections)

renderer = SVGRenderer()
renderer.render(diagram, "output.svg")
```

## Board Configuration System

Board definitions are JSON files in `src/pinviz/board_configs/`.

**Standard boards** (Pi 4, Pi 5): Vertical columns with 2 pins per row

```json
{
  "name": "Raspberry Pi 5",
  "svg_asset": "pi_5_mod.svg",
  "layout": {
    "left_col_x": 187.1,
    "right_col_x": 199.1,
    "start_y": 16.2,
    "row_spacing": 12.0
  },
  "pins": [...]
}
```

**Dual-sided boards** (Pico): Horizontal rows on top and bottom edges

```json
{
  "name": "Raspberry Pi Pico",
  "layout": {
    "top_header": {"start_x": 8.0, "pin_spacing": 12.0, "y": 6.5},
    "bottom_header": {"start_x": 8.0, "pin_spacing": 12.0, "y": 94.0}
  },
  "pins": [
    {"physical_pin": 1, "name": "GP0", "role": "GPIO", "gpio_bcm": 0, "header": "top"},
    ...
  ]
}
```

**Important:** Pico top header has **reversed pin order** (pin 20 left, pin 1 right).

## Device Configuration System

Device definitions are JSON files in `src/pinviz/device_configs/` organized by category (sensors/, leds/, displays/, io/).

**Minimal device** (smart defaults auto-calculate positions, dimensions, colors):

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

**Smart defaults:**

- Pin positions: Vertical/horizontal layout auto-calculated
- Device dimensions: Auto-sized based on pins
- Colors: Category-based (sensors=turquoise, LEDs=red, displays=blue, io=gray)
- Wire colors: Role-based (I2C=yellow, SPI=cyan, power=red, ground=black)

## CLI Architecture

Built with **Typer** (type-hint CLI) and **Rich** (terminal output).

**Structure:** `src/pinviz/cli/` - Modular commands in separate files
**Features:** JSON output (`--json`), structured logging
**Testing:** Use `typer.testing.CliRunner` for command tests

## Important Implementation Notes

- **Pin numbers**: Physical pin numbers (1-40), not BCM GPIO numbers
- **Wire routing**: "Rail" system - horizontal from pin → vertical along rail → horizontal to device
- **Layout mutability**: Layout engine mutates device positions; connections reference by name
- **Asset location**: Board SVG assets in `src/pinviz/assets/` (packaged with module)
- **Measurements**: All in SVG units (typically pixels)
- **Code quality**: Always run `ruff format .` and `ruff check .` before committing
- **Documentation**: Update mkdocs (in `docs/` dir) after changes
- **Planning**: Save dev plans to `plans/` dir (not committed to git)
- **Project cleanliness**: Keep root dir clean, essential files only
- **MCP support**: Check MCP compatibility for new features/updates

## Detailed Guides

For step-by-step instructions, see the `guides/` directory:

- **[guides/cli-development.md](guides/cli-development.md)** - Adding CLI commands, JSON schemas, testing
- **[guides/adding-boards.md](guides/adding-boards.md)** - Adding new board types (standard and dual-sided)
- **[guides/adding-devices.md](guides/adding-devices.md)** - Adding device templates with smart defaults
- **[guides/publishing.md](guides/publishing.md)** - Publishing to PyPI (tag-only workflow)

## Quick Reference

**Supported boards:** `raspberry_pi_5`, `raspberry_pi_4`, `raspberry_pi_pico`, `rpi5`, `rpi4`, `pico`, `rpi`

**Pin roles:** `GPIO`, `3V3`, `5V`, `GND`, `I2C_SDA`, `I2C_SCL`, `SPI_MOSI`, `SPI_MISO`, `SPI_SCLK`, `SPI_CE0`, `SPI_CE1`, `UART_TX`, `UART_RX`, `PWM`

**Wire styles:** `orthogonal` (default), `curved`, `mixed`

**Device categories:** `sensors`, `leds`, `displays`, `io`, `communication`, `power`
