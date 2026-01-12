# Examples

Explore example diagrams and configurations to learn how to use PinViz.

## Demo - Custom Device Creation

<p align="center">
  <img src="https://raw.githubusercontent.com/nordstad/PinViz/main/scripts/demos/output/custom_device_demo.gif" alt="PinViz Custom Device Demo" width="800">
</p>

## 🎯 Feature Showcase

Learn PinViz capabilities through these focused examples:

| Feature | Example | What it demonstrates |
|---------|---------|---------------------|
| **I2C Sensors** | [BH1750](#bh1750-light-sensor) | Automatic I2C color coding, bus sharing |
| **Inline Components** | [LED with Resistor](#led-with-resistor) | Resistors, capacitors, diodes on wires |
| **Multiple Devices** | [Traffic Light](#traffic-light) | Parallel connections, multiple LEDs |
| **Wire Routing** | [Multi-Device Setup](#multi-device-setup) | Custom wire colors, complex routing |
| **Pico Board** | [Pico LED](#pico-led-circuit) | Dual-sided board, horizontal pin layout |
| **Specifications Table** | [Pico LEDs with Specs](#pico-multi-led-circuit-with-specifications) | Device specs, part numbers, --show-legend |

## Quick Start with Built-in Examples

The fastest way to try PinViz is using the built-in examples:

```bash
# List all available examples
pinviz list

# Generate a specific example
pinviz example bh1750 -o bh1750.svg
pinviz example ir_led -o ir_led.svg
pinviz example i2c_spi -o i2c_spi.svg

# Include device specifications table (--show-legend flag)
pinviz render examples/leds_with_specs.yaml --show-legend
```

All example configurations are available in the [`examples/`](https://github.com/nordstad/PinViz/tree/main/examples) directory.

---

## Example Gallery

### BH1750 Light Sensor

Simple I2C sensor connection demonstrating automatic color coding for I2C bus (SDA/SCL).

**Configuration:** [`examples/bh1750.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/bh1750.yaml)

```yaml
title: "BH1750 Light Sensor Wiring"
board: "raspberry_pi_5"

devices:
  - type: "bh1750"
    name: "BH1750"

connections:
  - board_pin: 1    # 3V3
    device: "BH1750"
    device_pin: "VCC"

  - board_pin: 6    # GND
    device: "BH1750"
    device_pin: "GND"

  - board_pin: 5    # GPIO3 (I2C SCL)
    device: "BH1750"
    device_pin: "SCL"

  - board_pin: 3    # GPIO2 (I2C SDA)
    device: "BH1750"
    device_pin: "SDA"

```

**Generate:**

```bash
pinviz example bh1750 -o bh1750.svg
```

**Result:**

![BH1750 Light Sensor](https://raw.githubusercontent.com/nordstad/PinViz/main/images/bh1750.svg)

---

### LED with Resistor

Simple LED circuit demonstrating inline components (resistor on wire).

**Configuration:** [`examples/led_with_resistor.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/led_with_resistor.yaml)

```yaml
title: "LED with Current-Limiting Resistor"
board: "raspberry_pi_5"

devices:
  - type: "led"
    color: "Red"
    name: "Red LED"

connections:
  # LED Anode to GPIO17 via 220Ω resistor
  - board_pin: 11  # GPIO17
    device: "Red LED"
    device_pin: "+"
    color: "#FF0000"  # Red wire
    components:
      - type: "resistor"
        value: "220Ω"

  # LED Cathode to Ground
  - board_pin: 9  # GND
    device: "Red LED"
    device_pin: "-"
    color: "#000000"  # Black wire

```

**Generate:**

```bash
pinviz render examples/led_with_resistor.yaml -o led.svg
```

**Result:**

![LED with Resistor](https://raw.githubusercontent.com/nordstad/PinViz/main/images/led_with_resistor.svg)

**Key Features:**
- Inline resistor component on wire
- Custom wire colors (red for power, black for ground)
- Simple single-device connection

---

### Traffic Light

Multiple LEDs with individual resistors demonstrating parallel device connections.

**Configuration:** [`examples/traffic_light.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/traffic_light.yaml)

```yaml
title: "Traffic Light - 3 LEDs with Resistors"
board: "raspberry_pi_5"

devices:
  - type: "led"
    color: "Red"
    name: "Red LED"
  - type: "led"
    color: "Yellow"
    name: "Yellow LED"
  - type: "led"
    color: "Green"
    name: "Green LED"

connections:
  # Red LED (GPIO17)
  - board_pin: 11
    device: "Red LED"
    device_pin: "+"
    color: "#FF0000"
    components:
      - type: "resistor"
        value: "220Ω"
  - board_pin: 9
    device: "Red LED"
    device_pin: "-"
    color: "#000000"

  # Yellow LED (GPIO27)
  - board_pin: 13
    device: "Yellow LED"
    device_pin: "+"
    color: "#FFFF00"
    components:
      - type: "resistor"
        value: "220Ω"
  - board_pin: 14
    device: "Yellow LED"
    device_pin: "-"
    color: "#000000"

  # Green LED (GPIO22)
  - board_pin: 15
    device: "Green LED"
    device_pin: "+"
    color: "#00FF00"
    components:
      - type: "resistor"
        value: "220Ω"
  - board_pin: 20
    device: "Green LED"
    device_pin: "-"
    color: "#000000"

```

**Generate:**

```bash
pinviz render examples/traffic_light.yaml -o traffic_light.svg
```

**Result:**

![Traffic Light](https://raw.githubusercontent.com/nordstad/PinViz/main/images/traffic_light.svg)

**Key Features:**
- Multiple devices of the same type
- Each LED has its own resistor
- Color-coded wires matching LED colors
- Multiple ground connections

---

### Multi-Device Setup

BH1750 light sensor and IR LED ring demonstrating I2C bus sharing and custom wire colors.

**Configuration:** [`examples/bh1750_ir_led.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/bh1750_ir_led.yaml)

```yaml
title: "BH1750 Light Sensor + IR LED Ring"
board: "raspberry_pi_5"

devices:
  - type: "bh1750"
    name: "BH1750 Light Sensor"
  - type: "ir_led_ring"
    name: "IR LED Ring"

connections:
  # BH1750 Light Sensor
  - board_pin: 1
    device: "BH1750 Light Sensor"
    device_pin: "VCC"
    color: "#FF9800"  # Orange
  - board_pin: 9
    device: "BH1750 Light Sensor"
    device_pin: "GND"
    color: "#FFEB3B"  # Yellow
  - board_pin: 3
    device: "BH1750 Light Sensor"
    device_pin: "SDA"
    color: "#4CAF50"  # Green
  - board_pin: 5
    device: "BH1750 Light Sensor"
    device_pin: "SCL"
    color: "#2196F3"  # Blue

  # IR LED Ring
  - board_pin: 2
    device: "IR LED Ring"
    device_pin: "VCC"
    color: "#F44336"  # Red
  - board_pin: 6
    device: "IR LED Ring"
    device_pin: "GND"
    color: "#000000"  # Black
  - board_pin: 11
    device: "IR LED Ring"
    device_pin: "CTRL"
    color: "#F44336"  # Red

```

**Generate:**

```bash
pinviz render examples/bh1750_ir_led.yaml -o multi_device.svg
```

**Result:**

![BH1750 + IR LED Ring](https://raw.githubusercontent.com/nordstad/PinViz/main/images/bh1750_ir_led.svg)

**Key Features:**
- Two different device types
- I2C sensor + GPIO-controlled device
- Custom color palette for wire differentiation
- Multiple power and ground connections

---

### Device Specifications Table

Add a specifications table to your diagrams using the `--show-legend` CLI flag. This displays detailed information about each device below the diagram.

**Example with specifications:**

```bash
# Generate diagram with specifications table
pinviz render examples/leds_with_specs.yaml --show-legend -o leds_with_specs.svg
```

**Result:**

![Multi-LED Circuit with Specifications](https://raw.githubusercontent.com/nordstad/PinViz/main/images/leds_with_specs.svg)

**Configuration:** [`examples/leds_with_specs.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/leds_with_specs.yaml)

The specifications table is triggered by the `--show-legend` CLI flag and automatically includes device descriptions when defined in your YAML:

```yaml
title: "Multi-LED Circuit with Specifications"
board: "raspberry_pi_5"

devices:
  - type: "led"
    name: "Red LED"
    description: "Kingbright WP7113ID, 5mm, Vf: 2.0V, If: 20mA, 625nm"
    color: "Red"

  - type: "led"
    name: "Blue LED"
    description: "Lite-On LTL-4221N, 3mm, Vf: 3.2V, If: 20mA, 470nm"
    color: "Blue"

  - type: "led"
    name: "Green LED"
    description: "Kingbright WP7113SGC, 5mm, Vf: 2.2V, If: 20mA, 525nm"
    color: "Green"

connections:
  # Red LED (GPIO17)
  - board_pin: 11
    device: "Red LED"
    device_pin: "+"
    color: "#FF0000"
    components:
      - type: "resistor"
        value: "150Ω"
  # ... additional connections ...
```

**Key Features:**

- **CLI Flag**: Use `--show-legend` flag to enable the specifications table
- **Automatic Layout**: Displays device descriptions in a clean table below the diagram
- **Text Wrapping**: Long descriptions wrap properly for readability
- **Optional Metadata**: Device descriptions in YAML are optional; table only appears if descriptions exist
- **Part Details**: Perfect for documenting part numbers, electrical specs, and technical characteristics

**When to use:**

- Documentation that requires component details
- Projects with multiple similar devices
- Technical specifications needed for assembly
- Part numbers and electrical characteristics

---

## Raspberry Pi Pico Examples

The following examples demonstrate using PinViz with the Raspberry Pi Pico, which has a unique dual-sided GPIO header layout.

### Pico LED Circuit

Simple LED circuit on Raspberry Pi Pico demonstrating GPIO pin usage on the top header.

**Configuration:** [`examples/pico_led.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/pico_led.yaml)

```yaml
title: "Raspberry Pi Pico - Simple LED"
board: "raspberry_pi_pico"

devices:
  - type: "led"
    color: "Green"
    name: "Status LED"

connections:
  # LED Anode to GP0 via 220Ω resistor
  - board_pin: 1   # GP0 (top header, rightmost pin)
    device: "Status LED"
    device_pin: "+"
    color: "#00FF00"
    components:
      - type: "resistor"
        value: "220Ω"

  # LED Cathode to Ground
  - board_pin: 3   # GND (top header)
    device: "Status LED"
    device_pin: "-"
    color: "#000000"
```

**Generate:**

```bash
pinviz render examples/pico_led.yaml -o pico_led.svg
```

**Result:**

![Pico LED Circuit](https://raw.githubusercontent.com/nordstad/PinViz/main/images/pico_led.svg)

**Key Features:**
- Raspberry Pi Pico board with dual-sided header
- GP0 GPIO pin usage (top header)
- Inline resistor component
- Horizontal pin layout (Pico-style)

---

### Pico BME280 Sensor

I2C sensor connection on Raspberry Pi Pico using I2C0 bus (GP4 = SDA, GP5 = SCL).

**Configuration:** [`examples/pico_bme280.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/pico_bme280.yaml)

```yaml
title: "Raspberry Pi Pico - BME280 Sensor"
board: "raspberry_pi_pico"

devices:
  - type: "bme280"
    name: "BME280"

connections:
  # VCC to 3.3V
  - board_pin: 36  # 3V3 (bottom header)
    device: "BME280"
    device_pin: "VCC"
    color: "#FF0000"

  # GND to Ground
  - board_pin: 38  # GND (bottom header)
    device: "BME280"
    device_pin: "GND"
    color: "#000000"

  # SDA to GP4 (I2C0 SDA)
  - board_pin: 6   # GP4 (top header)
    device: "BME280"
    device_pin: "SDA"
    color: "#2196F3"  # Blue - visible against white background

  # SCL to GP5 (I2C0 SCL)
  - board_pin: 7   # GP5 (top header)
    device: "BME280"
    device_pin: "SCL"
    color: "#FF9800"  # Orange - visible against white background
```

**Generate:**

```bash
pinviz render examples/pico_bme280.yaml -o pico_bme280.svg
```

**Result:**

![Pico BME280 Sensor](https://raw.githubusercontent.com/nordstad/PinViz/main/images/pico_bme280.svg)

**Key Features:**
- I2C sensor on Pico's I2C0 bus
- Connections span top and bottom headers
- Power from bottom header (3V3, GND)
- Data lines from top header (GP4, GP5)
- Demonstrates Pico's dual-header layout

---

### Pico Multi-LED Circuit with Specifications

Three LEDs with resistors and detailed component specifications, demonstrating the `--show-legend` flag.

**Configuration:** [`examples/pico_leds_with_specs.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/pico_leds_with_specs.yaml)

```yaml
title: "Raspberry Pi Pico - Multi-LED Circuit with Specifications"
board: "raspberry_pi_pico"

devices:
  - type: "led"
    name: "Red LED"
    description: "Kingbright WP7113ID, 5mm, Vf: 2.0V, If: 20mA, 625nm"
    color: "Red"

  - type: "led"
    name: "Green LED"
    description: "Kingbright WP7113SGC, 5mm, Vf: 2.2V, If: 20mA, 525nm"
    color: "Green"

  - type: "led"
    name: "Blue LED"
    description: "Lite-On LTL-4221N, 3mm, Vf: 3.2V, If: 20mA, 470nm"
    color: "Blue"

connections:
  # Red LED (GP0)
  - board_pin: 1   # GP0 (top header)
    device: "Red LED"
    device_pin: "+"
    color: "#FF0000"
    components:
      - type: "resistor"
        value: "150Ω"

  - board_pin: 3   # GND (top header)
    device: "Red LED"
    device_pin: "-"
    color: "#000000"

  # Green LED (GP1)
  - board_pin: 2   # GP1 (top header)
    device: "Green LED"
    device_pin: "+"
    color: "#00FF00"
    components:
      - type: "resistor"
        value: "150Ω"

  - board_pin: 8   # GND (top header)
    device: "Green LED"
    device_pin: "-"
    color: "#000000"

  # Blue LED (GP2)
  - board_pin: 4   # GP2 (top header)
    device: "Blue LED"
    device_pin: "+"
    color: "#0000FF"
    components:
      - type: "resistor"
        value: "100Ω"

  - board_pin: 13  # GND (top header)
    device: "Blue LED"
    device_pin: "-"
    color: "#000000"
```

**Generate:**

```bash
pinviz render examples/pico_leds_with_specs.yaml --show-legend -o pico_leds_with_specs.svg
```

**Result:**

![Pico Multi-LED Circuit with Specifications](https://raw.githubusercontent.com/nordstad/PinViz/main/images/pico_leds_with_specs.svg)

**Key Features:**
- Three LEDs with individual resistors on Pico
- Device specifications table with part numbers and electrical characteristics
- Uses `--show-legend` CLI flag to display specs
- All connections on top header (GP0, GP1, GP2)
- Demonstrates inline resistor components
- Perfect for documenting component details in projects

---

**Board Aliases:**
You can use any of these board names in your configuration:
- `raspberry_pi_pico`
- `pico`
- `rpi pico`

---

## More Examples

All example files (YAML and Python) are available in the repository:

- **YAML Examples**: [`examples/`](https://github.com/nordstad/PinViz/tree/main/examples) directory
- **Python Examples**: Same directory with `_python.py` suffix
- **Generated Diagrams**: [`images/`](https://github.com/nordstad/PinViz/tree/main/images) directory

### Available Examples

**Raspberry Pi 5/4:**
- `bh1750.yaml` / `bh1750_python.py` - I2C light sensor
- `led_with_resistor.yaml` / `led_with_resistor_python.py` - LED with inline resistor
- `traffic_light.yaml` - Three LEDs with resistors
- `bh1750_ir_led.yaml` / `bh1750_ir_led_python.py` - Multi-device setup
- `ir_led_ring.yaml` / `ir_led_ring_python.py` - IR LED ring module
- `multi_device.yaml` / `multi_device_python.py` - Multiple I2C devices
- `ds18b20_temp.yaml` / `ds18b20_temp_python.py` - 1-Wire temperature sensor

**Raspberry Pi Pico:**
- `pico_led.yaml` - Simple LED circuit with resistor
- `pico_bme280.yaml` - I2C sensor using I2C0 bus
- `pico_leds_with_specs.yaml` - Three LEDs with specifications table

---

## Contributing Examples

Have a cool diagram to share? We'd love to include it!

**Submission guidelines:**

1. **YAML Configuration**: Well-commented configuration file
2. **Python Version** (optional): Equivalent Python code
3. **Description**: Brief description of what the example demonstrates
4. **Generated SVG**: The rendered diagram
5. **Real-world use case**: Bonus points for practical applications!

Submit your example as a pull request to the [`examples/`](https://github.com/nordstad/PinViz/tree/main/examples) directory.

**What makes a good example:**

- Clear, well-commented configuration
- Demonstrates a specific feature or pattern
- Real-world use case or common scenario
- Clean, readable diagram output
- Helpful for learning

---

## Next Steps

- [YAML Configuration Guide](yaml-config.md) - Learn all configuration options
- [Python API Guide](python-api.md) - Use PinViz programmatically
- [CLI Usage](cli.md) - Master the command-line interface
- [API Reference](../api/index.md) - Detailed API documentation
