# Publishing

Publishing is fully automated. Push a tag → everything else happens automatically.

## Quick reference

```bash
# 1. Bump version and update CHANGELOG
vim pyproject.toml   # version = "X.Y.Z"
vim CHANGELOG.md     # move [Unreleased] → [X.Y.Z] - YYYY-MM-DD

# 2. Commit and push
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to vX.Y.Z"
git push origin main

# 3. Tag and push — this triggers everything
git tag vX.Y.Z
git push origin vX.Y.Z
```

The workflow then:

1. Builds and smoke-tests the package
2. Publishes to PyPI
3. Creates the GitHub Release
4. Commits updated `CHANGELOG.md` to main
5. Updates `nordstad/homebrew-pinviz` formula with new URL + SHA256
6. Runs post-publish integration tests (Python 3.13)

## ⚠️ Never create releases manually

The workflow creates the GitHub Release automatically. If you create it manually
first (via CLI or UI), the workflow will fail trying to create a duplicate.

## Monitoring

```bash
gh run list --workflow=publish.yml --limit 3
gh run watch
gh run view --log-failed
```

## Homebrew setup (for new projects)

### Prerequisites

1. Create a `<org>/homebrew-<name>` repo (the `homebrew-` prefix is the Homebrew
   convention — it makes `brew tap <org>/<name>` resolve automatically without
   needing an explicit URL).

2. Add a `Formula/<name>.rb` with a placeholder URL/SHA256 — the workflow will
   update it on first release.

3. Create a fine-grained PAT scoped to the tap repo with **Contents R/W** and
   store it as `HOMEBREW_TAP_TOKEN` in the source repo secrets.

4. Add `brew-publish.yml` to `.github/workflows/` (copy from pinviz, substituting
   the package name in the three places marked below).

### brew-publish.yml template

```yaml
name: Update Homebrew Formula

on:
  workflow_run:
    workflows: ["Publish to PyPI"]   # ← must match your publish workflow name exactly
    types: [completed]
  workflow_dispatch:
    inputs:
      version:
        description: 'Version tag to publish (e.g. v1.0.0)'
        required: true

permissions:
  contents: read

jobs:
  update-homebrew:
    name: Update Homebrew Formula
    # Only run on successful tag-triggered publish runs, or manual dispatch
    if: >-
      github.event_name == 'workflow_dispatch' ||
      (github.event.workflow_run.conclusion == 'success' &&
       startsWith(github.event.workflow_run.head_branch, 'v'))
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Resolve version
        id: version
        env:
          DISPATCH_VERSION: ${{ github.event.inputs.version }}
          RUN_VERSION: ${{ github.event.workflow_run.head_branch }}
          EVENT_NAME: ${{ github.event_name }}
        run: |
          if [ "$EVENT_NAME" = "workflow_dispatch" ]; then
            echo "tag=${DISPATCH_VERSION}" >> "$GITHUB_OUTPUT"
          else
            echo "tag=${RUN_VERSION}" >> "$GITHUB_OUTPUT"
          fi

      - name: Checkout tap repo
        uses: actions/checkout@v6
        with:
          repository: <org>/homebrew-<name>   # ← change this
          token: ${{ secrets.HOMEBREW_TAP_TOKEN }}
          path: tap

      - name: Update formula url and sha256
        env:
          VERSION: ${{ steps.version.outputs.tag }}
          PYPI_PACKAGE: <name>                 # ← change this (PyPI package name)
        run: |
          VER="${VERSION#v}"
          INFO=$(curl -sf "https://pypi.org/pypi/${PYPI_PACKAGE}/${VER}/json")
          URL=$(echo "$INFO" | python3 -c "import sys,json; d=json.load(sys.stdin); print(next(f['url'] for f in d['urls'] if f['url'].endswith('.tar.gz')))")
          SHA=$(echo "$INFO" | python3 -c "import sys,json; d=json.load(sys.stdin); print(next(f['digests']['sha256'] for f in d['urls'] if f['url'].endswith('.tar.gz')))")
          FORMULA=tap/Formula/${PYPI_PACKAGE}.rb
          python3 - "$FORMULA" "$URL" "$SHA" <<'PYEOF'
          import sys, re
          path, new_url, new_sha = sys.argv[1], sys.argv[2], sys.argv[3]
          with open(path) as f:
              content = f.read()
          content = re.sub(
              r'(  url ")[^"]+\.tar\.gz(")',
              rf'\g<1>{new_url}\g<2>',
              content,
          )
          content = re.sub(
              r'(  url "[^"]+\.tar\.gz"\n  sha256 ")[^"]+(")',
              rf'\g<1>{new_sha}\g<2>',
              content,
          )
          with open(path, "w") as f:
              f.write(content)
          print(f"Updated {path}")
          PYEOF

      - name: Commit and push to tap repo
        env:
          VERSION: ${{ steps.version.outputs.tag }}
          PYPI_PACKAGE: <name>                 # ← change this
        run: |
          cd tap
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add Formula/${PYPI_PACKAGE}.rb
          git diff --cached --quiet && echo "No changes to commit" && exit 0
          git commit -m "chore: bump ${PYPI_PACKAGE} to ${VERSION}"
          git push origin main
```

### publish.yml: CHANGELOG commit pattern

When the publish workflow checks out a tag it's in detached HEAD. To commit
CHANGELOG back to main, copy the file before switching branches:

```yaml
- name: Commit and push CHANGELOG.md
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    if git diff --quiet CHANGELOG.md; then
      echo "No changes to commit"
    else
      cp CHANGELOG.md /tmp/CHANGELOG.md
      git fetch origin main
      git checkout main
      cp /tmp/CHANGELOG.md CHANGELOG.md
      git add CHANGELOG.md
      git commit -m "Update CHANGELOG.md for release ${GITHUB_REF#refs/tags/}"
      git push origin main
    fi
```

### Key gotchas

| Gotcha | Why |
| ------ | --- |
| Use `workflow_run`, not `release: published` | GitHub blocks `release: published` when the release is created via `GITHUB_TOKEN` |
| Guard with `startsWith(head_branch, 'v')` | `workflow_run` fires on every publish run, including pushes to main |
| Copy CHANGELOG before `git checkout main` | Tag checkout = detached HEAD; switching branches discards working tree changes |
| Don't use `dawidd6/action-homebrew-bump-formula` | It unconditionally updates Python resource stanzas and fails on virtualenv formulas |
| `workflow_dispatch` on brew-publish | Lets you rerun for a specific version without pushing a new tag |

### Runtime dependency updates

The workflow only updates the main package URL and SHA256. If you add or change
runtime dependencies, update the resource stanzas manually:

```bash
brew update-python-resources <org>/<name>/<name>
```

Commit the result to the tap repo before tagging the next release.
