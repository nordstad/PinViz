"""PinViz - Generate Raspberry Pi GPIO connection diagrams.

This is a test change to demonstrate Codecov PR comments.
"""

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
from .validation import DiagramValidator, ValidationIssue, ValidationLevel

# Get version from package metadata
try:
    from importlib.metadata import version

    __version__ = version("pinviz")
except Exception:
    __version__ = "unknown"

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
    # Validation
    "DiagramValidator",
    "ValidationIssue",
    "ValidationLevel",
]
