"""Command-line interface for pinviz."""

import argparse
import sys
from pathlib import Path
from typing import Any

from rich_argparse import RichHelpFormatter

from .config_loader import load_diagram
from .model import Diagram
from .render_svg import SVGRenderer

# Get version from package metadata
try:
    from importlib.metadata import version

    __version__ = version("pinviz")
except Exception:
    __version__ = "unknown"


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Raspberry Pi GPIO connection diagrams",
        formatter_class=RichHelpFormatter,
        epilog="""
Examples:
  # Generate diagram from YAML config
  pinviz diagram.yaml

  # Specify output path
  pinviz diagram.yaml -o output/wiring.svg

  # Use a built-in example
  pinviz example bh1750

For more information, visit: https://github.com/nordstad/PinViz
        """,
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Main render command (also default when no subcommand is given)
    render_parser = subparsers.add_parser(
        "render", help="Render a diagram from a configuration file (default)"
    )
    render_parser.add_argument("config", help="Path to YAML or JSON configuration file")
    render_parser.add_argument(
        "-o", "--output", help="Output SVG file path (default: <config>.svg)"
    )

    # Example command
    example_parser = subparsers.add_parser("example", help="Generate a built-in example diagram")
    example_parser.add_argument(
        "name",
        choices=["bh1750", "ir_led", "i2c_spi"],
        help="Example diagram name",
    )
    example_parser.add_argument(
        "-o",
        "--output",
        help="Output SVG file path (default: ./out/<example>.svg)",
    )

    # List command
    subparsers.add_parser("list", help="List available board and device templates")

    # Allow config file as first argument without subcommand
    if (
        len(sys.argv) > 1
        and not sys.argv[1].startswith("-")
        and sys.argv[1] not in ["render", "example", "list"]
    ):
        # Treat first argument as config file
        sys.argv.insert(1, "render")

    args = parser.parse_args()

    # Handle commands
    if args.command == "render" or (hasattr(args, "config")):
        return render_command(args)
    elif args.command == "example":
        return example_command(args)
    elif args.command == "list":
        return list_command()
    else:
        parser.print_help()
        return 1


def render_command(args: Any) -> int:
    """Render a diagram from a configuration file."""
    config_path = Path(args.config)

    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_path}", file=sys.stderr)
        return 1

    # Determine output path
    output_path = Path(args.output) if args.output else config_path.with_suffix(".svg")

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        print(f"Loading configuration from {config_path}...")
        diagram = load_diagram(config_path)

        print(f"Rendering diagram to {output_path}...")
        renderer = SVGRenderer()
        renderer.render(diagram, output_path)

        print(f"✓ Diagram generated successfully: {output_path}")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def example_command(args: Any) -> int:
    """Generate a built-in example diagram."""
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = Path("./out")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{args.name}.svg"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        print(f"Generating example diagram: {args.name}")

        # Create the example diagram
        if args.name == "bh1750":
            diagram = create_bh1750_example()
        elif args.name == "ir_led":
            diagram = create_ir_led_example()
        elif args.name == "i2c_spi":
            diagram = create_i2c_spi_example()
        else:
            print(f"Error: Unknown example: {args.name}", file=sys.stderr)
            return 1

        print(f"Rendering diagram to {output_path}...")
        renderer = SVGRenderer()
        renderer.render(diagram, output_path)

        print(f"✓ Example diagram generated successfully: {output_path}")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def list_command() -> int:
    """List available templates."""
    from .devices import get_registry

    print("Available Boards:")
    print("  - raspberry_pi_5 (alias: rpi5)")
    print("  - raspberry_pi (alias: rpi)")
    print()

    # List devices by category
    registry = get_registry()
    categories = registry.get_categories()

    print("Available Device Templates:")
    for category in categories:
        devices = registry.list_by_category(category)
        print(f"\n  {category.title()}:")
        for device in devices:
            print(f"    - {device.type_id}: {device.description}")

    print()
    print("Available Examples:")
    print("  - bh1750: BH1750 light sensor connected via I2C")
    print("  - ir_led: IR LED ring connected to GPIO")
    print("  - i2c_spi: Multiple I2C and SPI devices")
    print()

    return 0


def create_bh1750_example():
    """Create BH1750 example diagram."""
    from . import boards
    from .devices import bh1750_light_sensor
    from .model import Connection, Diagram

    board = boards.raspberry_pi_5()
    sensor = bh1750_light_sensor()

    connections = [
        Connection(1, "BH1750", "VCC"),  # 3V3 to VCC
        Connection(6, "BH1750", "GND"),  # GND to GND
        Connection(5, "BH1750", "SCL"),  # GPIO3/SCL to SCL
        Connection(3, "BH1750", "SDA"),  # GPIO2/SDA to SDA
    ]

    return Diagram(
        title="BH1750 Light Sensor Wiring",
        board=board,
        devices=[sensor],
        connections=connections,
        show_gpio_diagram=True,
    )


def create_ir_led_example() -> Diagram:
    """Create IR LED ring example diagram."""
    from . import boards
    from .devices import ir_led_ring
    from .model import Connection, Diagram

    board = boards.raspberry_pi_5()
    ir_led = ir_led_ring(12)

    connections = [
        Connection(2, "IR LED Ring (12)", "VCC"),  # 5V to VCC
        Connection(6, "IR LED Ring (12)", "GND"),  # GND to GND
        Connection(7, "IR LED Ring (12)", "CTRL"),  # GPIO4 to CTRL
    ]

    return Diagram(
        title="IR LED Ring Wiring",
        board=board,
        devices=[ir_led],
        connections=connections,
        show_gpio_diagram=True,
    )


def create_i2c_spi_example():
    """Create example with multiple I2C and SPI devices."""
    from . import boards
    from .devices import bh1750_light_sensor, generic_spi_device, simple_led
    from .model import Connection, Diagram

    board = boards.raspberry_pi_5()

    bh1750 = bh1750_light_sensor()
    spi_device = generic_spi_device("OLED Display")
    led = simple_led("Red")

    connections = [
        # BH1750 I2C sensor
        Connection(1, "BH1750", "VCC"),
        Connection(9, "BH1750", "GND"),
        Connection(5, "BH1750", "SCL"),
        Connection(3, "BH1750", "SDA"),
        # SPI OLED display
        Connection(17, "OLED Display", "VCC"),
        Connection(20, "OLED Display", "GND"),
        Connection(23, "OLED Display", "SCLK"),
        Connection(19, "OLED Display", "MOSI"),
        Connection(21, "OLED Display", "MISO"),
        Connection(24, "OLED Display", "CS"),
        # Simple LED
        Connection(11, "Red LED", "+"),  # GPIO17
        Connection(14, "Red LED", "-"),
    ]

    return Diagram(
        title="I2C and SPI Devices Example",
        board=board,
        devices=[bh1750, spi_device, led],
        connections=connections,
        show_gpio_diagram=True,
    )


if __name__ == "__main__":
    sys.exit(main())
