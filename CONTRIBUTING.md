# Contributing to ManifoldGuard

Thanks for helping improve ManifoldGuard. This project is moving toward a product-grade inference-time regulator, so contributions should preserve the core design principle: regulate candidate outputs against supplied reference structure without claiming universal truth access.

## Contribution Priorities

Good contributions usually improve one of these areas:

- Offline-first reliability.
- Deterministic regression coverage.
- Clearer evidence and reporting.
- Better docs for supported behavior and limits.
- Safer handling of dependency, packaging, and CI paths.
- More realistic reference/candidate corpora.

Avoid contributions that:

- Treat ManifoldGuard as a universal fact checker.
- Add network-required behavior to the default path.
- Hide optional dependency failures.
- Change public API signatures without a migration plan.
- Expand claims beyond the frozen evidence in `CLAIMS.md`.

## Development Setup

Core offline setup:

```bash
python -m pip install -e . --no-deps
```

Embedding-enabled setup:

```bash
python -m pip install -e .[embeddings]
```

The default contributor path should keep `use_embeddings=False` and `--no-embeddings` working without `sentence-transformers`.

## Test Expectations

Before proposing a code change, run the narrowest relevant test first, then the full suite when possible:

```bash
python -m pytest -q tests/test_tokens.py tests/test_regulator.py
python -m pytest -q tests/test_cli.py
python -m pytest -q
```

For CI or smoke checks, prefer deterministic offline paths. Do not require real model downloads for routine validation.

## CLI and Report Changes

When changing `manifold-check`, update all relevant surfaces:

- CLI behavior.
- Tests in `tests/test_cli.py`.
- Report schema docs in `docs/report_schema.md`.
- Product support contract in `docs/product_readiness_manifest.json`.
- README examples when user-facing behavior changes.
- `CHANGELOG.md`.

## Claim Discipline

ManifoldGuard claims must stay scoped to supplied reference manifolds and the frozen public corpus. If a change improves empirical results, include the dataset, command, and exact evidence needed to reproduce it.

Do not add marketing language that implies ManifoldGuard has direct access to external truth.

## Pull Request Checklist

- The change preserves offline-first operation.
- Optional embedding behavior remains explicit through `.[embeddings]`.
- Public behavior is documented.
- New or changed behavior has focused tests.
- Report formats remain backward-compatible unless a breaking change is called out.
- Claims remain aligned with `CLAIMS.md`.
- `CHANGELOG.md` records user-visible changes.
