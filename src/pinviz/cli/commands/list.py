"""List command implementation."""

from rich.console import Console
from rich.table import Table

from ..config import load_config
from ..context import AppContext

console = Console()


def list_command() -> None:
    """
    List available board and device templates.

    Shows all available board models, device templates (organized by category),
    and built-in examples.

    [bold]Examples:[/bold]

      pinviz list
    """
    ctx = AppContext(config=load_config())
    log = ctx.logger

    log.info("listing_templates")

    # Display boards
    console.print("\n[bold cyan]Available Boards:[/bold cyan]")
    console.print("  • raspberry_pi_5 (aliases: [dim]rpi5, rpi[/dim])")
    console.print()

    # List devices by category
    registry = ctx.registry
    categories = registry.get_categories()

    log.debug("device_categories_found", category_count=len(categories))

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

    examples_table.add_row("bh1750", "BH1750 light sensor connected via I2C")
    examples_table.add_row("ir_led", "IR LED ring connected to GPIO")
    examples_table.add_row("i2c_spi", "Multiple I2C and SPI devices")

    console.print(examples_table)
    console.print()

    log.info("templates_listed")
