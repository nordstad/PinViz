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
    echo "🎯 Current pin positions (single row per edge):"
    echo "   TOP HEADER (pins 20-1, left to right - REVERSED):"
    echo "     - start_x: 8.0"
    echo "     - pin_spacing: 12.0"
    echo "     - y: 6.5"
    echo ""
    echo "   BOTTOM HEADER (pins 21-40, left to right - NORMAL):"
    echo "     - start_x: 8.0"
    echo "     - pin_spacing: 12.0"
    echo "     - y: 94.0"
    echo ""
 
else
    echo "❌ Error rendering diagram"
    exit 1
fi
