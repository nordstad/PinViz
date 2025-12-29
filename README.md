# PinViz

<p align="center">
  <img src="https://raw.githubusercontent.com/nordstad/PinViz/main/assets/logo_512.png" alt="PinViz Logo" width="120">
</p>

<p align="center">
  <a href="https://github.com/nordstad/PinViz/actions/workflows/ci.yml"><img src="https://github.com/nordstad/PinViz/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://nordstad.github.io/PinViz/"><img src="https://img.shields.io/badge/docs-mkdocs-blue" alt="Documentation"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
  <a href="https://pypi.org/project/pinviz/"><img src="https://img.shields.io/pypi/v/pinviz.svg" alt="PyPI version"></a>
  <a href="https://pepy.tech/projects/pinviz"><img src="https://static.pepy.tech/personalized-badge/pinviz?period=total&units=international_system&left_color=black&right_color=green&left_text=downloads" alt="PyPI Downloads"></a>
</p>

Programmatically generate beautiful Raspberry Pi GPIO connection diagrams in SVG format.

PinViz makes it easy to create clear, professional wiring diagrams for your Raspberry Pi projects. Define your connections using simple YAML/JSON files or Python code, and automatically generate publication-ready SVG diagrams.

<p align="center">
  <img src="https://raw.githubusercontent.com/nordstad/PinViz/main/scripts/demos/output/quick_demo.gif" alt="PinViz Quick Demo" width="800">
</p>

