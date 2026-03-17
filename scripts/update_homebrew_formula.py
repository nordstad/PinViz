#!/usr/bin/env python3
"""Update the main package url and sha256 in Formula/pinviz.rb.

Usage:
    python3 scripts/update_homebrew_formula.py <version> <formula_path>

Fetches the tarball URL and sha256 for <version> from PyPI and rewrites
only the two lines in the formula that correspond to the main pinviz package.
Resource stanzas are left untouched.
"""

import json
import re
import sys
import urllib.request


def fetch_pypi_info(version: str) -> tuple[str, str]:
    url = f"https://pypi.org/pypi/pinviz/{version}/json"
    with urllib.request.urlopen(url) as resp:
        data = json.load(resp)
    tarball = next(f for f in data["urls"] if f["url"].endswith(".tar.gz"))
    return tarball["url"], tarball["digests"]["sha256"]


def update_formula(formula_path: str, new_url: str, new_sha: str) -> None:
    with open(formula_path) as f:
        content = f.read()

    # Replace the main package URL (matches only pinviz-*.tar.gz, not resources)
    content, n = re.subn(
        r'url "https://files\.pythonhosted\.org/packages/[^"]+/pinviz-[^"]+\.tar\.gz"',
        f'url "{new_url}"',
        content,
        count=1,
    )
    if n != 1:
        raise RuntimeError("Could not find main package url line in formula")

    # Replace the sha256 on the line immediately following the main url
    content, n = re.subn(
        r'(url "' + re.escape(new_url) + r'"\n  sha256 ")[a-f0-9]+"',
        f'url "{new_url}"\n  sha256 "{new_sha}"',
        content,
    )
    if n != 1:
        raise RuntimeError("Could not find sha256 line after main package url")

    with open(formula_path, "w") as f:
        f.write(content)
    print(f"Updated {formula_path}: url + sha256 for pinviz {new_url.split('/')[-1]}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <version> <formula_path>", file=sys.stderr)
        sys.exit(1)

    version, formula_path = sys.argv[1], sys.argv[2]
    pkg_url, pkg_sha = fetch_pypi_info(version)
    update_formula(formula_path, pkg_url, pkg_sha)
