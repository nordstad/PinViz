#!/usr/bin/env python3
"""Test script to verify YAML generation from MCP server is correct."""

import json
import sys
import tempfile
from pathlib import Path

# Add src to path so we can import pinviz
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pinviz.config_loader import load_diagram
from pinviz.render_svg import SVGRenderer


def test_yaml_generation():
    """Test that generate_diagram produces valid YAML that pinviz can render."""
    from pinviz.mcp.server import generate_diagram

    print("=" * 70)
    print("Testing YAML Generation from MCP Server")
    print("=" * 70)

    # Test 1: Generate diagram for BME280
    print("\n1. Generating diagram for BME280...")
    result_json = generate_diagram("connect BME280", output_format="yaml")
    result = json.loads(result_json)

    # Check response structure
    print(f"   Status: {result.get('status')}")
    assert result["status"] == "success", f"Expected success, got {result['status']}"

    # Check yaml_content field exists
    assert "yaml_content" in result, "Missing 'yaml_content' field"
    print("   ✓ yaml_content field present")

    # Extract YAML content
    yaml_content = result["yaml_content"]
    print(f"   ✓ YAML length: {len(yaml_content)} characters")

    # Verify YAML has full pin definitions (not just category)
    assert "pins:" in yaml_content, "YAML missing pin definitions"
    assert "role:" in yaml_content, "YAML missing pin roles"
    assert "category:" not in yaml_content, "YAML should not contain 'category' field"
    print("   ✓ YAML contains full pin definitions")

    # Print first few lines of YAML
    yaml_lines = yaml_content.split("\n")[:15]
    print("\n   Generated YAML (first 15 lines):")
    for line in yaml_lines:
        print(f"      {line}")

    # Test 2: Save YAML to file and load with pinviz
    print("\n2. Testing YAML can be loaded by pinviz...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        yaml_file = f.name

    try:
        # Load diagram using pinviz config_loader
        diagram = load_diagram(yaml_file)
        print("   ✓ Diagram loaded successfully")
        print(f"   - Title: {diagram.title}")
        print(f"   - Devices: {len(diagram.devices)}")
        print(f"   - Connections: {len(diagram.connections)}")

        # Verify device has pins
        assert len(diagram.devices) > 0, "No devices in diagram"
        device = diagram.devices[0]
        assert len(device.pins) > 0, "Device has no pins"
        print(f"   ✓ Device '{device.name}' has {len(device.pins)} pins")

        # Test 3: Render to SVG
        print("\n3. Testing SVG rendering...")
        svg_file = yaml_file.replace(".yaml", ".svg")
        renderer = SVGRenderer()
        renderer.render(diagram, svg_file)

        if Path(svg_file).exists():
            size = Path(svg_file).stat().st_size
            print("   ✓ SVG rendered successfully")
            print(f"   - File: {svg_file}")
            print(f"   - Size: {size:,} bytes")
        else:
            print("   ✗ SVG file not created")
            return False

        # Cleanup
        Path(yaml_file).unlink()
        Path(svg_file).unlink()

    except Exception as e:
        print(f"   ✗ Error loading/rendering diagram: {e}")
        import traceback

        traceback.print_exc()
        Path(yaml_file).unlink(missing_ok=True)
        return False

    print("\n" + "=" * 70)
    print("✅ All YAML generation tests passed!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = test_yaml_generation()
    sys.exit(0 if success else 1)
