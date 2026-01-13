# Add Device Interactive Wizard Demo - Showcase smart pin suggestions
# Run: vhs add_device_wizard_demo.tape

Set FontSize 16
Set Width 1200
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 80ms
Set Shell zsh
Set WindowBar Colorful

# Setup - set generic prompt and clean slate (hidden)
Hide
Type "export PS1='$ '"
Enter
Sleep 500ms
Type "cd /Users/sssenz/dev/slask/gpio-diagram-tool/pi-diagrammer/scripts/demos"
Enter
Sleep 500ms
Type "rm -rf ~/.config/pinviz/devices/dht22_sensor.json *.svg 2>/dev/null || true"
Enter
Sleep 500ms
Type "clear"
Enter
Show

Sleep 500ms

# Start the add-device wizard
Type "# Create a custom device with the interactive wizard"
Sleep 500ms
Enter
Sleep 1s

Type "uv run pinviz add-device"
Sleep 1s
Enter
Sleep 2s

# Device ID (short identifier)
Type "dht22_sensor"
Sleep 800ms
Enter
Sleep 1.5s

# Device name (display name)
Type "DHT22 Temperature & Humidity Sensor"
Sleep 800ms
Enter
Sleep 1.5s

# Category selection (use arrow keys to select 'sensors')
Sleep 500ms
Enter  # Select 'sensors' (first option)
Sleep 1.5s

# Number of pins
Type "3"
Sleep 500ms
Enter
Sleep 1.5s

# Pin 1 - VCC (shows smart suggestion for power)
Type "VCC"
Sleep 800ms
Enter
Sleep 1.5s

# Smart suggestion shows "3V3" highlighted - select it
Sleep 500ms
Enter  # Accept suggested 3V3
Sleep 1.5s

# Pin 2 - GND (shows smart suggestion for ground)
Type "GND"
Sleep 800ms
Enter
Sleep 1.5s

# Smart suggestion shows "GND" highlighted - select it
Sleep 500ms
Enter  # Accept suggested GND
Sleep 1.5s

# Pin 3 - DATA (shows smart suggestion for GPIO)
Type "DATA"
Sleep 800ms
Enter
Sleep 1.5s

# Smart suggestion shows "GPIO" highlighted - select it
Sleep 500ms
Enter  # Accept suggested GPIO
Sleep 1.5s

# Review and confirm
Sleep 1s
Type "y"  # Confirm to save
Sleep 500ms
Enter
Sleep 2s

# Show the generated config file
Type "# View the generated device configuration"
Sleep 500ms
Enter
Sleep 1s

Type "cat ~/.config/pinviz/devices/dht22_sensor.json"
Sleep 1s
Enter
Sleep 3s

# Validate the new device is available
Type "# Verify the device is now available"
Sleep 500ms
Enter
Sleep 1s

Type "uv run pinviz list | grep -i dht22"
Sleep 1s
Enter
Sleep 2s

# Create a quick diagram using the new device
Type "# Create a diagram with the new device"
Sleep 500ms
Enter
Sleep 1s

Type "vi dht22_diagram.yaml"
Sleep 1s
Enter
Sleep 800ms

# Enter insert mode
Sleep 500ms
Type "i"
Sleep 300ms

# Type the YAML configuration
Set TypingSpeed 20ms
Type 'title: "DHT22 Sensor Wiring"'
Enter
Type "board: raspberry_pi_5"
Enter
Type "devices:"
Enter
Type "  - type: dht22_sensor"
Enter
Type "    name: Climate Sensor"
Enter
Type "connections:"
Enter
Type "  - board_pin: 1   # 3.3V"
Enter
Type "    device: Climate Sensor"
Enter
Type "    device_pin: VCC"
Enter
Type "  - board_pin: 6   # Ground"
Enter
Type "    device: Climate Sensor"
Enter
Type "    device_pin: GND"
Enter
Type "  - board_pin: 7   # GPIO 4"
Enter
Type "    device: Climate Sensor"
Enter
Type "    device_pin: DATA"

# Restore normal typing speed and save
Set TypingSpeed 80ms
Sleep 1s
Escape
Sleep 500ms
Type ":wq"
Sleep 500ms
Enter
Sleep 1s

# Render the diagram
Type "uv run pinviz render dht22_diagram.yaml -o dht22.svg"
Sleep 1s
Enter
Sleep 3s

# Success message
Type "echo '✓ Custom device created and diagram generated!'"
Sleep 500ms
Enter
Sleep 2s

# Cleanup (hidden)
Hide
Type "rm -f dht22_diagram.yaml dht22.svg"
Enter
Type "rm -f ~/.config/pinviz/devices/dht22_sensor.json"
Enter
Show

Output output/add_device_wizard_demo.gif
