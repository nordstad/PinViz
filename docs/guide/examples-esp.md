# ESP32 and ESP8266 Examples

Examples for ESP32 DevKit V1, ESP8266 NodeMCU, and Wemos D1 Mini boards.

→ [All examples index](examples.md) | [Raspberry Pi](examples-raspberry-pi.md) | [Components](examples-components.md) | [Pico](examples-pico.md) | [Multi-Tier](examples-multi-tier.md)

All ESP boards use a dual-sided header layout. Physical pin numbers are used in
`board_pin` (not GPIO numbers). Use `pinviz list` to see each board's full pinout.

## Pin Reference

| Board | I2C | SPI | Power |
|-------|-----|-----|-------|
| **ESP32 DevKit V1** | GPIO21 (SDA), GPIO22 (SCL) | GPIO18 (SCK), GPIO19 (MISO), GPIO23 (MOSI), GPIO5 (CS) | 3V3, 5V, GND (multiple) |
| **ESP8266 NodeMCU** | GPIO4 (SDA), GPIO5 (SCL) | GPIO14 (SCK), GPIO12 (MISO), GPIO13 (MOSI), GPIO15 (CS) | 3V3, GND (4×) |
| **Wemos D1 Mini** | GPIO4 (SDA), GPIO5 (SCL) | GPIO14 (SCK), GPIO12 (MISO), GPIO13 (MOSI), GPIO15 (CS) | 3V3, 5V, GND |

---

## ESP32 Weather Station

BME280 environmental sensor and SSD1306 OLED display sharing the I2C bus on
ESP32 DevKit V1. Also available as the built-in `esp32_weather` example.

**Configuration:** [`examples/esp32_weather_station.yaml`](https://github.com/nordstad/PinViz/blob/main/examples/esp32_weather_station.yaml)

```yaml
title: "ESP32 Weather Station"
board: "esp32_devkit_v1"

devices:
  - type: "bme280"
    name: "BME280 Environmental Sensor"
  - type: "ssd1306"
    name: "SSD1306 OLED Display"

connections:
  # BME280 Sensor
  - board_pin: 1   # 3V3
    device: "BME280 Environmental Sensor"
    device_pin: "VCC"
  - board_pin: 3   # GND
    device: "BME280 Environmental Sensor"
    device_pin: "GND"
  - board_pin: 21  # GPIO21 (I2C SDA)
    device: "BME280 Environmental Sensor"
    device_pin: "SDA"
  - board_pin: 27  # GPIO22 (I2C SCL)
    device: "BME280 Environmental Sensor"
    device_pin: "SCL"

  # SSD1306 OLED Display (shares I2C bus)
  - board_pin: 1   # 3V3 (shared)
    device: "SSD1306 OLED Display"
    device_pin: "VCC"
  - board_pin: 4   # GND
    device: "SSD1306 OLED Display"
    device_pin: "GND"
  - board_pin: 21  # GPIO21 (I2C SDA, shared)
    device: "SSD1306 OLED Display"
    device_pin: "SDA"
  - board_pin: 27  # GPIO22 (I2C SCL, shared)
    device: "SSD1306 OLED Display"
    device_pin: "SCL"

show_legend: true
```

**Generate:**

```bash
pinviz example esp32_weather -o esp32_weather.svg
# Or from YAML file
pinviz render examples/esp32_weather_station.yaml -o esp32_weather.svg
```

**Result:**

![ESP32 Weather Station](https://raw.githubusercontent.com/nordstad/PinViz/main/images/esp32_weather_station.svg)

**Board aliases:** `esp32_devkit_v1`, `esp32`, `esp32_devkit`

---

## ESP32 DevKit V1 - I2C Sensor

Single BME280 sensor on ESP32 DevKit V1.

**Result:**

![ESP32 I2C Sensor](https://raw.githubusercontent.com/nordstad/PinViz/main/images/esp32_example.svg)

**Key Features:** I2C connection on GPIO21 (SDA) and GPIO22 (SCL), 3.3V power.

---

## ESP8266 NodeMCU - LED Example

Multiple LEDs with smart GND pin distribution using `board_pin_role`.

**Result:**

![ESP8266 NodeMCU LEDs](https://raw.githubusercontent.com/nordstad/PinViz/main/images/esp8266_nodemcu_example.svg)

**Key Features:** Smart pin assignment distributes GND connections across the
NodeMCU's 4 GND pins automatically. See [Smart Pin Assignment](../features/smart-pin-assignment.md).

**Board aliases:** `esp8266_nodemcu`, `esp8266`, `nodemcu`

---

## Wemos D1 Mini - OLED Display

I2C OLED display on the compact Wemos D1 Mini (16-pin dual-sided).

**Result:**

![Wemos D1 Mini OLED](https://raw.githubusercontent.com/nordstad/PinViz/main/images/wemos_d1_mini_example.svg)

**Key Features:** Compact 16-pin form factor, I2C on GPIO4 (SDA) and GPIO5 (SCL).
Good for space-constrained and battery-powered projects.

**Board aliases:** `wemos_d1_mini`, `d1mini`, `wemos`
