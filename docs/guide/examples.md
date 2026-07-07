# Examples

Explore example diagrams and configurations organised by board and feature.

## Demo - ESP32 Weather Station

<p align="center">
  <img src="https://raw.githubusercontent.com/nordstad/PinViz/main/scripts/demos/output/esp32_demo.gif" alt="PinViz ESP32 Demo" width="800">
</p>

## Demo - Custom Device Creation

<p align="center">
  <img src="https://raw.githubusercontent.com/nordstad/PinViz/main/scripts/demos/output/custom_device_demo.gif" alt="PinViz Custom Device Demo" width="800">
</p>

---

## Browse by Board or Feature

| Section | Examples |
|---------|---------|
| [Raspberry Pi](examples-raspberry-pi.md) | Wire visibility, BH1750 I2C sensor, traffic light, multi-device, specs table, dark mode |
| [Inline Components](examples-components.md) | LED + resistor, decoupling capacitor, flyback diode, all component types |
| [Raspberry Pi Pico](examples-pico.md) | Pico LED, Pico BME280, multi-LED with specs, dark mode |
| [ESP32 / ESP8266](examples-esp.md) | ESP32 weather station, NodeMCU LEDs, Wemos D1 Mini OLED |
| [Multi-Tier Connections](examples-multi-tier.md) | Motor control (L293D), relay control, Pico power chain |

---

## Feature Showcase

| Feature | Where to find it |
|---------|-----------------|
| Wire visibility (light & dark halos) | [Raspberry Pi → Wire Visibility](examples-raspberry-pi.md#wire-visibility-light-dark-colors) |
| Dark mode | [Raspberry Pi → BH1750 Dark Mode](examples-raspberry-pi.md#bh1750-sensor-dark-mode) • [Pico → Dark Mode](examples-pico.md#pico-led-dark-mode) |
| I2C sensor | [Raspberry Pi → BH1750](examples-raspberry-pi.md#bh1750-light-sensor) |
| Inline resistor / capacitor / diode | [Components](examples-components.md) |
| Multiple devices | [Raspberry Pi → Traffic Light](examples-raspberry-pi.md#traffic-light) |
| Device-to-device (multi-tier) | [Multi-Tier](examples-multi-tier.md) |
| Smart GND / power pin distribution | [ESP8266 → NodeMCU LED Example](examples-esp.md#esp8266-nodemcu-led-example) |
| Specifications table (`--show-legend`) | [Raspberry Pi → Specs Table](examples-raspberry-pi.md#device-specifications-table) • [Pico → Multi-LED with Specs](examples-pico.md#pico-multi-led-circuit-with-specifications) |

---

## Quick Start with Built-in Examples

```bash
# List all available examples
pinviz list

# Generate built-in examples
pinviz example bh1750 -o bh1750.svg
pinviz example ir_led -o ir_led.svg
pinviz example i2c_spi -o i2c_spi.svg
pinviz example esp32_weather -o esp32_weather.svg
```

All YAML example files are in the [`examples/`](https://github.com/nordstad/PinViz/tree/main/examples) directory.
Generated SVGs are in [`images/`](https://github.com/nordstad/PinViz/tree/main/images).

---

## Contributing Examples

Have a useful diagram to share? Submit a pull request to the
[`examples/`](https://github.com/nordstad/PinViz/tree/main/examples) directory with:

1. A well-commented YAML configuration file
2. A description of what the example demonstrates
3. The rendered SVG diagram

---

## Next Steps

- [YAML Configuration Guide](yaml-config.md) — all config options
- [CLI Usage](cli.md) — all commands and flags
- [Validation](../validation.md) — catch wiring errors
- [Multi-Level Connections](../multi-level-connections.md) — device-to-device wiring guide
