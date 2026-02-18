#!/usr/bin/env python3
"""
check_cli_docs.py — Detect drift between CLI --help output and docs/guide/cli.md.

For each PinViz subcommand, extract all options from --help and verify each
appears in docs/guide/cli.md.  Exit 1 if any undocumented options are found.

Usage:
    python scripts/check_cli_docs.py
    python scripts/check_cli_docs.py --verbose

Exit codes:
    0  No drift detected
    1  Drift detected (CLI options not found in docs)
    2  Setup error (docs file not found, pinviz not installed)
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Options present on every command — intentionally not re-documented per command
SKIP_OPTIONS = {"--help"}

# (human-readable label, pinviz subcommand args to produce --help)
COMMANDS: list[tuple[str, list[str]]] = [
    ("render", ["render", "--help"]),
    ("validate", ["validate", "--help"]),
    ("validate-devices", ["validate-devices", "--help"]),
    ("example", ["example", "--help"]),
    ("list", ["list", "--help"]),
    ("add-device", ["add-device", "--help"]),
]


def run_help(args: list[str]) -> str:
    """Run pinviz with the given args and return combined stdout+stderr."""
    result = subprocess.run(
        ["pinviz", *args],
        capture_output=True,
        text=True,
    )
    return result.stdout + result.stderr


def extract_options(help_text: str) -> set[str]:
    """Return all --option-name tokens from help text, excluding SKIP_OPTIONS."""
    found = set(re.findall(r"--[\w-]+", help_text))
    return found - SKIP_OPTIONS


def main() -> int:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    docs_path = Path(__file__).parent.parent / "docs" / "guide" / "cli.md"
    if not docs_path.exists():
        print(f"ERROR: docs file not found: {docs_path}", file=sys.stderr)
        return 2

    docs_text = docs_path.read_text()

    # Verify pinviz is available
    probe = subprocess.run(
        ["pinviz", "--version"], capture_output=True, text=True
    )
    if probe.returncode not in (0, 1):
        print(
            "ERROR: could not run 'pinviz'. Make sure pinviz is installed "
            "in the current environment (uv sync --dev).",
            file=sys.stderr,
        )
        return 2

    drift: list[tuple[str, list[str]]] = []

    for label, args in COMMANDS:
        help_text = run_help(args)
        options = extract_options(help_text)

        if verbose:
            print(f"  pinviz {label}: checking {len(options)} option(s): {sorted(options)}")

        missing = sorted(opt for opt in options if opt not in docs_text)
        if missing:
            drift.append((label, missing))

    if drift:
        print("CLI documentation drift detected.")
        print(
            "The following options appear in --help output but are not found "
            "in docs/guide/cli.md:\n"
        )
        for label, missing_opts in drift:
            for opt in missing_opts:
                print(f"  pinviz {label:<22}  {opt}")
        print(
            "\nFix: add the missing options to the relevant command section "
            "in docs/guide/cli.md."
        )
        return 1

    print("OK — no CLI documentation drift detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
