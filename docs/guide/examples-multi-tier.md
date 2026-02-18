# Multi-Tier Connection Examples

Examples showing device-to-device connections (board → driver → motor, board → relay → load, etc.)

→ [All examples index](examples.md) | [Raspberry Pi](examples-raspberry-pi.md) | [Components](examples-components.md) | [Pico](examples-pico.md) | [ESP32/ESP8266](examples-esp.md)

Multi-tier diagrams require the `from`/`to` connection syntax for device-to-device
links. See the [Multi-Level Connections guide](../multi-level-connections.md) for
the full feature reference.

## Connection Syntax

**Board to device** (both syntaxes work):

```yaml
connections:
  - board_pin: 1                    # traditional syntax
    device: "Device Name"
    device_pin: "PIN"

  - from: {board_pin: 1}            # from/to syntax
    to: {device: "Device Name", device_pin: "PIN"}
```

**Device to device** (requires `from`/`to`):

```yaml
connections:
  - from: {device: "Device1", device_pin: "OUT"}
    to: {device: "Device2", device_pin: "IN"}
```

You can mix both syntaxes freely in the same file.

---

## Motor Control with L293D

Three-tier chain: Raspberry Pi → L293D Motor Driver → DC Motor.

**Configuration:** [`examples/motor_control.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/motor_control.yaml)

```yaml
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

**Use cases:** Robot motor control, CNC machines, automated systems.

---

## Relay Control for High Voltage Devices

Two-tier chain: Raspberry Pi → Relay Module → Load. The relay provides
electrical isolation between the low-voltage Pi and a high-voltage load.

**Configuration:** [`examples/relay_control.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/relay_control.yaml)

```yaml
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
  - from: {board_pin: 2}
    to: {device: "5V Relay Module", device_pin: "VCC"}
  - from: {board_pin: 6}
    to: {device: "5V Relay Module", device_pin: "GND"}
  - from: {board_pin: 11}
    to: {device: "5V Relay Module", device_pin: "IN"}
  # Relay output to load (device-to-device)
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

**Use cases:** Home automation, lighting control, pump control, heating systems.

---

## Pico Power Distribution Chain

Three-tier chain: Raspberry Pi Pico → Voltage Regulator → LED. Demonstrates
proper multi-tier power chaining where each device draws from the previous.

**Configuration:** [`examples/pico_power_chain.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/pico_power_chain.yaml)

```yaml
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
  - from: {board_pin: 40}  # VBUS (5V)
    to: {device: "3.3V Regulator", device_pin: "VIN"}
  - from: {board_pin: 38}  # GND
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

**Key Features:** Only one connection per board pin (each device gets power from
the previous one). Works with Pico's dual-header layout.

---

## More Examples

Additional multi-tier examples in the repository:

- [`power_distribution.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/power_distribution.yaml) — complex chain with battery, charger, controller, and sensors
- [`multi_level_simple.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/multi_level_simple.yaml) — minimal voltage regulator chain
- [`multi_level_branching.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/multi_level_branching.yaml) — multiple devices sharing an intermediate power source
