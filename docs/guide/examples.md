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
| **Wire Visibility** | [Light & Dark Wires](#wire-visibility---light--dark-colors) | Automatic halo color selection for wire visibility |
| **I2C Sensors** | [BH1750](#bh1750-light-sensor) | Automatic I2C color coding, bus sharing |
| **Inline Components** | [LED with Resistor](#led-with-resistor) | Resistors, capacitors, diodes on wires |
| **Multiple Devices** | [Traffic Light](#traffic-light) | Parallel connections, multiple LEDs |
| **Multi-Tier Connections** | [Motor Control](#motor-control-with-l293d) | Device-to-device chains, motor drivers, relay control |
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

### Wire Visibility - Light & Dark Colors

Demonstrates PinViz's intelligent wire visibility system that automatically ensures all wire colors remain visible against white backgrounds. Light-colored wires receive dark halos, while dark wires keep traditional white halos.

**Configuration:** [`examples/wire_visibility.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/wire_visibility.yaml)

```yaml
title: "Wire Visibility - Light & Dark Colors"
board: "raspberry_pi_5"

devices:
  - name: "Light Colors Device"
    description: "Demonstrates automatic dark halos for light-colored wires"
    pins:
      - name: "WHITE"
        role: "GPIO"
      - name: "LIGHT_GRAY"
        role: "GPIO"
      - name: "PALE_YELLOW"
        role: "GPIO"
      - name: "CREAM"
        role: "GPIO"

  - name: "Dark Colors Device"
    description: "Shows traditional white halos for dark-colored wires"
    pins:
      - name: "BLACK"
        role: "GPIO"
      - name: "DARK_RED"
        role: "GPIO"
      - name: "NAVY"
        role: "GPIO"
      - name: "FOREST"
        role: "GPIO"

connections:
  # Light colored wires - automatically get dark gray halos
  - board_pin: 1
    device: "Light Colors Device"
    device_pin: "WHITE"
    color: "#FFFFFF"  # Pure white

  - board_pin: 3
    device: "Light Colors Device"
    device_pin: "LIGHT_GRAY"
    color: "#F0F0F0"  # Light gray

  - board_pin: 5
    device: "Light Colors Device"
    device_pin: "PALE_YELLOW"
    color: "#FFFFE0"  # Pale yellow

  - board_pin: 7
    device: "Light Colors Device"
    device_pin: "CREAM"
    color: "#FFFACD"  # Lemon chiffon

  # Dark colored wires - keep traditional white halos
  - board_pin: 11
    device: "Dark Colors Device"
    device_pin: "BLACK"
    color: "#000000"  # Black

  - board_pin: 13
    device: "Dark Colors Device"
    device_pin: "DARK_RED"
    color: "#8B0000"  # Dark red

  - board_pin: 15
    device: "Dark Colors Device"
    device_pin: "NAVY"
    color: "#000080"  # Navy blue

  - board_pin: 19
    device: "Dark Colors Device"
    device_pin: "FOREST"
    color: "#228B22"  # Forest green

show_legend: true
```

**Generate:**

```bash
pinviz render examples/wire_visibility.yaml -o wire_visibility.svg
```

**Result:**

![Wire Visibility Example](https://raw.githubusercontent.com/nordstad/PinViz/main/images/wire_visibility.svg)

**Key Features:**

- **Automatic visibility detection**: PinViz calculates color luminance using WCAG 2.0 formula
- **Dynamic halo colors**: Light wires (luminance > 0.7) get dark gray halos (#2C2C2C)
- **Traditional rendering preserved**: Dark/medium wires keep white halos
- **No configuration needed**: Works automatically for all custom wire colors
- **Professional results**: All wires remain clearly visible on white backgrounds

**How it works:**

1. When you specify a wire color (e.g., `color: "#FFFFFF"`), PinViz calculates its relative luminance
2. If the luminance exceeds 0.7 (very bright colors), a dark gray halo is used
3. Otherwise, the traditional white halo is applied
4. This ensures optimal visibility for both light and dark colored wires

**Perfect for:**

- Custom color palettes with light/pastel colors
- Documentation requiring specific brand colors
- Projects with white or cream colored wires
- Diagrams that need to maintain exact color specifications

---

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
    device_pin: "EN"
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

## Multi-Tier Connections

Multi-tier diagrams show connections that flow through intermediate devices, creating device chains like board → motor driver → motor or board → relay → load. This is a powerful feature for documenting complex systems with motor controllers, ADCs, power distribution, and relay switching.

### Motor Control with L293D

DC motor control through L293D motor driver IC, demonstrating a three-tier connection chain: Raspberry Pi → L293D Driver → DC Motor.

**Configuration:** [`examples/motor_control.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/motor_control.yaml)

```yaml
# Raspberry Pi → L293D Motor Driver → DC Motor
title: "DC Motor Control with L293D"
board: "raspberry_pi_5"
devices:
  - name: "L293D Driver"
    pins:
      - name: "VCC1"
        role: "5V"
      - name: "VCC2"
        role: "5V"
      - name: "GND"
        role: "GND"
      - name: "IN1"
        role: "GPIO"
      - name: "IN2"
        role: "GPIO"
      - name: "OUT1"
        role: "GPIO"
      - name: "OUT2"
        role: "GPIO"
  - name: "DC Motor"
    pins:
      - name: "MOTOR+"
        role: "GPIO"
      - name: "MOTOR-"
        role: "GPIO"
connections:
  # Power to driver
  - from: {board_pin: 2}
    to: {device: "L293D Driver", device_pin: "VCC1"}
  - from: {board_pin: 4}
    to: {device: "L293D Driver", device_pin: "VCC2"}
  - from: {board_pin: 6}
    to: {device: "L293D Driver", device_pin: "GND"}
  # Control signals
  - from: {board_pin: 11}
    to: {device: "L293D Driver", device_pin: "IN1"}
  - from: {board_pin: 13}
    to: {device: "L293D Driver", device_pin: "IN2"}
  # Driver to motor (device-to-device)
  - from: {device: "L293D Driver", device_pin: "OUT1"}
    to: {device: "DC Motor", device_pin: "MOTOR+"}
  - from: {device: "L293D Driver", device_pin: "OUT2"}
    to: {device: "DC Motor", device_pin: "MOTOR-"}
show_legend: true
```

**Generate:**

```bash
pinviz render examples/motor_control.yaml -o motor_control.svg
```

**Result:**

![Motor Control with L293D](https://raw.githubusercontent.com/nordstad/PinViz/main/images/motor_control.svg)

**Key Features:**

- **Three-tier connection chain**: Board → Driver → Motor
- **`from`/`to` syntax**: Device-to-device connections use `from: {device: "...", device_pin: "..."}` and `to: {device: "...", device_pin: "..."}`
- **Mixed connections**: Combines board-to-device and device-to-device connections
- **Real-world application**: Robot motor control, automated systems, CNC machines
- **Specifications table**: Includes `show_legend: true` for device details

---

### Relay Control for High Voltage Devices

Relay module controlling a high-voltage load, showing another practical multi-tier application.

**Configuration:** [`examples/relay_control.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/relay_control.yaml)

```yaml
# Pi → Relay Module → High Voltage Device (represented as load)
title: "Relay Control for High Voltage Device"
board: "raspberry_pi_5"
devices:
  - name: "5V Relay Module"
    pins:
      - name: "VCC"
        role: "5V"
      - name: "GND"
        role: "GND"
      - name: "IN"
        role: "GPIO"
      - name: "COM"
        role: "GPIO"
      - name: "NO"
        role: "GPIO"
  - name: "Load"
    pins:
      - name: "POWER"
        role: "GPIO"
      - name: "GND"
        role: "GND"
connections:
  # Power and control to relay
  - from: {board_pin: 2}
    to: {device: "5V Relay Module", device_pin: "VCC"}
  - from: {board_pin: 6}
    to: {device: "5V Relay Module", device_pin: "GND"}
  - from: {board_pin: 11}
    to: {device: "5V Relay Module", device_pin: "IN"}
  # Relay to load (device-to-device)
  - from: {device: "5V Relay Module", device_pin: "NO"}
    to: {device: "Load", device_pin: "POWER"}
show_legend: true
```

**Generate:**

```bash
pinviz render examples/relay_control.yaml -o relay_control.svg
```

**Result:**

![Relay Control](https://raw.githubusercontent.com/nordstad/PinViz/main/images/relay_control.svg)

**Key Features:**

- **Safety isolation**: Relay provides electrical isolation between low-voltage Pi and high-voltage load
- **Device-to-device connection**: Relay output connects directly to load
- **Simple two-tier chain**: Board → Relay → Load
- **Real-world application**: Home automation, lighting control, pump control, heating systems
- **Compact syntax**: Clean `from`/`to` connection format

---

### Pico Power Distribution Chain

Clean power distribution example on Raspberry Pi Pico showing a voltage regulator powering an LED. Demonstrates proper multi-tier power chaining without shared pins.

**Configuration:** [`examples/pico_power_chain.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/pico_power_chain.yaml)

```yaml
# Raspberry Pi Pico → Voltage Regulator → LED
# Simple multi-tier example showing power distribution chain
title: "Pico Power Distribution Chain"
board: "raspberry_pi_pico"
devices:
  - name: "3.3V Regulator"
    pins:
      - name: "VIN"
        role: "5V"
      - name: "GND_IN"
        role: "GND"
      - name: "VOUT"
        role: "3V3"
      - name: "GND_OUT"
        role: "GND"
  - type: "led"
    name: "Status LED"
    color: "Green"
connections:
  # Pico to regulator
  - from: {board_pin: 40}  # VBUS (5V, top header pin 40)
    to: {device: "3.3V Regulator", device_pin: "VIN"}
  - from: {board_pin: 38}  # GND (bottom header)
    to: {device: "3.3V Regulator", device_pin: "GND_IN"}

  # Regulator to LED (device-to-device)
  - from: {device: "3.3V Regulator", device_pin: "VOUT"}
    to: {device: "Status LED", device_pin: "+"}
    components:
      - type: "resistor"
        value: "220Ω"
  - from: {device: "3.3V Regulator", device_pin: "GND_OUT"}
    to: {device: "Status LED", device_pin: "-"}

show_legend: true
```

**Generate:**

```bash
pinviz render examples/pico_power_chain.yaml -o pico_power_chain.svg
```

**Result:**

![Pico Power Distribution Chain](https://raw.githubusercontent.com/nordstad/PinViz/main/images/pico_power_chain.svg)

**Key Features:**

- **Clean three-tier chain**: Pico → Regulator → LED
- **Proper power chaining**: Each device gets power from previous device, not directly from board
- **No shared pins**: Only one connection per board pin (validation enforced)
- **Dual-header board**: Works with Pico's horizontal pin layout (top and bottom headers)
- **Real-world application**: Power distribution, voltage conversion, LED indicators, battery-powered projects
- **Best practice**: Demonstrates proper multi-tier power flow without pin sharing

---

### Multi-Tier Connection Syntax

Multi-tier connections use the `from` and `to` keys with nested dictionaries:

**Board to device** (traditional syntax, still supported):

```yaml
connections:
  - board_pin: 1
    device: "Device Name"
    device_pin: "PIN"
```

**Board to device** (new `from`/`to` syntax):

```yaml
connections:
  - from: {board_pin: 1}
    to: {device: "Device Name", device_pin: "PIN"}
```

**Device to device** (requires `from`/`to` syntax):

```yaml
connections:
  - from: {device: "Device1", device_pin: "OUT"}
    to: {device: "Device2", device_pin: "IN"}
```

**Key points:**

- Both connection syntaxes work for board-to-device connections
- Device-to-device connections **require** the `from`/`to` syntax
- You can mix both syntaxes in the same configuration
- Works with all board types (Pi 5, Pi 4, Pico, etc.)

**Additional multi-tier examples** in the repository:

- `power_distribution.yaml` - Complex power chain with battery, charger, controller, and sensors
- `multi_level_simple.yaml` - Simple voltage regulator chain
- `multi_level_branching.yaml` - Multiple devices sharing intermediate power sources

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
