# Python API Demo - Show how to create diagrams programmatically
# Run: vhs python_api_demo.tape

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
Type "rm -f create_diagram.py sensor_diagram.svg 2>/dev/null || true"
Enter
Sleep 500ms
Type "clear"
Enter
Show

Sleep 500ms

# Create a Python script using vi
Type "vi create_diagram.py"
Sleep 1s
Enter
Sleep 800ms

# Show empty vi briefly, then enter insert mode
Sleep 500ms
Type "i"
Sleep 300ms

# Type the Python code (fast typing)
Set TypingSpeed 20ms
Type "from pinviz import boards, Device, DevicePin, Connection, Diagram, SVGRenderer"
Enter
Type "from pinviz.model import PinRole, Point"
Enter
Enter
Type "# Use predefined board"
Enter
Type "board = boards.raspberry_pi_5()"
Enter
Enter
Type "# Create custom sensor device"
Enter
Type 'sensor = Device('
Enter
Type '    name="DHT22",'
Enter
Type "    pins=["
Enter
Type '        DevicePin("VCC", PinRole.POWER_3V3, Point(0, 0)),'
Enter
Type '        DevicePin("DATA", PinRole.GPIO, Point(0, 20)),'
Enter
Type '        DevicePin("GND", PinRole.GROUND, Point(0, 40)),'
Enter
Type "    ]"
Enter
Type ")"
Enter
Enter
Type "# Define connections"
Enter
Type "connections = ["
Enter
Type '    Connection(1, "DHT22", "VCC"),'
Enter
Type '    Connection(7, "DHT22", "DATA"),'
Enter
Type '    Connection(9, "DHT22", "GND"),'
Enter
Type "]"
Enter
Enter
Type "# Create diagram"
Enter
Type "diagram = Diagram("
Enter
Type '    title="DHT22 Sensor - Python API",'
Enter
Type "    board=board,"
Enter
Type "    devices=[sensor],"
Enter
Type "    connections=connections"
Enter
Type ")"
Enter
Enter
Type "# Render to SVG"
Enter
Type "renderer = SVGRenderer()"
Enter
Type 'renderer.render(diagram, "sensor_diagram.svg")'
Enter
Type 'print("Diagram created: sensor_diagram.svg")'

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

# Run the Python script with uv
Type "uv run python create_diagram.py"
Sleep 1s
Enter
Sleep 4s

# Show success
Type "file sensor_diagram.svg"
Sleep 500ms
Enter
Sleep 2s

Output output/python_api_demo.gif
