#!/usr/bin/env python3
"""Update CHANGELOG.md with GitHub release notes."""

import re
import sys
from datetime import datetime
from pathlib import Path


def parse_github_release_notes(notes: str) -> dict[str, list[str]]:
    """
    Parse GitHub auto-generated release notes into categories.

    Args:
        notes: GitHub release notes text

    Returns:
        Dictionary mapping categories to list of changes
    """
    categories = {
        "Added": [],
        "Changed": [],
        "Fixed": [],
        "Removed": [],
        "Dependencies": [],
    }

    # Split into lines and process each PR
    for line in notes.split("\n"):
        line = line.strip()
        if not line.startswith("*"):
            continue

        # Extract PR title and link
        # Format: * PR title by @user in #123
        match = re.match(r"\*\s+(.+?)\s+by\s+@.+?\s+in\s+(https://.+)$", line)
        if not match:
            continue

        title = match.group(1)
        pr_link = match.group(2)

        # Categorize based on PR title
        title_lower = title.lower()

        if title_lower.startswith("bump "):
            # Dependency update
            categories["Dependencies"].append(f"- {title} ({pr_link})")
        elif any(
            word in title_lower for word in ["add", "new", "implement", "introduce", "create"]
        ):
            categories["Added"].append(f"- {title} ({pr_link})")
        elif any(word in title_lower for word in ["fix", "resolve", "correct", "repair", "patch"]):
            categories["Fixed"].append(f"- {title} ({pr_link})")
        elif any(word in title_lower for word in ["remove", "delete", "drop"]):
            categories["Removed"].append(f"- {title} ({pr_link})")
        else:
            # Default to Changed
            categories["Changed"].append(f"- {title} ({pr_link})")

    return categories


def format_changelog_entry(version: str, date: str, categories: dict[str, list[str]]) -> str:
    """
    Format a changelog entry in Keep a Changelog format.

    Args:
        version: Version number (e.g., "0.5.1")
        date: Release date in YYYY-MM-DD format
        categories: Dictionary of categorized changes

    Returns:
        Formatted changelog entry
    """
    lines = [f"## [{version}] - {date}", ""]

    # Add non-empty categories in standard order
    for category in ["Added", "Changed", "Fixed", "Removed", "Dependencies"]:
        if categories[category]:
            lines.append(f"### {category}")
            lines.extend(categories[category])
            lines.append("")

    return "\n".join(lines)


def update_changelog(
    changelog_path: Path, version: str, release_notes: str, date: str | None = None
) -> None:
    """
    Update CHANGELOG.md with a new release entry.

    Args:
        changelog_path: Path to CHANGELOG.md
        version: Version number (e.g., "0.5.1")
        release_notes: GitHub release notes
        date: Release date (defaults to today)
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # Parse release notes into categories
    categories = parse_github_release_notes(release_notes)

    # Format the new entry
    new_entry = format_changelog_entry(version, date, categories)

    # Read existing changelog
    content = changelog_path.read_text()

    # Find the ## [Unreleased] section
    unreleased_pattern = r"## \[Unreleased\]"
    match = re.search(unreleased_pattern, content)

    if not match:
        raise ValueError("Could not find [Unreleased] section in CHANGELOG.md")

    # Insert new entry after [Unreleased] section
    # Find the end of [Unreleased] section (empty lines after it)
    insert_pos = match.end()

    # Skip empty lines after [Unreleased]
    while insert_pos < len(content) and content[insert_pos] in "\n\r":
        insert_pos += 1

    # Insert the new entry
    updated_content = content[:insert_pos] + "\n" + new_entry + "\n" + content[insert_pos:]

    # Update the version comparison links at the bottom
    # Add new link for this version
    links_pattern = r"(\[Unreleased\]: https://github\.com/[^/]+/[^/]+/compare/)v[\d.]+\.\.\.HEAD"
    match = re.search(links_pattern, updated_content)

    if match:
        # Update Unreleased link to compare from new version
        updated_content = re.sub(links_pattern, rf"\g<1>v{version}...HEAD", updated_content)

        # Find previous version from the changelog
        prev_version_pattern = r"## \[(\d+\.\d+\.\d+)\]"
        versions = re.findall(prev_version_pattern, updated_content)

        # versions[0] is the new version we just added
        # versions[1] is the previous version
        if len(versions) >= 2:
            prev_version = versions[1]
            # Add link for new version after Unreleased link
            new_version_link = (
                f"[{version}]: https://github.com/nordstad/PinViz/compare/"
                f"v{prev_version}...v{version}"
            )
            # Insert after Unreleased link
            unreleased_link_end = updated_content.find("\n", match.end())
            updated_content = (
                updated_content[:unreleased_link_end]
                + f"\n{new_version_link}"
                + updated_content[unreleased_link_end:]
            )

    # Write updated content
    changelog_path.write_text(updated_content)


def main():
    """CLI entry point."""
    if len(sys.argv) not in [3, 4]:
        print("Usage: update_changelog.py VERSION RELEASE_NOTES_FILE [DATE]")
        print("Example: update_changelog.py 0.5.1 release_notes.txt 2025-12-28")
        sys.exit(1)

    version = sys.argv[1]
    notes_file = Path(sys.argv[2])
    date = sys.argv[3] if len(sys.argv) == 4 else None

    if not notes_file.exists():
        print(f"Error: Release notes file not found: {notes_file}", file=sys.stderr)
        sys.exit(1)

    release_notes = notes_file.read_text()
    changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"

    try:
        update_changelog(changelog_path, version, release_notes, date)
        print(f"✓ Updated CHANGELOG.md with version {version}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
