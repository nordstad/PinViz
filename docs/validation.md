# Validation

PinViz includes structural validation to catch common wiring mistakes before
diagram generation. This helps prevent hardware damage and troubleshooting
issues.

## ⚠️ DISCLAIMER

**This validation is provided as a convenience tool to catch common mistakes.
It is NOT a substitute for proper electrical engineering review and does not
guarantee the safety or correctness of your wiring.**

Users are solely responsible for verifying their wiring against component
datasheets, electrical specifications, and safety standards. Always test your
circuits carefully and consult with qualified professionals when needed. The
authors and contributors of this software assume no liability for any hardware
damage, personal injury, or other consequences resulting from the use of this
validation tool.

## Usage

### Validate Command

Use the `pinviz validate` command to check your configuration for errors:

```bash
pinviz validate my-diagram.yaml
```

Example output:

```text
Validating configuration: my-diagram.yaml

⚠️  Error: Pin 11 (GPIO17) used by multiple devices: LED1.+, LED2.+
⚠️  Warning: I2C address conflict at 0x23: BH1750-1, BH1750-2 (default address)

Found 1 error(s), 1 warning(s)
```

### Strict Mode

Use `--strict` to treat warnings as errors:

```bash
pinviz validate my-diagram.yaml --strict
```

### Automatic Validation During Render

The `render` command automatically validates your diagram and displays
warnings:

```bash
pinviz render my-diagram.yaml -o output.svg
```

If errors are found, rendering will be blocked:

```text
Loading configuration from my-diagram.yaml...

Validation Issues:
  ⚠️  Error: Pin 11 (GPIO17) used by multiple devices: LED1.+, LED2.+

❌ Found 1 error(s). Cannot generate diagram.
```

## Validation Checks

### 1. Duplicate GPIO Pin Detection

**Error:** Multiple devices connected to the same GPIO pin.

```yaml
# ❌ Error: Both LEDs on GPIO17
connections:
  - board_pin: 11  # GPIO17
    device: "LED1"
    device_pin: "+"
  - board_pin: 11  # GPIO17 - duplicate!
    device: "LED2"
    device_pin: "+"
```

**Note:** Power and ground pins can be safely shared:

```yaml
# ✅ OK: Multiple devices sharing 3.3V and GND
connections:
  - board_pin: 1   # 3.3V
    device: "Sensor1"
    device_pin: "VCC"
  - board_pin: 1   # 3.3V - shared OK
    device: "Sensor2"
    device_pin: "VCC"
```

### 2. I2C Address Conflicts

**Warning:** Multiple I2C devices with the same default address on the same
bus.

```yaml
# ⚠️  Warning: Both BH1750 sensors use address 0x23
devices:
  - type: "bh1750"
    name: "Light Sensor 1"
  - type: "bh1750"
    name: "Light Sensor 2"

connections:
  # Both connected to same I2C bus
  - board_pin: 3
    device: "Light Sensor 1"
    device_pin: "SDA"
  - board_pin: 3
    device: "Light Sensor 2"
    device_pin: "SDA"
```

**Fix:** Use the ADDR pin to change one sensor's address, or use separate
I2C buses.

### 3. Voltage Compatibility

**Error:** 5V board pin connected to 3.3V device pin (can damage device).

```yaml
# ❌ Error: 5V to 3.3V device
connections:
  - board_pin: 2   # 5V pin
    device: "3.3V Sensor"
    device_pin: "VCC"  # Expects 3.3V
```

**Warning:** 3.3V board pin connected to 5V device pin (device may not work
properly).

```yaml
# ⚠️  Warning: May not provide enough power
connections:
  - board_pin: 1   # 3.3V pin
    device: "5V Device"
    device_pin: "VCC"  # Expects 5V
```

### 4. GPIO Current Limits

**Warning:** Multiple devices driven by one GPIO pin (may exceed 16mA limit).

```yaml
# ⚠️  Warning: Current limit concern
connections:
  - board_pin: 11  # GPIO17
    device: "LED1"
    device_pin: "+"
  - board_pin: 11  # Same GPIO
    device: "LED2"
    device_pin: "+"
```

**Recommendation:** Use separate GPIO pins or add current-limiting resistors.

### 5. Connection Validity

**Error:** Invalid pin numbers, non-existent devices, or non-existent device
pins.

```yaml
# ❌ Error: Invalid pin number
connections:
  - board_pin: 99  # Pin 99 doesn't exist
    device: "LED"
    device_pin: "+"

# ❌ Error: Device not defined
connections:
  - board_pin: 11
    device: "NonExistentDevice"
    device_pin: "+"

# ❌ Error: Pin doesn't exist on device
connections:
  - board_pin: 11
    device: "LED"
    device_pin: "InvalidPin"  # LED only has + and -
```

## Programmatic Usage

You can also use validation in Python code:

```python
from pinviz import load_diagram
from pinviz.validation import DiagramValidator, ValidationLevel

# Load diagram
diagram = load_diagram("my-diagram.yaml")

# Validate
validator = DiagramValidator()
issues = validator.validate(diagram)

# Check for errors
errors = [i for i in issues if i.level == ValidationLevel.ERROR]
if errors:
    for error in errors:
        print(error)
    exit(1)

# Check for warnings
warnings = [i for i in issues if i.level == ValidationLevel.WARNING]
if warnings:
    for warning in warnings:
        print(warning)
```

## Best Practices

1. **Run validation early** - Check your configuration before generating
   diagrams to catch errors quickly.

2. **Address errors first** - Errors indicate critical issues that could
   damage hardware or prevent the diagram from working.

3. **Review warnings** - Warnings indicate potential issues that may cause
   problems. Use `--strict` mode in CI/CD to enforce addressing all
   warnings.

4. **Test with hardware** - Validation catches many common mistakes, but
   always verify your wiring with actual hardware and datasheets.

## Known Limitations

- I2C address detection is based on device name matching and default
  addresses. Custom I2C addresses in your hardware won't be detected.

- Current limit checks are basic warnings. Actual current draw depends on
  your specific components and usage.

- Voltage validation checks pin roles but doesn't verify component
  specifications from datasheets.
