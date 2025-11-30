# README.md Improvement Suggestions

## Overview
Current README: 588 lines - too long for quick scanning
Goal: Make it more user-friendly with TOC, collapsible sections, and better organization

## Proposed Changes

### 1. Add Table of Contents (Lines 20-30)

Add this after the intro paragraph:

```markdown
## 📚 Table of Contents

- [Features](#features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [CLI Commands](#-cli-commands)
- [MCP Server (AI-Powered)](#mcp-server-ai-powered-diagram-generation)
- [Example Diagrams](#️-example-diagrams)
- [Configuration Reference](#️-configuration-reference)
- [Development](#-development)
- [Documentation](#-documentation)

---
```

### 2. Collapse MCP Server Section (Lines 214-333)

Replace the long MCP Server section with:

```markdown
## MCP Server (AI-Powered Diagram Generation)

PinViz includes an **MCP (Model Context Protocol) server** that enables natural language diagram generation through AI assistants like Claude Desktop.

**Generate diagrams with prompts like:** "Connect BME280 and LED to my Raspberry Pi"

<details>
<summary><b>📖 Quick Start with Claude Desktop</b> (click to expand)</summary>

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

**Manual Method:**

1. Install PinViz: `uv tool install pinviz` (or `pip install pinviz`)
2. Edit `~/.config/claude/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "pinviz": {
         "command": "pinviz-mcp"
       }
     }
   }
   ```
3. Restart Claude Desktop

</details>

<details>
<summary><b>🔧 GitHub Copilot Setup</b></summary>

Add to your VS Code `settings.json`:

```json
{
  "github.copilot.chat.mcp.servers": {
    "pinviz": {
      "command": "pinviz-mcp"
    }
  }
}
```

Then use `@pinviz` in Copilot Chat.

</details>

<details>
<summary><b>✨ Key Features</b></summary>

- **Natural Language Parsing**: Convert prompts to diagrams
- **Intelligent Pin Assignment**: Auto I2C sharing, SPI chip selects
- **25+ Device Database**: Sensors, displays, HATs, components
- **URL-Based Discovery**: Add devices from datasheet URLs

</details>

**📖 Full Documentation:**
- [MCP Installation Guide →](https://nordstad.github.io/PinViz/mcp-server/installation/)
- [MCP Usage Guide →](https://nordstad.github.io/PinViz/mcp-server/usage/)
- [Contributing Devices →](https://nordstad.github.io/PinViz/mcp-server/contributing/)
```

### 3. Collapse Example Diagrams (Lines 333-398)

Replace the examples section with:

```markdown
## 🖼️ Example Diagrams

<details>
<summary><b>LED with Resistor</b> - Simple circuit with inline component</summary>

```bash
pinviz render examples/led_with_resistor.yaml -o led_with_resistor.svg
```

![LED with Resistor](https://raw.githubusercontent.com/nordstad/PinViz/main/images/led_with_resistor.svg)

</details>

<details>
<summary><b>Multi-Device Setup</b> - BH1750 + IR LED Ring</summary>

```bash
pinviz render examples/bh1750_ir_led.yaml -o bh1750_ir_led.svg
```

![BH1750 + IR LED Ring](https://raw.githubusercontent.com/nordstad/PinViz/main/images/bh1750_ir_led.svg)

</details>

<details>
<summary><b>Traffic Light</b> - Three LEDs with resistors</summary>

```bash
pinviz render examples/traffic_light.yaml -o traffic_light.svg
```

![Traffic Light](https://raw.githubusercontent.com/nordstad/PinViz/main/images/traffic_light.svg)

</details>

<details>
<summary><b>Raspberry Pi Zero 2 W</b> - Compact board layout</summary>

```bash
pinviz render examples/pi_zero_bh1750.yaml --no-gpio -o pi_zero_bh1750.svg
```

![Pi Zero BH1750](https://raw.githubusercontent.com/nordstad/PinViz/main/images/examples/pi_zero_bh1750_without_gpio.svg)

</details>

<details>
<summary><b>GPIO Reference Comparison</b> - With vs Without GPIO details</summary>

**With GPIO Details** (`--gpio`): Complete pinout reference (~130KB)

![BH1750 with GPIO](https://raw.githubusercontent.com/nordstad/PinViz/main/images/examples/bh1750_with_gpio.svg)

**Without GPIO Details** (`--no-gpio`): Cleaner, compact (~85KB, 35% smaller)

![BH1750 without GPIO](https://raw.githubusercontent.com/nordstad/PinViz/main/images/examples/bh1750_without_gpio.svg)

</details>

**📸 More Examples:**
- See all examples in [`examples/`](examples/) directory
- View generated diagrams in [`images/`](images/) directory
- [Browse example gallery in docs →](https://nordstad.github.io/PinViz/guide/examples/)
```

### 4. Collapse Configuration Reference (Lines 399-536)

Replace with:

