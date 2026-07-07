# Add Device Wizard Demo - Create a new device config interactively
# Run: vhs add_device_demo.tape

Set FontSize 16
Set Width 1200
Set Height 800
Set Theme "Dracula"
Set TypingSpeed 80ms
Set Shell zsh
Set WindowBar Colorful

# Setup - clean slate and remove any leftover from previous run (hidden)
Hide
Type "export PS1='$ '"
Enter
Sleep 500ms
Type "rm -f ../../src/pinviz/device_configs/sensors/aht20.json 2>/dev/null || true"
Enter
Sleep 500ms
Type "clear"
Enter
Show

Sleep 500ms

# Launch the interactive wizard
Type "uv run pinviz add-device"
Enter
Sleep 2s

# Device name
Type "AHT20 Temperature & Humidity Sensor"
Enter
Sleep 1s

# Device ID
Type "aht20"
Enter
Sleep 1.5s

# Category: Sensors is first in list - just Enter to accept
Enter
Sleep 1s

# Short description
Type "Ultra-compact I2C temperature and humidity sensor"
Enter
Sleep 1s

# Number of pins
Type "4"
Enter
Sleep 1s

# Pin 1: VCC - wizard suggests 3V3 as first option
Type "VCC"
Enter
Sleep 1.5s
Enter
Sleep 800ms

# Pin 2: GND - wizard suggests GND as first option
Type "GND"
Enter
Sleep 1.5s
Enter
Sleep 800ms

# Pin 3: SDA - wizard suggests I2C_SDA as first option
Type "SDA"
Enter
Sleep 1.5s
Enter
Sleep 800ms

# Pin 4: SCL - wizard suggests I2C_SCL as first option
Type "SCL"
Enter
Sleep 1.5s
Enter
Sleep 800ms

# I2C address
Type "0x38"
Enter
Sleep 1s

# Datasheet URL - skip
Enter
Sleep 800ms

# Setup notes - skip
Enter
Sleep 2s

# Config preview is shown, then "Save this configuration?" (default: Yes)
Enter
Sleep 4s

# Cleanup (hidden)
Hide
Type "rm -f ../../src/pinviz/device_configs/sensors/aht20.json 2>/dev/null || true"
Enter
Show

Output output/add_device_demo.gif
