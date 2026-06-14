# Package Installation

This document records install and smoke-test commands for package-index releases.

The package is not required for local development. Source checkout installs remain supported:

```bash
python -m pip install -e . --no-deps
python -m pip install numpy scipy
```

## PyPI install

After publishing to PyPI:

```bash
python -m pip install mbt-ai-tools
```

Optional embedding-backed mode:

```bash
python -m pip install "mbt-ai-tools[embeddings]"
```

Smoke check:

```bash
mbt-check --version
mbt-eval
```

## TestPyPI install

After publishing to TestPyPI, install with PyPI as an extra dependency source because runtime dependencies such as `numpy` and `scipy` are resolved from PyPI:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple \
  mbt-ai-tools
```

Optional embedding-backed mode:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple \
  "mbt-ai-tools[embeddings]"
```

Smoke check:

```bash
mbt-check --version
mbt-eval
```

Expected evaluator result:

```text
Status: passed
Cases: 220
Passed: 220
Failed: 0
```

## Offline-first guarantee

The default package install keeps core regulation offline-first. Use `mbt-check --no-embeddings` or Python API calls with `use_embeddings=False` when embedding dependencies are unavailable or intentionally disabled.

Embedding-backed behavior remains explicit through `mbt-ai-tools[embeddings]`.
