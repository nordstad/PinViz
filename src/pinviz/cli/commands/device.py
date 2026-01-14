"""Device command implementation (add-device wizard)."""

import asyncio

import typer

from ...device_wizard import main as wizard_main
from ..context import AppContext
from ..output import print_error


def add_device_command() -> None:
    """
    Interactive wizard to create a new device configuration.

    Launches an interactive wizard that guides you through creating a new
    device configuration file with prompts for device ID, category, pins,
    and other metadata.

    [bold]Examples:[/bold]

      pinviz add-device
    """
    ctx = AppContext()
    log = ctx.logger

    log.info("device_wizard_started")

    try:
        # Run the async wizard
        exit_code = asyncio.run(wizard_main())
        if exit_code != 0:
            raise typer.Exit(code=exit_code)

    except typer.Exit:
        # Let typer.Exit propagate - it's a normal exit mechanism, not an error
        raise

    except KeyboardInterrupt:
        ctx.console.print("\n")
        print_error("Wizard cancelled by user", ctx.console)
        log.info("device_wizard_cancelled")
        raise typer.Exit(code=1) from None

    except Exception as e:
        log.exception("device_wizard_error", error_type=type(e).__name__, error_message=str(e))
        print_error(str(e), ctx.console)
        raise typer.Exit(code=1) from None
