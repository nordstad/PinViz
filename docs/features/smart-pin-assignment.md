# Smart Pin Assignment

## Overview

The Smart Pin Assignment feature automatically distributes connections across multiple available pins of the same role (e.g., GND, 3V3), avoiding the poor practice of connecting multiple wires to a single pin.

## The Problem

When creating GPIO diagrams, it's common to have multiple devices that need the same type of pin (ground, power, etc.). Traditionally, you might connect all ground wires to a single GND pin:

```yaml
connections:
  - board_pin: 14  # GND
    device: "Sensor 1"
    device_pin: "GND"
  - board_pin: 14  # Same GND pin - BAD PRACTICE!
    device: "LED"
    device_pin: "Cathode"
```

**Problems with this approach:**
- Harder to solder multiple wires to one pin
- Difficult to connect breadboard jumpers
- Less reliable connections
- The system warns you about this issue

## The Solution: Role-Based Pin Assignment

Instead of specifying explicit pin numbers, you can specify the **pin role**, and the system will automatically distribute connections across all available pins of that role:

```yaml
connections:
  # First GND connection uses pin 14
  - board_pin_role: "GND"
    device: "Sensor 1"
    device_pin: "GND"

  # Second GND connection automatically uses pin 19 (next GND pin)
  - board_pin_role: "GND"
    device: "LED"
    device_pin: "Cathode"
```

## Supported Pin Roles

You can use role-based assignment for any pin role:

- `GND` - Ground pins
- `3V3` - 3.3V power pins
- `5V` - 5V power pins
- `GPIO` - Generic GPIO pins
- `I2C_SDA` - I2C data line
- `I2C_SCL` - I2C clock line
- `SPI_MOSI`, `SPI_MISO`, `SPI_SCLK`, `SPI_CE0`, `SPI_CE1` - SPI pins
- `UART_TX`, `UART_RX` - UART pins
- `PWM` - PWM-capable pins

## How It Works

The system uses a **round-robin distribution** algorithm:

1. When you first use `board_pin_role: "GND"`, it assigns the first available GND pin
2. The next `board_pin_role: "GND"` connection gets the second GND pin
3. If there are more connections than pins, it cycles back to the first pin

### Example: ESP8266 NodeMCU

The ESP8266 NodeMCU has **4 GND pins** (14, 19, 27, 28):

```yaml
title: "Multiple Device Wiring"
board: "esp8266_nodemcu"
devices:
  - type: "bh1750"
    name: "Light Sensor"
  - type: "led"
    name: "Status LED"
  - type: "button"
    name: "Reset Button"

connections:
  # Light sensor GND → pin 14 (first GND)
  - board_pin_role: "GND"
    device: "Light Sensor"
    device_pin: "GND"

  # LED GND → pin 19 (second GND)
  - board_pin_role: "GND"
    device: "Status LED"
    device_pin: "-"

  # Button GND → pin 27 (third GND)
  - board_pin_role: "GND"
    device: "Reset Button"
    device_pin: "GND"
```

## Usage Formats

### Legacy Format

```yaml
connections:
  - board_pin_role: "GND"
    device: "Device Name"
    device_pin: "Pin Name"
```

### New Format

```yaml
connections:
  - from:
      board_pin_role: "GND"
    to:
      device: "Device Name"
      device_pin: "Pin Name"
```

## Mixing Explicit and Role-Based Pins

You can freely mix explicit pin numbers with role-based assignment:

```yaml
connections:
  # Explicit pin for I2C (must be specific pins)
  - board_pin: 4
    device: "Sensor"
    device_pin: "SCL"

  # Role-based for power (can be any 3V3 pin)
  - board_pin_role: "3V3"
    device: "Sensor"
    device_pin: "VCC"

  # Role-based for ground (can be any GND pin)
  - board_pin_role: "GND"
    device: "Sensor"
    device_pin: "GND"
```

## Validation Warnings

The system still detects when multiple connections explicitly use the same pin and warns you:

```
⚠️  Configuration Warnings:
  • Multiple connections to board pin 14: Light Sensor:GND, LED:-
    📍 Location: Board pin 14
    💡 Suggestion: Use 'board_pin_role' instead of 'board_pin'
                  to automatically distribute connections
    Example: board_pin_role: 'GND' instead of board_pin: 14
```

## Benefits

✅ **Better physical connections** - Each wire gets its own pin
✅ **Easier soldering** - No multiple wires on one pad
✅ **Cleaner wiring** - Wires can be spread across the board
✅ **Automatic distribution** - No need to manually track which pins are used
✅ **Board flexibility** - Works with any board's available pins

## Board Support

This feature works with all supported boards:

- **Raspberry Pi** (5, 4, Pico) - Multiple GND and power pins
- **ESP32 DevKit V1** - Multiple GND and power pins
- **ESP8266 NodeMCU** - 4 GND pins, 3 3V3 pins
- **Wemos D1 Mini** - Multiple GND pins

The exact distribution depends on which pins are available on each board.

## Complete Example

### Before (Poor Practice)
```yaml
title: "ESP8266 - Multiple Devices"
board: "esp8266_nodemcu"
devices:
  - type: "bh1750"
    name: "Light Sensor"
  - type: "led"
    name: "Status LED"
connections:
  - board_pin: 12
    device: "Light Sensor"
    device_pin: "VCC"
  - board_pin: 14  # GND pin
    device: "Light Sensor"
    device_pin: "GND"
  - board_pin: 10
    device: "Status LED"
    device_pin: "+"
  - board_pin: 14  # Same GND pin - WARNING!
    device: "Status LED"
    device_pin: "-"
```

### After (Best Practice)
```yaml
title: "ESP8266 - Multiple Devices (Smart Pins)"
board: "esp8266_nodemcu"
devices:
  - type: "bh1750"
    name: "Light Sensor"
  - type: "led"
    name: "Status LED"
connections:
  - board_pin_role: "3V3"  # Auto-assigns to pin 12
    device: "Light Sensor"
    device_pin: "VCC"
  - board_pin_role: "GND"  # Auto-assigns to pin 14
    device: "Light Sensor"
    device_pin: "GND"
  - board_pin: 10
    device: "Status LED"
    device_pin: "+"
  - board_pin_role: "GND"  # Auto-assigns to pin 19 (different!)
    device: "Status LED"
    device_pin: "-"
```

## Tips

1. **Use role-based for power/ground** - These are interchangeable, so let the system distribute them
2. **Use explicit pins for protocols** - I2C, SPI, UART need specific pins
3. **Mix both approaches** - Use what makes sense for each connection
4. **Check board documentation** - Know which pins support which roles

## Technical Details

The pin assignment is implemented in the `PinAssigner` class in `config_loader.py`. It:

1. Scans the board definition to find all pins of each role
2. Maintains a counter for each role
3. Distributes connections using round-robin (modulo) assignment
4. Logs pin assignments for debugging
