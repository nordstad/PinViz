"""Command-line interface for pinviz."""

import argparse
import sys
from pathlib import Path
from typing import Any

from rich_argparse import RichHelpFormatter

from .config_loader import load_diagram
from .model import Diagram
from .render_svg import SVGRenderer


class CustomHelpFormatter(RichHelpFormatter):
    """Custom formatter that preserves epilog formatting."""

    # Class variable to store the original epilog
    original_epilog = None

    def format_help(self):
        """Override to handle epilog separately."""
        # Get the normal formatted help
        help_text = super().format_help()

        # If there's an epilog that got wrapped, replace it with the original
        if CustomHelpFormatter.original_epilog and "Examples:" in help_text:
            # Split at "Examples:" and replace everything after
            parts = help_text.split("Examples:", 1)
            if len(parts) == 2:
                # Add back our properly formatted epilog
                help_text = parts[0] + CustomHelpFormatter.original_epilog

        return help_text


# Get version from package metadata
try:
    from importlib.metadata import version

    __version__ = version("pinviz")
except Exception:
    __version__ = "unknown"


def main() -> int:
    """Main CLI entry point."""

    # Define custom epilog with examples
    # Using a more compact format that works better with formatters
    epilog = "\n".join(
        [
            "Examples:",
            "  pinviz render diagram.yaml                     # Generate diagram from YAML config",
            "  pinviz render diagram.yaml -o out/wiring.svg   # Specify output path",
            "  pinviz example bh1750                          # Use a built-in example",
            "  pinviz list                                     # List available templates",
            "",
            "For more information, visit: https://github.com/nordstad/PinViz",
        ]
    )

    # Store epilog in formatter class for later use
    CustomHelpFormatter.original_epilog = epilog

    parser = argparse.ArgumentParser(
        prog="pinviz",
        description="Generate Raspberry Pi GPIO connection diagrams",
        formatter_class=CustomHelpFormatter,
        epilog=epilog,
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="Commands",
        metavar="COMMAND",
        required=True,
    )

    # Main render command
    render_parser = subparsers.add_parser(
        "render",
        help="Render a diagram from a configuration file",
        description="Render a diagram from a YAML or JSON configuration file",
    )
    render_parser.add_argument(
        "config",
        metavar="CONFIG_FILE",
        help="Path to YAML or JSON configuration file",
    )
    render_parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        help="Output SVG file path (default: <config>.svg)",
    )
    gpio_group = render_parser.add_mutually_exclusive_group()
    gpio_group.add_argument(
        "--gpio",
        action="store_true",
        dest="show_gpio",
        help="Show GPIO pin reference diagram",
    )
    gpio_group.add_argument(
        "--no-gpio",
        action="store_false",
        dest="show_gpio",
        help="Hide GPIO pin reference diagram (default: use config file setting)",
    )
    render_parser.set_defaults(show_gpio=None)  # None means use config file value

    # Example command
    example_parser = subparsers.add_parser(
        "example",
        help="Generate a built-in example diagram",
        description="Generate one of the built-in example diagrams",
    )
    example_parser.add_argument(
        "name",
        metavar="NAME",
        choices=["bh1750", "ir_led", "i2c_spi"],
        help="Example name: bh1750, ir_led, i2c_spi",
    )
    example_parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        help="Output SVG file path (default: ./out/<name>.svg)",
    )
    gpio_group = example_parser.add_mutually_exclusive_group()
    gpio_group.add_argument(
        "--gpio",
        action="store_true",
        dest="show_gpio",
        help="Show GPIO pin reference diagram",
    )
    gpio_group.add_argument(
        "--no-gpio",
        action="store_false",
        dest="show_gpio",
        help="Hide GPIO pin reference diagram (default: show)",
    )
    example_parser.set_defaults(show_gpio=True)  # Examples default to showing GPIO

    # List command
    subparsers.add_parser(
        "list",
        help="List available board and device templates",
        description="List all available board models, device templates, and examples",
    )

    args = parser.parse_args()

    # Handle commands
    if args.command == "render":
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

        # Override show_gpio_diagram if CLI flag is specified
        if hasattr(args, "show_gpio") and args.show_gpio is not None:
            from dataclasses import replace

            diagram = replace(diagram, show_gpio_diagram=args.show_gpio)

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

        # Override show_gpio_diagram if CLI flag is explicitly specified
        if hasattr(args, "show_gpio"):
            from dataclasses import replace

            diagram = replace(diagram, show_gpio_diagram=args.show_gpio)

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
    print("  - raspberry_pi_5 (aliases: rpi5, rpi)")
    print("  - raspberry_pi_zero_2w (aliases: raspberry_pi_zero, pizero, zero2w, zero, rpizero)")
    print()

    # List devices by category
    registry = get_registry()
    categories = registry.get_categories()

    print("Available Device Templates:")
    for category in categories:
        devices = registry.list_by_category(category)
        print(f"\n  {category.title()}:")
        for device in devices:
            if device.url:
                print(f"    - {device.type_id}: {device.description}")
                print(f"      📖 {device.url}")
            else:
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
