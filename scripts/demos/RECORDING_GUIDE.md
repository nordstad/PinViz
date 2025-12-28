# Recording Terminal Demos as GIFs

This guide explains how to record terminal demos for PinViz documentation.

## 🎬 Quick Start (Recommended: VHS)

**VHS** is the easiest modern tool for creating terminal GIFs with scripting support.

### Install VHS

```bash
# macOS
brew install vhs

# Other platforms
go install github.com/charmbracelet/vhs@latest
```

### Record Demo

```bash
cd scripts/demos
vhs demo.tape
# Output: demo.gif
```

## 🛠️ Alternative Tools

### 1. **asciinema** + **agg** (High Quality)

Record terminal session and convert to GIF:

```bash
# Install
pip install asciinema
cargo install agg  # or download from https://github.com/asciinema/agg

# Record
asciinema rec demo.cast

# Convert to GIF
agg demo.cast demo.gif
```

**Pros:** High quality, editable recordings
**Cons:** Two-step process

### 2. **Terminalizer** (Interactive)

```bash
# Install
npm install -g terminalizer

# Record (interactive)
terminalizer record demo

# Render GIF
terminalizer render demo
```

**Pros:** Interactive recording with config
**Cons:** Node.js dependency, slower rendering

### 3. **ttygif** (Linux/macOS)

```bash
# macOS
brew install ttygif

# Record
ttyrec demo.tty

# Convert to GIF
ttygif demo.tty
```

**Pros:** Simple, native
**Cons:** Basic features only

### 4. **Peek** (Linux, GUI)

GUI application for screen recording:

```bash
# Ubuntu/Debian
sudo apt install peek

# Fedora
sudo dnf install peek
```

**Pros:** Easy GUI, WYSIWYG
**Cons:** Linux only, requires manual interaction

## 📐 Recommended Settings

### GIF Specifications
- **Width:** 1200px (fits GitHub README)
- **Height:** 800px
- **Framerate:** 30 FPS
- **Theme:** Dracula or Nord (good contrast)
- **Font Size:** 14-16pt (readable on mobile)

### Timing Guidelines
- **Typing speed:** 100ms per character (realistic)
- **Command execution:** 1-2s pause before showing output
- **Between steps:** 2-3s pause
- **Total duration:** 30-60 seconds (optimal for attention span)

## 🎨 VHS Configuration

Edit `demo.tape` to customize:

```tape
# Window settings
Set Width 1200
Set Height 800
Set Theme "Dracula"
Set Padding 20

# Speed settings
Set TypingSpeed 100ms    # Typing speed
Set PlaybackSpeed 1.0    # Overall playback speed
Set Framerate 30         # FPS
```

Available themes: `Dracula`, `Nord`, `Monokai`, `Solarized Light`, `Solarized Dark`

## 📝 Recording Best Practices

### Do's ✅
- Start with a clean terminal
- Use a readable theme with good contrast
- Add 2-3 second pauses between major steps
- Show both commands and outputs
- End with a clear success message
- Keep total duration under 60 seconds

### Don'ts ❌
- Don't include authentication or secrets
- Don't use tiny fonts (< 14pt)
- Don't skip command outputs
- Don't record errors (unless demonstrating troubleshooting)
- Don't make it too fast (< 80ms typing speed)
- Don't exceed 5MB file size (optimize if needed)

## 🎯 Demo Script Structure

1. **Title screen** (2s) - Show what demo covers
2. **Installation** (5-7s) - `uv tool install pinviz`
3. **Verification** (3-5s) - `pinviz --version`
4. **List examples** (5-7s) - `pinviz list`
5. **Generate diagram** (5-7s) - `pinviz example bh1750 -o diagram.svg`
6. **View diagram** (2-3s) - `open diagram.svg` (text only, don't actually open)
7. **Success message** (3s) - Clear completion indicator

**Total:** ~30-40 seconds

## 🔄 Optimizing GIF Size

### Using gifsicle

```bash
# Install
brew install gifsicle  # macOS
sudo apt install gifsicle  # Ubuntu

# Optimize
gifsicle -O3 --colors 256 demo.gif -o demo_optimized.gif
```

### Using ImageMagick

```bash
# Install
brew install imagemagick  # macOS

# Optimize and reduce colors
convert demo.gif -fuzz 10% -layers Optimize demo_optimized.gif
```

### Target Sizes
- **Ideal:** < 2MB (fast loading on mobile)
- **Maximum:** < 5MB (GitHub limit)
- **Reduce colors:** 256 or fewer
- **Reduce framerate:** 20-30 FPS

## 🚀 Automated Recording with GitHub Actions

Create `.github/workflows/record-demo.yml`:

```yaml
name: Record Demo GIF

on:
  workflow_dispatch:  # Manual trigger
  push:
    branches: [main]
    paths:
      - 'scripts/demos/**/*.tape'

jobs:
  record:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install VHS
        run: |
          wget https://github.com/charmbracelet/vhs/releases/download/v0.7.0/vhs_0.7.0_amd64.deb
          sudo dpkg -i vhs_0.7.0_amd64.deb

      - name: Record demo
        run: |
          cd scripts/demos
          vhs demo.tape

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: demo-gif
          path: scripts/demos/*.gif
```

## 📖 Resources

- **VHS:** https://github.com/charmbracelet/vhs
- **asciinema:** https://asciinema.org/
- **agg:** https://github.com/asciinema/agg
- **Terminalizer:** https://terminalizer.com/
- **GIF optimization:** https://www.lcdf.org/gifsicle/

## 💡 Tips

1. **Test first:** Run your script manually before recording
2. **Clean environment:** Use a fresh terminal or virtual environment
3. **Preview:** Check the GIF before committing (VLC, browser)
4. **Mobile-friendly:** Test how it looks on small screens
5. **Accessibility:** Include text descriptions in README

## 🎬 Example Usage in README

```markdown
## Quick Start

![PinViz Demo](https://raw.githubusercontent.com/nordstad/PinViz/main/images/demo.gif)

See PinViz in action! Install, create, and view your first GPIO diagram in 30 seconds.
```
