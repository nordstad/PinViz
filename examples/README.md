# PinViz Examples

This directory contains example configuration files demonstrating various features of PinViz.

## Multi-Level Connection Examples

These examples demonstrate the new multi-level connection feature that allows device-to-device connections in addition to board-to-device connections.

### multi_level_simple.yaml

**Simple Power Chain: Board → Regulator → LED**

A basic linear chain demonstrating:
- Board power to voltage regulator
- Regulator output to LED
- Proper ground connections through the chain

This example shows the simplest form of multi-level connections with a single path from board through an intermediate device to a final device.

**Key Features:**
- Custom voltage regulator device definition
- Device-to-device connections using `from`/`to` syntax
- Linear power distribution chain

### multi_level_branching.yaml

**Power Distribution Tree: Board → Power Supply → [LED1, LED2, LED3]**

Demonstrates branching connections where:
- Single board power pin feeds a power supply
- Power supply output branches to multiple LEDs
- Multiple devices share the same power source

This example shows how one device can supply power to multiple downstream devices, creating a tree structure.

**Key Features:**
- One-to-many device connections
- Multiple devices receiving power from single source
- Proper ground distribution

### power_distribution.yaml

**Realistic ESP32 Project: LiPo → TP4056 Charger → ESP32 → Sensors**

A realistic project setup demonstrating:
- Battery-powered system with charging circuit
- Microcontroller powered by battery charger
- Multiple sensors powered by microcontroller
- Mixed power and signal connections (I2C, GPIO)

This example shows a complete power distribution system with:
- USB power input from Raspberry Pi
- LiPo battery management
- Voltage regulation for microcontroller
- 3.3V power distribution to sensors
- I2C communication bus

**Key Features:**
- Complex multi-level power distribution
- Battery management integration
- Mixed power and signal connections
- Real-world project architecture

### invalid_cycle.yaml

**Cycle Detection Test: Device A ↔ Device B**

An intentionally invalid configuration for testing cycle detection:
- Device A output connects to Device B input
- Device B output connects back to Device A input
- Creates a circular dependency

This example should be **rejected** by the validation system with a cycle detection error.

**Purpose:** Used for testing the graph validation algorithm to ensure cycles are properly detected and reported.

## Basic Examples

### Single Device Examples

- **bh1750.yaml** - BH1750 light sensor with I2C connection
- **dht22.yaml** - DHT22 temperature/humidity sensor
- **simple_led_default.yaml** - Basic LED with default settings
- **simple_led_minimal.yaml** - Minimal LED configuration
- **button_input_default.yaml** - Push button with pull-up resistor
- **pir.yaml** - PIR motion sensor

### Multi-Device Examples

- **bh1750_ir_led.yaml** - Light sensor and IR LED combination
- **multi_device.yaml** - Multiple devices on one board
- **traffic_light.yaml** - Three-LED traffic light system
- **smart_sensor_station.yaml** - Complete sensor station with multiple sensors

### Advanced Examples

- **led_with_resistor.yaml** - LED with inline resistor component
- **leds_with_specs.yaml** - Multiple LEDs with detailed specifications
- **i2c_sensor_default.yaml** - Generic I2C sensor
- **distance_sensor.yaml** - Ultrasonic distance sensor
- **ds18b20_temp.yaml** - DS18B20 1-Wire temperature sensor
- **mcp3008.yaml** - MCP3008 ADC with SPI interface

### Board-Specific Examples

#### Raspberry Pi 4

- **pi4_bh1750.yaml** - Light sensor on Pi 4
- **pi4_button_led.yaml** - Button and LED on Pi 4
- **pi4_traffic_light.yaml** - Traffic light on Pi 4
- **pi4_i2c_spi_combo.yaml** - Combined I2C and SPI devices

#### Raspberry Pi Pico

- **pico_minimal.yaml** - Minimal Pico example
- **pico_led.yaml** - Simple LED on Pico
- **pico_bme280.yaml** - BME280 sensor on Pico
- **pico_leds_with_specs.yaml** - Multiple LEDs with specifications on Pico

## Python API Examples

Some examples also include Python API equivalents:

- **bh1750_python.py** - Programmatic BH1750 example
- **bh1750_ir_led_python.py** - BH1750 and IR LED via Python API
- **led_with_resistor_python.py** - LED with resistor via Python API
- **multi_device_python.py** - Multiple devices via Python API
- **ds18b20_temp_python.py** - DS18B20 sensor via Python API

## Using Examples

### Render an Example

```bash
# Using the render command
pinviz render examples/bh1750.yaml -o output.svg

# Or the shorthand
pinviz examples/bh1750.yaml -o output.svg
```

### Validate an Example

```bash
# Validate configuration
pinviz validate examples/multi_level_simple.yaml

# Strict validation (includes graph cycle detection)
pinviz validate examples/multi_level_simple.yaml --strict

# Test cycle detection (should fail)
pinviz validate examples/invalid_cycle.yaml --strict
```

### Use Built-in Examples

```bash
# List available built-in examples
pinviz list

# Generate a built-in example
pinviz example bh1750 -o output.svg
```

## Creating Your Own Examples

See [VALIDATION.md](VALIDATION.md) for detailed information on:
- Configuration file structure
- Valid board names and device types
- Pin roles and wire styles
- Common validation errors
- Best practices

## Documentation

For more information:
- **Project Documentation**: See main [README.md](../README.md)
- **Configuration Validation**: See [VALIDATION.md](VALIDATION.md)
- **CLI Reference**: Run `pinviz --help`
- **Adding Boards**: See [guides/adding-boards.md](../guides/adding-boards.md)
- **Adding Devices**: See [guides/adding-devices.md](../guides/adding-devices.md)
