"""PinViz MCP Server - Generate GPIO wiring diagrams from natural language.

This MCP server provides tools to:
- List available devices in the database
- Get detailed device information
- Generate wiring diagrams from natural language prompts (Phase 2)

Resources:
- device_database: Access to the full device catalog
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .device_manager import DeviceManager

# Initialize FastMCP server
mcp = FastMCP("PinViz Diagram Generator")

# Initialize device manager
device_manager = DeviceManager()


@mcp.tool()
def list_devices(
    category: str | None = None,
    protocol: str | None = None,
    query: str | None = None,
) -> str:
    """List available devices in the database with optional filtering.

    Args:
        category: Filter by category (display, sensor, hat, component, actuator, breakout)
        protocol: Filter by protocol (I2C, SPI, UART, GPIO, 1-Wire, PWM)
        query: Search query for device name, description, or tags

    Returns:
        JSON string with list of matching devices
    """
    devices = device_manager.search_devices(
        query=query,
        category=category,
        protocol=protocol,
    )

    result = {
        "total": len(devices),
        "devices": [
            {
                "id": device.id,
                "name": device.name,
                "category": device.category,
                "description": device.description,
                "protocols": device.protocols,
                "voltage": device.voltage,
                "tags": device.tags or [],
            }
            for device in devices
        ],
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def get_device_info(device_id: str) -> str:
    """Get detailed information about a specific device.

    Args:
        device_id: The unique device identifier or name (supports fuzzy matching)

    Returns:
        JSON string with complete device specifications
    """
    # Try by ID first
    device = device_manager.get_device_by_id(device_id)

    # If not found by ID, try fuzzy name matching
    if device is None:
        device = device_manager.get_device_by_name(device_id, fuzzy=True)

    if device is None:
        return json.dumps({"error": f"Device '{device_id}' not found"})

    return json.dumps(device.to_dict(), indent=2)


@mcp.tool()
def search_devices_by_tags(tags: list[str]) -> str:
    """Search for devices by tags.

    Args:
        tags: List of tags to search for (all must match)

    Returns:
        JSON string with list of matching devices
    """
    devices = device_manager.search_devices(tags=tags)

    result = {
        "total": len(devices),
        "tags": tags,
        "devices": [
            {
                "id": device.id,
                "name": device.name,
                "category": device.category,
                "tags": device.tags or [],
            }
            for device in devices
        ],
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def get_database_summary() -> str:
    """Get statistics and summary of the device database.

    Returns:
        JSON string with database statistics
    """
    summary = device_manager.get_summary()
    return json.dumps(summary, indent=2)


@mcp.tool()
def generate_diagram(prompt: str, output_format: str = "yaml") -> str:
    """Generate a GPIO wiring diagram from a natural language prompt.

    NOTE: This is a Phase 1 placeholder. Full implementation comes in Phase 2.

    Args:
        prompt: Natural language description of the wiring (e.g., "connect BH1750 sensor")
        output_format: Output format - 'yaml' or 'svg' (default: yaml)

    Returns:
        YAML configuration or SVG diagram as string
    """
    return json.dumps(
        {
            "status": "not_implemented",
            "message": "Diagram generation will be implemented in Phase 2",
            "prompt": prompt,
            "output_format": output_format,
            "note": (
                "Phase 2 will implement natural language parsing, "
                "pin assignment, and diagram generation"
            ),
        },
        indent=2,
    )


@mcp.resource("device://database")
def get_device_database() -> str:
    """Expose the complete device database as a resource.

    Returns:
        JSON string with all devices in the database
    """
    database_path = Path(__file__).parent / "devices" / "database.json"
    with open(database_path) as f:
        return f.read()


@mcp.resource("device://schema")
def get_device_schema() -> str:
    """Expose the device database JSON schema.

    Returns:
        JSON schema for device entries
    """
    schema_path = Path(__file__).parent / "devices" / "schema.json"
    with open(schema_path) as f:
        return f.read()


@mcp.resource("device://categories")
def get_categories() -> str:
    """Get list of all device categories.

    Returns:
        JSON list of category names
    """
    categories = device_manager.list_categories()
    return json.dumps({"categories": categories}, indent=2)


@mcp.resource("device://protocols")
def get_protocols() -> str:
    """Get list of all supported protocols.

    Returns:
        JSON list of protocol names
    """
    protocols = device_manager.list_protocols()
    return json.dumps({"protocols": protocols}, indent=2)


def main():
    """Run the MCP server with stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
