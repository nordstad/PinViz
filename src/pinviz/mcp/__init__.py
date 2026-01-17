"""PinViz MCP Server - Natural language to GPIO wiring diagrams."""

# Get version from package metadata
try:
    from importlib.metadata import version

    __version__ = version("pinviz")
except Exception:
    __version__ = "unknown"
