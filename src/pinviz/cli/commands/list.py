"""List command implementation."""

from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from ..config import load_config
from ..context import AppContext
from ..output import BoardInfo, DeviceInfo, ListOutputJson, output_json

console = Console()


def list_command(
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            help="Output machine-readable JSON",
        ),
    ] = False,
) -> None:
    """
    List available board and device templates.

    Shows all available board models, device templates (organized by category),
    and built-in examples.

    [bold]Examples:[/bold]

      pinviz list

      pinviz list --json
    """
    ctx = AppContext(config=load_config())
    log = ctx.logger

    log.info("listing_templates")

    # Collect board information
    boards = [
        BoardInfo(
            name="raspberry_pi_5",
            aliases=["rpi5", "rpi"],
        )
    ]

    # List devices by category
    registry = ctx.registry
    categories = registry.get_categories()

    log.debug("device_categories_found", category_count=len(categories))

    # Collect all device information
    all_devices: list[DeviceInfo] = []
    for category in sorted(categories):
        devices = registry.list_by_category(category)
        for device in devices:
            all_devices.append(
                DeviceInfo(
                    id=device.type_id,
                    category=category,
                    description=device.description,
                    url=device.url,
                )
            )

    # Define examples
    examples = [
        {"name": "bh1750", "description": "BH1750 light sensor connected via I2C"},
        {"name": "ir_led", "description": "IR LED ring connected to GPIO"},
        {"name": "i2c_spi", "description": "Multiple I2C and SPI devices"},
    ]

    # Output results
    if json_output:
        result = ListOutputJson(
            status="success",
            boards=boards,
            devices=all_devices,
            examples=examples,
        )
        output_json(result, console)
    else:
        # Display boards
        console.print("\n[bold cyan]Available Boards:[/bold cyan]")
        console.print("  • raspberry_pi_5 (aliases: [dim]rpi5, rpi[/dim])")
        console.print()

        console.print("[bold cyan]Available Device Templates:[/bold cyan]")

        for category in sorted(categories):
            devices = registry.list_by_category(category)

            # Create a table for this category
            table = Table(
                title=f"{category.title()}",
                show_header=True,
                header_style="bold magenta",
                border_style="dim",
                title_style="bold yellow",
            )
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Description", style="white")
            table.add_column("Documentation", style="blue dim")

            for device in devices:
                doc_link = f"[link={device.url}]🔗 Docs[/link]" if device.url else "[dim]—[/dim]"
                table.add_row(
                    device.type_id,
                    device.description or "[dim]No description[/dim]",
                    doc_link,
                )

            console.print(table)
            console.print()

        # Display examples
        console.print("[bold cyan]Available Examples:[/bold cyan]")

        examples_table = Table(show_header=True, header_style="bold magenta", border_style="dim")
        examples_table.add_column("Name", style="cyan", no_wrap=True)
        examples_table.add_column("Description", style="white")

        for example in examples:
            examples_table.add_row(example["name"], example["description"])

        console.print(examples_table)
        console.print()

    log.info("templates_listed")
