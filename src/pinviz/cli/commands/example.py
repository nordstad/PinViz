"""Example command implementation."""

from pathlib import Path
from typing import Annotated

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from ... import boards
from ...devices import get_registry
from ...model import Connection, Diagram
from ...render_svg import SVGRenderer
from ...validation import DiagramValidator, ValidationLevel
from ..config import load_config
from ..context import AppContext
from ..output import (
    ExampleOutputJson,
    output_json,
    print_error,
    print_success,
    print_validation_issues,
    print_warning,
)


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
        Connection(7, "IR LED Ring (12)", "CTRL"),  # GPIO4 to CTRL
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


def example_command(
    name: Annotated[
        str,
        typer.Argument(
            help="Example name: bh1750, ir_led, i2c_spi",
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output SVG file path (default: ./out/<name>.svg)",
        ),
    ] = None,
    no_title: Annotated[
        bool,
        typer.Option(
            "--no-title",
            help="Hide the diagram title in the SVG output",
        ),
    ] = False,
    no_board_name: Annotated[
        bool,
        typer.Option(
            "--no-board-name",
            help="Hide the board name in the SVG output",
        ),
    ] = False,
    show_legend: Annotated[
        bool,
        typer.Option(
            "--show-legend",
            help="Show device specifications table below the diagram",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output machine-readable JSON status",
        ),
    ] = False,
) -> None:
    """
    Generate a built-in example diagram.

    [bold]Examples:[/bold]

      pinviz example bh1750

      pinviz example ir_led -o images/ir_led.svg

      pinviz example i2c_spi --show-legend
    """
    ctx = AppContext(config=load_config())
    log = ctx.logger

    # Validate example name
    if name not in ["bh1750", "ir_led", "i2c_spi"]:
        if json_output:
            result = ExampleOutputJson(
                status="error",
                example_name=name,
                output_path=None,
                errors=[f"Unknown example: {name}. Available: bh1750, ir_led, i2c_spi"],
            )
            output_json(result, ctx.console)
        else:
            print_error(f"Unknown example: {name}", ctx.console)
            ctx.console.print("\nAvailable examples: [cyan]bh1750, ir_led, i2c_spi[/cyan]")
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
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=ctx.console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Generating example: {name}...", total=None)

            # Create the example diagram
            if name == "bh1750":
                diagram = create_bh1750_example()
            elif name == "ir_led":
                diagram = create_ir_led_example()
            elif name == "i2c_spi":
                diagram = create_i2c_spi_example()

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
        log.exception(
            "example_generation_failed",
            example_name=name,
            output_path=str(output_path),
            error_type=type(e).__name__,
            error_message=str(e),
        )

        if json_output:
            result = ExampleOutputJson(
                status="error",
                example_name=name,
                output_path=None,
                errors=[str(e)],
            )
            output_json(result, ctx.console)
        else:
            print_error(str(e), ctx.console)

        raise typer.Exit(code=1) from None
