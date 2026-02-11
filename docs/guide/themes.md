# Themes

PinViz supports both light and dark themes for your diagrams, allowing you to match your documentation's appearance or improve visibility in different viewing environments.

## Overview

The theme system provides:

- **Light mode** (default) - Traditional white background with dark text
- **Dark mode** - Dark background (#1E1E1E) with light text, optimized for dark theme documentation

Wire colors and pin role colors remain unchanged across themes to maintain electrical conventions and functional identification.

## Using Themes

### YAML/JSON Configuration

Add the `theme` field to your configuration file:

```yaml
title: "My Diagram"
board: "raspberry_pi_5"
theme: "dark"  # Options: "light" (default), "dark"

devices:
  - type: "bh1750"
    name: "Light Sensor"

connections:
  - board_pin: 1
    device: "Light Sensor"
    device_pin: "VCC"
  # ... more connections
```

### CLI Override

Override the theme from the command line:

```bash
# Use dark theme regardless of config
pinviz render diagram.yaml --theme dark -o output.svg

# Use light theme
pinviz render diagram.yaml --theme light -o output.svg
```

The CLI `--theme` flag takes precedence over the configuration file.

### Python API

Set the theme when creating a diagram:

```python
from pinviz import Diagram, boards
from pinviz.theme import Theme
from pinviz.render_svg import SVGRenderer

diagram = Diagram(
    title="My Diagram",
    board=boards.raspberry_pi_5(),
    devices=[...],
    connections=[...],
    theme=Theme.DARK  # or Theme.LIGHT
)

renderer = SVGRenderer()
renderer.render(diagram, "output.svg")
```

Or override it after loading from config:

```python
from pinviz.config_loader import load_diagram
from pinviz.theme import Theme
from pinviz.render_svg import SVGRenderer

diagram = load_diagram("config.yaml")
diagram.theme = Theme.DARK  # Override config

renderer = SVGRenderer()
renderer.render(diagram, "output.svg")
```

## Theme Details

### Light Theme (Default)

- **Canvas**: White background
- **Text**: Dark gray (#333, #666)
- **Tables**: Light gray backgrounds (#F8F9FA, #E9ECEF)
- **Pin labels**: Black background with white text
- **Borders**: Dark gray (#333)

### Dark Theme

- **Canvas**: Dark gray (#1E1E1E - VS Code dark theme color)
- **Text**: Light gray (#E0E0E0, #B0B0B0) for high contrast
- **Tables**: Dark gray backgrounds (#2D2D2D, #3A3A3A)
- **Pin labels**: White background with black text (inverted for contrast)
- **Borders**: Light gray (#E0E0E0)

### What Stays the Same

The following elements remain consistent across themes to maintain clarity and electrical conventions:

- **Wire colors** - Follow electrical conventions (red=5V, orange=3.3V, black=GND, yellow=I2C, cyan=SPI, etc.)
- **Pin role colors** - Functional identification on GPIO header (orange=3V3, red=5V, gray=GND, magenta=I2C, blue=SPI, green=GPIO)
- **Device colors** - Category-based colors (turquoise=sensors, red=LEDs, blue=displays). Can be overridden per device using named colors or hex codes (see [YAML Configuration](yaml-config.md#device-colors))
- **Wire halos** - Dynamically adapt based on wire luminance for visibility

## Examples

### Simple Example

**Light mode:**
```yaml
title: "BH1750 Light Sensor"
board: "raspberry_pi_5"
theme: "light"

devices:
  - type: "bh1750"

connections:
  - board_pin: 1
    device: "BH1750"
    device_pin: "VCC"
  - board_pin: 6
    device: "BH1750"
    device_pin: "GND"
  - board_pin: 3
    device: "BH1750"
    device_pin: "SDA"
  - board_pin: 5
    device: "BH1750"
    device_pin: "SCL"
```

**Dark mode:**
```yaml
title: "BH1750 Light Sensor (Dark Mode)"
board: "raspberry_pi_5"
theme: "dark"

devices:
  - type: "bh1750"

connections:
  - board_pin: 1
    device: "BH1750"
    device_pin: "VCC"
  - board_pin: 6
    device: "BH1750"
    device_pin: "GND"
  - board_pin: 3
    device: "BH1750"
    device_pin: "SDA"
  - board_pin: 5
    device: "BH1750"
    device_pin: "SCL"
```

### Complex Example with Legend

```yaml
title: "I2C and SPI Devices (Dark Mode)"
board: "raspberry_pi_5"
theme: "dark"
show_legend: true

devices:
  - type: "bh1750"
    name: "Light Sensor"
  - type: "ssd1306"
    name: "OLED Display"
  - type: "spi_device"
    name: "SPI Module"

connections:
  # Light Sensor (I2C)
  - board_pin: 1
    device: "Light Sensor"
    device_pin: "VCC"
  - board_pin: 6
    device: "Light Sensor"
    device_pin: "GND"
  - board_pin: 3
    device: "Light Sensor"
    device_pin: "SDA"
  - board_pin: 5
    device: "Light Sensor"
    device_pin: "SCL"

  # OLED Display (I2C - shared bus)
  - board_pin: 17
    device: "OLED Display"
    device_pin: "VCC"
  - board_pin: 20
    device: "OLED Display"
    device_pin: "GND"
  - board_pin: 3
    device: "OLED Display"
    device_pin: "SDA"
  - board_pin: 5
    device: "OLED Display"
    device_pin: "SCL"

  # SPI Module
  - board_pin: 17
    device: "SPI Module"
    device_pin: "VCC"
  - board_pin: 25
    device: "SPI Module"
    device_pin: "GND"
  - board_pin: 19
    device: "SPI Module"
    device_pin: "MOSI"
  - board_pin: 21
    device: "SPI Module"
    device_pin: "MISO"
  - board_pin: 23
    device: "SPI Module"
    device_pin: "SCLK"
  - board_pin: 24
    device: "SPI Module"
    device_pin: "CS"
```

## Use Cases

### Documentation Integration

**Dark theme documentation:**
```bash
# Generate diagram matching your dark-themed docs
pinviz render sensor_wiring.yaml --theme dark -o docs/images/sensor_wiring.svg
```

**Light theme documentation:**
```bash
# Generate diagram for light-themed docs
pinviz render sensor_wiring.yaml --theme light -o docs/images/sensor_wiring.svg
```

### Presentations

Dark mode diagrams work better on:
- Dark backgrounds in slide decks
- Terminal/console documentation
- Dark IDE themes
- Developer documentation portals

Light mode diagrams work better on:
- Traditional printed documentation
- Light-themed websites
- PDF reports
- Datasheets

### Accessibility

Choose the theme that provides the best contrast ratio for your audience:

- **Dark mode**: Reduces eye strain in low-light environments
- **Light mode**: Better for bright environments and printing

## Best Practices

1. **Match your documentation**: Use the same theme as your documentation platform for visual consistency
2. **Consider printing**: Use light mode if diagrams will be printed
3. **Test both themes**: View diagrams in both themes to ensure readability
4. **Use legends wisely**: Enable legends (`show_legend: true`) in complex diagrams for better understanding
5. **File naming**: Use descriptive names like `sensor_wiring_dark.svg` to distinguish theme variants

## Examples in Repository

Check out these example files:

- `examples/bh1750_dark.yaml` - Simple dark mode diagram
- `examples/i2c_spi_dark.yaml` - Complex dark mode with multiple devices
- `examples/bh1750.yaml` - Light mode (default) for comparison

Generate them:

```bash
pinviz render examples/bh1750_dark.yaml -o out/bh1750_dark.svg
pinviz render examples/i2c_spi_dark.yaml -o out/i2c_spi_dark.svg
```

## Troubleshooting

### Theme not applying

Make sure you're using the correct syntax:

```yaml
theme: "dark"  # ✓ Correct
theme: dark    # ✓ Also works (no quotes)
theme: "Dark"  # ✓ Case-insensitive
theme: darkmode  # ✗ Invalid - use "dark" or "light"
```

### CLI override not working

The `--theme` flag must be specified correctly:

```bash
pinviz render config.yaml --theme dark  # ✓ Correct
pinviz render config.yaml -t dark       # ✗ Use full --theme flag
```

### Colors look wrong

Wire colors and pin colors are theme-independent by design. Only the background, text, and UI elements change between themes. This ensures:

- Consistent electrical conventions
- Functional pin identification
- Easier diagram comparison across themes
