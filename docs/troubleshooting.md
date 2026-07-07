# Troubleshooting

Common errors and how to fix them.

## Quick Reference

| Error message | Likely cause | Jump to |
|---|---|---|
| `Configuration file not found` | Wrong path or filename | [File not found](#file-not-found) |
| `Unknown board` | Unsupported board name | [Unknown board](#unknown-board-name) |
| `Invalid board pin number` | Pin number outside board range | [Invalid pin number](#invalid-pin-number) |
| `Device '...' not found in diagram` | Mismatched device name | [Device not found](#device-not-found) |
| `Multiple connections to board pin` | Two devices on the same physical pin | [Duplicate pin](#duplicate-gpio-pin) |
| `I2C pin ... shared by` | Expected — I2C devices share SDA/SCL | [I2C bus sharing](#i2c-bus-sharing) |
| `Voltage mismatch` | Connecting 5V output to 3.3V input | [Voltage mismatch](#voltage-mismatch) |
| `Cycle detected` | Device-to-device connection loop | [Cycle detected](#cycle-detected-in-multi-level-connections) |
| SVG opens blank or is empty | Viewer does not support inline SVG | [SVG not rendering](#svg-not-rendering) |
| `No pins with role` | `board_pin_role` used with unsupported role | [No pins with role](#no-pins-with-role) |

---

## File Not Found

**Error:**

```
Error: Configuration file not found: my-diagram.yaml
```

**Causes and fixes:**

- The path is relative to where you run the command, not where the YAML file lives.
  Run from the directory containing the file, or use an absolute path:
  ```bash
  pinviz render /absolute/path/to/my-diagram.yaml
  ```
- Typo in the filename. Check `ls` / `dir` to confirm the exact name.
- Wrong extension — PinViz accepts `.yaml`, `.yml`, and `.json` only.

---

## Unknown Board Name

**Error:**

```
ValueError: Unknown board: 'raspberry_pi_3'
```

**Fix:** Use a supported board alias. Run `pinviz list` to see all available boards.

Supported aliases:

| Board | Aliases |
|---|---|
| Raspberry Pi 5 | `raspberry_pi_5`, `rpi5`, `rpi` |
| Raspberry Pi 4 | `raspberry_pi_4`, `rpi4`, `pi4` |
| Raspberry Pi Pico | `raspberry_pi_pico`, `pico` |
| ESP32 DevKit V1 | `esp32_devkit_v1`, `esp32`, `esp32_devkit` |
| ESP8266 NodeMCU | `esp8266_nodemcu`, `esp8266`, `nodemcu` |
| Wemos D1 Mini | `wemos_d1_mini`, `d1mini`, `wemos` |

---

## Invalid Pin Number

**Error:**

```
Invalid board pin number: 41
```

**Causes and fixes:**

- Pin numbers in `board_pin` are **physical pin numbers**, not BCM GPIO numbers.
  Raspberry Pi boards use physical pins 1–40. ESP32/ESP8266 boards use pins 1–30.
- You may be mixing up physical pin number with GPIO number. For example, GPIO 18
  is physical pin 12 on the Raspberry Pi.

Check the board's pin layout with `pinviz list` or refer to
[pinout.xyz](https://pinout.xyz) for Raspberry Pi boards.

---

## Device Not Found

**Error:**

```
Device 'BH1750 Sensor' not found in diagram
```

**Cause:** The `device` name in a connection does not exactly match the `name`
field of a device in the `devices` list. Names are case-sensitive.

**Fix:** Make sure the names match exactly:

```yaml
devices:
  - type: "bh1750"
    name: "BH1750"   # ← this name

connections:
  - board_pin: 1
    device: "BH1750"  # ← must match exactly
    device_pin: "VCC"
```

---

## Duplicate GPIO Pin

**Warning:**

```
⚠️  Warning: Multiple connections to board pin 14: Sensor:GND, LED:-
    💡 Suggestion: Use 'board_pin_role' instead of 'board_pin'
```

**What it means:** Two connections reference the same physical pin. This is
physically awkward (two wires on one pin) but not a wiring error for power/ground.

**Fix:** Use `board_pin_role` to let PinViz distribute power and ground connections
automatically across the board's available pins:

```yaml
# Instead of this:
- board_pin: 14
  device: "Sensor"
  device_pin: "GND"
- board_pin: 14       # ← warning: same pin
  device: "LED"
  device_pin: "-"

# Use this:
- board_pin_role: "GND"
  device: "Sensor"
  device_pin: "GND"
- board_pin_role: "GND"   # ← auto-assigns next available GND pin
  device: "LED"
  device_pin: "-"
```

See the [Smart Pin Assignment guide](features/smart-pin-assignment.md) for details.

---

## I2C Bus Sharing

**Warning:**

```
⚠️  Warning: I2C pin GPIO2 shared by: BH1750:SDA, OLED:SDA
```

**This is expected and not a problem.** I2C is a bus protocol — multiple devices
share the same SDA and SCL lines by design. PinViz warns about shared pins
by default, but this warning is safe to ignore for I2C devices.

If you want to suppress the warning, run validation in non-strict mode (the
default) and ignore the I2C sharing warnings:

```bash
pinviz validate my-diagram.yaml   # warnings shown but exit code 0
```

For true pin conflicts (two non-I2C devices on the same GPIO), the validator
reports an ERROR rather than a WARNING.

---

## Voltage Mismatch

**Error or Warning:**

```
⚠️  Error: Voltage mismatch — 5V output connected to 3.3V input
```

**What it means:** A 5V board pin is connected to a device pin rated for 3.3V,
which can damage the device.

**Fix options:**

1. Use the correct power pin. For 3.3V devices, connect to a 3V3 pin (e.g.,
   physical pin 1 or 17 on Raspberry Pi) instead of a 5V pin (pins 2 or 4).
2. Add a voltage regulator or level shifter between the board and device.
3. If you are certain the connection is safe, use `pinviz validate` without
   `--strict` — errors will be shown but the diagram will still render.

---

## Cycle Detected in Multi-Level Connections

**Error:**

```
Cycle detected: DeviceA → DeviceB → DeviceC → DeviceA
```

**What it means:** A chain of device-to-device connections loops back on itself.
PinViz cannot determine a layout for circular dependencies.

**Fix:** Remove one connection to break the cycle. The connection graph must be
a directed acyclic graph (DAG).

See the [Multi-Level Connections guide](multi-level-connections.md) for how
device-to-device wiring works.

---

## SVG Not Rendering

**Symptom:** The SVG file opens as a blank page, shows only an outline, or
displays no content.

**Cause:** Some SVG viewers do not support all SVG features PinViz uses
(embedded images, advanced path rendering).

**Recommended viewers:**

- **Web browser** — Chrome, Firefox, Safari, Edge all render PinViz SVGs correctly.
  Drag and drop the `.svg` file onto a browser tab.
- **VS Code** — Install the [SVG Preview](https://marketplace.visualstudio.com/items?itemName=SimonSiefke.svg-preview) extension.
- **Inkscape** — Full SVG support.

**Avoid:** macOS Preview (limited SVG support), some older image viewers.

---

## No Pins with Role

**Error:**

```
Board 'raspberry_pi_pico' has no pins with role 'SPI_CE1'.
```

**What it means:** You used `board_pin_role` with a pin role that does not exist
on the selected board, or the board has no remaining unassigned pins of that role.

**Fix:**

1. Check which pin roles the board supports with `pinviz list`.
2. Use an explicit `board_pin` with the specific pin number instead of a role.
3. If all pins of a role are already assigned, add more devices and use different
   roles, or switch to explicit pin numbers.

---

## Getting More Help

- Run `pinviz validate my-diagram.yaml` — the validator provides specific error
  messages with suggested fixes.
- Run `pinviz validate my-diagram.yaml --show-graph` to visualise the connection
  graph and spot structural issues.
- Check the [CLI reference](guide/cli.md) for all available options.
- Open an issue at [github.com/nordstad/PinViz](https://github.com/nordstad/PinViz/issues).
