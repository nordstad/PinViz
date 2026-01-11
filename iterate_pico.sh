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
    echo "🎯 Key positions to adjust (single row per edge):"
    echo "   TOP HEADER (pins 1-20 in one row):"
    echo "     - start_x: 30.0 (X position of first pin)"
    echo "     - pin_spacing: 10.0 (horizontal spacing between pins)"
    echo "     - y: 15.0 (fixed Y position for all top pins)"
    echo ""
    echo "   BOTTOM HEADER (pins 21-40 in one row):"
    echo "     - start_x: 30.0 (X position of first pin)"
    echo "     - pin_spacing: 10.0 (horizontal spacing between pins)"
    echo "     - y: 86.0 (fixed Y position for all bottom pins)"
    echo ""

    # Open in default browser on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open out/test_pico.svg
    fi
else
    echo "❌ Error rendering diagram"
    exit 1
fi
