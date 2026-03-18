#!/usr/bin/env python3
"""Update the main package url and sha256 in the Homebrew tap formula.

Fetches tarball URL and sha256 for <version> from PyPI and rewrites
only the two lines that correspond to the main pinviz package.
Resource stanzas are left untouched.

Usage:
    python3 scripts/update_tap_formula.py <version> <formula_path>
"""

import json
import re
import sys
from urllib.request import urlopen


def fetch_pypi_info(version: str) -> tuple[str, str]:
    url = f"https://pypi.org/pypi/pinviz/{version}/json"
    with urlopen(url) as resp:
        data = json.load(resp)
    tarball = next(f for f in data["urls"] if f["url"].endswith(".tar.gz"))
    return tarball["url"], tarball["digests"]["sha256"]


def update_formula(formula_path: str, new_url: str, new_sha: str) -> None:
    with open(formula_path) as f:
        lines = f.readlines()
    out = []
    pending_sha = False
    for line in lines:
        if re.search(
            r'url "https://files\.pythonhosted\.org/packages/[^"]+/pinviz-[0-9][^"]+\.tar\.gz"',
            line,
        ):
            out.append(f'  url "{new_url}"\n')
            pending_sha = True
        elif pending_sha and re.match(r"  sha256 \"", line):
            out.append(f'  sha256 "{new_sha}"\n')
            pending_sha = False
        else:
            out.append(line)
    with open(formula_path, "w") as f:
        f.writelines(out)
    print(f"Updated {formula_path}: url + sha256 for pinviz {version}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <version> <formula_path>", file=sys.stderr)
        sys.exit(1)

    version, formula_path = sys.argv[1], sys.argv[2]
    pkg_url, pkg_sha = fetch_pypi_info(version)
    update_formula(formula_path, pkg_url, pkg_sha)
