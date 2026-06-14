# Release Checklist

Use this checklist before publishing a release candidate, final release, or public performance claim. The canonical maintainer sequence is documented in `RELEASE_PROCESS.md`.

## Release Identity

- Confirm the intended version in `pyproject.toml`.
- Confirm `mbt-check --version` reports the intended version after install.
- Confirm `docs/product_readiness_manifest.json` `project.package_version` matches `pyproject.toml` version.
- Confirm installed distribution version from `mbt-ai-tools` metadata matches both manifest and `pyproject.toml` version.
- Confirm `CHANGELOG.md` has a dated section for the release.
- Confirm package URLs point to the public repository.
- Confirm the release tag name matches the changelog section.

## Offline-First Install Gate

The core install must remain usable without embedding dependencies:

```bash
python -m pip install -e .
python -m pip install -e . --no-deps
python -m pytest -q
```

Required evidence:

- Full test suite passes.
- `python scripts/preflight.py` passes (docs + tests, includes schema validation).
- `--no-embeddings` CLI regulation works.
- `use_embeddings=False` Python API regulation works.
- JSON, Markdown, and CSV report modes work without optional embedding dependencies.

## Embeddings Install Gate

The optional embedding extra must remain explicit:

```bash
python -m pip install -e .[embeddings]
```

Required evidence:

- Import-level smoke checks pass.
- CI installability matrix runs `python -m pip install -e . --no-deps` and `python -m pip install -e .[embeddings]` on Ubuntu with public entrypoints importable in both modes.
- `docs-quality` workflow includes the same two-mode installability smoke checks.
- `python scripts/preflight.py --docs-only` passes for embeddings mode.
- No CI step requires real model downloads.
- Missing dependency errors remain actionable when the extra is absent.
- Token-shock paths remain available when embedding dependencies are installed.

## CI Parity Gate

Before merging release-bound changes:

1. Run the preflight matrix path in CI:

```bash
python scripts/preflight.py
python scripts/preflight.py --docs-only
```

2. Confirm `python scripts/docs_quality.py --skip-schema` and `python scripts/docs_quality.py` pass in at least one clean environment.

3. Generate release evidence:

```bash
python scripts/validate_examples.py
mbt-eval
mbt-eval --output regulator-evaluation.json
python scripts/evaluate_regulator.py
python scripts/evaluate_regulator.py --output regulator-evaluation.json
python scripts/build_eval_report.py --input regulator-evaluation.json --output docs/evaluation_report.md
python scripts/release_evidence.py --run --output release-evidence.json
python scripts/release_readiness.py --evidence release-evidence.json
```

Equivalent one-command path:

```bash
python scripts/release_check.py --output release-evidence.json
```

Required evidence:

- Example fixture validation exits successfully.
- Frozen regression corpus evaluation reports `Status: passed`.
- Frozen regression corpus JSON output includes taxonomy metrics by case family.
- Installed `mbt-eval` and `python scripts/evaluate_regulator.py` remain equivalent.
- The packaged default corpus for `mbt-eval` is included in package data.
- `docs/evaluation_report.md` is regenerated from the regulator evaluation artifact.
- `summary.status` is `passed`.
- Every required gate has status `passed`.
- Release readiness prints `Status: ready`.
- The JSON file is stored with release notes or attached to the release candidate review.
- Core CI uploads `release-evidence.json` and `regulator-evaluation.json` as workflow artifacts.

### Manual CI path (optional)

For release-incident triage, run the release workflow with inputs to control scope:

- `run_installability`: enable/disable installability matrix
- `run_preflight`: enable/disable preflight matrix
- `run_tests`: enable/disable test matrix

```yaml
on:
  workflow_dispatch:
    inputs:
      run_installability:
        description: Run installability matrix
        required: false
        default: true
        type: boolean
      run_preflight:
        description: Run preflight matrix
        required: false
        default: true
        type: boolean
      run_tests:
        description: Run test matrix
        required: false
        default: true
        type: boolean
```

For docs-quality workflow triage, control scope with:

```yaml
on:
  workflow_dispatch:
    inputs:
      run_core_mode:
        description: Run core mode docs-quality checks
        required: false
        default: true
        type: boolean
      run_embeddings_mode:
        description: Run embeddings mode docs-quality checks
        required: false
        default: true
        type: boolean
      run_schema_checks:
        description: Run schema validation checks
        required: false
        default: true
        type: boolean
```

## CLI Report Gate

Run a deterministic batch fixture:

```bash
mbt-check --input-jsonl examples/batch_input.jsonl --no-embeddings --summary --fail-on-block
mbt-check --input-jsonl examples/batch_input.jsonl --no-embeddings --format markdown --output audit.md
mbt-check --input-jsonl examples/batch_input.jsonl --no-embeddings --format csv --output audit.csv
```

Required evidence:

- JSONL batch output has one report per input row.
- `--summary` appends a final summary record.
- `--fail-on-block` returns status `2` when any row blocks.
- Markdown output is readable as an audit report.
- CSV output opens as one row per candidate evaluation.
- `--token-shock` is accepted only when embedding dependencies are available.

## Documentation Gate

Confirm these documents match release behavior:

- `README.md`
- `CLAIMS.md`
- `REPLICATION.md`
- `RELEASE_PROCESS.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `SUPPORT.md`
- `docs/report_schema.md`
- `docs/product_readiness_manifest.json`
- `docs/quality_gates.md`
- Release scripts listed in the product readiness manifest exist and are runnable.

Required evidence:

- Install guidance shows both core and `.[embeddings]` modes.
- Report docs cover JSON, Markdown, and CSV.
- Support boundaries still say MBT-5 is not a universal fact checker.
- Public claims are limited to supplied references and frozen corpus evidence.

## Claim Gate

Before adding or changing any public claim:

- Identify the exact dataset or ledger.
- Record the exact command or procedure.
- Record the confusion matrix or metric output.
- Confirm the claim does not imply external truth access.
- Confirm the claim is scoped to supplied reference manifolds.

Do not release marketing or README copy that expands beyond `CLAIMS.md`.

## GitHub Release Gate

Before publishing a GitHub release:

- Main branch CI is green.
- Release tag CI is green.
- Release notes list user-facing changes.
- Known limitations are stated plainly.
- Generated reports or examples are deterministic and free of secrets.

After publishing:

- Confirm the release page points to the correct tag.
- Confirm the tag points to the intended commit.
- Confirm issue templates and support docs are visible in GitHub.

## Package Publish Gate

Before publishing to a package index:

- Confirm `.github/workflows/package-publish.yml` built distributions on the release tag.
- Confirm `python -m twine check dist/*` passed in CI.
- Confirm PyPI Trusted Publishing environments exist for `testpypi` and `pypi`.
- Publish to TestPyPI first with `workflow_dispatch`, `target=testpypi`, and `publish=true`.
- Publish to PyPI only after TestPyPI install smoke checks pass.

Do not publish packages from a blocked release evidence report.
