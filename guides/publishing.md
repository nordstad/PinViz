# Publishing to PyPI

The project uses GitHub Actions for automated PyPI publishing. **IMPORTANT:** Follow this exact process to avoid workflow failures.

## Quick Reference (TL;DR)

```bash
# 1. Update version and CHANGELOG
vim pyproject.toml  # Change version to "0.13.0"
vim CHANGELOG.md    # Move [Unreleased] → [0.13.0] with date

# 2. Commit and push
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.13.0"
git push

# 3. Create and push tag (ONLY!)
git tag v0.13.0
git push origin v0.13.0

# 4. Wait for workflow - it handles everything automatically!
# ✅ Builds package
# ✅ Publishes to PyPI
# ✅ Creates GitHub release (DO NOT create manually!)
# ✅ Updates CHANGELOG

# ❌ DO NOT: gh release create v0.13.0
# ❌ DO NOT: Create release via GitHub UI
```

## ⚠️ CRITICAL: DO NOT Manually Create GitHub Releases

**❌ NEVER DO THIS:**
```bash
# DO NOT create releases manually with gh CLI
gh release create v0.13.0 --title "..." --notes "..."

# DO NOT create releases through GitHub web UI
# (Releases → Draft a new release → Create release)
```

**Why this fails:**
1. Creating a GitHub release manually triggers the publish workflow
2. The workflow tries to create the same release → **FAILS** with error:
   ```
   RequestError [HttpError]: Validation Failed:
   {"resource":"Release","code":"already_exists","field":"tag_name"}
   ```
3. Package gets published to PyPI ✅ but workflow shows as failed ❌
4. Release format doesn't match previous releases (breaks consistency)

**✅ CORRECT APPROACH:**
```bash
# 1. Just push the git tag
git tag v0.13.0
git push origin v0.13.0

# 2. Wait for the workflow to automatically:
#    - Build package
#    - Publish to PyPI
#    - Create GitHub release (with standard format)
```

The workflow creates releases automatically with the correct format and author (`github-actions[bot]`).

---

## Correct Publishing Process

### Step 0: Pre-Publish Validation (CRITICAL)

**Before bumping the version**, run these checks to catch issues early:

```bash
# 1. Run all tests locally
uv run pytest

# 2. Run the full CI test suite
uv run pytest --cov=src/pinviz --cov-report=term-missing

# 3. CRITICAL: Validate post-publish tests with current API
# This catches outdated API usage that would fail after publishing
./scripts/validate-post-publish-tests.sh

# 4. Test package build
uv build
uv pip install dist/*.whl --force-reinstall
uv run pinviz --version
uv run pinviz example bh1750 -o test.svg

# 5. Check for breaking API changes
# If you modified the public API, update .github/workflows/publish.yml
# Search for these patterns and update if needed:
#   - "from pinviz import ..."
#   - "devices.*("
#   - "boards.*("
```

**Why this matters**: The post-publish integration tests in `.github/workflows/publish.yml` run AFTER the package is published to PyPI. If they fail due to outdated API usage, the package is already live but marked as failed. This validation script catches these issues BEFORE publishing.

### Step 1: Bump Version and Update CHANGELOG

Update both `pyproject.toml` and `CHANGELOG.md`:

```bash
# 1. Edit pyproject.toml and change version number
# Example: version = "0.13.0"

# 2. Edit CHANGELOG.md and move [Unreleased] section to new version
# Change:
#   ## [Unreleased]
#   ### Added
#   - Feature X
# To:
#   ## [Unreleased]
#
#   ## [0.13.0] - 2026-02-11
#   ### Added
#   - Feature X
```

### Step 2: Commit Version Bump

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.13.0"
git push origin main
```

### Step 3: Create and Push Git Tag ONLY

**⚠️ CRITICAL: Only create the git tag. Do NOT create a GitHub Release!**

```bash
# Create tag locally
git tag v0.9.1

# Push ONLY the tag
git push origin v0.9.1

