# Python API

Programmatic usage of PinViz.

## Basic Usage

```python
from pinviz import boards, devices, Connection, Diagram, SVGRenderer

board = boards.raspberry_pi_5()
sensor = devices.bh1750_light_sensor()

connections = [
    Connection(1, "BH1750", "VCC"),
    Connection(6, "BH1750", "GND"),
]

diagram = Diagram(
    title="Example",
    board=board,
    devices=[sensor],
    connections=connections
)

renderer = SVGRenderer()
renderer.render(diagram, "output.svg")
```

See the [API Reference](../api/index.md) for detailed documentation.
