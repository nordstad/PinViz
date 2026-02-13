#!/bin/bash
# Device Spacing Consistency Checker
# Ensures all devices use the standard 10px spacing

echo "=== PinViz Device Spacing Consistency Check ==="
echo ""

ERRORS=0

# Check for non-standard start_y values
echo "Checking start_y values (should be 10.0)..."
NON_STANDARD_START=$(find src/pinviz/device_configs -name "*.json" -exec grep -H "start_y" {} \; | grep -v "10.0")
if [ -n "$NON_STANDARD_START" ]; then
    echo "❌ Found non-standard start_y values:"
    echo "$NON_STANDARD_START"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ All start_y values are 10.0"
fi

echo ""

# Check for non-standard pin_spacing values
echo "Checking pin_spacing values (should be 10.0)..."
NON_STANDARD_SPACING=$(find src/pinviz/device_configs -name "*.json" -exec grep -H "pin_spacing" {} \; | grep -v "10.0")
if [ -n "$NON_STANDARD_SPACING" ]; then
    echo "❌ Found non-standard pin_spacing values:"
    echo "$NON_STANDARD_SPACING"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ All pin_spacing values are 10.0"
fi

echo ""

# Check examples for manual positions with non-10px spacing
echo "Checking example YAML files for consistent 10px spacing..."
EXAMPLE_ERRORS=0
for file in examples/*.yaml; do
    if grep -q "position: {x:" "$file"; then
        # Extract y values and check spacing
        Y_VALUES=$(grep "position: {x:" "$file" | sed 's/.*y: \([0-9]*\).*/\1/' | sort -n)
        if [ -n "$Y_VALUES" ]; then
            PREV=""
            FILE_OK=true
            while read -r Y; do
                if [ -n "$PREV" ]; then
                    DIFF=$((Y - PREV))
                    if [ "$DIFF" -ne 10 ] && [ "$DIFF" -ne 0 ]; then
                        echo "❌ $file: Found ${DIFF}px spacing between pins (should be 10px)"
                        FILE_OK=false
                        EXAMPLE_ERRORS=$((EXAMPLE_ERRORS + 1))
                    fi
                fi
                PREV=$Y
            done <<< "$Y_VALUES"

            if [ "$FILE_OK" = true ]; then
                echo "✅ $file: Consistent 10px spacing"
            fi
        fi
    fi
done

if [ $EXAMPLE_ERRORS -gt 0 ]; then
    ERRORS=$((ERRORS + EXAMPLE_ERRORS))
fi

echo ""
echo "=== Summary ==="
if [ $ERRORS -eq 0 ]; then
    echo "✅ All devices and examples have consistent spacing!"
    exit 0
else
    echo "❌ Found $ERRORS spacing inconsistencies"
    exit 1
fi
