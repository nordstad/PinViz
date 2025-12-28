from pinviz import Connection, Device, DevicePin, Diagram, PinRole, Point, SVGRenderer, boards

# Use predefined board
board = boards.raspberry_pi_5()

# Create custom sensor device
sensor = Device(
    name="DHT22",
    pins=[
        DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0)),
        DevicePin("DATA", PinRole.GPIO, Point(0, 20)),
        DevicePin("GND", PinRole.GROUND, Point(0, 40)),
    ]
)

# Define connections
connections = [
    Connection(1, "DHT22", "VCC"),
    Connection(7, "DHT22", "DATA"),
    Connection(9, "DHT22", "GND"),
]

# Create diagram
diagram = Diagram(
    title="DHT22 Sensor - Python API",
    board=board,
    devices=[sensor],
    connections=connections
)

# Render to SVG
renderer = SVGRenderer()
renderer.render(diagram, "sensor_diagram.svg")
print("Diagram created: sensor_diagram.svg")
