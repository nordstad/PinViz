"""Example command implementation."""

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from ... import boards
from ...devices import get_registry
from ...model import Connection, Diagram
from ...render_svg import SVGRenderer
from ...validation import DiagramValidator, ValidationLevel
from ..context import AppContext
from ..decorators import handle_command_exception, progress_indicator
from ..output import (
    ExampleOutputJson,
    output_json,
    print_error,
    print_success,
    print_validation_issues,
    print_warning,
)
from ..types import JsonOption, NoBoardNameOption, NoTitleOption, OutputOption, ShowLegendOption


def create_bh1750_example() -> Diagram:
    """Create BH1750 example diagram."""
    board = boards.raspberry_pi_5()
    registry = get_registry()
    sensor = registry.create("bh1750")

    connections = [
        Connection(1, "BH1750 Light Sensor", "VCC"),  # 3V3 to VCC
        Connection(6, "BH1750 Light Sensor", "GND"),  # GND to GND
        Connection(5, "BH1750 Light Sensor", "SCL"),  # GPIO3/SCL to SCL
        Connection(3, "BH1750 Light Sensor", "SDA"),  # GPIO2/SDA to SDA
    ]

    return Diagram(
        title="BH1750 Light Sensor Wiring",
        board=board,
        devices=[sensor],
        connections=connections,
    )


def create_ir_led_example() -> Diagram:
    """Create IR LED ring example diagram."""
    board = boards.raspberry_pi_5()
    registry = get_registry()
    ir_led = registry.create("ir_led_ring", num_leds=12)

    connections = [
        Connection(2, "IR LED Ring (12)", "VCC"),  # 5V to VCC
        Connection(6, "IR LED Ring (12)", "GND"),  # GND to GND
        Connection(7, "IR LED Ring (12)", "EN"),  # GPIO4 to EN
    ]

    return Diagram(
        title="IR LED Ring Wiring",
        board=board,
        devices=[ir_led],
        connections=connections,
    )


def create_i2c_spi_example() -> Diagram:
    """Create example with multiple I2C and SPI devices."""
    board = boards.raspberry_pi_5()
    registry = get_registry()

    bh1750 = registry.create("bh1750")
    spi_device = registry.create("spi_device", name="OLED Display")
    led = registry.create("led", color_name="Red")

    connections = [
        # BH1750 I2C sensor
        Connection(1, "BH1750 Light Sensor", "VCC"),
        Connection(9, "BH1750 Light Sensor", "GND"),
        Connection(5, "BH1750 Light Sensor", "SCL"),
        Connection(3, "BH1750 Light Sensor", "SDA"),
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
    )


# Example registry: maps example names to factory functions
EXAMPLE_REGISTRY: dict[str, Callable[[], Diagram]] = {
    "bh1750": create_bh1750_example,
    "ir_led": create_ir_led_example,
    "i2c_spi": create_i2c_spi_example,
}


def get_available_examples() -> list[str]:
    """Get list of available example names.

    Returns:
        Sorted list of example names
    """
    return sorted(EXAMPLE_REGISTRY.keys())


def example_command(
    name: Annotated[
        str,
        typer.Argument(
            help="Example name: bh1750, ir_led, i2c_spi",
        ),
    ],
    output: OutputOption = None,
    no_title: NoTitleOption = False,
    no_board_name: NoBoardNameOption = False,
    show_legend: ShowLegendOption = False,
    json_output: JsonOption = False,
) -> None:
    """
    Generate a built-in example diagram.

    [bold]Examples:[/bold]

      pinviz example bh1750

      pinviz example ir_led -o images/ir_led.svg

      pinviz example i2c_spi --show-legend
    """
    ctx = AppContext()
    log = ctx.logger

    # Validate example name
    available = get_available_examples()
    if name not in EXAMPLE_REGISTRY:
        available_str = ", ".join(available)
        if json_output:
            result = ExampleOutputJson(
                status="error",
                example_name=name,
                output_path=None,
                errors=[f"Unknown example: {name}. Available: {available_str}"],
            )
            output_json(result, ctx.console)
        else:
            print_error(f"Unknown example: {name}", ctx.console)
            ctx.console.print(f"\nAvailable examples: [cyan]{available_str}[/cyan]")
        raise typer.Exit(code=1)

    # Determine output path
    if output:
        output_path = output
    else:
        output_dir = Path("./out")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{name}.svg"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with progress_indicator(ctx.console, "") as progress:
            task = progress.add_task(f"Generating example: {name}...", total=None)

            # Create the example diagram using the registry
            example_factory = EXAMPLE_REGISTRY[name]
            diagram = example_factory()

            log.debug(
                "example_diagram_created",
                device_count=len(diagram.devices),
                connection_count=len(diagram.connections),
            )

            # Apply visibility flags
            if no_title:
                diagram.show_title = False
            if no_board_name:
                diagram.show_board_name = False
            if show_legend:
                diagram.show_legend = True

            # Validate diagram before rendering
            validator = DiagramValidator()
            issues = validator.validate(diagram)

            if issues:
                errors = [i for i in issues if i.level == ValidationLevel.ERROR]
                warnings = [i for i in issues if i.level == ValidationLevel.WARNING]

                log.info(
                    "validation_completed",
                    total_issues=len(issues),
                    errors=len(errors),
                    warnings=len(warnings),
                )

                # Show validation issues
                if errors or warnings:
                    progress.stop()
                    print_validation_issues(issues, ctx.console)

                # Fail on errors
                if errors:
                    log.error("example_validation_failed", error_count=len(errors))
                    print_error(
                        f"Found {len(errors)} error(s). Cannot generate example.", ctx.console
                    )
                    raise typer.Exit(code=1)

                if warnings:
                    log.warning("example_validation_warnings", warning_count=len(warnings))
                    print_warning(
                        f"Found {len(warnings)} warning(s). Review the example carefully.",
                        ctx.console,
                    )
                    ctx.console.print()
                    progress.start()

            # Render
            renderer = SVGRenderer()
            renderer.render(diagram, output_path)
            progress.update(task, completed=True)

        if json_output:
            result = ExampleOutputJson(
                status="success",
                example_name=name,
                output_path=str(output_path),
            )
            output_json(result, ctx.console)
        else:
            print_success(f"Example generated: {output_path}", ctx.console)

        log.info("example_generated", example_name=name, output_path=str(output_path))

    except typer.Exit:
        raise
    except Exception as e:
        handle_command_exception(
            e,
            "example_generation",
            ctx.console,
            log,
            json_output,
            lambda msg: ExampleOutputJson(
                status="error",
                example_name=name,
                output_path=None,
                errors=[msg],
            ),
        )
