# Demo Videos

This directory contains demo recordings for PinViz documentation.

## Structure

```
demos/
├── output/                       # Completed GIF videos
│   ├── quick_demo.gif
│   ├── custom_device_demo.gif
│   ├── add_device_wizard_demo.gif
│   └── python_api_demo.gif      # (committed)
├── simple_demo.tape              # Quick installation demo
├── custom_device_demo.tape       # YAML configuration demo
├── add_device_wizard_demo.tape   # Interactive wizard demo
├── python_api_demo.tape          # Python API demo
├── demo.tape                     # Full feature demo
├── README.md                     # This file
└── RECORDING_GUIDE.md            # Recording instructions
```

## Available Demos

- `simple_demo.tape` - Quick 30-second installation and first diagram
- `custom_device_demo.tape` - Creating custom devices with YAML
- `add_device_wizard_demo.tape` - Interactive device wizard with smart pin suggestions
- `python_api_demo.tape` - Creating diagrams with Python API
- `validation_demo.tape` - Hardware validation and error detection
- `demo.tape` - Full feature demo

## Record Demo

```bash
cd scripts/demos
vhs simple_demo.tape
# Output: output/quick_demo.gif
```

See [RECORDING_GUIDE.md](./RECORDING_GUIDE.md) for details.
