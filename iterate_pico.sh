#!/bin/bash
# Quick iteration script for Pico pin position tuning
# Usage: ./iterate_pico.sh

echo "🔧 Rendering Pico test diagram..."
uv run pinviz render test_pico.yaml -o out/test_pico.svg

if [ $? -eq 0 ]; then
    echo "✅ Diagram generated: out/test_pico.svg"
    echo ""
    echo "📋 To iterate:"
    echo "   1. Open out/test_pico.svg in a browser"
    echo "   2. Edit pin positions in: src/pinviz/board_configs/raspberry_pi_pico.json"
    echo "   3. Run: ./iterate_pico.sh again"
    echo ""
    echo "🎯 Key positions to adjust (horizontal pin layout):"
    echo "   TOP HEADER (pins 1-20):"
    echo "     - start_x: 30.0 (X position of first pin)"
    echo "     - column_spacing: 20.0 (horizontal spacing between pins)"
    echo "     - top_row_y: 10.0 (Y position of odd pins: 1,3,5...19)"
    echo "     - bottom_row_y: 22.0 (Y position of even pins: 2,4,6...20)"
    echo ""
    echo "   BOTTOM HEADER (pins 21-40):"
    echo "     - start_x: 30.0 (X position of first pin)"
    echo "     - column_spacing: 20.0 (horizontal spacing between pins)"
    echo "     - top_row_y: 79.0 (Y position of odd pins: 21,23,25...39)"
    echo "     - bottom_row_y: 91.0 (Y position of even pins: 22,24,26...40)"
    echo ""

    # Open in default browser on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open out/test_pico.svg
    fi
else
    echo "❌ Error rendering diagram"
    exit 1
fi
