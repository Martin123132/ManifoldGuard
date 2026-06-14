# Package Installation

> Compatibility note: `manifold-check` and `manifold-eval` are the preferred CLI commands. Existing automation can continue using `mbt-check` and `mbt-eval` during the transition.

This document records install and smoke-test commands for package-index releases.

The package is not required for local development. Source checkout installs remain supported:

```bash
python -m pip install -e . --no-deps
python -m pip install numpy scipy
```

## PyPI install

After publishing to PyPI:

```bash
python -m pip install manifold-guard
```

Optional embedding-backed mode:

```bash
python -m pip install "manifold-guard[embeddings]"
```

Smoke check:

```bash
manifold-check --version
manifold-eval
```

## TestPyPI install

After publishing to TestPyPI, install with PyPI as an extra dependency source because runtime dependencies such as `numpy` and `scipy` are resolved from PyPI:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple \
  manifold-guard
```

Optional embedding-backed mode:

```bash
python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple \
  "manifold-guard[embeddings]"
```

Smoke check:

```bash
manifold-check --version
manifold-eval
```

Expected evaluator result:

```text
Status: passed
Cases: 220
Passed: 220
Failed: 0
```

## Offline-first guarantee

The default package install keeps core regulation offline-first. Use `manifold-check --no-embeddings` or Python API calls with `use_embeddings=False` when embedding dependencies are unavailable or intentionally disabled.

Embedding-backed behavior remains explicit through `manifold-guard[embeddings]`.
