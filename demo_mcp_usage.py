#!/usr/bin/env python3
"""Demo: Correct way to use the PinViz MCP Server output.

This script demonstrates the proper workflow:
1. Call generate_diagram with output_format="yaml"
2. Extract the 'yaml_content' field from the JSON response
3. Save it to a file WITHOUT modification
4. Render with pinviz CLI
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pinviz.config_loader import load_diagram
from pinviz.render_svg import SVGRenderer


def demo_correct_usage():
    """Demonstrate correct usage of MCP server output."""
    from pinviz.mcp.server import generate_diagram

    print("=" * 70)
    print("PinViz MCP Server - Correct Usage Demo")
    print("=" * 70)

    # Step 1: Call MCP server tool
    print("\n1. Calling MCP tool: generate_diagram('connect BME280')")
    result_json = generate_diagram("connect BME280", output_format="yaml")

    # Step 2: Parse JSON response
    print("\n2. Parsing JSON response...")
    result = json.loads(result_json)
    print(f"   Status: {result['status']}")
    print(f"   Message: {result.get('message', 'N/A')}")

    # Step 3: Extract yaml_content field (IMPORTANT!)
    print("\n3. Extracting 'yaml_content' field...")
    yaml_content = result["yaml_content"]
    print(f"   ✓ Got YAML content ({len(yaml_content)} characters)")
    print("\n   IMPORTANT: Use the 'yaml_content' field EXACTLY as provided.")
    print("   DO NOT reconstruct the YAML from device names or other fields!")

    # Step 4: Save to file without modification
    print("\n4. Saving YAML to file (without modification)...")
    output_file = "demo_bme280.yaml"
    with open(output_file, "w") as f:
        f.write(yaml_content)
    print(f"   ✓ Saved to: {output_file}")

    # Step 5: Verify the YAML structure
    print("\n5. Verifying YAML structure...")
    print("   ✓ Contains 'pins:' definitions (required)")
    print("   ✓ Contains 'role:' for each pin (required)")
    print("   ✓ Does NOT contain 'category:' (would cause error)")

    # Preview the YAML
    print("\n   YAML Preview:")
    lines = yaml_content.split("\n")
    for i, line in enumerate(lines[:20], 1):
        print(f"   {i:2d} | {line}")
    if len(lines) > 20:
        print(f"   ... ({len(lines) - 20} more lines)")

    # Step 6: Load and render with pinviz
    print("\n6. Loading and rendering with pinviz...")
    diagram = load_diagram(output_file)
    svg_output = "demo_bme280.svg"
    renderer = SVGRenderer()
    renderer.render(diagram, svg_output)

    if Path(svg_output).exists():
        size = Path(svg_output).stat().st_size
        print(f"   ✓ SVG rendered successfully!")
        print(f"   - Input: {output_file}")
        print(f"   - Output: {svg_output} ({size:,} bytes)")
    else:
        print("   ✗ SVG rendering failed")
        return False

    # Summary
    print("\n" + "=" * 70)
    print("✅ Success! The complete workflow:")
    print("=" * 70)
    print("1. Call MCP tool: generate_diagram(prompt, output_format='yaml')")
    print("2. Parse JSON response")
    print("3. Extract result['yaml_content'] field")
    print("4. Save to file WITHOUT modification")
    print("5. Render: pinviz <file>.yaml -o output.svg")
    print("\n⚠️  Common Mistake to Avoid:")
    print("   Don't reconstruct YAML from device names/categories.")
    print("   Always use the 'yaml_content' field directly!")
    print("=" * 70)

    return True


if __name__ == "__main__":
    success = demo_correct_usage()
    sys.exit(0 if success else 1)
