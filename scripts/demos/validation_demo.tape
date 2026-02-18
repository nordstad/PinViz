# Validation & Logging Demo - Show hardware validation and structured logging
# Run: vhs validation_demo.tape

Set FontSize 16
Set Width 1200
Set Height 700
Set Theme "Dracula"
Set TypingSpeed 80ms
Set Shell zsh
Set WindowBar Colorful

# Setup - set generic prompt and clean slate (hidden)
Hide
Type "export PS1='$ '"
Enter
Sleep 500ms
Type "rm -f bad_wiring.yaml fixed_wiring.yaml *.svg 2>/dev/null || true"
Enter
Sleep 500ms
Type "clear"
Enter
Show

Sleep 500ms

# Create a config with validation errors using vi
Type "vi bad_wiring.yaml"
Sleep 1s
Enter
Sleep 800ms

# Enter insert mode
Sleep 500ms
Type "i"
Sleep 300ms

# Type the YAML configuration with errors
Set TypingSpeed 20ms
Type 'title: "Wiring with Errors"'
Enter
Type "board: raspberry_pi_5"
Enter
Type "devices:"
Enter
Type "  - type: bh1750"
Enter
Type "    name: Sensor1"
Enter
Type "  - type: bh1750"
Enter
Type "    name: Sensor2"
Enter
Type "connections:"
Enter
Type "  # Pin conflict - both devices on pin 3"
Enter
Type "  - board_pin: 3"
Enter
Type "    device: Sensor1"
Enter
Type "    device_pin: SDA"
Enter
Type "  - board_pin: 3"
Enter
Type "    device: Sensor2"
Enter
Type "    device_pin: SDA"
Enter
Type "  # I2C address conflict - same default address"
Enter
Type "  - board_pin: 5"
Enter
Type "    device: Sensor1"
Enter
Type "    device_pin: SCL"
Enter
Type "  - board_pin: 5"
Enter
Type "    device: Sensor2"
Enter
Type "    device_pin: SCL"

# Restore normal typing speed and save
Set TypingSpeed 80ms
Sleep 1s
Escape
Sleep 500ms
Type ":wq"
Sleep 500ms
Enter
Sleep 1s

# Validate - this will catch the errors
Type "pinviz validate bad_wiring.yaml"
Sleep 1s
Enter
Sleep 3s

# Show with connection graph
Type "pinviz validate bad_wiring.yaml --show-graph"
Sleep 1s
Enter
Sleep 4s

# Create fixed version using vi
Type "vi fixed_wiring.yaml"
Sleep 1s
Enter
Sleep 800ms

# Enter insert mode
Sleep 500ms
Type "i"
Sleep 300ms

# Type the fixed YAML configuration
Set TypingSpeed 20ms
Type 'title: "Fixed Wiring"'
Enter
Type "board: raspberry_pi_5"
Enter
Type "devices:"
Enter
Type "  - type: bh1750"
Enter
Type "    name: LightSensor"
Enter
Type "connections:"
Enter
Type "  - board_pin: 1"
Enter
Type "    device: LightSensor"
Enter
Type "    device_pin: VCC"
Enter
Type "  - board_pin: 6"
Enter
Type "    device: LightSensor"
Enter
Type "    device_pin: GND"
Enter
Type "  - board_pin: 3"
Enter
Type "    device: LightSensor"
Enter
Type "    device_pin: SDA"
Enter
Type "  - board_pin: 5"
Enter
Type "    device: LightSensor"
Enter
Type "    device_pin: SCL"

# Restore normal typing speed and save
Set TypingSpeed 80ms
Sleep 1s
Escape
Sleep 500ms
Type ":wq"
Sleep 500ms
Enter
Sleep 1s

# Validate the fixed version
Type "pinviz validate fixed_wiring.yaml"
Sleep 1s
Enter
Sleep 2s

# Render successfully
Type "pinviz render fixed_wiring.yaml -o fixed.svg"
Sleep 1s
Enter
Sleep 2s

# Success message
Type "echo '✓ Validation prevents hardware damage!'"
Sleep 500ms
Enter
Sleep 2s

# Cleanup (hidden)
Hide
Type "rm -f bad_wiring.yaml fixed_wiring.yaml fixed.svg"
Enter
Show

Output output/validation_demo.gif
