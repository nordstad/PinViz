# Example Diagram Guidelines

This document provides guidelines for creating high-quality example diagrams for the PinViz project.

## Core Principles

### 1. No "Wire Stubs" - Only Connect Functional Pins

**Rule:** Only connect pins that serve a functional purpose in the example circuit. Device pins can be visible without wires attached.

**Why:** Showing wires to pins that serve no purpose creates misleading "wire stubs" that imply functionality when there is none.

**The "Wire Stub" Problem:**
A wire stub occurs when a pin is connected but serves no functional purpose in the circuit:
- ❌ Data output pin (DOUT, MISO, OUT) connected but nothing is reading the data
- ❌ Data input pin (DIN, MOSI) connected but no commands/data are being sent
- ❌ Signal pins on "wiring reference" examples that don't represent working circuits

**Examples:**
- ✅ Good: MCP3008 ADC with DOUT connected AND analog sensor feeding data (functional)
- ❌ Bad: MCP3008 ADC with DOUT connected but NO sensor (pointless wire stub)
- ✅ Good: SPI device showing power, SCLK, CS (bus control) - MOSI/MISO pins visible but not wired
- ❌ Bad: SPI device with MOSI/MISO wired in a "wiring reference" example (implies data transfer)

**Categories:**

**Wiring Reference Examples** (show HOW to connect):
- Connect: Power (VCC, GND)
- Connect: Bus control (SCLK, CS for SPI; SCL, SDA for I2C)
- DO NOT Connect: Pure data pins (MOSI, MISO, DOUT, DIN, OUT)
- Example: `pir.yaml` - shows power wiring only, OUT visible but not connected

**Functional Examples** (show WORKING circuits):
- Connect: All pins needed for the circuit to function
- Example: `smart_sensor_station.yaml` - sensors reading data, all data pins connected

