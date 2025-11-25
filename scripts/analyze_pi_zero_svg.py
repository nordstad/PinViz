#!/usr/bin/env python3
"""
Script to analyze pi_zero.svg and extract GPIO pin positions.

This script parses the Pi Zero SVG file and identifies the GPIO pin positions
by looking for the copper-colored ellipses that represent the 40-pin header.
"""

import xml.etree.ElementTree as ET
from pathlib import Path


def parse_transform(transform_str):
    """Parse SVG transform matrix and return matrix components."""
    if not transform_str or "matrix" not in transform_str:
        return None

    # Extract matrix values: matrix(a, b, c, d, e, f)
    # Transforms point (x,y) to (ax + cy + e, bx + dy + f)
    import re
    match = re.search(r'matrix\(([-\d.]+),([-\d.]+),([-\d.]+),([-\d.]+),([-\d.]+),([-\d.]+)\)', transform_str)
    if match:
        a, b, c, d, e, f = map(float, match.groups())
        return (a, b, c, d, e, f)
    return None


def apply_transform(cx, cy, matrix):
    """Apply transform matrix to a point."""
    if matrix is None:
        return cx, cy
    a, b, c, d, e, f = matrix
    x = a * cx + c * cy + e
    y = b * cx + d * cy + f
    return x, y


def analyze_svg():
    """Analyze the Pi Zero SVG and extract GPIO pin positions."""
    # Path to the Pi Zero SVG
    svg_path = Path(__file__).parent.parent / "src" / "pinviz" / "assets" / "pi_zero.svg"

    if not svg_path.exists():
        print(f"❌ SVG file not found: {svg_path}")
        return

    print(f"📂 Analyzing: {svg_path}")
    print()

    # Parse SVG
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # SVG namespace
    ns = {'svg': 'http://www.w3.org/2000/svg'}

    # Find viewBox
    viewbox = root.get('viewBox')
    print(f"📐 ViewBox: {viewbox}")
    print()

    # Find all ellipses (GPIO pins are ellipses)
    ellipses = []

    # Look for ellipses with copper color stroke (GPIO pins)
    copper_color = "rgb(170,137,100)"

    for g in root.iter('{http://www.w3.org/2000/svg}g'):
        # Get transform from parent group
        transform = g.get('transform', '')
        matrix = parse_transform(transform)

        for ellipse in g.findall('{http://www.w3.org/2000/svg}ellipse'):
            style = ellipse.get('style', '')
            cx = float(ellipse.get('cx', 0))
            cy = float(ellipse.get('cy', 0))

            # Check if this is a GPIO pin (copper colored)
            if copper_color in style:
                # Apply transform
                final_x, final_y = apply_transform(cx, cy, matrix)
                ellipses.append((final_x, final_y))

    print(f"🔍 Found {len(ellipses)} GPIO pin ellipses")
    print()

    if not ellipses:
        print("⚠️  No GPIO pins found. Analyzing all ellipses...")
        # Fallback: show all ellipses
        for g in root.iter('{http://www.w3.org/2000/svg}g'):
            transform = g.get('transform', '')
            matrix = parse_transform(transform)

            for ellipse in g.findall('{http://www.w3.org/2000/svg}ellipse'):
                cx = float(ellipse.get('cx', 0))
                cy = float(ellipse.get('cy', 0))
                final_x, final_y = apply_transform(cx, cy, matrix)
                style = ellipse.get('style', '')[:100]
                print(f"  Ellipse at ({final_x:.2f}, {final_y:.2f}) - style: {style}...")
        return

    # Sort by Y position first, then X (to identify rows and columns)
    sorted_by_y = sorted(ellipses, key=lambda p: (p[1], p[0]))
    sorted_by_x = sorted(ellipses, key=lambda p: (p[0], p[1]))

    print("📍 GPIO Pin Positions (sorted by Y, then X):")
    print()
    print("     X       Y")
    print("  " + "-" * 20)
    for i, (x, y) in enumerate(sorted_by_y, 1):
        print(f"  {x:7.2f} {y:7.2f}  (pin {i}?)")

    print()
    print("📊 Analysis:")
    print()

    # Find unique X positions (should be 2 columns)
    x_positions = sorted(set(round(x, 1) for x, y in ellipses))
    print(f"  Column X positions: {x_positions}")

    # Find unique Y positions (should be 20 rows)
    y_positions = sorted(set(round(y, 1) for x, y in ellipses))
    print(f"  Row Y positions ({len(y_positions)} rows)")

    if len(y_positions) >= 2:
        y_spacing = y_positions[1] - y_positions[0]
        print(f"  Row spacing: {y_spacing:.2f}")

    if len(x_positions) >= 2:
        x_spacing = x_positions[1] - x_positions[0]
        print(f"  Column spacing: {x_spacing:.2f}")

    print()
    print("🎯 Recommended Pin Position Values:")
    print()
    print(f"  left_col_x = {x_positions[0]:.2f}" if len(x_positions) > 0 else "  left_col_x = ???")
    print(f"  right_col_x = {x_positions[1]:.2f}" if len(x_positions) > 1 else "  right_col_x = ???")
    print(f"  start_y = {y_positions[0]:.2f}" if len(y_positions) > 0 else "  start_y = ???")
    print(f"  row_spacing = {y_spacing:.2f}" if len(y_positions) >= 2 else "  row_spacing = ???")

    print()
    print("💡 Note: These values should be used in _create_40_pin_header_pi_zero()")
    print("   and may need fine-tuning after visual testing.")


if __name__ == "__main__":
    analyze_svg()
