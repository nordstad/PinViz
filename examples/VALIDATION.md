# Configuration Validation Examples

This document provides examples of configuration validation and common error messages.

## Valid Configuration Examples

### Minimal Configuration

```yaml
title: "Simple LED"
devices:
  - type: led
    name: "Status LED"
connections:
  - board_pin: 11
    device: "Status LED"
    device_pin: "Anode"
  - board_pin: 6
    device: "Status LED"
    device_pin: "Cathode"
```

### Complete Configuration with All Options

```yaml
title: "BH1750 Light Sensor"
board: "raspberry_pi_5"
show_legend: true
show_gpio_diagram: false
devices:
  - type: bh1750
    name: "Light Sensor"
connections:
  - board_pin: 1
    device: "Light Sensor"
    device_pin: "VCC"
    color: "#FF0000"
    style: "mixed"
  - board_pin: 3
    device: "Light Sensor"
    device_pin: "SDA"
    net: "I2C_SDA"
  - board_pin: 5
    device: "Light Sensor"
    device_pin: "SCL"
    net: "I2C_SCL"
  - board_pin: 6
    device: "Light Sensor"
    device_pin: "GND"
```

### Custom Device Definition

```yaml
title: "Custom Sensor Module"
devices:
  - name: "My Custom Sensor"
    width: 100.0
    height: 50.0
    color: "#FF5733"
    pins:
      - name: "VCC"
        role: "3V3"
      - name: "GND"
        role: "GND"
      - name: "DATA"
        role: "GPIO"
        position:
          x: 10.0
          y: 25.0
connections:
  - board_pin: 1
    device: "My Custom Sensor"
    device_pin: "VCC"
```

### Connection with Inline Component

```yaml
title: "LED with Resistor"
devices:
  - type: led
    color: "Red"
connections:
  - board_pin: 11
    device: "LED"
    device_pin: "Anode"
    components:
      - type: resistor
        value: "220Ω"
        position: 0.5
```

## Common Validation Errors

### Error: Invalid Board Name

**Configuration:**
```yaml
board: "arduino_uno"  # Invalid
devices:
  - type: led
connections:
  - board_pin: 1
    device: "LED"
    device_pin: "Anode"
```

**Error Message:**
```
Configuration validation failed:
  • board: Invalid board name 'arduino_uno'. Must be one of: raspberry_pi, raspberry_pi_5, rpi, rpi5
```

**Fix:**
Use a valid board name:
```yaml
board: "raspberry_pi_5"  # or "rpi5", "rpi"
```

### Error: Invalid Pin Number

**Configuration:**
```yaml
devices:
  - type: led
connections:
  - board_pin: 42  # Invalid (must be 1-40)
    device: "LED"
    device_pin: "Anode"
```

**Error Message:**
```
Configuration validation failed:
  • connections -> 0 -> board_pin: Input should be less than or equal to 40
```

**Fix:**
Use a valid pin number (1-40):
```yaml
connections:
  - board_pin: 11  # Valid GPIO pin
```

### Error: Missing Required Fields

**Configuration:**
```yaml
devices:
  - type: led
connections:
  - board_pin: 11
    device: "LED"
    # Missing device_pin
```

**Error Message:**
```
Configuration validation failed:
  • connections -> 0 -> device_pin: Field required
```

**Fix:**
Add the required field:
```yaml
connections:
  - board_pin: 11
    device: "LED"
    device_pin: "Anode"  # Added
```

### Error: Invalid Device Type

**Configuration:**
```yaml
devices:
  - type: unknown_sensor  # Invalid
connections:
  - board_pin: 1
    device: "Unknown Sensor"
    device_pin: "VCC"
```

**Error Message:**
```
Configuration validation failed:
  • devices -> 0 -> type: Invalid device type 'unknown_sensor'. Must be one of: bh1750, button, i2c, i2c_device, ir_led_ring, led, spi, spi_device
```

**Fix:**
Use a valid device type or create a custom device:
```yaml
devices:
  - type: bh1750  # Valid predefined type
```

or

```yaml
devices:
  - name: "Unknown Sensor"  # Custom device
    pins:
      - name: "VCC"
        role: "3V3"
```

### Error: Invalid Pin Role

**Configuration:**
```yaml
devices:
  - name: "Custom Device"
    pins:
      - name: "DATA"
        role: "INVALID_ROLE"  # Invalid
connections:
  - board_pin: 1
    device: "Custom Device"
    device_pin: "DATA"
```

**Error Message:**
```
Configuration validation failed:
  • devices -> 0 -> pins -> 0 -> role: Invalid pin role 'INVALID_ROLE'. Must be one of: 3V3, 5V, GND, GPIO, I2C_SCL, I2C_SDA, PWM, SPI_CE0, SPI_CE1, SPI_MISO, SPI_MOSI, SPI_SCLK, UART_RX, UART_TX
```

