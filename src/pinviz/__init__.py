"""PinViz - Generate Raspberry Pi GPIO connection diagrams."""

from . import boards, devices
from .config_loader import load_diagram
from .model import (
    Board,
    Component,
    ComponentType,
    Connection,
    Device,
    DevicePin,
    Diagram,
    HeaderPin,
    PinRole,
    Point,
    WireColor,
    WireStyle,
)
from .render_svg import SVGRenderer

__version__ = "0.1.0"

__all__ = [
    # Core models
    "Board",
    "HeaderPin",
    "Device",
    "DevicePin",
    "Connection",
    "Component",
    "ComponentType",
    "Diagram",
    "Point",
    "PinRole",
    "WireColor",
    "WireStyle",
    # Modules
    "boards",
    "devices",
    # Functions
    "load_diagram",
    # Renderer
    "SVGRenderer",
]
