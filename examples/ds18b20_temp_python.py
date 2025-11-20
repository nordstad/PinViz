"""Example: DS18B20 waterproof temperature sensor (Pure Python API)."""

from pinviz import (
    Component,
    ComponentType,
    Connection,
    Diagram,
    SVGRenderer,
    WireColor,
    boards,
    devices,
)

# Create board and DS18B20 sensor device
board = boards.raspberry_pi_5()
temp_sensor = devices.ds18b20_temp_sensor()

# Define connections with pull-up resistor
connections = [
    # VCC to 3.3V power
    Connection(
        board_pin=1,  # 3.3V
        device_name="DS18B20",
        device_pin_name="VCC",
        color=WireColor.RED,
    ),
    # DATA to GPIO4 (default 1-Wire pin) with 4.7kΩ pull-up resistor
    Connection(
        board_pin=7,  # GPIO4
        device_name="DS18B20",
        device_pin_name="DATA",
        color=WireColor.YELLOW,
        components=[
            Component(
                type=ComponentType.RESISTOR,
                value="4.7kΩ",
                position=0.3,  # Pull-up resistor positioned near Pi side
            )
        ],
    ),
    # GND to Ground
    Connection(
        board_pin=9,  # GND
        device_name="DS18B20",
        device_pin_name="GND",
        color=WireColor.BLACK,
    ),
]

# Create diagram
diagram = Diagram(
    title="DS18B20 Waterproof Temperature Sensor",
    board=board,
    devices=[temp_sensor],
    connections=connections,
    show_legend=True,
)

# Render to SVG
renderer = SVGRenderer()
renderer.render(diagram, "out/ds18b20_temp_python.svg")

print("✓ Diagram generated: out/ds18b20_temp_python.svg")
