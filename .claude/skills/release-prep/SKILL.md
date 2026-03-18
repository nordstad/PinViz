---
name: release-prep
description: Prepare a pinviz release - run pre-publish validation, bump version in pyproject.toml, update CHANGELOG.md, then show the exact git commands to tag and push. Does NOT push or tag automatically.
disable-model-invocation: true
---

Prepare a new pinviz release following `guides/publishing.md` exactly.

## Step 1: Determine the new version

Ask the user: "What is the new version number? (current: check pyproject.toml)"

Read `pyproject.toml` to show the current version. Confirm the new version follows semver:
- **Patch** (x.y.Z): bug fixes only
- **Minor** (x.Y.0): new backward-compatible features
- **Major** (X.0.0): breaking API changes

## Step 2: Check the working tree is clean

```bash
git status --short
git log --oneline $(git describe --tags --abbrev=0)..HEAD
```

Show the user the commits since the last tag so they can confirm the changelog reflects all changes. If there are uncommitted changes, warn and stop.

## Step 3: Pre-publish validation (CRITICAL — run all four)

### 3a. Full test suite
```bash
uv run pytest --tb=short -q
```

### 3b. Post-publish test compatibility check
```bash
./scripts/validate-post-publish-tests.sh
```

### 3c. Ruff lint + format
```bash
uv run ruff check . && uv run ruff format --check .
```

### 3d. Package build validation
```bash
uv build && uv run twine check dist/*
```

Stop and report if any step fails. Do not proceed with version bump until all checks pass.

## Step 4: Update pyproject.toml

Edit `pyproject.toml`: change `version = "OLD"` to `version = "NEW"`.

## Step 5: Update CHANGELOG.md

Move the `[Unreleased]` content to a new versioned section. The format must be:

```markdown
## [Unreleased]

## [X.Y.Z] - YYYY-MM-DD

### Added / Changed / Fixed / ...
- <existing unreleased entries>
```

Today's date in `YYYY-MM-DD` format. If `[Unreleased]` is empty, note that to the user — they may want to add entries before releasing.

## Step 6: Check if dependencies changed

Compare the runtime dependencies in `pyproject.toml` against the last known resource stanzas by running:

```bash
gh api repos/nordstad/homebrew-pinviz/contents/Formula/pinviz.rb --jq '.content' | base64 -d | grep -A2 "resource "
```

If any runtime dependency was **added, removed, or version-bumped**, warn the user:

> ⚠️  Runtime dependencies have changed. After the publish CI completes and PyPI is live, regenerate the Homebrew resource stanzas (see post-release steps below).
> The publish workflow only auto-updates the main package URL/SHA256 — it does not refresh resource stanzas.

If no runtime dependencies changed, note that no formula update is needed.

## Step 7: Show the git commands — do NOT run them

Print these exact commands for the user to review and run manually:

```bash
# 1. Commit the version bump
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to vX.Y.Z"
git push origin main

# 2. Tag and push (triggers the publish workflow)
git tag vX.Y.Z
git push origin vX.Y.Z
```

The publish workflow will automatically:
- Build and publish to PyPI
- Create the GitHub Release
- Update `CHANGELOG.md` and commit to main
- Push updated `Formula/pinviz.rb` (URL + SHA256) to `nordstad/homebrew-pinviz` main

Then show this reminder:

> ⚠️  Do NOT create a GitHub Release manually (no `gh release create`, no GitHub UI).
> The publish workflow creates the release automatically when the tag is pushed.
> Monitor with: `gh run watch --workflow=publish.yml`

## Post-release: Update Homebrew resource stanzas (if deps changed)

Only needed when runtime dependencies were added, removed, or version-bumped (flagged in Step 6).

Must run **after** the publish CI completes and the package is live on PyPI:

```bash
# 1. Pull — CI commits CHANGELOG.md to main
git pull origin main

# 2. Regenerate all resource stanzas from the live PyPI package
brew update-python-resources nordstad/pinviz/pinviz

# 3. Commit the updated formula to the tap repo
cd "$(brew --repository nordstad/pinviz)"
git add Formula/pinviz.rb
git commit -m "chore: update Homebrew resource stanzas for vX.Y.Z"
git push origin main
```

> Note: `brew update-python-resources` only accepts a tap reference (`nordstad/pinviz/pinviz`), not a local file path.
> The formula lives in `nordstad/homebrew-pinviz`, not the source repo.
