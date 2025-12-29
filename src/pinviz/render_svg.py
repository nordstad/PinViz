"""SVG rendering for GPIO diagrams."""

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import svgwrite

from .layout import LayoutConfig, LayoutEngine, RoutedWire, create_bezier_path
from .model import DEFAULT_COLORS, Board, ComponentType, Device, Diagram, PinRole, Point


class SVGRenderer:
    """
    Render GPIO wiring diagrams to SVG format.

    Converts a Diagram object into a scalable SVG image showing the Raspberry Pi
    board, connected devices, wire connections, and optional GPIO reference diagram.

    The renderer handles:
        - Board SVG asset embedding
        - Device box rendering with labeled pins
        - Wire routing with rounded corners
        - Inline component symbols (resistors, capacitors, diodes)
        - GPIO pin numbering and color coding
        - Optional GPIO reference diagram
        - Automatic layout via LayoutEngine

    Examples:
        >>> from pinviz import boards, devices, Connection, Diagram, SVGRenderer
        >>>
        >>> diagram = Diagram(
        ...     title="LED Circuit",
        ...     board=boards.raspberry_pi_5(),
        ...     devices=[devices.led()],
        ...     connections=[
        ...         Connection(11, "LED", "Anode"),
        ...         Connection(6, "LED", "Cathode")
        ...     ]
        ... )
        >>>
        >>> renderer = SVGRenderer()
        >>> renderer.render(diagram, "led_circuit.svg")
    """

    def __init__(self, layout_config: LayoutConfig | None = None):
        """
        Initialize SVG renderer with optional layout configuration.

        Args:
            layout_config: Layout configuration for spacing and margins.
                If None, uses default LayoutConfig.
        """
        self.layout_config = layout_config or LayoutConfig()
        self.layout_engine = LayoutEngine(self.layout_config)
        self._init_svg_handlers()

    def _init_svg_handlers(self) -> None:
        """Initialize SVG element handlers."""
        self._svg_handlers = {
            "rect": self._handle_rect,
            "circle": self._handle_circle,
            "ellipse": self._handle_ellipse,
            "line": self._handle_line,
            "polyline": self._handle_polyline,
            "polygon": self._handle_polygon,
            "path": self._handle_path,
            "text": self._handle_text,
            "g": self._handle_group,
        }

    def render(self, diagram: Diagram, output_path: str | Path) -> None:
        """
        Render a diagram to an SVG file.

        Args:
            diagram: The diagram to render
            output_path: Output file path
        """
        # Calculate layout
        canvas_width, canvas_height, routed_wires = self.layout_engine.layout_diagram(diagram)

        # Create SVG drawing
        dwg = svgwrite.Drawing(str(output_path), size=(f"{canvas_width}px", f"{canvas_height}px"))

        # Add white background
        dwg.add(dwg.rect(insert=(0, 0), size=(canvas_width, canvas_height), fill="white"))

        # Draw title
        if diagram.title:
            dwg.add(
                dwg.text(
                    diagram.title,
                    insert=(canvas_width / 2, 25),
                    text_anchor="middle",
                    font_size="20px",
                    font_family="Arial, sans-serif",
                    font_weight="bold",
                    fill="#333",
                )
            )

        # Draw board
        self._draw_board(dwg, diagram.board)

        # Draw wires first so they appear behind devices
        # Sort wires for proper z-order to prevent overlapping/hiding
        # Primary: source pin X position (left column pins first, right column on top)
        # Secondary: destination Y (lower devices first)
        # Tertiary: rail X position (further right first)
        # This ensures wires from right GPIO column are always on top
        sorted_wires = sorted(
            routed_wires,
            key=lambda w: (
                w.from_pin_pos.x,  # Left column first, right column on top
                -w.to_pin_pos.y,  # Lower Y (higher devices) drawn last
                -(w.path_points[2].x if len(w.path_points) > 2 else w.path_points[0].x),
            ),
        )
        for wire in sorted_wires:
            self._draw_wire(dwg, wire)

        # Draw devices on top of wires
        for device in diagram.devices:
            self._draw_device(dwg, device)

        # Draw GPIO pin diagram on the right if enabled
        if diagram.show_gpio_diagram:
            self._draw_gpio_diagram(dwg, canvas_width)

        # Legend removed per user request - cleaner diagram

        # Save
        dwg.save()

    def _draw_board(self, dwg: svgwrite.Drawing, board: Board) -> None:
        """
        Draw the Raspberry Pi board with GPIO pins.

        Embeds the board SVG asset, draws GPIO pin numbers with color-coded backgrounds,
        and adds the board name label. Falls back to simple rectangle if SVG asset
        is not available.

        Args:
            dwg: The SVG drawing object
            board: The board to render
        """
        x = self.layout_config.board_margin_left
        y = self.layout_config.board_margin_top

        # Load and embed the board SVG
        if Path(board.svg_asset_path).exists():
            try:
                # Parse the SVG file
                tree = ET.parse(board.svg_asset_path)
                root = tree.getroot()

                # Create a group for the board with proper positioning
                board_group = dwg.g(transform=f"translate({x}, {y})")

                # Inline the SVG content by parsing and recreating elements
                self._inline_svg_elements(board_group, root, dwg)

                dwg.add(board_group)

            except Exception as e:
                # Fallback: draw a simple rectangle
                print(f"Warning: Could not load board SVG ({e}), using fallback")
                self._draw_board_fallback(dwg, board, x, y)
        else:
            # Fallback: draw a simple rectangle
            self._draw_board_fallback(dwg, board, x, y)

        # Draw GPIO pin numbers
        self._draw_gpio_pin_numbers(dwg, board, x, y)

        # Draw board label
        dwg.add(
            dwg.text(
                board.name,
                insert=(x + board.width / 2, y + board.height + 20),
                text_anchor="middle",
                font_size="14px",
                font_family="Arial, sans-serif",
                font_weight="bold",
                fill="#333",
            )
        )

    def _draw_gpio_pin_numbers(
        self, dwg: svgwrite.Drawing, board: Board, x: float, y: float
    ) -> None:
        """
        Draw pin numbers on GPIO header with color-coded backgrounds.

        Creates small circles at each pin location with the physical pin number (1-40)
        and color-coded background based on pin role (power, ground, GPIO, I2C, SPI, etc.).

        Args:
            dwg: The SVG drawing object
            board: The board containing pin definitions
            x: Board X offset
            y: Board Y offset
        """
        # Use the same offset as defined in layout config for consistency
        pin_number_y_offset = self.layout_config.pin_number_y_offset

        # Color mapping for pin backgrounds based on pin role
        from .model import PinRole

        role_colors = {
            PinRole.POWER_3V3: "#FFA500",  # Orange
            PinRole.POWER_5V: "#FF0000",  # Red
            PinRole.GROUND: "#D3D3D3",  # Light gray
            PinRole.I2C_SDA: "#FF00FF",  # Magenta
            PinRole.I2C_SCL: "#FF00FF",  # Magenta
            PinRole.I2C_EEPROM: "#FFFF00",  # Yellow
            PinRole.SPI_MOSI: "#0000FF",  # Blue
            PinRole.SPI_MISO: "#0000FF",  # Blue
            PinRole.SPI_SCLK: "#0000FF",  # Blue
            PinRole.SPI_CE0: "#0000FF",  # Blue
            PinRole.SPI_CE1: "#0000FF",  # Blue
            PinRole.UART_TX: "#0000FF",  # Blue
            PinRole.UART_RX: "#0000FF",  # Blue
            PinRole.PWM: "#00FF00",  # Green
            PinRole.GPIO: "#00FF00",  # Green
            PinRole.PCM_CLK: "#00FF00",  # Green
            PinRole.PCM_FS: "#00FF00",  # Green
            PinRole.PCM_DIN: "#00FF00",  # Green
            PinRole.PCM_DOUT: "#00FF00",  # Green
        }

        # Use larger pins for Pi Zero boards (smaller board, needs bigger pins)
        is_pi_zero = "Zero" in board.name
        pin_radius = 7.5 if is_pi_zero else 4.5
        pin_font_size = "6px" if is_pi_zero else "4.5px"

        for pin in board.pins:
            pin_x = x + pin.position.x
            pin_y = y + pin.position.y + pin_number_y_offset

            # Draw circle background for pin number
            # Match the size of connector circles in pi2.svg (r=2.088)
            # Use larger size for better visibility: r=4.5 (Pi 5) or r=7.5 (Pi Zero)
            # Use color based on pin role
            bg_color = role_colors.get(pin.role, "#FFFFFF")  # Default to white if role not found

            dwg.add(
                dwg.circle(
                    center=(pin_x, pin_y),
                    r=pin_radius,
                    fill=bg_color,
                    stroke="#333",
                    stroke_width=0.5,
                    opacity=0.95,
                )
            )

            # Draw pin number - scaled to fit in circle
            font_size = pin_font_size  # Scaled to fit in circle
            # Use white text on blue backgrounds for better readability
            text_color = "#FFFFFF" if bg_color == "#0000FF" else "#000000"
            dwg.add(
                dwg.text(
                    str(pin.number),
                    insert=(pin_x, pin_y + 1.5),
                    text_anchor="middle",
                    font_size=font_size,
                    font_family="Arial, sans-serif",
                    font_weight="bold",
                    fill=text_color,
                )
            )

    def _inline_svg_elements(self, parent_group, svg_root, dwg: svgwrite.Drawing) -> None:
        """
        Inline SVG elements from external SVG file.

        Recursively processes all elements in the SVG and adds them to the parent group.
        """
        # SVG namespace
        svg_ns = "{http://www.w3.org/2000/svg}"

        # Process all children of the SVG root (skip root itself)
        for child in svg_root:
            # Strip namespace from tag
            tag = child.tag.replace(svg_ns, "") if svg_ns in child.tag else child.tag

            # Get all attributes
            attribs = {k.replace(svg_ns, ""): v for k, v in child.attrib.items()}

            # Create element based on tag type
            if tag == "defs":
                # Handle defs section - add to main drawing's defs
                for def_child in child:
                    def_tag = (
                        def_child.tag.replace(svg_ns, "")
                        if svg_ns in def_child.tag
                        else def_child.tag
                    )
                    def_attribs = {k.replace(svg_ns, ""): v for k, v in def_child.attrib.items()}

                    # Handle gradients
                    if def_tag == "linearGradient":
                        gradient = dwg.linearGradient(**def_attribs)
                        for stop in def_child:
                            stop_attribs = self._parse_stop_attributes(stop)
                            gradient.add_stop_color(**stop_attribs)
                        dwg.defs.add(gradient)
                    elif def_tag == "radialGradient":
                        gradient = dwg.radialGradient(**def_attribs)
                        for stop in def_child:
                            stop_attribs = self._parse_stop_attributes(stop)
                            gradient.add_stop_color(**stop_attribs)
                        dwg.defs.add(gradient)
            elif tag == "g":
                # Handle group
                g = dwg.g(**attribs)
                # Recursively process children
                for grandchild in child:
                    self._add_svg_element(g, grandchild, dwg, svg_ns)
                parent_group.add(g)
            else:
                # Handle other elements
                self._add_svg_element(parent_group, child, dwg, svg_ns)

    def _add_svg_element(self, parent, element, dwg: svgwrite.Drawing, svg_ns: str) -> None:
        """Add a single SVG element to parent."""
        tag = element.tag.replace(svg_ns, "") if svg_ns in element.tag else element.tag

        # Filter attributes: only keep SVG namespace attributes and non-namespaced attributes
        attribs = {}
        for k, v in element.attrib.items():
            # Keep non-namespaced attributes (no braces)
            if not k.startswith("{"):
                attribs[k] = v
            # Keep SVG namespace attributes (remove namespace prefix)
            elif k.startswith(svg_ns):
                attribs[k.replace(svg_ns, "")] = v

        # Dispatch to appropriate handler
        handler = self._svg_handlers.get(tag)
        if handler:
            svg_element = handler(element, attribs, dwg, svg_ns)
            if svg_element:
                parent.add(svg_element)

    def _handle_rect(self, element, attribs, dwg, svg_ns):
        params = {}
        if "x" in attribs and "y" in attribs:
            params["insert"] = (attribs.pop("x"), attribs.pop("y"))
        if "width" in attribs and "height" in attribs:
            params["size"] = (attribs.pop("width"), attribs.pop("height"))
        params.update(attribs)
        return dwg.rect(**params)

    def _handle_circle(self, element, attribs, dwg, svg_ns):
        params = {}
        if "cx" in attribs and "cy" in attribs:
            params["center"] = (attribs.pop("cx"), attribs.pop("cy"))
        if "r" in attribs:
            params["r"] = attribs.pop("r")
        params.update(attribs)
        return dwg.circle(**params)

    def _handle_ellipse(self, element, attribs, dwg, svg_ns):
        params = {}
        if "cx" in attribs and "cy" in attribs:
            params["center"] = (attribs.pop("cx"), attribs.pop("cy"))
        if "rx" in attribs:
            params["r"] = (attribs.pop("rx"), attribs.pop("ry", attribs.get("rx")))
        params.update(attribs)
        return dwg.ellipse(**params)

    def _handle_line(self, element, attribs, dwg, svg_ns):
        params = {}
        if "x1" in attribs and "y1" in attribs:
            params["start"] = (attribs.pop("x1"), attribs.pop("y1"))
        if "x2" in attribs and "y2" in attribs:
            params["end"] = (attribs.pop("x2"), attribs.pop("y2"))
        params.update(attribs)
        return dwg.line(**params)

    def _handle_polyline(self, element, attribs, dwg, svg_ns):
        params = {}
        if "points" in attribs:
            points_str = attribs.pop("points")
            points = []
            for point in points_str.split():
                coords = point.split(",")
                if len(coords) == 2:
                    points.append((float(coords[0]), float(coords[1])))
            params["points"] = points
        params.update(attribs)
        return dwg.polyline(**params)

    def _handle_polygon(self, element, attribs, dwg, svg_ns):
        params = {}
        if "points" in attribs:
            points_str = attribs.pop("points")
            points = []
            for point in points_str.split():
                coords = point.split(",")
                if len(coords) == 2:
                    points.append((float(coords[0]), float(coords[1])))
            params["points"] = points
        params.update(attribs)
        return dwg.polygon(**params)

    def _handle_path(self, element, attribs, dwg, svg_ns):
        params = {}
        if "d" in attribs:
            params["d"] = attribs.pop("d")
        params.update(attribs)
        return dwg.path(**params)

    def _handle_text(self, element, attribs, dwg, svg_ns):
        text_content = element.text or ""
        params = {}
        if "x" in attribs and "y" in attribs:
            params["insert"] = (attribs.pop("x"), attribs.pop("y"))
        params.update(attribs)
        return dwg.text(text_content, **params)

    def _handle_group(self, element, attribs, dwg, svg_ns):
        g = dwg.g(**attribs)
        for child in element:
            self._add_svg_element(g, child, dwg, svg_ns)
        return g

    def _parse_stop_attributes(self, stop_element) -> dict:
        """Parse gradient stop attributes, handling inline styles."""
        svg_ns = "{http://www.w3.org/2000/svg}"
        attribs = {k.replace(svg_ns, ""): v for k, v in stop_element.attrib.items()}

        # Parse style attribute if present
        if "style" in attribs:
            style_str = attribs.pop("style")
            # Parse CSS style string
            for style_item in style_str.split(";"):
                if ":" in style_item:
                    key, value = style_item.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    # Map CSS properties to the ones we need
                    if key == "stop-color":
                        attribs["color"] = value
                    elif key == "stop-opacity":
                        attribs["opacity"] = value

        # Map offset if present
        result = {}
        if "offset" in attribs:
            result["offset"] = attribs["offset"]
        if "color" in attribs:
            result["color"] = attribs["color"]
        if "opacity" in attribs:
            result["opacity"] = attribs["opacity"]

        return result

    def _draw_board_fallback(self, dwg: svgwrite.Drawing, board: Board, x: float, y: float) -> None:
        """Draw a simple representation of the board when SVG asset is not available."""
        # Board rectangle
        dwg.add(
            dwg.rect(
                insert=(x, y),
                size=(board.width, board.height),
                rx=8,
                ry=8,
                fill="#2d8e3a",
                stroke="#1a5a23",
                stroke_width=2,
            )
        )

        # GPIO header representation
        header_x = x + board.header_offset.x
        header_y = y + board.header_offset.y

        dwg.add(
            dwg.rect(
                insert=(header_x - 5, header_y - 5),
                size=(35, 100),
                rx=2,
                ry=2,
                fill="#1a1a1a",
                stroke="#000",
            )
        )

    def _draw_device(self, dwg: svgwrite.Drawing, device: Device) -> None:
        """
        Draw a device or module as a colored rectangle with labeled pins.

        Renders the device name above the box, draws a rounded rectangle for the
        device body, and adds labeled pin markers with black backgrounds for
        readability.

        Args:
            dwg: The SVG drawing object
            device: The device to render
        """
        x = device.position.x
        y = device.position.y

        # Use full device name (no truncation)
        display_name = device.name

        # Adjust font size based on name length for better fit
        name_length = len(display_name)
        if name_length <= 20:
            font_size = "12px"
        elif name_length <= 30:
            font_size = "10px"
        else:
            font_size = "9px"

        # Device name above the box
        text_x = x + device.width / 2
        text_y = y - 5  # Position above the box

        dwg.add(
            dwg.text(
                display_name,
                insert=(text_x, text_y),
                text_anchor="middle",
                font_size=font_size,
                font_family="Arial, sans-serif",
                font_weight="bold",
                fill="#333",
            )
        )

        # Device box
        dwg.add(
            dwg.rect(
                insert=(x, y),
                size=(device.width, device.height),
                rx=5,
                ry=5,
                fill=device.color,
                stroke="#333",
                stroke_width=2,
                opacity=0.9,
            )
        )

        # Draw pins
        for pin in device.pins:
            pin_x = x + pin.position.x
            pin_y = y + pin.position.y

            # Pin circle
            dwg.add(dwg.circle(center=(pin_x, pin_y), r=3, fill="#FFD700", stroke="#333"))

            # Pin label with black background inside device box (to the right of pin)
            label_padding = 4
            label_x = pin_x + 6  # Position to the right of the pin circle
            label_y = pin_y

            # Estimate label dimensions
            label_width = len(pin.name) * 4.2  # ~4.2px per character at 7px font
            label_height = 10

            # Draw black background for pin label
            dwg.add(
                dwg.rect(
                    insert=(label_x, label_y - label_height / 2),
                    size=(label_width + label_padding * 2, label_height),
                    rx=2,
                    ry=2,
                    fill="#000000",
                    opacity=0.8,
                )
            )

            # Draw pin label text in white
            dwg.add(
                dwg.text(
                    pin.name,
                    insert=(label_x + label_padding, label_y + 2.5),
                    text_anchor="start",
                    font_size="7px",
                    font_family="Arial, sans-serif",
                    fill="#FFFFFF",
                )
            )

    def _point_along_path(self, points: list[Point], position: float) -> tuple[Point, float]:
        """
        Calculate a point along a path at the given position (0.0-1.0).

        Returns:
            Tuple of (point, angle_degrees) where angle is the tangent direction
        """
        if position <= 0.0:
            # Angle from first to second point
            dx = points[1].x - points[0].x
            dy = points[1].y - points[0].y
            angle = math.degrees(math.atan2(dy, dx))
            return points[0], angle
        if position >= 1.0:
            # Angle from second-to-last to last point
            dx = points[-1].x - points[-2].x
            dy = points[-1].y - points[-2].y
            angle = math.degrees(math.atan2(dy, dx))
            return points[-1], angle

        # Calculate total path length
        segments = []
        total_length = 0.0
        for i in range(len(points) - 1):
            dx = points[i + 1].x - points[i].x
            dy = points[i + 1].y - points[i].y
            seg_length = math.sqrt(dx * dx + dy * dy)
            segments.append(seg_length)
            total_length += seg_length

        # Find target distance along path
        target_dist = position * total_length
        current_dist = 0.0

        # Find which segment contains the target point
        for i, seg_length in enumerate(segments):
            if current_dist + seg_length >= target_dist:
                # Interpolate within this segment
                segment_position = (target_dist - current_dist) / seg_length
                p1 = points[i]
                p2 = points[i + 1]

                x = p1.x + segment_position * (p2.x - p1.x)
                y = p1.y + segment_position * (p2.y - p1.y)

                # Calculate angle
                dx = p2.x - p1.x
                dy = p2.y - p1.y
                angle = math.degrees(math.atan2(dy, dx))

                return Point(x, y), angle

            current_dist += seg_length

        # Fallback (shouldn't reach here)
        return points[-1], 0.0

    def _draw_resistor_symbol(
        self, dwg: svgwrite.Drawing, center: Point, angle: float, color: str, value: str
    ) -> None:
        """Draw a resistor symbol at the given position and angle."""
        # Resistor dimensions
        width = 20.0
        height = 6.0

        # Create group for resistor
        g = dwg.g()

        # Draw rectangle for resistor body
        rect = dwg.rect(
            insert=(-width / 2, -height / 2),
            size=(width, height),
            fill="white",
            stroke=color,
            stroke_width=2,
        )

        # Draw lead lines (extending from resistor body)
        lead_length = 8.0
        left_lead = dwg.line(
            start=(-width / 2 - lead_length, 0),
            end=(-width / 2, 0),
            stroke=color,
            stroke_width=2,
        )
        right_lead = dwg.line(
            start=(width / 2, 0), end=(width / 2 + lead_length, 0), stroke=color, stroke_width=2
        )

        g.add(rect)
        g.add(left_lead)
        g.add(right_lead)

        # Add value label
        text = dwg.text(
            value,
            insert=(0, -height / 2 - 5),
            text_anchor="middle",
            font_size="10px",
            font_family="Arial, sans-serif",
            fill="#333",
            font_weight="bold",
        )
        g.add(text)

        # Apply rotation and translation
        g.translate(center.x, center.y)
        g.rotate(angle)

        dwg.add(g)

    def _draw_wire(self, dwg: svgwrite.Drawing, wire: RoutedWire) -> None:
        """
        Draw a wire connection with optional inline components.

        Renders wires with rounded corners and white halos for visibility. If the
        wire has inline components (resistors, capacitors, diodes), breaks the wire
        into segments and draws component symbols at specified positions.

        Args:
            dwg: The SVG drawing object
            wire: The routed wire with path and color information
        """
        if not wire.connection.components:
            self._draw_simple_wire(dwg, wire)
        else:
            self._draw_wire_with_components(dwg, wire)

        self._draw_wire_endpoints(dwg, wire)

    def _draw_simple_wire(self, dwg: svgwrite.Drawing, wire: RoutedWire) -> None:
        """Draw a simple wire without components."""
        path_d = create_bezier_path(wire.path_points, self.layout_config.corner_radius)
        self._draw_wire_halo(dwg, path_d)
        self._draw_wire_core(dwg, path_d, wire.color)

    def _draw_wire_with_components(self, dwg: svgwrite.Drawing, wire: RoutedWire) -> None:
        """Draw a wire broken into segments by inline components."""
        component_positions = sorted(
            [(comp, comp.position) for comp in wire.connection.components], key=lambda x: x[1]
        )

        prev_pos = 0.0
        for comp, comp_pos in component_positions:
            # Draw wire segment from prev_pos to comp_pos
            if comp_pos > prev_pos + 0.01:
                self._draw_wire_segment(dwg, wire, prev_pos, comp_pos)

            # Draw component symbol
            comp_pt, angle = self._point_along_path(wire.path_points, comp_pos)
            if comp.type == ComponentType.RESISTOR:
                self._draw_resistor_symbol(dwg, comp_pt, angle, wire.color, comp.value)

            prev_pos = comp_pos

        # Draw final segment from last component to end
        if prev_pos < 0.99:
            self._draw_wire_segment(dwg, wire, prev_pos, 1.0)

    def _draw_wire_segment(
        self, dwg: svgwrite.Drawing, wire: RoutedWire, start_pos: float, end_pos: float
    ) -> None:
        """Draw a segment of a wire between two positions (0.0-1.0)."""
        segment_points = self._get_path_segment(wire.path_points, start_pos, end_pos)
        if len(segment_points) >= 2:
            path_d = create_bezier_path(segment_points, self.layout_config.corner_radius)
            self._draw_wire_halo(dwg, path_d)
            self._draw_wire_core(dwg, path_d, wire.color)

    def _get_path_segment(
        self, path_points: list[Point], start_pos: float, end_pos: float
    ) -> list[Point]:
        """Extract points from path between start_pos and end_pos."""
        if start_pos >= end_pos:
            return []

        segment_points = []

        # Add start point
        if start_pos > 0.0:
            start_pt, _ = self._point_along_path(path_points, start_pos)
            segment_points.append(start_pt)

        # Add all intermediate path points that fall within range
        total_length = 0.0
        segment_lengths = []
        for i in range(len(path_points) - 1):
            dx = path_points[i + 1].x - path_points[i].x
            dy = path_points[i + 1].y - path_points[i].y
            seg_len = math.sqrt(dx * dx + dy * dy)
            segment_lengths.append(seg_len)
            total_length += seg_len

        cumulative = 0.0
        for i, seg_len in enumerate(segment_lengths):
            pos_at_start = cumulative / total_length
            pos_at_end = (cumulative + seg_len) / total_length

            # Include point if it's within our range
            if start_pos <= pos_at_start <= end_pos:
                segment_points.append(path_points[i])
            if start_pos <= pos_at_end <= end_pos:
                segment_points.append(path_points[i + 1])

            cumulative += seg_len

        # Add end point
        if end_pos < 1.0:
            end_pt, _ = self._point_along_path(path_points, end_pos)
            segment_points.append(end_pt)

        # Remove duplicates while preserving order
        seen = set()
        unique_points = []
        for pt in segment_points:
            key = (round(pt.x, 2), round(pt.y, 2))
            if key not in seen:
                seen.add(key)
                unique_points.append(pt)

        return unique_points if len(unique_points) >= 2 else segment_points

    def _draw_wire_halo(self, dwg: svgwrite.Drawing, path_d: str) -> None:
        """Draw the white halo around a wire for visibility."""
        dwg.add(
            dwg.path(
                d=path_d,
                stroke="white",
                stroke_width=7,
                fill="none",
                stroke_linecap="round",
                stroke_linejoin="round",
                opacity=1.0,
            )
        )

    def _draw_wire_core(self, dwg: svgwrite.Drawing, path_d: str, color: str) -> None:
        """Draw the colored core of a wire."""
        dwg.add(
            dwg.path(
                d=path_d,
                stroke=color,
                stroke_width=3,
                fill="none",
                stroke_linecap="round",
                stroke_linejoin="round",
                opacity=0.8,
            )
        )

    def _draw_wire_endpoints(self, dwg: svgwrite.Drawing, wire: RoutedWire) -> None:
        """Draw the start and end connection dots."""
        # Start point
        dwg.add(dwg.circle(center=(wire.from_pin_pos.x, wire.from_pin_pos.y), r=4, fill="white"))
        dwg.add(dwg.circle(center=(wire.from_pin_pos.x, wire.from_pin_pos.y), r=3, fill=wire.color))
        # End point
        dwg.add(dwg.circle(center=(wire.to_pin_pos.x, wire.to_pin_pos.y), r=4, fill="white"))
        dwg.add(dwg.circle(center=(wire.to_pin_pos.x, wire.to_pin_pos.y), r=3, fill=wire.color))

    def _draw_legend(
        self,
        dwg: svgwrite.Drawing,
        routed_wires: list[RoutedWire],
        canvas_width: float,
        canvas_height: float,
    ) -> None:
        """Draw the legend showing wire color meanings."""
        legend_x = canvas_width - self.layout_config.legend_width - self.layout_config.legend_margin
        legend_y = (
            canvas_height - self.layout_config.legend_height - self.layout_config.legend_margin
        )

        # Legend background
        dwg.add(
            dwg.rect(
                insert=(legend_x, legend_y),
                size=(self.layout_config.legend_width, self.layout_config.legend_height),
                rx=5,
                ry=5,
                fill="white",
                stroke="#333",
                stroke_width=1,
                opacity=0.95,
            )
        )

        # Legend title
        dwg.add(
            dwg.text(
                "Wire Colors",
                insert=(legend_x + self.layout_config.legend_width / 2, legend_y + 20),
                text_anchor="middle",
                font_size="12px",
                font_family="Arial, sans-serif",
                font_weight="bold",
                fill="#333",
            )
        )

        # Collect unique colors and their roles
        color_roles: dict[str, set[PinRole]] = {}
        for wire in routed_wires:
            color = wire.color
            # Try to determine the role from the connection
            # This is a simplified version; in practice, you'd look up the actual pin role
            if color not in color_roles:
                color_roles[color] = set()

            # Find the role by reverse lookup in DEFAULT_COLORS
            for role, default_color in DEFAULT_COLORS.items():
                if default_color == color:
                    color_roles[color].add(role)
                    break

        # Draw legend entries
        entry_y = legend_y + 35
        line_height = 18

        for color, roles in sorted(color_roles.items()):
            if entry_y > legend_y + self.layout_config.legend_height - 10:
                break  # Don't overflow legend box

            # Color swatch
            dwg.add(
                dwg.line(
                    start=(legend_x + 10, entry_y),
                    end=(legend_x + 30, entry_y),
                    stroke=color,
                    stroke_width=4,
                    stroke_linecap="round",
                )
            )

            # Role label
            role_text = ", ".join(sorted(r.value for r in roles))
            if not role_text:
                role_text = "Signal"

            dwg.add(
                dwg.text(
                    role_text,
                    insert=(legend_x + 35, entry_y + 4),
                    font_size="10px",
                    font_family="Arial, sans-serif",
                    fill="#333",
                )
            )

            entry_y += line_height

    def _draw_gpio_diagram(self, dwg: svgwrite.Drawing, canvas_width: float) -> None:
        """
        Draw the GPIO pin reference diagram on the right side.

        Embeds the GPIO pin reference SVG showing all pins with their roles,
        scaled and positioned on the right side of the canvas. This provides
        a quick reference for pin functions.

        Args:
            dwg: The SVG drawing object
            canvas_width: Total canvas width for positioning
        """
        # Path to the GPIO diagram SVG
        gpio_svg_path = Path(__file__).parent / "assets" / "gpio_pins.svg"

        if not gpio_svg_path.exists():
            print(f"Warning: GPIO diagram not found at {gpio_svg_path}")
            return

        try:
            # Parse the GPIO SVG file
            tree = ET.parse(gpio_svg_path)
            root = tree.getroot()

            # Extract viewBox to get original dimensions
            viewbox_str = root.get("viewBox")
            if viewbox_str:
                viewbox_parts = viewbox_str.split()
                original_width = float(viewbox_parts[2])
            else:
                # Fallback dimensions if no viewBox
                original_width = 500.0

            # Calculate scale and position
            target_width = self.layout_config.gpio_diagram_width
            scale = target_width / original_width

            # Position on the right side, aligned from top with margin
            x = canvas_width - target_width - self.layout_config.gpio_diagram_margin
            y = self.layout_config.board_margin_top

            # Create a group for the GPIO diagram with scaling and positioning
            gpio_group = dwg.g(transform=f"translate({x}, {y}) scale({scale})")

            # Inline the SVG content
            self._inline_svg_elements(gpio_group, root, dwg)

            dwg.add(gpio_group)

        except Exception as e:
            print(f"Warning: Could not load GPIO diagram ({e})")

    def render_to_string(self, diagram: Diagram) -> str:
        """
        Render a diagram to an SVG string.

        Args:
            diagram: The diagram to render

        Returns:
            SVG content as string
        """
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as f:
            temp_path = f.name

        try:
            self.render(diagram, temp_path)
            with open(temp_path) as f:
                return f.read()
        finally:
            Path(temp_path).unlink(missing_ok=True)
