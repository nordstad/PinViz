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
    echo "🎯 Key positions to adjust:"
    echo "   - left_header.left_col_x  (currently: 20.0)"
    echo "   - left_header.right_col_x (currently: 32.0)"
    echo "   - left_header.start_y     (currently: 15.0)"
    echo "   - right_header.left_col_x  (currently: 217.0)"
    echo "   - right_header.right_col_x (currently: 229.0)"
    echo "   - right_header.start_y     (currently: 15.0)"
    echo ""

    # Open in default browser on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open out/test_pico.svg
    fi
else
    echo "❌ Error rendering diagram"
    exit 1
fi
