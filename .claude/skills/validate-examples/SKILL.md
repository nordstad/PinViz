---
name: validate-examples
description: Run full example validation - renders all YAML/JSON configs and executes all Python example scripts, mirroring the CI verify-examples job
---

Run the full example validation pipeline for pinviz. This mirrors the CI `verify-examples` job.

## Steps

### 1. Validate all YAML and JSON config files

Use `pinviz validate` on every config in examples/:

```bash
find examples/ -name "*.yaml" -o -name "*.json" | sort | xargs -I{} sh -c 'echo "Validating {}..." && uv run pinviz validate "{}" --json || echo "FAILED: {}"'
```

Report any failures immediately with the filename and error.

### 2. Render all YAML and JSON configs

Render each config to a temp file to catch layout/rendering errors:

```bash
mkdir -p /tmp/pinviz-validate
find examples/ -name "*.yaml" -o -name "*.json" | sort | while read f; do
  out="/tmp/pinviz-validate/$(basename $f .yaml).svg"
  echo "Rendering $f..."
  uv run pinviz render "$f" -o "$out" || echo "FAILED: $f"
done
```

### 3. Execute all Python example scripts

Run each `*_python.py` script to verify the programmatic API works:

```bash
find examples/ -name "*_python.py" | sort | while read f; do
  echo "Running $f..."
  uv run python "$f" || echo "FAILED: $f"
done
```

### 4. Run example-related tests

```bash
uv run pytest tests/ -k "example" -v --tb=short
```

## Reporting

After all steps, summarize:
- Total configs validated / rendered
- Total Python scripts executed
- Any failures, grouped by step, with filename and error message

Exit with a clear PASS or FAIL status.
