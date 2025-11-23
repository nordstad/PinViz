"""PinViz MCP Server - Generate GPIO wiring diagrams from natural language.

This MCP server provides tools to:
- List available devices in the database
- Get detailed device information
- Generate wiring diagrams from natural language prompts (Phase 2)
- Parse device specifications from documentation URLs (Phase 3)
- Add user devices to the database (Phase 3)

Resources:
- device_database: Access to the full device catalog
"""

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .device_manager import Device, DeviceManager, DevicePin

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
        JSON response with diagram data or error information.

        When output_format is 'yaml':
        - The response contains a 'yaml_content' field with the complete PinViz YAML configuration
        - This YAML should be saved to a file (e.g., diagram.yaml) and rendered with:
          pinviz render diagram.yaml -o output.svg
        - DO NOT modify or reconstruct the YAML - use the 'yaml_content' field exactly as provided
        - The YAML includes full device pin definitions required by the pinviz CLI
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
            # Generate YAML-style output with full device definitions
            yaml_output = f"""title: "{diagram_title}"
board: "{parsed.board}"
devices:
"""
            for device_data in devices_data:
                yaml_output += f'  - name: "{device_data["name"]}"\n'
                # Add pins array with full pin definitions
                if "pins" in device_data and device_data["pins"]:
                    yaml_output += "    pins:\n"
                    for pin in device_data["pins"]:
                        yaml_output += f'      - name: "{pin["name"]}"\n'
                        yaml_output += f'        role: "{pin["role"]}"\n'

            yaml_output += "\nconnections:\n"
            for conn in connections:
                yaml_output += f"  - board_pin: {conn['board_pin']}\n"
                yaml_output += f'    device: "{conn["device"]}"\n'
                yaml_output += f'    device_pin: "{conn["device_pin"]}"\n'

            result["yaml_content"] = yaml_output
            result["output"] = yaml_output  # Keep for backward compatibility
            result["message"] = (
                "Complete PinViz YAML configuration generated. "
                "Save the 'yaml_content' field to a file and render with: "
                "pinviz render <file>.yaml -o output.svg"
            )

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


@mcp.tool()
def add_user_device(device_data: dict) -> str:
    """Manually add a device to the user devices database.

    Use this tool to add custom devices. You can ask your LLM to help you
    create the device specification by analyzing datasheets or product pages.

    Args:
        device_data: Device specification dictionary following the schema

    Returns:
        JSON string with result of adding the device
    """
    try:
        # Validate the device data
        from .device_validator import validate_device_entry

        is_valid, errors = validate_device_entry(device_data)

        if not is_valid:
            return json.dumps(
                {
                    "status": "error",
                    "error": "Device validation failed",
                    "validation_errors": errors,
                },
                indent=2,
            )

        # Convert to Device object
        pins = [
            DevicePin(
                name=pin["name"],
                role=pin["role"],
                position=pin["position"],
                description=pin.get("description"),
                optional=pin.get("optional", False),
            )
            for pin in device_data["pins"]
        ]

        device = Device(
            id=device_data["id"],
            name=device_data["name"],
            category=device_data["category"],
            description=device_data["description"],
            pins=pins,
            protocols=device_data["protocols"],
            voltage=device_data["voltage"],
            manufacturer=device_data.get("manufacturer"),
            datasheet_url=device_data.get("datasheet_url"),
            i2c_address=device_data.get("i2c_address"),
            i2c_addresses=device_data.get("i2c_addresses"),
            current_draw=device_data.get("current_draw"),
            dimensions=device_data.get("dimensions"),
            tags=device_data.get("tags"),
            notes=device_data.get("notes"),
            requires_pullup=device_data.get("requires_pullup", False),
        )

        # Add to user database
        device_manager.add_user_device(device)

        return json.dumps(
            {
                "status": "success",
                "message": f"Device '{device.name}' added to user database with ID '{device.id}'",
                "device_id": device.id,
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps(
            {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            },
            indent=2,
        )


@mcp.tool()
def list_user_devices() -> str:
    """List all devices in the user devices database.

    Returns:
        JSON string with list of user devices
    """
    user_devices = device_manager.user_devices

    result = {
        "total": len(user_devices),
        "devices": [
            {
                "id": device.id,
                "name": device.name,
                "category": device.category,
                "description": device.description,
                "protocols": device.protocols,
                "voltage": device.voltage,
            }
            for device in user_devices
        ],
    }

    return json.dumps(result, indent=2)


@mcp.tool()
def remove_user_device(device_id: str) -> str:
    """Remove a device from the user devices database.

    Args:
        device_id: The unique device identifier to remove

    Returns:
        JSON string with result of removal
    """
    success = device_manager.remove_user_device(device_id)

    if success:
        return json.dumps(
            {
                "status": "success",
                "message": f"Device '{device_id}' removed from user database",
            },
            indent=2,
        )
    else:
        return json.dumps(
            {
                "status": "error",
                "error": f"Device '{device_id}' not found in user database",
            },
            indent=2,
        )


def main():
    """Run the MCP server with stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