**How to Decide:**
Ask: "If someone builds this exact circuit, will it DO something meaningful?"
- If YES → Connect all functional pins (it's a working example)
- If NO → Only connect power and bus control (it's a wiring reference)

**Solution:** Device pins are ALWAYS visible (part of device design), but wires are only drawn for functional connections

### 2. Represent Real-World Use Cases

**Rule:** Examples should demonstrate actual, practical circuits that users might build.

**Why:** Users learn better from realistic examples they can replicate.

**Examples:**
- ✅ Good: "BME280 Temperature/Humidity/Pressure Sensor" - common use case
- ✅ Good: "HC-SR04 Ultrasonic Distance Sensor" - specific project
- ❌ Bad: "Generic SPI Device" - too abstract without context

**Guidelines:**
- Use real sensor/module names (BH1750, DHT22, etc.)
- Show complete working circuits with power, ground, and data connections
- Include common accessories (LEDs for status, buttons for input)

### 3. Clear, Descriptive Titles

**Rule:** Each example should have a clear title that describes what it demonstrates.

**Format:** `[Component Name] - [Purpose/Application]` or `[Project Description]`

**Examples:**
- ✅ Good: "BH1750 Light Sensor - I2C Connection"
- ✅ Good: "Smart Sensor Station - Environmental Monitoring"
- ✅ Good: "DC Motor Control with L293D"
- ❌ Bad: "Test Circuit"
- ❌ Bad: "Multi Device Example"

### 4. Minimize Wire Crossings

**Rule:** Route wires to avoid unnecessary crossings and maintain visual clarity.

**Why:** Crossed wires are harder to follow and can be confusing to trace.

**Guidelines:**
- Group related connections (e.g., all I2C wires together)
- Use consistent wire colors based on function
- Consider device placement to minimize wire length and crossings

**Note:** The layout engine handles most routing automatically, but device order in the YAML affects positioning.

### 5. Follow Pin Role Conventions

**Rule:** Use appropriate pin roles for connections to enable proper validation.

**Pin Roles:**
- Power: `3V3`, `5V`
- Ground: `GND`
- I2C: `I2C_SDA`, `I2C_SCL`
- SPI: `SPI_MOSI`, `SPI_MISO`, `SPI_SCLK`, `SPI_CE0`, `SPI_CE1`
- UART: `UART_TX`, `UART_RX`
- PWM: `PWM`
- General: `GPIO`

**Guidelines:**
- Use specific roles (I2C_SDA) instead of generic (GPIO) when applicable
- Match roles on both ends of connections when possible
- Validation warnings help catch role mismatches

### 6. Include Essential Documentation

**Rule:** Each example YAML should include comments explaining the circuit.

**Required Information:**
- What the circuit does
- Key connections or special wiring notes
- Any non-obvious design choices

**Example:**
```yaml
# HC-SR04 Ultrasonic Distance Sensor
title: "HC-SR04 - Distance Measurement"
board: "raspberry_pi_5"
devices:
  - type: "hcsr04"
connections:
  # Power connections
  - board_pin: 2   # 5V (HC-SR04 requires 5V)
    device: "HC-SR04"
    device_pin: "VCC"
  # Trigger and Echo pins for distance measurement
  - board_pin: 11  # GPIO 17 - Trigger
    device: "HC-SR04"
    device_pin: "TRIG"
  - board_pin: 13  # GPIO 27 - Echo (with voltage divider in real circuit)
    device: "HC-SR04"
    device_pin: "ECHO"
```

### 7. Validation Must Pass

**Rule:** All examples must pass validation without critical errors.

**Process:**
```bash
# Before committing
uv run pinviz validate examples/your_example.yaml --strict
```

**Acceptable:**
- ✅ Warnings about incompatible pin roles (if justified)
- ✅ Warnings about unusual connections (if intentional)

**Not Acceptable:**
- ❌ Errors about missing devices or pins
- ❌ Errors about invalid board pin numbers
- ❌ Errors about circular dependencies

### 8. Keep Examples Focused

**Rule:** Each example should demonstrate one or two concepts, not everything at once.

**Why:** Focused examples are easier to understand and more useful as references.

**Examples:**
- ✅ Good: "BH1750 Light Sensor" - shows I2C connection
- ✅ Good: "I2C OLED + SPI Accelerometer" - shows using both buses
- ❌ Bad: "Everything Circuit" - 10 different sensors and modules

**Guidelines:**
- Single-device examples: Show basic wiring for one component
- Multi-device examples: Show specific integration patterns (I2C bus sharing, device-to-device communication)
- Complex examples: Must have clear purpose (e.g., "Smart Sensor Station")

### 9. No Duplicate Examples

**Rule:** Avoid creating examples that demonstrate the same concept.

**Process:**
- Check existing examples before creating new ones
- Update existing examples instead of creating duplicates
- If variations are needed, name them clearly (e.g., `led_basic.yaml` vs `led_with_resistor.yaml`)

### 10. Maintain Consistency

**Rule:** Follow the established naming and structure conventions.

**File Naming:**
- Use lowercase with underscores: `bh1750_light_sensor.yaml`
- Match YAML filename to generated SVG: `example.yaml` → `images/example.svg`
- Use descriptive names, not generic ones

**YAML Structure:**
```yaml
title: "Descriptive Title"
board: "raspberry_pi_5"  # or "rpi4", "pico"
devices:
  - type: "predefined_type"  # Use device templates when available
    name: "Optional Name Override"
  - name: "Custom Device"  # Only for devices not in templates
    pins:
      - name: "Pin Name"
        role: "Pin Role"
connections:
  - board_pin: 1
    device: "Device Name"
    device_pin: "Pin Name"
show_legend: true  # Usually true for examples
```

## Example Categories

### Basic Examples (Single Device)
- Purpose: Show how to wire a single sensor/module
- Examples: `bh1750.yaml`, `dht22.yaml`, `led.yaml`
- Should include: Power, ground, and data connections

### Multi-Device Examples (Shared Bus)
- Purpose: Show how multiple devices share I2C or SPI
- Examples: `smart_sensor_station.yaml`, `multi_device.yaml`
- Should include: Proper bus sharing, unique addresses/chip selects

### Multi-Level Examples (Device-to-Device)
- Purpose: Demonstrate device-to-device connections
- Examples: `analog_input.yaml`, `motor_control.yaml`, `power_distribution.yaml`
- Should include: Clear flow from board → intermediate device → end device

### Board-Specific Examples
- Purpose: Show board-specific features or configurations
- Examples: `pico_led.yaml`, `pi4_traffic_light.yaml`
- Should include: Board name in filename, board-specific pin considerations

## Review Checklist

Before submitting a new example or updating an existing one:

- [ ] YAML validates without critical errors (`pinviz validate --strict`)
- [ ] All device pins are connected or documented as unused
- [ ] Title clearly describes what the circuit does
- [ ] Circuit represents a real-world use case
- [ ] Comments explain non-obvious wiring choices
- [ ] SVG renders correctly (`pinviz render examples/your_example.yaml -o images/your_example.svg`)
- [ ] No duplicate examples exist
- [ ] Filename follows naming conventions
- [ ] Wire colors are appropriate (auto-assigned or manually specified)
- [ ] Example is focused on 1-2 concepts

## Common Pitfalls to Avoid

### 1. Incomplete Power Connections
❌ Bad: Connecting only VCC, forgetting GND
✅ Good: Always show both power and ground connections

### 2. Wrong Pin Numbers
❌ Bad: Using BCM GPIO numbers instead of physical pin numbers
✅ Good: Use physical pin numbers (1-40 for Pi, 1-40 for Pico)

### 3. Unrealistic Circuits
❌ Bad: "Test Device" with arbitrary pins
✅ Good: Real sensor with actual pinout

### 4. Missing Resistors in LED Circuits
⚠️ Note: Current-limiting resistors should be mentioned in comments
```yaml
# LED circuit (use 220Ω-330Ω resistor in series with LED in real circuit)
```

### 5. Reusing Pins Incorrectly
❌ Bad: Using same GPIO for multiple functions
✅ Good: Unique GPIO for each function (unless intentionally shared like I2C bus)

## Maintenance

### Regenerating All Examples
```bash
# Regenerate all SVGs from YAML configs
for yaml in examples/*.yaml; do
  base=$(basename "$yaml" .yaml)
  uv run pinviz render "$yaml" -o "images/$base.svg"
done
```

### Cleaning Up Orphaned SVGs
```bash
# Find SVGs without corresponding YAML
for svg in images/*.svg; do
  base=$(basename "$svg" .svg)
  if [ ! -f "examples/$base.yaml" ]; then
    echo "Orphaned: $svg"
  fi
done
```

### Validating All Examples
```bash
# Validate all examples
for yaml in examples/*.yaml; do
  echo "Validating $yaml"
  uv run pinviz validate "$yaml" --strict || echo "FAILED: $yaml"
done
```

## Resources

- [Adding Devices Guide](../guides/adding-devices.md)
- [Adding Boards Guide](../guides/adding-boards.md)
- [Pin Role Reference](../README.md#pin-roles)
- [YAML Configuration Syntax](../README.md#configuration-file-structure)

## Questions?

If you have questions about these guidelines or need clarification on example creation:
- Check existing examples for reference
- Review the PinViz documentation
- Open an issue on GitHub for discussion
