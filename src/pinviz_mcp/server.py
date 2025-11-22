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
def generate_diagram(prompt: str, output_format: str = "yaml", title: str | None = None) -> str:
    """Generate a GPIO wiring diagram from a natural language prompt.

    This tool uses Phase 2 implementation with:
    - Natural language parsing (regex + LLM fallback)
    - Intelligent pin assignment (I2C sharing, SPI chip selects, power distribution)
    - Automatic wire color assignment
    - Conflict detection and warnings

    Args:
        prompt: Natural language description (e.g., "connect BME280 and LED")
        output_format: Output format - 'yaml', 'json', or 'summary' (default: yaml)
        title: Optional diagram title (auto-generated if not provided)

    Returns:
        JSON response with diagram data or error information
    """
    from .parser import PromptParser
    from .pin_assignment import PinAssigner

    try:
        # Step 1: Parse natural language prompt
        parser = PromptParser(use_llm=False)
        parsed = parser.parse(prompt)

        if not parsed.devices:
            return json.dumps(
                {
                    "status": "error",
                    "error": "No devices found in prompt",
                    "prompt": prompt,
                    "suggestion": "Try: 'connect BME280' or 'BME280 and LED'",
                },
                indent=2,
            )

        # Step 2: Look up devices in database
        devices_data = []
        not_found = []

        for device_name in parsed.devices:
            # Try fuzzy matching
            device = device_manager.get_device_by_name(device_name, fuzzy=True)
            if device:
                devices_data.append(device.to_dict())
            else:
                not_found.append(device_name)

        if not devices_data:
            return json.dumps(
                {
                    "status": "error",
                    "error": "No matching devices found in database",
                    "requested": parsed.devices,
                    "suggestion": "Use list_devices tool to see available devices",
                },
                indent=2,
            )

        # Step 3: Assign pins intelligently
        pin_assigner = PinAssigner()
        assignments, warnings = pin_assigner.assign_pins(devices_data)

        # Step 4: Generate diagram output
        diagram_title = title or (
            f"{', '.join([d['name'] for d in devices_data])} Wiring"
            if len(devices_data) <= 3
            else "Multi-Device Wiring Diagram"
        )

        # Generate connections list for output
        connections = [
            {
                "board_pin": a.board_pin_number,
                "device": a.device_name,
                "device_pin": a.device_pin_name,
                "role": a.pin_role.value,
            }
            for a in assignments
        ]

        # Prepare result based on format
        result = {
            "status": "success",
            "title": diagram_title,
            "board": parsed.board,
            "devices": [d["name"] for d in devices_data],
            "connections": len(assignments),
            "parsing_method": parsed.parsing_method,
            "confidence": parsed.confidence,
        }

        if warnings:
            result["warnings"] = warnings

        if not_found:
            result["not_found"] = not_found

        if output_format == "yaml":
            # Generate YAML-style output
            yaml_output = f"""title: "{diagram_title}"
board: "{parsed.board}"
devices:
"""
            for device_data in devices_data:
                yaml_output += f'  - name: "{device_data["name"]}"\n'
                yaml_output += f'    category: "{device_data["category"]}"\n'

            yaml_output += "\nconnections:\n"
            for conn in connections:
                yaml_output += f"  - board_pin: {conn['board_pin']}\n"
                yaml_output += f'    device: "{conn["device"]}"\n'
                yaml_output += f'    device_pin: "{conn["device_pin"]}"\n'
                yaml_output += f'    role: "{conn["role"]}"\n'

            result["output"] = yaml_output

        elif output_format == "json":
            result["details"] = {
                "devices": devices_data,
                "connections": connections,
            }

        else:  # summary format
            result["summary"] = (
                f"Generated diagram with {len(devices_data)} device(s) "
                f"and {len(assignments)} connection(s)"
            )

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps(
            {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "prompt": prompt,
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