```markdown
## ⚙️ Configuration Reference

<details>
<summary><b>📋 Diagram Options</b></summary>

### GPIO Pin Reference

Control whether to show the GPIO pinout diagram:

**YAML:**
```yaml
show_gpio_diagram: true  # default: false
```

**CLI:**
```bash
pinviz example bh1750 --gpio -o diagram.svg      # ~130KB with GPIO
pinviz example bh1750 --no-gpio -o diagram.svg   # ~85KB without GPIO
```

</details>

<details>
<summary><b>🎛️ Board Selection</b></summary>

- `raspberry_pi_5` (aliases: `rpi5`, `rpi`)
- `raspberry_pi_zero_2w` (aliases: `pizero`, `zero2w`, `zero`)

</details>

<details>
<summary><b>🔌 Built-in Device Types</b></summary>

- `bh1750` - I2C light sensor
- `ir_led_ring` - IR LED ring module
- `i2c_device` - Generic I2C device
- `spi_device` - Generic SPI device
- `led` - Simple LED
- `button` - Push button

</details>

<details>
<summary><b>🔗 Connection Configuration</b></summary>

```yaml
connections:
  - board_pin: 1           # Physical pin (1-40)
    device: "Device Name"
    device_pin: "VCC"
    color: "#FF0000"       # Optional custom color
    style: "mixed"         # orthogonal, curved, mixed
    components:            # Optional inline components
      - type: "resistor"
        value: "220Ω"
        position: 0.55     # 0.0 (board) to 1.0 (device)
```

</details>

<details>
<summary><b>⚡ Inline Components</b></summary>

Add resistors, capacitors, or diodes on wires:

```yaml
components:
  - type: "resistor"   # resistor, capacitor, diode
    value: "220Ω"
    position: 0.55     # Position along wire (0.0-1.0)
```

Python API:
```python
from pinviz import Component, ComponentType

Component(type=ComponentType.RESISTOR, value="220Ω", position=0.55)
```

</details>

<details>
<summary><b>🎨 Custom Devices</b></summary>

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
      # ...more pins
```

</details>

**📖 Full Configuration Guide:**
- [YAML Configuration →](https://nordstad.github.io/PinViz/guide/yaml-config/)
- [Python API Reference →](https://nordstad.github.io/PinViz/guide/python-api/)
- [API Documentation →](https://nordstad.github.io/PinViz/api/)
```

### 5. Add Documentation Section

Add this new section before "Development":

```markdown
## 📖 Documentation

**Full documentation available at [nordstad.github.io/PinViz](https://nordstad.github.io/PinViz/)**

### User Guides
- [Installation Guide](https://nordstad.github.io/PinViz/getting-started/installation/)
- [Quick Start Tutorial](https://nordstad.github.io/PinViz/getting-started/quickstart/)
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

### Development
- [Contributing Guide](https://nordstad.github.io/PinViz/development/contributing/)
- [Architecture Overview](https://nordstad.github.io/PinViz/development/architecture/)
```

### 6. Simplify Features Section (Lines 24-44)

Collapse into a more scannable format:

```markdown
## ✨ Features

### 📦 PinViz Package

<details>
<summary><b>View all features</b></summary>

- **Declarative Configuration**: YAML/JSON files
- **Programmatic API**: Python code generation
- **Automatic Wire Routing**: Orthogonal, curved, mixed styles
- **Inline Components**: Resistors, capacitors, diodes on wires
- **Color-Coded Wires**: Auto-color by function (I2C, SPI, power, ground)
- **Built-in Templates**: Pre-configured boards and devices
- **GPIO Pin Reference**: Optional pinout diagram
- **SVG Output**: Scalable vector graphics

</details>

**[→ See all CLI features in docs](https://nordstad.github.io/PinViz/guide/cli/)**

### 🤖 MCP Server (AI-Powered)

<details>
<summary><b>View all features</b></summary>

- **Natural Language**: "Connect BME280 and LED to my Pi"
- **Intelligent Pin Assignment**: I2C sharing, SPI chip selects, conflict detection
- **25+ Device Database**: Sensors, displays, HATs, components
- **URL-Based Discovery**: Parse datasheets from manufacturer sites
- **AI Integration**: Claude Desktop, GitHub Copilot, MCP clients

</details>

**[→ Learn more about MCP →](https://nordstad.github.io/PinViz/mcp-server/)**
```

## Summary of Benefits

### Before (Current)
- ❌ 588 lines - difficult to scan
- ❌ All content visible - overwhelming
- ❌ Large embedded images slow loading
- ❌ Duplicates documentation content
- ❌ No quick navigation

### After (Improved)
- ✅ ~300-350 lines collapsed state
- ✅ Scannable structure with TOC
- ✅ Progressive disclosure (expand what you need)
- ✅ Links to docs for detailed info
- ✅ Quick navigation with TOC
- ✅ Faster load time (images collapsed)
- ✅ Better mobile experience

## Implementation Priority

1. **High Priority (Do First)**
   - Add Table of Contents
   - Collapse MCP Server section
   - Collapse Example Diagrams
   - Add Documentation section with links

2. **Medium Priority**
   - Collapse Configuration Reference
   - Simplify Features section
   - Add "Read More" links throughout

3. **Low Priority (Nice to Have)**
   - Add image thumbnails
   - Add badges/shields for stats
   - Add sponsor/support section

## Estimated Impact

- **Reduction**: ~40-50% of visible content (collapsed)
- **Load Time**: 30-40% faster (images collapsed)
- **User Experience**: Much easier to find relevant information
- **Maintenance**: Easier to keep README concise, detailed docs in mkdocs

## Alternative: Minimal README

For an even more aggressive approach, create a very minimal README that focuses on:
1. What is PinViz (2-3 sentences)
2. Quick Install (2 lines)
3. Quick Start (1 example)
4. Link to full documentation

This would reduce README to ~150 lines and push everything else to mkdocs.
