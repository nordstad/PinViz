"""Layout engine for positioning components and routing wires.

This package provides modular layout functionality split into focused components:
- types: Layout data types and configuration
- engine: Main LayoutEngine orchestrator
- positioning: Device positioning logic
- routing: Wire routing logic
- sizing: Canvas size calculation
- utils: Utility functions (create_bezier_path)

For backward compatibility, all public classes are re-exported at the package level.
"""

# Re-export all public classes for backward compatibility
from .engine import LayoutEngine
from .positioning import DevicePositioner
from .routing import WireRouter
from .sizing import CanvasSizer
from .types import (
    LayoutConfig,
    LayoutConstants,
    LayoutResult,
    RoutedWire,
    WireData,
)
from .utils import create_bezier_path

__all__ = [
    # Main engine
    "LayoutEngine",
    # Configuration and types
    "LayoutConfig",
    "LayoutConstants",
    "LayoutResult",
    "RoutedWire",
    "WireData",
    # Component classes
    "DevicePositioner",
    "WireRouter",
    "CanvasSizer",
    # Utilities
    "create_bezier_path",
]
