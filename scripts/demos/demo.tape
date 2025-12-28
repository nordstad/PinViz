# VHS tape file for recording PinViz demo as GIF
# Install VHS: brew install vhs (macOS) or go install github.com/charmbracelet/vhs@latest
# Run: vhs demo.tape
# Output: demo.gif

# Settings
Set FontSize 16
Set Width 1200
Set Height 800
Set Theme "Dracula"
Set Padding 20
Set Framerate 30
Set PlaybackSpeed 1.0
Set TypingSpeed 100ms

# Title screen
Type "# PinViz - Raspberry Pi GPIO Diagram Generator"
Sleep 500ms
Enter
Type "# Quick Start Demo"
Sleep 500ms
Enter
Enter
Sleep 1s

# Step 1: Installation
Type "# Step 1: Install PinViz"
Sleep 500ms
Enter
Sleep 500ms
Type "uv tool install pinviz"
Sleep 500ms
Enter
Sleep 3s

# Step 2: Verify installation
Type "# Step 2: Verify installation"
Sleep 500ms
Enter
Sleep 500ms
Type "pinviz --version"
Sleep 500ms
Enter
Sleep 2s

# Step 3: List examples
Type "# Step 3: See available examples"
Sleep 500ms
Enter
Sleep 500ms
Type "pinviz list"
Sleep 500ms
Enter
Sleep 3s

# Step 4: Generate diagram
Type "# Step 4: Generate your first diagram"
Sleep 500ms
Enter
Sleep 500ms
Type "pinviz example bh1750 -o my_first_diagram.svg"
Sleep 500ms
Enter
Sleep 2s

# Step 5: View diagram
Type "# Step 5: View your diagram"
Sleep 500ms
Enter
Sleep 500ms
Type "open my_first_diagram.svg"
Sleep 500ms
Enter
Sleep 2s

# Success message
Type@500ms "echo '✓ Success! Your first GPIO diagram is ready!'"
Enter
Sleep 500ms
Type@500ms "echo 'Visit: https://nordstad.github.io/PinViz'"
Enter
Sleep 3s

# Output
Output demo.gif
