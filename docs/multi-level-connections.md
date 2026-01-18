# Multi-Level Device Connections Guide

## Overview

Multi-level support allows you to create diagrams where devices connect to other devices, not just to the board. This enables realistic representations of:

- Power distribution networks
- Signal processing chains
- Motor control setups
- Complex projects with intermediate components

## Configuration Syntax

### Board-to-Device (Original Format)

Still fully supported:

```yaml
connections:
  - board_pin: 1
    device: "LED"
    device_pin: "VCC"
```

### Device-to-Device (New Format)

```yaml
connections:
  - from:
      device: "Regulator"
      device_pin: "VOUT"
    to:
      device: "LED"
      device_pin: "VCC"
```

### Unified Format (Recommended)

For clarity, you can use the `from/to` syntax for all connections:

```yaml
connections:
  # Board source
  - from: {board_pin: 1}
    to: {device: "LED", device_pin: "VCC"}

  # Device source
  - from: {device: "Regulator", device_pin: "VOUT"}
    to: {device: "LED", device_pin: "VCC"}
```

## Layout Behavior

Devices are automatically positioned in horizontal tiers based on connection depth:

- **Level 0**: Devices directly connected to board
- **Level 1**: Devices connected to Level 0 devices
- **Level 2**: Devices connected to Level 1 devices
- And so on...

## Validation

PinViz automatically validates your connection graph:

```bash
pinviz validate examples/power_distribution.yaml --show-graph
```

Common validation checks:

- **Cycle detection**: Ensures no circular dependencies
- **Pin compatibility**: Warns about voltage mismatches
- **Orphaned devices**: Flags unconnected devices

## Examples

See the `examples/` directory for complete examples:

- `multi_level_simple.yaml` - Basic power chain
- `multi_level_branching.yaml` - Tree structure
- `power_distribution.yaml` - Realistic project
- `pico_power_chain.yaml` - Pico-based power distribution

## Troubleshooting

### "Cycle detected" Error

Your configuration has circular dependencies:

```text
Device A → Device B → Device C → Device A
```

**Solution:** Remove one connection to break the cycle.

### "Pin role incompatible" Warning

Example: Connecting 5V output to 3.3V input.

**Solution:** Add voltage regulator or level shifter.

### "Device positioned incorrectly"

Very deep chains (>10 levels) may have layout issues.

**Solution:** Simplify diagram or break into multiple diagrams.

## Advanced Features

### Mixed Connection Types

You can mix board-to-device and device-to-device connections in the same diagram:

```yaml
connections:
  # Power from board
  - from: {board_pin: 2}
    to: {device: "Regulator", device_pin: "VIN"}

  # Regulated power to multiple devices
  - from: {device: "Regulator", device_pin: "VOUT"}
    to: {device: "LED1", device_pin: "+"}

  - from: {device: "Regulator", device_pin: "VOUT"}
    to: {device: "LED2", device_pin: "+"}

  # Data from board
  - from: {board_pin: 3}
    to: {device: "Sensor", device_pin: "SDA"}
```

### Wire Styling

Device-to-device connections support all wire styling options:

```yaml
connections:
  - from: {device: "Regulator", device_pin: "VOUT"}
    to: {device: "LED", device_pin: "VCC"}
    color: "#FF0000"
    style: "curved"
```

### Inline Components

Add resistors, capacitors, or diodes on device-to-device connections:

```yaml
connections:
  - from: {device: "Regulator", device_pin: "VOUT"}
    to: {device: "LED", device_pin: "+"}
    components:
      - type: "resistor"
        value: "220Ω"
```
