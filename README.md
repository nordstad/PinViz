# PinViz

<p align="center">
  <img src="https://raw.githubusercontent.com/nordstad/PinViz/main/assets/logo_512.png" alt="PinViz Logo" width="120">
</p>

<p align="center">
  <a href="https://github.com/nordstad/PinViz/actions/workflows/ci.yml"><img src="https://github.com/nordstad/PinViz/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://codecov.io/gh/nordstad/PinViz"><img src="https://codecov.io/gh/nordstad/PinViz/branch/main/graph/badge.svg" alt="Coverage"></a>
  <a href="https://nordstad.github.io/PinViz/"><img src="https://img.shields.io/badge/docs-mkdocs-blue" alt="Documentation"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
  <a href="https://pypi.org/project/pinviz/"><img src="https://img.shields.io/pypi/v/pinviz.svg" alt="PyPI version"></a>
  <a href="https://github.com/nordstad/PinViz/blob/main/Formula/pinviz.rb"><img src="https://img.shields.io/badge/homebrew-tap-orange?logo=homebrew" alt="Homebrew"></a>
  <a href="https://pepy.tech/projects/pinviz"><img src="https://static.pepy.tech/personalized-badge/pinviz?period=total&units=international_system&left_color=black&right_color=green&left_text=downloads" alt="PyPI Downloads"></a>
</p>

**Programmatically generate beautiful GPIO connection diagrams for Raspberry Pi and ESP32/ESP8266 boards in SVG format.**

PinViz makes it easy to create clear, professional wiring diagrams for your microcontroller projects. Define your connections using simple YAML/JSON files or Python code, and automatically generate publication-ready SVG diagrams.

## Example Diagram

<p align="center">
  <img src="https://raw.githubusercontent.com/nordstad/PinViz/main/images/bh1750.svg" alt="BH1750 Light Sensor Wiring Diagram" width="600">
</p>

