"""Tests for generated board artwork assets."""

import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _load_generator():
    """Import the standalone generator script (scripts/ is not a package)."""
    path = _ROOT / "scripts" / "gen_esp32_s3_devkitc1_svg.py"
    spec = importlib.util.spec_from_file_location("gen_esp32_s3_devkitc1_svg", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_esp32_s3_devkitc1_asset_matches_generator():
    """The committed SVG must be exactly what the generator produces.

    Guards against hand-edits to the asset and against the generator drifting
    from the committed artwork. Regenerate with
    ``python scripts/gen_esp32_s3_devkitc1_svg.py`` if this fails intentionally.
    """
    generator = _load_generator()
    committed = (_ROOT / "src" / "pinviz" / "assets" / "esp32_s3_devkitc1_mod.svg").read_text()
    assert generator.build() == committed
