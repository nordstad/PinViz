# Simplified 30-second PinViz demo
# Run: vhs simple_demo.tape

Set FontSize 16
Set Width 1000
Set Height 600
Set Theme "Dracula"
Set TypingSpeed 80ms
Set Shell zsh
Set WindowBar Colorful

# Setup - set generic prompt and uninstall silently (completely hidden)
Hide
Type "export PS1='$ '"
Enter
Sleep 500ms
Type "uv tool uninstall pinviz 2>/dev/null || true"
Enter
Sleep 2s
Type "clear"
Enter
Show

Sleep 500ms

# Install fresh
Type "uv tool install pinviz"
Sleep 1s
Enter
Sleep 4s
Sleep 1.5s

# Generate diagram
Type "pinviz example bh1750 -o diagram.svg"
Enter
Sleep 3s

# Verify success without showing username
Type "file diagram.svg"
Enter
Sleep 2s

Output output/quick_demo.gif
