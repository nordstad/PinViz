# Wire Routing System

## Overview

The PinViz wire routing system provides professional, collision-free wire
routing for GPIO diagrams. The system uses an intelligent rail-based routing
approach with automatic spacing and bundling to create clean, readable
diagrams.

## Key Features

### 1. Rail-Based Routing

Wires are routed using a "rail" system:

- **Horizontal segment**: From GPIO pin to vertical rail
- **Vertical segment**: Along the rail to the target height
- **Horizontal segment**: From rail to device pin

This creates clean orthogonal paths that are easy to follow.

### 2. Intelligent Spacing

The router automatically prevents wire overlap through:

- **Minimum spacing guarantees**: Configurable `wire_spacing` parameter
  (default: 8.0px)
- **Collision detection**: Checks for conflicts in overlapping Y ranges
- **Dynamic adjustment**: Automatically shifts wires right to maintain
  clearance

### 3. Wire Bundling

Wires from the same source pin are bundled together:

- Sorted by destination Y coordinate for natural grouping
- Tighter spacing within bundles (`bundle_spacing`: 4.0px)
- Wider spacing between different pin groups (`wire_spacing`: 8.0px)

### 4. Deterministic Output

- Same inputs always produce the same diagram
- No random routing or unpredictable behavior
- Consistent, repeatable results for version control

## Configuration Parameters

All routing parameters are configurable through `LayoutConfig`:

```python
from pinviz import SVGRenderer, LayoutConfig

config = LayoutConfig(
    rail_offset=40.0,         # Distance from board to wire rail
    wire_spacing=8.0,         # Minimum spacing between parallel wires
    bundle_spacing=4.0,       # Spacing within a wire bundle
    corner_radius=5.0,        # Radius for rounded corners
)

renderer = SVGRenderer(layout_config=config)
```

### Parameter Descriptions

| Parameter | Default | Description |
|-----------|---------|-------------|
| `rail_offset` | 40.0 | Horizontal distance from board to first rail |
| `wire_spacing` | 8.0 | Minimum spacing between wires from pins |
| `bundle_spacing` | 4.0 | Spacing within same bundle (tighter) |
| `corner_radius` | 5.0 | Radius for rounded corners in styles |

## How It Works

### Step 1: Wire Grouping

Connections are grouped by their source GPIO pin:

```text
Pin 1: [VCC_conn1, VCC_conn2]
Pin 3: [SDA_conn]
Pin 5: [SCL_conn]
Pin 6: [GND_conn1, GND_conn2, GND_conn3]
```

### Step 2: Bundle Sorting

Within each group, wires are sorted by destination Y coordinate to create
natural bundles:

```text
Pin 6: [GND to Device1 (y=60), GND to Device2 (y=80),
        GND to Device3 (y=100)]
```

### Step 3: Rail Assignment

Each wire gets a rail X position based on:

1. **Base position**: `pin.x + rail_offset`
2. **Bundle offset**: `+ index * bundle_spacing` (for wires from same pin)
3. **Collision check**: Adjusted right if conflicts with existing wires

### Step 4: Collision Detection

For each new wire, the router checks all previously routed wires:

```python
for existing_wire in used_rails:
    if y_ranges_overlap(new_wire, existing_wire):
        if abs(new_wire.rail_x - existing_wire.rail_x) < wire_spacing:
            new_wire.rail_x = existing_wire.rail_x + wire_spacing
```

This ensures minimum spacing is maintained even when wires from different pins
overlap vertically.

### Step 5: Path Creation

The final path consists of 4 waypoints:

1. Start: GPIO pin position
2. Rail entry: `(rail_x, pin_y)`
3. Rail exit: `(rail_x, device_y)`
4. End: Device pin position

## Tuning for Your Diagrams

### Dense Diagrams (Many Wires)

For diagrams with 15+ wires:

```python
config = LayoutConfig(
    rail_offset=50.0,         # More space for rails
    wire_spacing=10.0,        # Wider spacing
    bundle_spacing=5.0,       # Slightly wider bundles
)
```

