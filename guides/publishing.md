# Publishing to PyPI

The project uses GitHub Actions for automated PyPI publishing. **IMPORTANT:** Follow this exact process to avoid workflow failures.

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

### Step 1: Bump Version

Update the version in `pyproject.toml`:

```bash
# Edit pyproject.toml and change version number
# Example: version = "0.9.1"
```

### Step 2: Commit Version Bump

```bash
git add pyproject.toml
git commit -m "chore: bump version to 0.9.1"
git push origin main
```

### Step 3: Create and Push Git Tag ONLY

```bash
# Create tag locally
git tag v0.9.1

# Push ONLY the tag (do NOT create a GitHub Release manually)
git push origin v0.9.1
```

### Step 4: Let the Workflow Handle Everything

The GitHub Actions workflow (`.github/workflows/publish.yml`) will automatically:

1. ✅ Build the package
2. ✅ Run comprehensive smoke tests
3. ✅ Publish to PyPI with trusted publishing
4. ✅ Create a GitHub Release with auto-generated release notes
5. ✅ Update `CHANGELOG.md` with release information
6. ✅ Run post-publish integration tests on Python 3.12 and 3.13

## Common Mistakes to Avoid

### DO NOT: Create a GitHub Release manually through the GitHub UI

Creating a GitHub Release manually will:

- Automatically create a git tag
- Trigger the publish workflow
- Cause the workflow to fail when it tries to create the same release again
- Result in error: `Validation Failed: {"resource":"Release","code":"already_exists","field":"tag_name"}`

### DO: Only push git tags and let the workflow create the GitHub Release

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

**If the workflow fails:**

1. **Check which stage failed:**
   - Build stage: Fix code/tests and create a new patch version
   - Publish stage: Check PyPI credentials and permissions
   - Test stage: The package is already published; fix issues in next release

2. **If a release exists but workflow failed:**
   - The package is likely already on PyPI (check <https://pypi.org/project/pinviz/>)
   - Delete the GitHub Release if needed: `gh release delete v0.9.1`
   - Delete the tag: `git tag -d v0.9.1 && git push origin --delete v0.9.1`
   - Fix the issue and retry with a new patch version

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
