"""Tests for SVG rendering."""

import xml.etree.ElementTree as ET

from pinviz import boards
from pinviz.devices import bh1750_light_sensor, generic_spi_device, simple_led
from pinviz.layout import LayoutConfig
from pinviz.model import Connection, Diagram
from pinviz.render_svg import SVGRenderer


def test_renderer_creation():
    """Test creating an SVGRenderer."""
    renderer = SVGRenderer()
    assert renderer is not None
    assert renderer.layout_config is not None
    assert renderer.layout_engine is not None


def test_renderer_with_custom_config():
    """Test creating renderer with custom layout config."""
    config = LayoutConfig(board_margin_left=100.0)
    renderer = SVGRenderer(config)
    assert renderer.layout_config.board_margin_left == 100.0


def test_render_creates_svg_file(sample_diagram, temp_output_dir):
    """Test that render creates an SVG file."""
    output_path = temp_output_dir / "test_render.svg"
    renderer = SVGRenderer()

    renderer.render(sample_diagram, output_path)

    assert output_path.exists()
    assert output_path.suffix == ".svg"


def test_render_creates_valid_svg(sample_diagram, temp_output_dir):
    """Test that render creates valid SVG."""
    output_path = temp_output_dir / "test_valid.svg"
    renderer = SVGRenderer()

    renderer.render(sample_diagram, output_path)

    # Parse the SVG to verify it's valid XML
    tree = ET.parse(output_path)
    root = tree.getroot()

    # Check it's an SVG element
    assert "svg" in root.tag.lower()


def test_render_includes_title(sample_diagram, temp_output_dir):
    """Test that rendered SVG includes the diagram title."""
    output_path = temp_output_dir / "test_title.svg"
    renderer = SVGRenderer()

    renderer.render(sample_diagram, output_path)

    # Read the SVG file
    content = output_path.read_text()

    # Check that title appears in the SVG
    assert sample_diagram.title in content


def test_render_with_path_object(sample_diagram, temp_output_dir):
    """Test rendering with Path object."""
    output_path = temp_output_dir / "test_path.svg"
    renderer = SVGRenderer()

    renderer.render(sample_diagram, output_path)

    assert output_path.exists()


def test_render_with_string_path(sample_diagram, temp_output_dir):
    """Test rendering with string path."""
    output_path = temp_output_dir / "test_string.svg"
    renderer = SVGRenderer()

    renderer.render(sample_diagram, str(output_path))

    assert output_path.exists()


def test_render_includes_devices(sample_diagram, temp_output_dir):
    """Test that rendered SVG includes device representations."""
    output_path = temp_output_dir / "test_devices.svg"
    renderer = SVGRenderer()

    renderer.render(sample_diagram, output_path)

    content = output_path.read_text()

    # Check that device name appears in the SVG
    assert sample_diagram.devices[0].name in content


def test_render_includes_wires(sample_diagram, temp_output_dir):
    """Test that rendered SVG includes wire paths."""
    output_path = temp_output_dir / "test_wires.svg"
    renderer = SVGRenderer()

    renderer.render(sample_diagram, output_path)

    content = output_path.read_text()

    # SVG should contain path elements for wires
    assert "<path" in content


def test_render_creates_background(sample_diagram, temp_output_dir):
    """Test that SVG has a white background."""
    output_path = temp_output_dir / "test_bg.svg"
    renderer = SVGRenderer()

    renderer.render(sample_diagram, output_path)

    content = output_path.read_text()

    # Should have a white background rectangle
    assert 'fill="white"' in content or "fill='white'" in content


