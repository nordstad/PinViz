#!/usr/bin/env python3
"""Test URL-based device discovery (Phase 3 feature).

This script demonstrates the complete workflow:
1. Parse device specifications from a URL
2. Validate the extracted specifications
3. Save to user database
4. Generate diagram using the parsed device
5. Render to SVG

Requirements:
- ANTHROPIC_API_KEY environment variable must be set
- Internet connection (to fetch URL content)
"""

import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_url_discovery(url: str, save_to_db: bool = True):
    """Test URL-based device discovery."""
    from pinviz.mcp.connection_builder import ConnectionBuilder
    from pinviz.mcp.device_manager import DeviceManager
    from pinviz.mcp.pin_assignment import PinAssigner
    from pinviz.mcp.server import parse_device_from_url
    from pinviz.render_svg import SVGRenderer

    print("=" * 70)
    print("PinViz MCP Server - URL-Based Device Discovery Test")
    print("=" * 70)

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n❌ ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("\nTo use URL-based device discovery, you need a Claude API key:")
        print("  1. Get an API key from: https://console.anthropic.com/")
        print("  2. Set it in your environment:")
        print("     export ANTHROPIC_API_KEY='your-api-key-here'")
        print("\nAlternatively, test with devices already in the database:")
        print("  python test_mcp_local.py")
        return False

    print(f"\n✓ ANTHROPIC_API_KEY found ({len(api_key)} characters)")
    print("\n1. Parsing device from URL...")
    print(f"   URL: {url}")

    # Step 1: Parse device from URL
    try:
        result_json = parse_device_from_url(url, save_to_user_db=save_to_db)
        result = json.loads(result_json)

        if result["status"] == "error":
            print(f"\n❌ Error parsing URL: {result['error']}")
            return False

        print(f"   ✓ Status: {result['status']}")

        # Extract device info
        device = result["device"]
        extraction = result["extraction"]
        validation = result["validation"]

        print("\n2. Extracted Device Information:")
        print(f"   Name: {device['name']}")
        print(f"   Category: {device['category']}")
        print(f"   Description: {device['description'][:80]}...")
        print(f"   Protocols: {', '.join(device['protocols'])}")
        print(f"   Voltage: {device['voltage']}")
        print(f"   Pins: {len(device['pins'])} pins")

        # Show pin details
        print("\n   Pin Configuration:")
        for pin in device["pins"][:6]:  # Show first 6 pins
            print(f"     - {pin['name']:10s} ({pin['role']})")
        if len(device["pins"]) > 6:
            print(f"     ... and {len(device['pins']) - 6} more pins")

        print("\n3. Extraction Metadata:")
        print(f"   Confidence: {extraction['confidence']:.0%}")
        print(f"   Method: {extraction['method']}")
        if extraction.get("missing_fields"):
            print(f"   Missing fields: {', '.join(extraction['missing_fields'])}")

        print("\n4. Validation Results:")
        print(f"   Valid: {'✓ Yes' if validation['is_valid'] else '✗ No'}")
        if validation["errors"]:
            print("   Errors:")
            for error in validation["errors"]:
                print(f"     - {error}")

        if not validation["is_valid"]:
            print("\n⚠️  Device has validation errors. Fix before using.")
            return False

        # Step 2: Generate diagram using the device
        if save_to_db:
            print("\n5. Device saved to user database")
            print(f"   Device ID: {device['id']}")

            # Now try to generate a diagram
            print("\n6. Generating diagram with the new device...")
            device_name = device["name"]

            # Initialize components
            dm = DeviceManager()
            assigner = PinAssigner()
            builder = ConnectionBuilder()
            renderer = SVGRenderer()

            # Get the device from user database
            user_device = dm.get_device_by_id(device["id"])
            if not user_device:
                print("   ✗ Device not found in user database")
                return False

            print(f"   ✓ Found device in database: {user_device.name}")

            # Build diagram
            device_spec = user_device.to_dict()
            assignments, warnings = assigner.assign_pins([device_spec])

            print(f"   ✓ Pin assignments: {len(assignments)} connections")
            if warnings:
                print(f"   Warnings: {warnings}")

            # Build and render
            diagram = builder.build_diagram(
                assignments=assignments,
                devices_data=[device_spec],
                title=f"{device_name} Wiring Diagram",
                board_name="raspberry_pi_5",
            )

            output_file = f"url_test_{device['id']}.svg"
            renderer.render(diagram, output_file)

            if Path(output_file).exists():
                size = Path(output_file).stat().st_size
                print("\n7. Diagram Generated:")
                print(f"   ✓ File: {output_file}")
                print(f"   ✓ Size: {size:,} bytes")
            else:
                print("\n   ✗ Failed to generate diagram")
                return False

        print("\n" + "=" * 70)
        print("✅ URL-based device discovery successful!")
        print("=" * 70)
        print("\nWorkflow Summary:")
        print("1. Fetched content from URL")
        print("2. Extracted device specs using Claude API")
        print("3. Validated device specifications")
        if save_to_db:
            print("4. Saved to user database")
            print("5. Generated diagram with pin assignments")
            print("6. Rendered to SVG")
        print("\nThe device is now available for future diagrams!")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run URL discovery test."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test URL-based device discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with peppe8o.com tutorial
  python test_url_discovery.py https://peppe8o.com/ssd1306-raspberry-pi-oled-display/

  # Test with Adafruit product page
  python test_url_discovery.py https://www.adafruit.com/product/938

  # Parse without saving to database
  python test_url_discovery.py --no-save https://peppe8o.com/ssd1306-raspberry-pi-oled-display/

Supported domains:
  - adafruit.com
  - sparkfun.com
  - waveshare.com
  - pimoroni.com
  - raspberrypi.com
  - seeedstudio.com
  - peppe8o.com
        """,
    )

    parser.add_argument("url", help="URL to device documentation")
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save device to user database",
    )

    args = parser.parse_args()

    success = test_url_discovery(args.url, save_to_db=not args.no_save)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
