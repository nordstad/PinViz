# Python API

Programmatic usage of PinViz.

## Demo

<p align="center">
  <img src="https://raw.githubusercontent.com/nordstad/PinViz/main/scripts/demos/output/python_api_demo.gif" alt="PinViz Python API Demo" width="800">
</p>

## Basic Usage

```python
from pinviz import boards, devices, Connection, Diagram, SVGRenderer

# Create board - choose one:
board = boards.raspberry_pi_5()      # Raspberry Pi 5
# board = boards.raspberry_pi_4()      # Raspberry Pi 4 Model B

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
