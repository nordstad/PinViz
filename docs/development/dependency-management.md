# Dependency Management

## Overview

PinViz uses `uv.lock` to ensure reproducible builds across all environments. This lock file is critical for:

- **Reproducible builds**: Same dependencies everywhere
- **Security**: Dependabot monitors `uv.lock` for vulnerabilities
- **CI/CD**: Automated testing with exact dependency versions

## Quick Reference

### Always Commit `uv.lock`

When you modify `pyproject.toml`, always commit the updated `uv.lock` file:

```bash
# After editing pyproject.toml
uv lock          # Update lock file
uv sync --dev    # Sync environment
git add uv.lock pyproject.toml
git commit -m "Add new dependency"
```

### Verify Lock File

Check if `uv.lock` is in sync with `pyproject.toml`:

```bash
uv lock --check
```

This command returns:
- Exit code 0: Lock file is in sync
- Exit code 1: Lock file is out of sync (run `uv lock` to fix)

## Automated Protection

### Pre-commit Hooks

Install pre-commit hooks to automatically validate `uv.lock` before commits:

```bash
# One-time setup
uvx pre-commit install

# The hooks will now run automatically on git commit
```

The pre-commit configuration (`.pre-commit-config.yaml`) includes:
- `uv-lock`: Automatically updates lock file if out of sync
- `ruff`: Lints and formats code
- Basic checks: trailing whitespace, YAML validation, etc.

### CI Pipeline

GitHub Actions automatically validates `uv.lock` on every push and PR:

```yaml
- name: Verify uv.lock is in sync
  run: uv lock --check
```

If the CI fails with a lock file error:

1. Pull the latest changes
2. Run `uv lock` locally
3. Commit and push the updated lock file

## Common Scenarios

### Adding a New Dependency

```bash
# Edit pyproject.toml to add dependency
vim pyproject.toml

# Update lock file
uv lock

# Install the dependency
uv sync --dev

# Commit both files
git add pyproject.toml uv.lock
git commit -m "Add requests dependency"
```

### Dependabot Updates

When Dependabot creates a PR to update dependencies:

1. Dependabot automatically updates `uv.lock`
2. CI validates the lock file
3. Review and merge the PR

### Merge Conflicts

If you have local changes to `uv.lock` and remote changes conflict:

```bash
# Stash local changes
git stash

# Pull latest changes
git pull

# Regenerate lock file (if needed)
uv sync --dev

# Your environment is now in sync
```

## Why This Matters

### For Maintainers

- **Security**: Dependabot can only monitor dependencies it knows about
- **Debugging**: Exact dependency versions help reproduce issues
- **Releases**: Lock file ensures consistent release builds

### For Contributors

- **Onboarding**: New contributors get exact working versions
- **CI Reliability**: Tests run with same dependencies locally and in CI
- **No Surprises**: No "works on my machine" issues

## Troubleshooting

### Lock file out of sync

**Error**: `CI fails with "uv.lock is out of sync"`

**Solution**:
```bash
uv lock
git add uv.lock
git commit -m "Update lock file"
git push
```

### Pre-commit hook fails

**Error**: `pre-commit hook updates uv.lock`

**Solution**: This is expected! The hook auto-fixes the lock file:
```bash
# The lock file is now staged automatically
git commit
```

### Missing dependencies

**Error**: `Import errors after git pull`

**Solution**:
```bash
uv sync --dev
```

## Best Practices

1. **Always commit lock file changes**: Never add `uv.lock` to `.gitignore`
2. **Run `uv lock` after editing `pyproject.toml`**: Keep them in sync
3. **Use pre-commit hooks**: Catch issues before pushing
4. **Review Dependabot PRs promptly**: Keep dependencies up to date
5. **Don't manually edit `uv.lock`**: Always use `uv lock` command

## References

- [uv Documentation](https://docs.astral.sh/uv/)
- [Dependabot Configuration](../.github/dependabot.yml)
- [Pre-commit Configuration](../.pre-commit-config.yaml)
- [CI Workflow](../.github/workflows/ci.yml)