## 📚 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [CLI Commands](#-cli-commands)
- [MCP Server (AI-Powered)](#-mcp-server-ai-powered)
- [Example Diagrams](#️-example-diagrams)
- [Configuration Reference](#️-configuration-reference)
- [Documentation](#-documentation)
- [Development](#-development)
- [Contributing](#-contributing)

---

## ✨ Features

### 📦 PinViz Package

**Core capabilities for creating wiring diagrams:**

- **Declarative Configuration**: Define diagrams using YAML or JSON files
- **Programmatic API**: Create diagrams with Python code
- **Automatic Wire Routing**: Smart wire routing with configurable styles (orthogonal, curved, mixed)
- **Inline Components**: Add resistors, capacitors, and diodes directly on wires
- **Color-Coded Wires**: Automatic color assignment based on pin function (I2C, SPI, power, ground, etc.)
- **Built-in Templates**: Pre-configured boards (Raspberry Pi 5, Pi Zero) and common devices
- **GPIO Pin Reference**: Optional GPIO pinout diagram for easy reference
- **SVG Output**: Scalable, high-quality vector graphics

<details>
<summary><b>👉 View Python API example</b> <i>(click to expand)</i></summary>

```python
from pinviz import boards, devices, Connection, Diagram, SVGRenderer

board = boards.raspberry_pi_5()
sensor = devices.bh1750_light_sensor()

connections = [
    Connection(1, "BH1750", "VCC"),  # 3V3 to VCC
    Connection(6, "BH1750", "GND"),  # GND to GND
    Connection(5, "BH1750", "SCL"),  # GPIO3/SCL to SCL
    Connection(3, "BH1750", "SDA"),  # GPIO2/SDA to SDA
]

diagram = Diagram(
    title="BH1750 Light Sensor",
    board=board,
    devices=[sensor],
    connections=connections
)

renderer = SVGRenderer()
renderer.render(diagram, "output.svg")
```

</details>

**[→ Full CLI documentation](https://nordstad.github.io/PinViz/guide/cli/) | [→ Python API reference](https://nordstad.github.io/PinViz/guide/python-api/)**

### 🤖 MCP Server (AI-Powered)

**Generate diagrams from natural language with AI assistants:**

- **Natural Language**: "Connect BME280 and LED to my Raspberry Pi"
- **Intelligent Pin Assignment**: Automatic I2C bus sharing, SPI chip select allocation, and conflict detection
- **25+ Device Database**: Sensors, displays, HATs, components with automatic pin mapping
- **URL-Based Discovery**: Add new devices by parsing datasheets from manufacturer websites
- **AI Integration**: Works with Claude Desktop, GitHub Copilot, and other MCP-compatible clients

**[→ MCP Server documentation](https://nordstad.github.io/PinViz/mcp-server/)**

## 📥 Installation

### For CLI Usage (Recommended)

Install as a standalone tool with global access to the CLI:

```bash
uv tool install pinviz
```

After installation, `pinviz` will be available globally in your terminal. See [Quick Start](#-quick-start) below to generate your first diagram.

### As a Project Dependency

If you want to use PinViz as a library in your Python project:

```bash
# Using uv
uv add pinviz

# Using pip
pip install pinviz
```

**Note**: If you install with `uv add`, the CLI tool will only be available via `uv run pinviz`. For direct CLI access, use `uv tool install` instead.

## 🚀 Quick Start

### 1. Try a Built-in Example

The fastest way to get started is to generate one of the built-in examples:

```bash
# Generate a BH1750 light sensor wiring diagram
pinviz example bh1750 -o bh1750.svg

# See all available examples
pinviz list
```

This creates an SVG file you can open in any web browser or vector graphics editor.

> **Note**: If you installed with `uv add` instead of `uv tool install`, prefix commands with `uv run`:
> ```bash
> uv run pinviz example bh1750 -o bh1750.svg
> ```

### 2. Create Your Own Diagram

Once you've seen what PinViz can do, create your own configuration file using YAML or JSON format.

**YAML format** (`my-diagram.yaml`):

```yaml
title: "BH1750 Light Sensor Wiring"
board: "raspberry_pi_5"  # or "raspberry_pi_zero_2w" for Pi Zero

devices:
  - type: "bh1750"
    name: "BH1750"

connections:
  - board_pin: 1     # 3V3
    device: "BH1750"
    device_pin: "VCC"

  - board_pin: 6     # GND
    device: "BH1750"
    device_pin: "GND"

  - board_pin: 5     # GPIO3 (I2C SCL)
    device: "BH1750"
    device_pin: "SCL"

  - board_pin: 3     # GPIO2 (I2C SDA)
    device: "BH1750"
    device_pin: "SDA"

show_gpio_diagram: true  # Optional: include GPIO pin reference
```

**JSON format** (`my-diagram.json`):

```json
{
  "title": "BH1750 Light Sensor Wiring",
  "board": "raspberry_pi_5",
  "devices": [
    {
      "type": "bh1750",
      "name": "BH1750"
    }
  ],
  "connections": [
    {"board_pin": 1, "device": "BH1750", "device_pin": "VCC"},
    {"board_pin": 6, "device": "BH1750", "device_pin": "GND"},
    {"board_pin": 5, "device": "BH1750", "device_pin": "SCL"},
    {"board_pin": 3, "device": "BH1750", "device_pin": "SDA"}
  ],
  "show_gpio_diagram": true
}
```

Generate your diagram (works with both YAML and JSON):

```bash
pinviz render my-diagram.yaml -o output.svg
```

### 3. Using Python API

For programmatic diagram generation in your Python projects:

```python
from pinviz import boards, devices, Connection, Diagram, SVGRenderer

# Create board and device
board = boards.raspberry_pi_5()  # or boards.raspberry_pi_zero_2w()
sensor = devices.bh1750_light_sensor()

# Define connections
connections = [
    Connection(1, "BH1750", "VCC"),  # 3V3 to VCC
    Connection(6, "BH1750", "GND"),  # GND to GND
    Connection(5, "BH1750", "SCL"),  # GPIO3/SCL to SCL
    Connection(3, "BH1750", "SDA"),  # GPIO2/SDA to SDA
]

# Create and render diagram
diagram = Diagram(
    title="BH1750 Light Sensor Wiring",
    board=board,
    devices=[sensor],
    connections=connections,
    show_gpio_diagram=True  # Optional: include GPIO pin reference
)

renderer = SVGRenderer()
renderer.render(diagram, "output.svg")
```

<details>
<summary><b>👉 Custom Wire Colors</b> <i>(click to expand)</i></summary>

Use the `WireColor` enum for standard electronics wire colors:

```python
from pinviz import (
    boards, devices, Connection, Diagram, SVGRenderer, WireColor
)

# Define connections with custom colors
connections = [
    Connection(1, "BH1750", "VCC", color=WireColor.RED),
    Connection(6, "BH1750", "GND", color=WireColor.BLACK),
    Connection(5, "BH1750", "SCL", color=WireColor.BLUE),
    Connection(3, "BH1750", "SDA", color=WireColor.GREEN),
]

# Or use hex colors directly
connections = [
    Connection(1, "BH1750", "VCC", color="#FF0000"),  # Red
]
```

**Available colors**: RED, BLACK, WHITE, GREEN, BLUE, YELLOW, ORANGE, PURPLE, GRAY, BROWN, PINK, CYAN, MAGENTA, LIME, TURQUOISE

</details>

## 💻 CLI Commands

See the [Quick Start](#-quick-start) section for basic usage. All examples below assume you installed with `uv tool install pinviz` or `pip install pinviz`. If you installed with `uv add`, prefix all commands with `uv run`.

### Rendering Custom Diagrams

```bash
# From YAML/JSON file with specified output
pinviz render my-diagram.yaml -o output.svg

# Short form (output defaults to <config-name>.svg)
pinviz render my-diagram.yaml
```

### Working with Built-in Examples

```bash
# List all available built-in examples
pinviz list

# Generate a specific example
pinviz example bh1750 -o bh1750.svg
pinviz example ir_led -o ir_led.svg
pinviz example i2c_spi -o i2c_spi.svg
```

**[→ Full CLI documentation](https://nordstad.github.io/PinViz/guide/cli/)**

## 🤖 MCP Server (AI-Powered)

PinViz includes an **MCP (Model Context Protocol) server** that enables natural language diagram generation through AI assistants like Claude Desktop.

**Generate diagrams with prompts like:**
- "Connect a BME280 temperature sensor to my Raspberry Pi 5"
- "Wire a BH1750 light sensor and LED on GPIO 17"
- "Set up environmental monitoring with BME280 and DHT22"

<details>
<summary><b>👉 📖 Quick Start with Claude Desktop</b> (click to expand)</summary>

### Installation

**Easiest Method (using Claude CLI):**

```bash
# Using uv (recommended)
uv tool install pinviz
claude mcp add pinviz pinviz-mcp

# OR using pip
pip install pinviz
claude mcp add pinviz pinviz-mcp

# Restart Claude Desktop
```

**Manual Method (edit config file):**

1. **Install PinViz**:
   ```bash
   # Using uv (recommended)
   uv tool install pinviz

   # OR using pip
   pip install pinviz
   ```

2. **Configure Claude Desktop**:

   Edit `~/.config/claude/claude_desktop_config.json` (macOS/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

   ```json
   {
     "mcpServers": {
       "pinviz": {
         "command": "pinviz-mcp"
       }
     }
   }
   ```

3. **Restart Claude Desktop**

**Start generating diagrams:**

```
"Connect a BME280 temperature sensor to my Raspberry Pi 5"
```

</details>

<details>
<summary><b>👉 🔧 GitHub Copilot (VS Code)</b> <i>(click to expand)</i></summary>

1. **Install PinViz**:
   ```bash
   # Using uv (recommended)
   uv tool install pinviz

   # OR using pip
   pip install pinviz
   ```

2. **Add to your VS Code `settings.json`**:
   ```json
   {
     "github.copilot.chat.mcp.servers": {
       "pinviz": {
         "command": "pinviz-mcp"
       }
     }
   }
   ```

3. **Reload VS Code** and use `@pinviz` in Copilot Chat:
   ```
   @pinviz Connect BME280 and LED to Raspberry Pi 5
   ```

</details>

<details>
<summary><b>👉 ✨ Key Features</b> <i>(click to expand)</i></summary>

**Intelligent Pin Assignment:**
- Automatic I2C bus sharing (multiple devices on SDA/SCL)
- SPI chip select allocation (CE0, CE1)
- Power distribution (cycles through 3.3V and 5V pins)
- Conflict detection and resolution

**Device Database:**
- 25+ devices covering sensors, displays, HATs, and components
- Categories: sensor, display, hat, component, actuator, breakout
- Protocols: I2C, SPI, UART, GPIO, 1-Wire, PWM

**Hybrid Parsing:**
- Regex patterns for common prompts (80% of cases, instant)
- Claude API fallback for complex prompts (20% of cases)

</details>

<details>
<summary><b>👉 🛠️ Available MCP Tools</b> <i>(click to expand)</i></summary>

- `generate_diagram` - Convert natural language to wiring diagrams (YAML/JSON/summary)
- `list_devices` - Browse 25+ devices by category/protocol
- `get_device_info` - Get detailed device specifications
- `search_devices_by_tags` - Find devices by tags
- `parse_device_from_url` - Add new devices from datasheet URLs
- `get_database_summary` - View database statistics

</details>

**📖 Full MCP Documentation:**
- [MCP Installation Guide →](https://nordstad.github.io/PinViz/mcp-server/installation/)
- [MCP Usage Guide & Examples →](https://nordstad.github.io/PinViz/mcp-server/usage/)
- [Contributing Devices →](https://nordstad.github.io/PinViz/mcp-server/contributing/)

## 🖼️ Example Diagrams

> **💡 Click any example below to view the code and diagram!**

<details>
<summary><b>👉 LED with Resistor</b> - Simple circuit with inline component <i>(click to expand)</i></summary>

```bash
pinviz render examples/led_with_resistor.yaml -o led_with_resistor.svg
```

![LED with Resistor](https://raw.githubusercontent.com/nordstad/PinViz/main/images/led_with_resistor.svg)

</details>

<details>
<summary><b>👉 Multi-Device Setup</b> - BH1750 + IR LED Ring <i>(click to expand)</i></summary>

```bash
pinviz render examples/bh1750_ir_led.yaml -o bh1750_ir_led.svg
```

![BH1750 + IR LED Ring](https://raw.githubusercontent.com/nordstad/PinViz/main/images/bh1750_ir_led.svg)

</details>

<details>
<summary><b>👉 Traffic Light</b> - Three LEDs with resistors <i>(click to expand)</i></summary>

```bash
pinviz render examples/traffic_light.yaml -o traffic_light.svg
```

![Traffic Light](https://raw.githubusercontent.com/nordstad/PinViz/main/images/traffic_light.svg)

</details>

<details>
<summary><b>👉 Raspberry Pi Zero 2 W</b> - Compact board layout <i>(click to expand)</i></summary>

```bash
pinviz render examples/pi_zero_bh1750.yaml --no-gpio -o pi_zero_bh1750.svg
```

![Pi Zero BH1750](https://raw.githubusercontent.com/nordstad/PinViz/main/images/examples/pi_zero_bh1750_without_gpio.svg)

</details>

<details>
<summary><b>👉 GPIO Reference Comparison</b> - With vs Without GPIO details <i>(click to expand)</i></summary>

### With GPIO Details

Shows complete GPIO pinout reference for easy wiring verification (`--gpio`, ~130KB).

```bash
pinviz example bh1750 --gpio -o diagram.svg
```

![BH1750 with GPIO](https://raw.githubusercontent.com/nordstad/PinViz/main/images/examples/bh1750_with_gpio.svg)

### Without GPIO Details

Cleaner, more compact diagram - 35% smaller file size (`--no-gpio`, ~85KB).

```bash
pinviz example bh1750 --no-gpio -o diagram.svg
```

![BH1750 without GPIO](https://raw.githubusercontent.com/nordstad/PinViz/main/images/examples/bh1750_without_gpio.svg)

</details>

**📸 More Examples:**
- See all examples in the [`examples/`](examples/) directory (includes both YAML and JSON formats)
- View generated diagrams in the [`images/`](images/) directory
- [Browse example gallery in docs →](https://nordstad.github.io/PinViz/guide/examples/)

## ⚙️ Configuration Reference

> **💡 Click any section below to see detailed configuration options!**

<details>
<summary><b>👉 📋 Diagram Options</b> <i>(click to expand)</i></summary>

### GPIO Pin Reference

Control whether to show the GPIO pin reference diagram on the right side. This displays all 40 GPIO pins with their functions and color-coded roles.

**In YAML config:**

```yaml
show_gpio_diagram: true  # Include GPIO pin reference (default: false)
```

**Via CLI:**

```bash
# Show GPIO details (larger file, more complete reference)
pinviz example bh1750 --gpio -o diagram.svg

# Hide GPIO details (smaller file, cleaner look)
pinviz example bh1750 --no-gpio -o diagram.svg

# For config files (CLI flag overrides config value)
pinviz render diagram.yaml --gpio -o output.svg
```

**Comparison:**

- **With GPIO** (`--gpio`): ~130KB SVG, includes full pinout reference
- **Without GPIO** (`--no-gpio`): ~85KB SVG, 35% smaller, cleaner diagram

</details>

<details>
<summary><b>👉 🎛️ Board Selection</b> <i>(click to expand)</i></summary>

Currently supported boards:

- `raspberry_pi_5` (aliases: `rpi5`, `rpi`) - Raspberry Pi 5 with 40-pin GPIO header
- `raspberry_pi_zero_2w` (aliases: `raspberry_pi_zero`, `pizero`, `zero2w`, `zero`, `rpizero`) - Raspberry Pi Zero / Zero 2 W with 40-pin GPIO header

</details>

<details>
<summary><b>👉 🔌 Built-in Device Types</b> <i>(click to expand)</i></summary>

**Sensors:**
- `bh1750` - BH1750 I2C ambient light sensor ([datasheet](https://www.mouser.com/datasheet/2/348/bh1750fvi-e-186247.pdf))
- `ds18b20` - DS18B20 waterproof 1-Wire temperature sensor ([datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/DS18B20.pdf))

**LEDs:**
- `led` - Simple LED with anode/cathode pins ([docs](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header))
- `ir_led_ring` - IR LED ring module with control pin ([product page](https://www.electrokit.com/led-ring-for-raspberry-pi-kamera-ir-leds))

**I/O:**
- `button` - Push button or switch with pull-up/pull-down configuration ([docs](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header))

**Generic:**
- `i2c_device` - Generic I2C device with standard pinout ([docs](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#i2c))
- `spi_device` - Generic SPI device with standard pinout ([docs](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#spi))

Run `pinviz list` to see all available devices with their documentation links.

</details>

<details>
<summary><b>👉 🔗 Connection Configuration</b> <i>(click to expand)</i></summary>

Connections use **physical pin numbers** (1-40), not BCM GPIO numbers:

```yaml
connections:
  - board_pin: 1           # Physical pin number (required)
    device: "Device Name"  # Device name (required)
    device_pin: "VCC"      # Device pin name (required)
    color: "#FF0000"       # Custom wire color (optional)
    style: "mixed"         # Wire style: orthogonal, curved, mixed (optional)
    components:            # Inline components (optional)
      - type: "resistor"
        value: "220Ω"
        position: 0.55     # Position along wire (0.0-1.0, default: 0.55)
```

</details>

<details>
<summary><b>👉 ⚡ Inline Components</b> <i>(click to expand)</i></summary>

Add resistors, capacitors, or diodes directly on wire connections:

**YAML:**

```yaml
connections:
  - board_pin: 11
    device: "Red LED"
    device_pin: "+"
    color: "#FF0000"
    components:
      - type: "resistor"   # Component type: resistor, capacitor, diode
        value: "220Ω"      # Display value (required)
        position: 0.55     # Position along wire path (0.0 = board, 1.0 = device)
```

**Python API:**

```python
from pinviz import Component, ComponentType, Connection

connection = Connection(
    board_pin=11,
    device_name="Red LED",
    device_pin_name="+",
    color="#FF0000",
    components=[
        Component(
            type=ComponentType.RESISTOR,
            value="220Ω",
            position=0.55
        )
    ]
)
```

</details>

<details>
<summary><b>👉 🎨 Custom Devices</b> <i>(click to expand)</i></summary>

Define custom devices inline:

```yaml
devices:
  - name: "My Custom Sensor"
    width: 80.0
    height: 50.0
    color: "#4A90E2"
    pins:
      - name: "VCC"
        role: "3V3"
        position: {x: 5.0, y: 10.0}
      - name: "GND"
        role: "GND"
        position: {x: 5.0, y: 20.0}
      - name: "SDA"
        role: "I2C_SDA"
        position: {x: 5.0, y: 30.0}
      - name: "SCL"
        role: "I2C_SCL"
        position: {x: 5.0, y: 40.0}
```

</details>

<details>
<summary><b>👉 🎯 Pin Roles</b> <i>(click to expand)</i></summary>

Supported pin roles (for automatic color assignment):

- `3V3`, `5V` - Power rails
- `GND` - Ground
- `GPIO` - General purpose I/O
- `I2C_SDA`, `I2C_SCL` - I2C bus
- `SPI_MOSI`, `SPI_MISO`, `SPI_SCLK`, `SPI_CE0`, `SPI_CE1` - SPI bus
- `UART_TX`, `UART_RX` - UART serial
- `PWM` - PWM output

</details>

**📖 Full Configuration Guide:**
- [YAML Configuration →](https://nordstad.github.io/PinViz/guide/yaml-config/)
- [Python API Reference →](https://nordstad.github.io/PinViz/guide/python-api/)
- [API Documentation →](https://nordstad.github.io/PinViz/api/)

## 📖 Documentation

**Full documentation available at [nordstad.github.io/PinViz](https://nordstad.github.io/PinViz/)**

### Getting Started
- [Installation Guide](https://nordstad.github.io/PinViz/getting-started/installation/)
- [Quick Start Tutorial](https://nordstad.github.io/PinViz/getting-started/quickstart/)

### User Guides
- [CLI Usage](https://nordstad.github.io/PinViz/guide/cli/)
- [YAML Configuration](https://nordstad.github.io/PinViz/guide/yaml-config/)
- [Python API](https://nordstad.github.io/PinViz/guide/python-api/)
- [Examples Gallery](https://nordstad.github.io/PinViz/guide/examples/)

### MCP Server
- [MCP Installation](https://nordstad.github.io/PinViz/mcp-server/installation/)
- [MCP Usage Guide](https://nordstad.github.io/PinViz/mcp-server/usage/)
- [Contributing Devices](https://nordstad.github.io/PinViz/mcp-server/contributing/)

### API Reference
- [API Overview](https://nordstad.github.io/PinViz/api/)
- [Boards Module](https://nordstad.github.io/PinViz/api/boards/)
- [Devices Module](https://nordstad.github.io/PinViz/api/devices/)
- [Model Reference](https://nordstad.github.io/PinViz/api/model/)
- [Config Loader](https://nordstad.github.io/PinViz/api/config_loader/)
- [Layout Engine](https://nordstad.github.io/PinViz/api/layout/)
- [SVG Renderer](https://nordstad.github.io/PinViz/api/render_svg/)

### Development
- [Contributing Guide](https://nordstad.github.io/PinViz/development/contributing/)
- [Architecture Overview](https://nordstad.github.io/PinViz/development/architecture/)
- [Dependency Management](https://nordstad.github.io/PinViz/development/dependency-management/)

## 🔧 Development

### Setup

```bash
# Clone repository
git clone https://github.com/nordstad/PinViz.git
cd PinViz

# Install dependencies
uv sync --dev
```

### Code Quality

```bash
# Lint and format
uv run ruff check .
uv run ruff format .

# Run tests
uv run pytest
```

### Build Documentation

```bash
# Install docs dependencies
uv sync --group docs

# Build documentation
uv run mkdocs build

# Serve documentation locally
uv run mkdocs serve
```

**[→ Full contributing guide](https://nordstad.github.io/PinViz/development/contributing/)**

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

**See our [Contributing Guide](https://nordstad.github.io/PinViz/development/contributing/) for:**
- Code style guidelines
- Development workflow
- Testing requirements
- Pull request process

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Credits

Board and GPIO pin SVG assets courtesy of [FreeSVG.org](https://freesvg.org/)

## 👤 Author

**Even Nordstad**

- GitHub: [@nordstad](https://github.com/nordstad)
- Project: [PinViz](https://github.com/nordstad/PinViz)
- Documentation: [nordstad.github.io/PinViz](https://nordstad.github.io/PinViz/)
