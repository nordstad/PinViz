# Custom Device Demo - Show how to create custom devices in PinViz
# Run: vhs custom_device_demo.tape

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
Type "rm -f my_sensor.yaml my_sensor.svg 2>/dev/null || true"
Enter
Sleep 500ms
Type "clear"
Enter
Show

Sleep 500ms

# Create a custom YAML config using vi
Type "vi my_sensor.yaml"
Sleep 1s
Enter
Sleep 800ms

# Show empty vi briefly, then enter insert mode
Sleep 500ms
Type "i"
Sleep 300ms

# Type the YAML configuration (fast typing)
Set TypingSpeed 20ms
Type 'title: "DHT22 Temperature Sensor"'
Enter
Type "board: raspberry_pi_5"
Enter
Type "devices:"
Enter
Type '  - name: "DHT22"'
Enter
Type "    pins:"
Enter
Type '      - name: "VCC"'
Enter
Type '        role: "3V3"'
Enter
Type '      - name: "DATA"'
Enter
Type '        role: "GPIO"'
Enter
Type '      - name: "GND"'
Enter
Type '        role: "GND"'
Enter
Type "connections:"
Enter
Type "  - board_pin: 1"
Enter
Type '    device: "DHT22"'
Enter
Type '    device_pin: "VCC"'
Enter
Type "  - board_pin: 7"
Enter
Type '    device: "DHT22"'
Enter
Type '    device_pin: "DATA"'
Enter
Type "  - board_pin: 9"
Enter
Type '    device: "DHT22"'
Enter
Type '    device_pin: "GND"'

# Restore normal typing speed
Set TypingSpeed 80ms
Sleep 1s

# Exit insert mode and save
Escape
Sleep 500ms
Type ":wq"
Sleep 500ms
Enter
Sleep 1s

# Show the file
Type "cat my_sensor.yaml"
Sleep 1s
Enter
Sleep 3s

# Generate the diagram
Type "pinviz render my_sensor.yaml -o my_sensor.svg"
Sleep 1s
Enter
Sleep 3s

# Success
Type "echo '✓ Custom device diagram created!'"
Sleep 500ms
Enter
Sleep 2s

Output output/custom_device_demo.gif
