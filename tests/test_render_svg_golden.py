"""Golden-output tests for representative rendered SVGs."""

import difflib
import os
import xml.etree.ElementTree as ET
from pathlib import Path

from pinviz.config_loader import load_diagram
from pinviz.render_svg import SVGRenderer

GOLDEN_DIR = Path(__file__).parent / "golden_svg"
GOLDEN_CASES = [
    ("examples/bh1750.yaml", "bh1750.svg"),
    ("examples/pico_minimal.yaml", "pico_minimal.svg"),
    ("examples/multi_level_branching.yaml", "multi_level_branching.svg"),
]


def _canonicalize_svg(path: Path) -> str:
    return ET.canonicalize(path.read_text())


def _render_example(example_path: str, output_path: Path) -> None:
    diagram = load_diagram(example_path, emit_validation_output=False)
    SVGRenderer().render(diagram, output_path)


def _diff_preview(expected: str, actual: str, *, max_lines: int = 40) -> str:
    diff_lines = list(
        difflib.unified_diff(
            expected.splitlines(),
            actual.splitlines(),
            fromfile="expected",
            tofile="actual",
            lineterm="",
        )
    )
    return "\n".join(diff_lines[:max_lines])


def test_rendered_svgs_match_goldens(tmp_path):
    """Representative renders should stay byte-stable after XML canonicalization."""
    update_goldens = os.getenv("PINVIZ_UPDATE_GOLDENS") == "1"

    for example_path, golden_name in GOLDEN_CASES:
        actual_path = tmp_path / golden_name
        golden_path = GOLDEN_DIR / golden_name

        _render_example(example_path, actual_path)

        if update_goldens:
            golden_path.parent.mkdir(parents=True, exist_ok=True)
            golden_path.write_text(actual_path.read_text())

        assert golden_path.exists(), f"Missing golden SVG: {golden_path}"

        actual = _canonicalize_svg(actual_path)
        expected = _canonicalize_svg(golden_path)

        assert actual == expected, (
            f"Golden SVG mismatch for {example_path}\n"
            f"Update with: PINVIZ_UPDATE_GOLDENS=1 uv run pytest -q "
            f"{Path(__file__).name}\n\n"
            f"{_diff_preview(expected, actual)}"
        )
