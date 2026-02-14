"""ESP32 Weather Station - BME280 + SSD1306 OLED Example.

This example shows how to read temperature, humidity, and pressure
from a BME280 sensor and display it on an SSD1306 OLED using an
ESP32 DevKit V1. Both devices share the I2C bus (GPIO21=SDA, GPIO22=SCL).

Requirements (MicroPython):
    pip install micropython-bme280
    pip install micropython-ssd1306

Wiring:
    BME280 VCC  → 3V3 (pin 1)
    BME280 GND  → GND (pin 3)
    BME280 SDA  → GPIO21 (pin 21)
    BME280 SCL  → GPIO22 (pin 27)
    OLED VCC    → 3V3 (pin 1)
    OLED GND    → GND (pin 3)
    OLED SDA    → GPIO21 (pin 21)
    OLED SCL    → GPIO22 (pin 27)
"""

from machine import I2C, Pin
from time import sleep

import bme280
import ssd1306

# Initialize I2C bus on ESP32 default pins
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)

# Initialize sensors
bme = bme280.BME280(i2c=i2c, addr=0x76)
oled = ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

while True:
    # Read sensor data
    temp, pressure, humidity = bme.values

    # Display on OLED
    oled.fill(0)
    oled.text("Weather Station", 0, 0)
    oled.text(f"Temp: {temp}", 0, 16)
    oled.text(f"Hum:  {humidity}", 0, 28)
    oled.text(f"Pres: {pressure}", 0, 40)
    oled.show()

    sleep(2)
