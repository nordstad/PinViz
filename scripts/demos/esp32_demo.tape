# ESP32 Demo - PinViz works beyond Raspberry Pi
# Run: vhs esp32_demo.tape

Set FontSize 16
Set Width 1100
Set Height 650
Set Theme "Dracula"
Set TypingSpeed 80ms
Set Shell zsh
Set WindowBar Colorful

# Setup - clean slate (hidden)
Hide
Type "export PS1='$ '"
Enter
Sleep 500ms
Type "rm -f esp32_weather.svg 2>/dev/null || true"
Enter
Sleep 500ms
Type "clear"
Enter
Show

Sleep 500ms

# Generate ESP32 weather station diagram
Type "pinviz example esp32_weather -o esp32_weather.svg"
Enter
Sleep 3s

# Verify the output
Type "file esp32_weather.svg"
Enter
Sleep 2s

Type "echo '✓ Works with ESP32, Pico, ESP8266, Wemos D1 Mini and more!'"
Enter
Sleep 3s

# Cleanup (hidden)
Hide
Type "rm -f esp32_weather.svg"
Enter
Show

Output output/esp32_demo.gif
