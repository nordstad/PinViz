"""Example: IR LED ring module wiring diagram (Pure Python API)."""

from pinviz import Connection, Diagram, SVGRenderer, boards, devices

# Create board and devices
board = boards.raspberry_pi_5()
led_ring = devices.ir_led_ring(num_leds=12)

# Define connections
connections = [
    Connection(2, "IR_LED_Ring", "VCC"),  # Pin 2 (5V) to VCC
    Connection(9, "IR_LED_Ring", "GND"),  # Pin 9 (GND) to GND
    Connection(11, "IR_LED_Ring", "CTRL"),  # Pin 11 (GPIO17) to control pin
]

# Create diagram
diagram = Diagram(
    title="12-LED IR Ring Module Wiring",
    board=board,
    devices=[led_ring],
    connections=connections,
    show_legend=True,
)

# Render to SVG
renderer = SVGRenderer()
renderer.render(diagram, "ir_led_ring_diagram.svg")

print("✓ Diagram generated: ir_led_ring_diagram.svg")