def test_render_single_device_diagram(rpi5_board, bh1750_device, temp_output_dir):
    """Test rendering a simple single-device diagram."""
    connections = [
        Connection(1, "BH1750", "VCC"),
        Connection(6, "BH1750", "GND"),
        Connection(3, "BH1750", "SDA"),
        Connection(5, "BH1750", "SCL"),
    ]
    diagram = Diagram(
        title="BH1750 Sensor",
        board=rpi5_board,
        devices=[bh1750_device],
        connections=connections,
    )

    output_path = temp_output_dir / "single_device.svg"
    renderer = SVGRenderer()

    renderer.render(diagram, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    assert "BH1750" in content


def test_render_multi_device_diagram(rpi5_board, bh1750_device, led_device, temp_output_dir):
    """Test rendering a diagram with multiple devices."""
    connections = [
        Connection(1, "BH1750", "VCC"),
        Connection(6, "BH1750", "GND"),
        Connection(7, "LED", "+"),
        Connection(9, "LED", "-"),
    ]
    diagram = Diagram(
        title="Multi-Device Diagram",
        board=rpi5_board,
        devices=[bh1750_device, led_device],
        connections=connections,
    )

    output_path = temp_output_dir / "multi_device.svg"
    renderer = SVGRenderer()

    renderer.render(diagram, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    assert "BH1750" in content


def test_render_diagram_with_no_connections(rpi5_board, bh1750_device, temp_output_dir):
    """Test rendering a diagram with devices but no connections."""
    diagram = Diagram(
        title="No Connections",
        board=rpi5_board,
        devices=[bh1750_device],
        connections=[],
    )

    output_path = temp_output_dir / "no_connections.svg"
    renderer = SVGRenderer()

    renderer.render(diagram, output_path)

    assert output_path.exists()
    # Should still render the device
    content = output_path.read_text()
    assert "BH1750" in content


def test_render_diagram_with_gpio_diagram(sample_diagram, temp_output_dir):
    """Test rendering with GPIO diagram enabled."""
    sample_diagram.show_gpio_diagram = True
    output_path = temp_output_dir / "with_gpio.svg"
    renderer = SVGRenderer()

    renderer.render(sample_diagram, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    # GPIO diagram should add additional visual elements
    assert len(content) > 100  # Non-trivial content


def test_render_with_custom_margins(sample_diagram, temp_output_dir):
    """Test rendering with custom margin configuration."""
    config = LayoutConfig(board_margin_left=100.0, board_margin_top=100.0)
    renderer = SVGRenderer(config)

    output_path = temp_output_dir / "custom_margins.svg"
    renderer.render(sample_diagram, output_path)

    assert output_path.exists()


def test_render_with_custom_device_spacing(temp_output_dir):
    """Test rendering with custom device spacing."""
    config = LayoutConfig(device_spacing_vertical=50.0)
    renderer = SVGRenderer(config)

    board = boards.raspberry_pi_5()
    sensor = bh1750_light_sensor()
    led = simple_led()

    connections = [
        Connection(1, "BH1750", "VCC"),
        Connection(6, "BH1750", "GND"),
    ]

    diagram = Diagram(
        title="Custom Spacing",
        board=board,
        devices=[sensor, led],
        connections=connections,
    )

    output_path = temp_output_dir / "custom_spacing.svg"
    renderer.render(diagram, output_path)

    assert output_path.exists()


def test_svg_has_viewbox(sample_diagram, temp_output_dir):
    """Test that SVG has proper dimensions."""
    output_path = temp_output_dir / "test_viewbox.svg"
    renderer = SVGRenderer()

    renderer.render(sample_diagram, output_path)

    tree = ET.parse(output_path)
    root = tree.getroot()

    # SVG should have width and height or viewBox
    assert "width" in root.attrib or "viewBox" in root.attrib


def test_svg_elements_are_structured(sample_diagram, temp_output_dir):
    """Test that SVG contains expected element types."""
    output_path = temp_output_dir / "test_structure.svg"
    renderer = SVGRenderer()

    renderer.render(sample_diagram, output_path)

    content = output_path.read_text()

    # Should contain various SVG elements
    assert "<rect" in content  # For devices and background
    assert "<text" in content  # For labels
    assert "<path" in content  # For wires


def test_render_handles_missing_board_asset(sample_diagram, temp_output_dir):
    """Test that renderer handles missing board SVG asset gracefully."""
    # Use a non-existent asset path
    sample_diagram.board.svg_asset_path = "/nonexistent/path/board.svg"

    output_path = temp_output_dir / "missing_asset.svg"
    renderer = SVGRenderer()

    # Should not raise exception, should render fallback
    renderer.render(sample_diagram, output_path)

    assert output_path.exists()


def test_render_bh1750_example(temp_output_dir):
    """Test rendering the BH1750 example diagram."""
    board = boards.raspberry_pi_5()
    sensor = bh1750_light_sensor()

    connections = [
        Connection(1, "BH1750", "VCC"),
        Connection(6, "BH1750", "GND"),
        Connection(5, "BH1750", "SCL"),
        Connection(3, "BH1750", "SDA"),
    ]

    diagram = Diagram(
        title="BH1750 Light Sensor",
        board=board,
        devices=[sensor],
        connections=connections,
        show_gpio_diagram=True,
    )

    output_path = temp_output_dir / "bh1750_example.svg"
    renderer = SVGRenderer()

    renderer.render(diagram, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 1000  # Should be substantial file


def test_render_multi_device_example(temp_output_dir):
    """Test rendering a complex multi-device example."""
    board = boards.raspberry_pi_5()
    sensor = bh1750_light_sensor()
    spi = generic_spi_device("Display")
    led = simple_led("Status")

    connections = [
        # I2C sensor
        Connection(1, "BH1750", "VCC"),
        Connection(6, "BH1750", "GND"),
        Connection(5, "BH1750", "SCL"),
        Connection(3, "BH1750", "SDA"),
        # SPI display
        Connection(17, "Display", "VCC"),
        Connection(20, "Display", "GND"),
        Connection(23, "Display", "SCLK"),
        Connection(19, "Display", "MOSI"),
        # LED
        Connection(11, "Status LED", "+"),
        Connection(14, "Status LED", "-"),
    ]

    diagram = Diagram(
        title="Complex Multi-Device Example",
        board=board,
        devices=[sensor, spi, led],
        connections=connections,
    )

    output_path = temp_output_dir / "complex_example.svg"
    renderer = SVGRenderer()

    renderer.render(diagram, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    assert "BH1750" in content
    assert "Display" in content


def test_render_overwrites_existing_file(sample_diagram, temp_output_dir):
    """Test that render overwrites existing SVG file."""
    output_path = temp_output_dir / "overwrite.svg"

    # Create initial file
    output_path.write_text("<svg>initial</svg>")

    # Render new diagram
    renderer = SVGRenderer()
    renderer.render(sample_diagram, output_path)

    # File should be overwritten with new content
    content = output_path.read_text()

    assert "initial" not in content
    assert sample_diagram.title in content


def test_render_handles_missing_svg_asset(sample_diagram, temp_output_dir):
    """Test that render handles missing SVG asset file gracefully."""
    from unittest.mock import patch

    output_path = temp_output_dir / "missing_asset.svg"
    renderer = SVGRenderer()

    # Patch ET.parse to raise FileNotFoundError
    with patch("xml.etree.ElementTree.parse", side_effect=FileNotFoundError("File not found")):
        # Should not raise, but use fallback rendering
        renderer.render(sample_diagram, output_path)

    # File should still be created with fallback rendering
    assert output_path.exists()
    content = output_path.read_text()
    assert sample_diagram.title in content


def test_render_handles_malformed_svg_asset(sample_diagram, temp_output_dir):
    """Test that render handles malformed SVG asset file gracefully."""
    from unittest.mock import patch

    output_path = temp_output_dir / "malformed_asset.svg"
    renderer = SVGRenderer()

    # Patch ET.parse to raise ParseError
    with patch("xml.etree.ElementTree.parse", side_effect=ET.ParseError("Invalid XML")):
        # Should not raise, but use fallback rendering
        renderer.render(sample_diagram, output_path)

    # File should still be created with fallback rendering
    assert output_path.exists()
    content = output_path.read_text()
    assert sample_diagram.title in content


def test_render_handles_permission_denied(sample_diagram, temp_output_dir):
    """Test that render handles permission denied errors gracefully."""
    from unittest.mock import patch

    output_path = temp_output_dir / "permission_denied.svg"
    renderer = SVGRenderer()

    # Patch ET.parse to raise PermissionError
    with patch(
        "xml.etree.ElementTree.parse",
        side_effect=PermissionError("Permission denied"),
    ):
        # Should not raise, but use fallback rendering
        renderer.render(sample_diagram, output_path)

    # File should still be created with fallback rendering
    assert output_path.exists()
    content = output_path.read_text()
    assert sample_diagram.title in content


def test_render_handles_io_error(sample_diagram, temp_output_dir):
    """Test that render handles I/O errors gracefully."""
    from unittest.mock import patch

    output_path = temp_output_dir / "io_error.svg"
    renderer = SVGRenderer()

    # Patch ET.parse to raise OSError
    with patch("xml.etree.ElementTree.parse", side_effect=OSError("Disk full")):
        # Should not raise, but use fallback rendering
        renderer.render(sample_diagram, output_path)

    # File should still be created with fallback rendering
    assert output_path.exists()
    content = output_path.read_text()
    assert sample_diagram.title in content
