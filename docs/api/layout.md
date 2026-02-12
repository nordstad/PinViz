# Layout

Diagram layout engine for positioning devices and routing wires.

**New in v0.15.0**: The layout system has been refactored into a modular package structure for better maintainability:

- **`layout.engine`** - Main `LayoutEngine` orchestrator
- **`layout.positioning`** - `DevicePositioner` for multi-tier device placement
- **`layout.routing`** - `WireRouter` for smooth Bezier curve routing
- **`layout.sizing`** - `CanvasSizer` for calculating canvas dimensions
- **`layout.types`** - `LayoutConfig`, `LayoutResult`, and constants
- **`layout.utils`** - Utility functions (e.g., `create_bezier_path`)

The public API remains unchanged - import from `pinviz.layout` as before.

::: pinviz.layout
    options:
      show_root_heading: true
      show_source: true
