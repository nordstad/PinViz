"""Example: BH1750 light sensor wiring diagram (Pure Python API)."""

from pinviz import (
    Connection,
    Diagram,
    SVGRenderer,
    WireColor,
    boards,
    devices,
)

# Create board and devices
board = boards.raspberry_pi_5()
sensor = devices.bh1750_light_sensor()

# Define connections with custom wire colors using WireColor enum
connections = [
    Connection(1, "BH1750", "VCC", color=WireColor.RED),  # Pin 1 (3V3) to VCC
    Connection(6, "BH1750", "GND", color=WireColor.BLACK),  # Pin 6 (GND) to GND
    Connection(5, "BH1750", "SCL", color=WireColor.BLUE),  # Pin 5 (GPIO3/SCL) to SCL
    Connection(3, "BH1750", "SDA", color=WireColor.GREEN),  # Pin 3 (GPIO2/SDA) to SDA
]

# Create diagram
diagram = Diagram(
    title="BH1750 Light Sensor Wiring",
    board=board,
    devices=[sensor],
    connections=connections,
    show_legend=True,
)

# Render to SVG
renderer = SVGRenderer()
renderer.render(diagram, "bh1750_diagram.svg")

print("✓ Diagram generated: bh1750_diagram.svg")