### Compact Diagrams (Few Wires)

For simple diagrams with 4-8 wires:

```python
config = LayoutConfig(
    rail_offset=35.0,         # Compact layout
    wire_spacing=6.0,         # Tighter overall
    bundle_spacing=3.0,       # Tight bundles
)
```

### Debug/Visualization

To see wire routing more clearly:

```python
config = LayoutConfig(
    wire_spacing=15.0,        # Extra wide spacing
    bundle_spacing=8.0,       # Visible bundle separation
)
```

## Future Enhancements

The routing system is designed for incremental improvement. Potential
enhancements:

1. **Adaptive Rail Spacing**: Automatically adjust rail_offset based on wire
   count
2. **Multi-Rail Routing**: Use multiple parallel rails for very dense diagrams
3. **Fan-Out Optimization**: Special handling for many wires to the same device
4. **Crossing Minimization**: Reorder wires within bundles to reduce crossings
5. **A* Pathfinding**: Advanced obstacle avoidance for complex layouts
   (experimental module available)

## API Reference

### LayoutEngine Methods

#### `_route_wires(diagram: Diagram) -> list[RoutedWire]`

Routes all wires in a diagram using the improved spacing algorithm.

**Returns**: List of `RoutedWire` objects with calculated paths

#### `_find_clear_rail_position(preferred_x, y_min, y_max, used_rails) -> float`

Finds a collision-free rail X position for a wire.

**Parameters**:

- `preferred_x`: Desired rail X position
- `y_min`, `y_max`: Vertical range of the wire
- `used_rails`: List of existing rail positions

**Returns**: Adjusted X position with guaranteed clearance

#### `_calculate_wire_path_with_rail(from_pos, to_pos, rail_x, style) -> list[Point]`

Creates waypoints for a wire path using rail-based routing.

**Parameters**:

- `from_pos`: Starting point (GPIO pin)
- `to_pos`: Ending point (device pin)
- `rail_x`: X position of the vertical rail
- `style`: `WireStyle` enum (ORTHOGONAL, CURVED, MIXED)

**Returns**: List of waypoints defining the path

## Examples

### Basic Usage

```python
from pinviz import boards, devices, Connection, Diagram, SVGRenderer

diagram = Diagram(
    title="Sensor Connections",
    board=boards.raspberry_pi_5(),
    devices=[devices.bh1750_light_sensor()],
    connections=[
        Connection(1, "BH1750", "VCC"),
        Connection(6, "BH1750", "GND"),
        Connection(3, "BH1750", "SDA"),
        Connection(5, "BH1750", "SCL"),
    ]
)

renderer = SVGRenderer()
renderer.render(diagram, "sensor.svg")
```

The routing system automatically:

- Groups power and ground wires from common pins
- Spaces them to prevent overlap
- Creates clean bundles for related signals

### Custom Routing Configuration

```python
from pinviz import SVGRenderer, LayoutConfig

# Create custom layout configuration
config = LayoutConfig(
    rail_offset=45.0,
    wire_spacing=10.0,
    bundle_spacing=5.0,
    corner_radius=8.0,
)

# Use custom config
renderer = SVGRenderer(layout_config=config)
renderer.render(diagram, "custom_routing.svg")
```

## Troubleshooting

### Wires Still Overlap

If you see overlapping wires:

1. Increase `wire_spacing` (try 10.0 or 12.0)
2. Increase `rail_offset` to provide more routing space
3. Check if wire colors are too similar (may look like overlap)

### Wires Too Spread Out

If diagram is too wide:

1. Decrease `wire_spacing` (try 6.0)
2. Decrease `rail_offset` (try 30.0 or 35.0)
3. Decrease `bundle_spacing` (try 3.0)

### Unexpected Routing

The routing is deterministic based on:

- Source pin number
- Destination Y coordinate
- Order in connections list

To change routing order, reorder connections in your configuration.
