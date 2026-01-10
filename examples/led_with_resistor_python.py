"""Example: LED with current-limiting resistor (Pure Python API)."""

from pinviz import (
    Component,
    ComponentType,
    Connection,
    Diagram,
    SVGRenderer,
    WireColor,
    boards,
)
from pinviz.devices import get_registry

# Create board and LED device
board = boards.raspberry_pi_5()
registry = get_registry()
led = registry.create("led", color_name="Red")

# Define connections with inline resistor component
connections = [
    # LED Anode to GPIO17 via 220Ω resistor
    Connection(
        board_pin=11,  # GPIO17
        device_name="Red LED",
        device_pin_name="+",
        color=WireColor.RED,
        components=[
            Component(
                type=ComponentType.RESISTOR,
                value="220Ω",
                position=0.55,  # 55% along wire (default, toward LED side)
            )
        ],
    ),
    # LED Cathode to Ground
    Connection(
        board_pin=9,  # GND
        device_name="Red LED",
        device_pin_name="-",
        color=WireColor.BLACK,
    ),
]

# Create diagram
diagram = Diagram(
    title="LED with Current-Limiting Resistor",
    board=board,
    devices=[led],
    connections=connections,
    show_legend=True,
)

# Render to SVG
renderer = SVGRenderer()
renderer.render(diagram, "out/led_with_resistor_python.svg")

print("✓ Diagram generated: out/led_with_resistor_python.svg")