**[→ See more examples](https://nordstad.github.io/PinViz/guide/examples/)**

## Features

- 📝 **Declarative Configuration**: Define diagrams using YAML or JSON files
- 🎨 **Automatic Wire Routing**: Smart wire routing with configurable styles (orthogonal, curved, mixed)
- 🎯 **Color-Coded Wires**: Automatic color assignment based on pin function (I2C, SPI, power, ground, etc.)
- ⚡ **Inline Components**: Add resistors, capacitors, and diodes directly on wires
- 🔌 **Built-in Templates**: Pre-configured boards (Raspberry Pi, ESP32, ESP8266) and common devices
- 🐍 **Python API**: Create diagrams programmatically with Python code
- 🤖 **MCP Server**: Generate diagrams from natural language with AI assistants
- 🌙 **Dark Mode**: Built-in light and dark themes for better visibility
- 📦 **SVG Output**: Scalable, high-quality vector graphics
- ✨ **Modern CLI**: Rich terminal output with progress indicators and colored messages
- 🔧 **JSON Output**: Machine-readable output for CI/CD integration

## Supported Boards

| Board              | Aliases                                      | GPIO Pins            | Description                                          |
| ------------------ | -------------------------------------------- | -------------------- | ---------------------------------------------------- |
| Raspberry Pi 5     | `raspberry_pi_5`, `rpi5`, `rpi`              | 40-pin               | Latest Raspberry Pi with improved GPIO capabilities  |
| Raspberry Pi 4     | `raspberry_pi_4`, `rpi4`                     | 40-pin               | Popular Raspberry Pi model with full GPIO header     |
| Raspberry Pi Pico  | `raspberry_pi_pico`, `pico`                  | 40-pin (dual-sided)  | RP2040-based microcontroller board                   |
| ESP32 DevKit V1    | `esp32_devkit_v1`, `esp32`, `esp32_devkit`   | 30-pin (dual-sided)  | ESP32 development board with WiFi/Bluetooth          |
| ESP8266 NodeMCU    | `esp8266_nodemcu`, `esp8266`, `nodemcu`      | 30-pin (dual-sided)  | ESP8266 WiFi development board                       |
| Wemos D1 Mini      | `wemos_d1_mini`, `d1mini`, `wemos`           | 16-pin (dual-sided)  | Compact ESP8266 development board                    |

All boards include full pin definitions with GPIO numbers, I2C, SPI, UART, and PWM support.

## Installation

### Homebrew (macOS)

```zsh
brew tap nordstad/PinViz https://github.com/nordstad/PinViz
brew install pinviz
```

### pip / uv (cross-platform)

```bash
uv tool install pinviz
```

```bash
pip install pinviz
```

Or as a project dependency:

```bash
uv add pinviz
```

## Quick Start

<p align="center">
  <img src="https://raw.githubusercontent.com/nordstad/PinViz/main/scripts/demos/output/quick_demo.gif" alt="PinViz Quick Demo" width="800">
</p>

### Try a Built-in Example

```bash
# Generate a BH1750 light sensor wiring diagram
pinviz example bh1750 -o bh1750.svg

# See all available examples
pinviz list
```

### Create Your Own Diagram

Create a YAML configuration file (`my-diagram.yaml`):

```yaml
title: "BH1750 Light Sensor Wiring"
board: "raspberry_pi_5"

devices:
  - type: "bh1750"
    name: "BH1750"
    color: "turquoise"  # Named color support (or use hex: "#50E3C2")

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
```

Generate your diagram:

```bash
pinviz render my-diagram.yaml -o output.svg
```

### Python API

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

## CLI Commands Examples

PinViz provides a modern CLI

### Rendering Diagrams

```bash
# Generate diagram from YAML config
pinviz render examples/bh1750.yaml -o output.svg
```

### Validation

```bash
# Validate diagram configuration
pinviz validate examples/bh1750.yaml
```

### List Templates

```bash
# List all boards, devices, and examples
pinviz list
```

## MCP Server (AI-Powered)

PinViz includes an **MCP (Model Context Protocol) server** that enables natural language diagram generation through AI assistants like Claude Desktop. Generate diagrams with prompts like "Connect a BME280 temperature sensor to my Raspberry Pi 5" with intelligent pin assignment, automatic I2C bus sharing, and conflict detection.

**[→ Full MCP documentation](https://nordstad.github.io/PinViz/mcp-server/)**

## Documentation

**Full documentation:** [nordstad.github.io/PinViz](https://nordstad.github.io/PinViz/)

- [Installation Guide](https://nordstad.github.io/PinViz/getting-started/installation/) - Detailed installation instructions
- [Quick Start Tutorial](https://nordstad.github.io/PinViz/getting-started/quickstart/) - Step-by-step getting started guide
- [CLI Usage](https://nordstad.github.io/PinViz/guide/cli/) - Command-line interface reference
- [YAML Configuration](https://nordstad.github.io/PinViz/guide/yaml-config/) - Complete YAML configuration guide
- [Python API](https://nordstad.github.io/PinViz/guide/python-api/) - Programmatic API reference
- [Examples Gallery](https://nordstad.github.io/PinViz/guide/examples/) - More example diagrams and configurations
- [API Reference](https://nordstad.github.io/PinViz/api/) - Complete API documentation

## Contributing

Contributions are welcome! Please see our [Contributing Guide](https://nordstad.github.io/PinViz/development/contributing/) for details.

**Adding new devices:** See [guides/adding-devices.md](guides/adding-devices.md) for device configuration details.

## License

MIT License - See [LICENSE](LICENSE) file for details

## Credits

Board and GPIO pin SVG assets courtesy of [Wikimedia Commons](https://commons.wikimedia.org/)

## Author

Even Nordstad

- GitHub: [@nordstad](https://github.com/nordstad)
- Project: [PinViz](https://github.com/nordstad/PinViz)
- Documentation: [nordstad.github.io/PinViz](https://nordstad.github.io/PinViz/)