# ❌ DO NOT run: gh release create v0.9.1
# ❌ DO NOT use GitHub UI to create release
# The workflow will create the release automatically!
```

**What happens next:**
1. Tag push triggers `.github/workflows/publish.yml`
2. Workflow builds, tests, and publishes to PyPI
3. Workflow automatically creates GitHub release with standard format
4. Workflow updates CHANGELOG.md
5. Done! ✅

### Step 4: Let the Workflow Handle Everything

The GitHub Actions workflow (`.github/workflows/publish.yml`) will automatically:

1. ✅ Build the package
2. ✅ Run comprehensive smoke tests
3. ✅ Publish to PyPI with trusted publishing
4. ✅ Create a GitHub Release with auto-generated release notes
5. ✅ Update `CHANGELOG.md` with release information
6. ✅ Run post-publish integration tests on Python 3.12 and 3.13

## Common Mistakes to Avoid

### ❌ MISTAKE #1: Creating GitHub Releases Manually

**DON'T DO THIS:**
- ❌ Creating releases through GitHub web UI (Releases → Draft new release)
- ❌ Using `gh release create v0.x.x` CLI command
- ❌ Creating release before/after pushing tag manually

**WHY IT FAILS:**
1. Manual release creation happens at a different time than workflow execution
2. Creates a race condition: workflow tries to create release that already exists
3. Results in workflow failure with error:
   ```
   RequestError [HttpError]: Validation Failed:
   {"resource":"Release","code":"already_exists","field":"tag_name"}
   ```
4. Package publishes successfully to PyPI ✅ but workflow shows failed ❌
5. Release format differs from previous releases (author, format, content)

**CORRECT APPROACH:**
✅ **Only push git tags** → Let the workflow create the release automatically

**Timeline comparison:**

**❌ Wrong (manual release):**
```
1. git tag v0.13.0
2. git push --tags
3. Workflow starts...
4. Meanwhile, YOU run: gh release create v0.13.0  ← DON'T DO THIS
5. Workflow publishes to PyPI ✅
6. Workflow tries to create release → FAILS ❌ (already exists)
```

**✅ Correct (automated):**
```
1. git tag v0.13.0
2. git push --tags
3. Workflow runs:
   - Builds package
   - Publishes to PyPI ✅
   - Creates release ✅
   - Done!
```

**IF YOU ALREADY MADE THIS MISTAKE:**
```bash
# 1. Delete the manual release
gh release delete v0.13.0 --yes

# 2. Re-run the failed workflow job
gh run list --workflow=publish.yml --limit 1  # Get run ID
gh run rerun <run-id> --failed

# 3. Workflow will now create release successfully
```

### ✅ CORRECT: Only push git tags and let the workflow handle releases

## Workflow Stages

### Stage 1: Build and Validate (runs on tag push)

```bash
# Pre-publish checks:
- Build wheel and source distribution with uv
- Validate package metadata with twine
- Install built wheel in clean environment
- Run 10 smoke tests covering all features
- Test CLI installation, examples, validation, logging
```

### Stage 2: Publish to PyPI (after build succeeds)

```bash
# PyPI publication:
- Download build artifacts
- Publish to PyPI using trusted publishing (no API tokens needed)
- Create GitHub Release with auto-generated notes
- Update CHANGELOG.md with release information
- Commit and push CHANGELOG changes to main branch
```

### Stage 3: Test Published Package (after publish succeeds)

```bash
# Post-publish verification:
- Test on Python 3.12 and 3.13
- Install from PyPI with retry logic (handles propagation delay)
- Run 11 comprehensive integration tests
- Verify Python API, CLI commands, device templates
- Test validation, wire styles, multi-device scenarios
```

## Monitoring the Release

After pushing a tag, monitor the workflow:

```bash
# View recent workflow runs
gh run list --workflow=publish.yml --limit 5

# Watch the current run in real-time
gh run watch

# View logs if there are failures
gh run view --log-failed
```

## Troubleshooting

### Issue #1: Workflow fails with "Release already exists"

**Symptoms:**
```
RequestError [HttpError]: Validation Failed:
{"resource":"Release","code":"already_exists","field":"tag_name"}
```
- Package shows up on PyPI ✅
- Workflow shows as failed ❌
- Release exists on GitHub with wrong format/author

**Cause:** You manually created a GitHub release (via CLI or web UI)

**Fix:**
```bash
# 1. Delete the manual release
gh release delete v0.13.0 --yes

# 2. Get the failed workflow run ID
gh run list --workflow=publish.yml --limit 1

# 3. Re-run the failed job
gh run rerun <run-id> --failed

# 4. Workflow will now create the release successfully
```

**Prevention:** Never manually create releases! Only push tags and let the workflow handle everything.

---

### Issue #2: Other Workflow Failures

**If the workflow fails:**

1. **Check which stage failed:**
   - Build stage: Fix code/tests and create a new patch version
   - Publish stage: Check PyPI credentials and permissions (or see Issue #1 above)
   - Test stage: The package is already published; fix issues in next release

2. **If you need to completely redo a release:**
   - Check if package is on PyPI: <https://pypi.org/project/pinviz/>
   - If published to PyPI: You CANNOT republish the same version (PyPI doesn't allow it)
   - Delete GitHub Release: `gh release delete v0.9.1 --yes`
   - Delete the tag locally: `git tag -d v0.9.1`
   - Delete the tag remotely: `git push origin --delete v0.9.1`
   - Increment to a new patch version (e.g., v0.9.2) and try again

3. **PyPI package not appearing immediately:**
   - The workflow includes retry logic with 30-second delays
   - PyPI propagation can take 1-2 minutes
   - The test stage will retry up to 5 times (2.5 minutes total)

## Version Numbering

Follow semantic versioning (semver):

- **Major (1.0.0)**: Breaking changes, incompatible API changes
- **Minor (0.9.0)**: New features, backward-compatible
- **Patch (0.9.1)**: Bug fixes, backward-compatible

## Pre-Release Versions

For alpha/beta releases, append suffix to version:

```toml
version = "0.10.0-beta.1"
```

The workflow automatically marks releases with `-` in the version as pre-releases on GitHub.