**Fix:**
Use a valid pin role:
```yaml
pins:
  - name: "DATA"
    role: "GPIO"  # Valid role
```

### Error: Invalid Color Format

**Configuration:**
```yaml
devices:
  - name: "My Device"
    color: "red"  # Invalid (must be hex)
    pins:
      - name: "VCC"
        role: "3V3"
connections:
  - board_pin: 1
    device: "My Device"
    device_pin: "VCC"
```

**Error Message:**
```
Configuration validation failed:
  • devices -> 0 -> color: String should match pattern '^#[0-9A-Fa-f]{6}$'
```

**Fix:**
Use hex color format:
```yaml
devices:
  - name: "My Device"
    color: "#FF0000"  # Valid hex color
```

### Error: Duplicate Pin Names

**Configuration:**
```yaml
devices:
  - name: "Bad Device"
    pins:
      - name: "VCC"
        role: "3V3"
      - name: "VCC"  # Duplicate!
        role: "5V"
connections:
  - board_pin: 1
    device: "Bad Device"
    device_pin: "VCC"
```

**Error Message:**
```
Configuration validation failed:
  • devices -> 0: Duplicate pin names found in device 'Bad Device': VCC
```

**Fix:**
Use unique pin names:
```yaml
devices:
  - name: "Good Device"
    pins:
      - name: "VCC_3V3"
        role: "3V3"
      - name: "VCC_5V"
        role: "5V"
```

### Note: Empty Lists Are Allowed

Empty device and connection lists are valid (though not very useful):
```yaml
title: "Empty Diagram"
devices: []
connections: []
```

This can be useful for testing or building configurations programmatically.

### Error: Invalid Wire Style

**Configuration:**
```yaml
devices:
  - type: led
connections:
  - board_pin: 11
    device: "LED"
    device_pin: "Anode"
    style: "zigzag"  # Invalid
```

**Error Message:**
```
Configuration validation failed:
  • connections -> 0 -> style: Invalid wire style 'zigzag'. Must be one of: curved, mixed, orthogonal
```

**Fix:**
Use a valid wire style:
```yaml
connections:
  - board_pin: 11
    device: "LED"
    device_pin: "Anode"
    style: "mixed"  # or "orthogonal", "curved"
```

### Error: Invalid Component Type

**Configuration:**
```yaml
devices:
  - type: led
connections:
  - board_pin: 11
    device: "LED"
    device_pin: "Anode"
    components:
      - type: "inductor"  # Invalid
        value: "1mH"
```

**Error Message:**
```
Configuration validation failed:
  • connections -> 0 -> components -> 0 -> type: Invalid component type 'inductor'. Must be one of: capacitor, diode, led, resistor
```

**Fix:**
Use a valid component type:
```yaml
components:
  - type: "resistor"  # Valid
    value: "220Ω"
```

## Validation Best Practices

1. **Start Simple**: Begin with a minimal configuration and add complexity gradually.

2. **Use Valid Board Names**: Stick to the supported board names listed in the error messages.

3. **Check Pin Numbers**: Raspberry Pi GPIO has pins 1-40. Physical pin numbers, not BCM numbers.

4. **Use Hex Colors**: Always use hex format (#RRGGBB) for colors, not color names.

5. **Unique Device Names**: If using multiple devices of the same type, give them unique names.

6. **Unique Pin Names**: Within a custom device, all pin names must be unique.

7. **Match Connection Device Names**: Ensure connection `device` fields match actual device names.

8. **Valid Pin Roles**: Use only the predefined pin roles from the documentation.

9. **Component Positions**: Component positions must be between 0.0 (start of wire) and 1.0 (end of wire).

10. **Wire Styles**: Use "mixed" for automatic style selection, "orthogonal" for right angles, or "curved" for bezier curves.

## Schema Reference

For the complete schema specification, see the [schemas.py](../src/pinviz/schemas.py) module.

Valid values for enumerations:

- **Board names**: `raspberry_pi_5`, `raspberry_pi`, `rpi5`, `rpi`
- **Device types**: `bh1750`, `ir_led_ring`, `i2c_device`, `i2c`, `spi_device`, `spi`, `led`, `button`
- **Pin roles**: `GPIO`, `I2C_SDA`, `I2C_SCL`, `SPI_MOSI`, `SPI_MISO`, `SPI_SCLK`, `SPI_CE0`, `SPI_CE1`, `UART_TX`, `UART_RX`, `PWM`, `3V3`, `5V`, `GND`
- **Wire styles**: `orthogonal`, `curved`, `mixed`
- **Component types**: `resistor`, `capacitor`, `led`, `diode`
