"""PinViz - Generate Raspberry Pi GPIO connection diagrams."""

import logging

import structlog

# Standard library practice for packages: suppress output when used as a library.
# The CLI overrides this via configure_logging() in its callback.
logging.getLogger("pinviz").addHandler(logging.NullHandler())
structlog.configure(
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=False,
)

from . import boards, devices  # noqa: E402
from .config_loader import load_diagram  # noqa: E402
from .model import (  # noqa: E402
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
from .render_svg import SVGRenderer  # noqa: E402
from .validation import DiagramValidator, ValidationIssue, ValidationLevel  # noqa: E402

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
