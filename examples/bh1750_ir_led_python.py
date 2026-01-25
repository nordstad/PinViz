"""Example: BH1750 light sensor + IR LED ring wiring diagram (Pure Python API)."""

from pinviz import (
    Connection,
    Diagram,
    SVGRenderer,
    WireColor,
    boards,
)
from pinviz.devices import get_registry

# Create board and devices
board = boards.raspberry_pi_5()
registry = get_registry()
sensor = registry.create("bh1750", name="BH1750 Light Sensor")
ir_ring = registry.create("ir_led_ring", num_leds=12, name="IR LED Ring")

# Define connections with custom wire colors
connections = [
    # BH1750 Light Sensor (I2C)
    Connection(1, "BH1750 Light Sensor", "VCC", color=WireColor.ORANGE),  # Pin 1 (3.3V) to VCC
    Connection(9, "BH1750 Light Sensor", "GND", color=WireColor.YELLOW),  # Pin 9 (GND) to GND
    Connection(3, "BH1750 Light Sensor", "SDA", color=WireColor.GREEN),  # Pin 3 (GPIO2/SDA) to SDA
    Connection(5, "BH1750 Light Sensor", "SCL", color=WireColor.BLUE),  # Pin 5 (GPIO3/SCL) to SCL
    # IR LED Ring (5V power + GPIO control)
    Connection(2, "IR LED Ring", "VCC", color=WireColor.RED),  # Pin 2 (5V) to VCC
    Connection(6, "IR LED Ring", "GND", color=WireColor.BLACK),  # Pin 6 (GND) to GND
    Connection(11, "IR LED Ring", "EN", color=WireColor.RED),  # Pin 11 (GPIO17) to EN
]

# Create diagram
diagram = Diagram(
    title="BH1750 Light Sensor + IR LED Ring",
    board=board,
    devices=[sensor, ir_ring],
    connections=connections,
    show_legend=True,
)

# Render to SVG
renderer = SVGRenderer()
renderer.render(diagram, "out/bh1750_ir_led_python.svg")

print("✓ Diagram generated: out/bh1750_ir_led_python.svg")
