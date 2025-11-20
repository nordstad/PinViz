"""Example: Multiple devices (I2C + SPI) wiring diagram (Pure Python API)."""

from pinviz import Connection, Diagram, SVGRenderer, boards, devices

# Create board and devices
board = boards.raspberry_pi_5()
i2c_sensor = devices.generic_i2c_device("OLED_Display", has_int_pin=False)
spi_sensor = devices.generic_spi_device("Accel_SPI")

# Define connections for I2C device (OLED Display)
i2c_connections = [
    Connection(1, "OLED_Display", "VCC"),  # Pin 1 (3V3) to VCC
    Connection(6, "OLED_Display", "GND"),  # Pin 6 (GND) to GND
    Connection(5, "OLED_Display", "SCL"),  # Pin 5 (GPIO3/I2C SCL) to SCL
    Connection(3, "OLED_Display", "SDA"),  # Pin 3 (GPIO2/I2C SDA) to SDA
]

# Define connections for SPI device (Accelerometer)
spi_connections = [
    Connection(17, "Accel_SPI", "VCC"),  # Pin 17 (3V3) to VCC
    Connection(20, "Accel_SPI", "GND"),  # Pin 20 (GND) to GND
    Connection(23, "Accel_SPI", "SCLK"),  # Pin 23 (GPIO11/SPI SCLK) to SCLK
    Connection(19, "Accel_SPI", "MOSI"),  # Pin 19 (GPIO10/SPI MOSI) to MOSI
    Connection(21, "Accel_SPI", "MISO"),  # Pin 21 (GPIO9/SPI MISO) to MISO
    Connection(24, "Accel_SPI", "CS"),  # Pin 24 (GPIO8/SPI CE0) to CS
]

# Combine all connections
connections = i2c_connections + spi_connections

# Create diagram
diagram = Diagram(
    title="Multi-Device Wiring: I2C OLED + SPI Accelerometer",
    board=board,
    devices=[i2c_sensor, spi_sensor],
    connections=connections,
    show_legend=True,
)

# Render to SVG
renderer = SVGRenderer()
renderer.render(diagram, "multi_device_diagram.svg")

print("✓ Diagram generated: multi_device_diagram.svg")
