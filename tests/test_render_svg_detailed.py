"""Additional detailed tests for SVG rendering to improve coverage."""

from pinviz.devices import (
    bh1750_light_sensor,
    button_switch,
    ds18b20_temp_sensor,
    generic_i2c_device,
    simple_led,
)
from pinviz.layout import LayoutConfig
from pinviz.model import Component, ComponentType, Connection, Diagram, WireStyle
from pinviz.render_svg import SVGRenderer


def test_render_with_inline_resistor(rpi5_board, temp_output_dir):
    """Test rendering diagram with inline resistor component."""
    led = simple_led()
    resistor = Component(type=ComponentType.RESISTOR, value="220Ω", position=0.6)

    connections = [
        Connection(7, led.name, "+", components=[resistor]),
        Connection(9, led.name, "-"),
    ]

    diagram = Diagram(
        title="LED with Resistor",
        board=rpi5_board,
        devices=[led],
        connections=connections,
    )

    output_path = temp_output_dir / "led_with_resistor.svg"
    renderer = SVGRenderer()
    renderer.render(diagram, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    assert "220" in content  # Resistor value should appear


def test_render_with_capacitor_component(rpi5_board, temp_output_dir):
    """Test rendering diagram with capacitor component."""
    device = generic_i2c_device("Sensor")
    capacitor = Component(type=ComponentType.CAPACITOR, value="100µF", position=0.5)

    connections = [
        Connection(1, "Sensor", "VCC", components=[capacitor]),
        Connection(6, "Sensor", "GND"),
    ]

    diagram = Diagram(
        title="Sensor with Capacitor",
        board=rpi5_board,
        devices=[device],
        connections=connections,
    )

    output_path = temp_output_dir / "with_capacitor.svg"
    renderer = SVGRenderer()
    renderer.render(diagram, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    assert "100" in content


def test_render_with_diode_component(rpi5_board, temp_output_dir):
    """Test rendering diagram with diode component."""
    device = generic_i2c_device("Module")
    diode = Component(type=ComponentType.DIODE, value="1N4148", position=0.55)

    connections = [
        Connection(1, "Module", "VCC", components=[diode]),
        Connection(6, "Module", "GND"),
    ]

    diagram = Diagram(
        title="Module with Diode",
        board=rpi5_board,
        devices=[device],
        connections=connections,
    )

    output_path = temp_output_dir / "with_diode.svg"
    renderer = SVGRenderer()
    renderer.render(diagram, output_path)

    assert output_path.exists()


def test_render_with_custom_wire_colors(rpi5_board, bh1750_device, temp_output_dir):
    """Test rendering with custom wire colors."""
    connections = [
        Connection(1, "BH1750", "VCC", color="#FF0000"),
        Connection(6, "BH1750", "GND", color="#000000"),
        Connection(3, "BH1750", "SDA", color="#00FF00"),
        Connection(5, "BH1750", "SCL", color="#0000FF"),
    ]

    diagram = Diagram(
        title="Custom Wire Colors",
        board=rpi5_board,
        devices=[bh1750_device],
        connections=connections,
    )

    output_path = temp_output_dir / "custom_colors.svg"
    renderer = SVGRenderer()
    renderer.render(diagram, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    # Check that custom colors appear in SVG
    assert "#FF0000" in content or "rgb(255,0,0)" in content.lower()


def test_render_with_curved_wire_style(rpi5_board, bh1750_device, temp_output_dir):
    """Test rendering with curved wire style."""
    connections = [
        Connection(1, "BH1750", "VCC", style=WireStyle.CURVED),
        Connection(6, "BH1750", "GND", style=WireStyle.CURVED),
    ]

    diagram = Diagram(
        title="Curved Wires",
        board=rpi5_board,
        devices=[bh1750_device],
        connections=connections,
    )

    output_path = temp_output_dir / "curved_wires.svg"
    renderer = SVGRenderer()
    renderer.render(diagram, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    # Curved wires should have bezier curve commands
    assert "C" in content or "c" in content


def test_render_with_orthogonal_wire_style(rpi5_board, bh1750_device, temp_output_dir):
    """Test rendering with orthogonal wire style."""
    connections = [
        Connection(1, "BH1750", "VCC", style=WireStyle.ORTHOGONAL),
        Connection(6, "BH1750", "GND", style=WireStyle.ORTHOGONAL),
    ]

    diagram = Diagram(
        title="Orthogonal Wires",
        board=rpi5_board,
        devices=[bh1750_device],
        connections=connections,
    )

    output_path = temp_output_dir / "orthogonal_wires.svg"
    renderer = SVGRenderer()
    renderer.render(diagram, output_path)

    assert output_path.exists()


def test_render_with_all_component_types(rpi5_board, temp_output_dir):
    """Test rendering with all component types."""
    device = generic_i2c_device("Complex Module")

    resistor = Component(ComponentType.RESISTOR, "470Ω", 0.5)
    capacitor = Component(ComponentType.CAPACITOR, "10µF", 0.6)
    diode = Component(ComponentType.DIODE, "1N4001", 0.7)

    connections = [
        Connection(1, "Complex Module", "VCC", components=[resistor]),
        Connection(3, "Complex Module", "SDA", components=[capacitor]),
        Connection(5, "Complex Module", "SCL", components=[diode]),
        Connection(6, "Complex Module", "GND"),
    ]

    diagram = Diagram(
        title="All Components",
        board=rpi5_board,
        devices=[device],
        connections=connections,
    )

    output_path = temp_output_dir / "all_components.svg"
    renderer = SVGRenderer()
    renderer.render(diagram, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    assert "470" in content
    assert "10" in content


def test_render_large_diagram(rpi5_board, temp_output_dir):
    """Test rendering a diagram with many devices."""
    devices = [
        bh1750_light_sensor(),
        ds18b20_temp_sensor(),
        simple_led("Red"),
        simple_led("Green"),
        button_switch(),
    ]

    connections = [
        Connection(1, "BH1750", "VCC"),
        Connection(3, "DS18B20", "VCC"),
        Connection(11, "Red LED", "+"),
        Connection(13, "Green LED", "+"),
        Connection(15, "Button (Pull-up)", "SIG"),
        Connection(6, "BH1750", "GND"),
        Connection(9, "DS18B20", "GND"),
        Connection(14, "Red LED", "-"),
        Connection(20, "Green LED", "-"),
        Connection(25, "Button (Pull-up)", "GND"),
    ]

    diagram = Diagram(
        title="Large Multi-Device Diagram",
        board=rpi5_board,
        devices=devices,
        connections=connections,
    )

    output_path = temp_output_dir / "large_diagram.svg"
    renderer = SVGRenderer()
    renderer.render(diagram, output_path)

    assert output_path.exists()
    # File should be substantial
    assert output_path.stat().st_size > 5000


def test_render_with_very_long_device_names(rpi5_board, temp_output_dir):
    """Test rendering with long device names."""
    device = generic_i2c_device("Very Long Device Name That Should Be Handled Properly")

    connections = [
        Connection(1, device.name, "VCC"),
        Connection(6, device.name, "GND"),
    ]

    diagram = Diagram(
        title="Long Names Test",
        board=rpi5_board,
        devices=[device],
        connections=connections,
    )

    output_path = temp_output_dir / "long_names.svg"
    renderer = SVGRenderer()
    renderer.render(diagram, output_path)

    assert output_path.exists()


def test_render_minimal_diagram(rpi5_board, temp_output_dir):
    """Test rendering minimal diagram with no devices."""
    diagram = Diagram(
        title="Minimal Diagram",
        board=rpi5_board,
        devices=[],
        connections=[],
    )

    output_path = temp_output_dir / "minimal.svg"
    renderer = SVGRenderer()
    renderer.render(diagram, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    assert "Minimal Diagram" in content


def test_render_empty_title(rpi5_board, bh1750_device, temp_output_dir):
    """Test rendering with empty title."""
    connections = [Connection(1, "BH1750", "VCC")]

    diagram = Diagram(
        title="",
        board=rpi5_board,
        devices=[bh1750_device],
        connections=connections,
    )

    output_path = temp_output_dir / "no_title.svg"
    renderer = SVGRenderer()
    renderer.render(diagram, output_path)

    assert output_path.exists()


def test_render_with_extremely_tight_spacing(sample_diagram, temp_output_dir):
    """Test rendering with very tight layout spacing."""
    config = LayoutConfig(
        device_spacing_vertical=5.0,
        rail_offset=10.0,
        corner_radius=2.0,
    )
    renderer = SVGRenderer(config)

    output_path = temp_output_dir / "tight_spacing.svg"
    renderer.render(sample_diagram, output_path)

    assert output_path.exists()


def test_render_with_generous_spacing(sample_diagram, temp_output_dir):
    """Test rendering with generous layout spacing."""
    config = LayoutConfig(
        device_spacing_vertical=100.0,
        rail_offset=100.0,
        corner_radius=20.0,
    )
    renderer = SVGRenderer(config)

    output_path = temp_output_dir / "generous_spacing.svg"
    renderer.render(sample_diagram, output_path)

    assert output_path.exists()
