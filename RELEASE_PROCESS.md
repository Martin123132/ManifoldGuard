# Release Process

This is the canonical maintainer flow for MBT-5 release candidates, final releases, and public performance claims. It turns the release checklist, quality gates, install modes, and generated evidence into one repeatable handoff.

## 1. Confirm release identity

Before running release gates, confirm the release target is internally consistent:

- `pyproject.toml` contains the intended version.
- `mbt-check --version` reports the intended version after install.
- Installed `mbt-ai-tools` distribution metadata reports the same version.
- `docs/product_readiness_manifest.json` `project.package_version` matches the package version.
- `CHANGELOG.md` contains a dated section for the release before tagging.
- Package URLs point to the public GitHub repository.
- The release tag name matches the changelog section.

Do not tag a release while version, manifest, metadata, or changelog identity is inconsistent.

## 2. Confirm install modes

MBT-5 is offline-first by default. The core path must remain usable without embedding dependencies:

```bash
python -m pip install -e .
python -m pip install -e . --no-deps
```

The optional embedding path must remain explicit:

```bash
python -m pip install -e .[embeddings]
```

If `sentence-transformers` is unavailable, use offline literal/relation-only regulation with `--no-embeddings` / `use_embeddings=False`.

Embedding-backed paths may expose token-shock diagnostics. Strict offline CLI mode rejects `--token-shock` when `--no-embeddings` is selected.

## 3. Run local gates

Run the deterministic checks from a clean working environment before release review:

```bash
python scripts/validate_examples.py
python scripts/docs_quality.py
mbt-eval
mbt-eval --output regulator-evaluation.json
python scripts/evaluate_regulator.py
python scripts/evaluate_regulator.py --output regulator-evaluation.json
python scripts/build_eval_report.py --input regulator-evaluation.json --output docs/evaluation_report.md
python -m pytest -q
python scripts/preflight.py
python scripts/preflight.py --docs-only
```

Required evidence:

- Example fixtures validate against current CLI behavior.
- Docs-quality exits successfully.
- Frozen regression corpus evaluation reports `Status: passed`.
- Frozen regression corpus JSON output includes taxonomy metrics by case family.
- Installed `mbt-eval` and script-based evaluator paths are equivalent.
- The packaged default corpus for `mbt-eval` is included in package data.
- `docs/evaluation_report.md` is regenerated from `regulator-evaluation.json`.
- Full pytest suite passes.
- Full preflight prints `Preflight completed successfully.`.
- Docs-only preflight prints `Preflight completed successfully.`.

If any gate fails, fix the underlying issue before generating release evidence.

The one-command maintainer path is:

```bash
python scripts/release_check.py --output release-evidence.json
```

## 4. Generate release evidence

Create a machine-readable release evidence file:

```bash
python scripts/release_evidence.py --run --output release-evidence.json
```

Required evidence:

- `summary.status` is `passed`.
- Every required gate has status `passed`.
- Command outputs are bounded and free of secrets.
- The generated JSON file is stored with release notes or release-candidate review material.

## 5. Check release readiness

Summarize the generated evidence:

```bash
python scripts/release_readiness.py --evidence release-evidence.json
```

Required output:

```text
Status: ready
Blockers: none
```

Do not publish, tag, or expand public claims if readiness reports `blocked`.

## 6. Confirm CI parity

GitHub Actions should mirror the release process:

- Core mode installs with `python -m pip install -e . --no-deps` and runs the full offline suite.
- Embeddings mode installs with `python -m pip install -e .[embeddings]` and runs deterministic smoke checks.
- Docs-quality workflow validates required docs, examples, schema fixtures, package URL parity, and installability smoke checks.
- Core CI uploads `release-evidence.json` and `regulator-evaluation.json` as release artifacts.
- No CI step requires real embedding model downloads.
- Manual `workflow_dispatch` controls remain documented in `docs/release_checklist.md`.

Release-bound commits should have green workflow results before tagging.

## 7. Enforce claim discipline

MBT-5 regulates output against supplied references. It does not know external truth.

Before adding or repeating a public claim:

- Identify the exact dataset, frozen corpus, ledger, or supplied reference manifest.
- Record the exact command or procedure.
- Record the metric output or confusion matrix.
- Confirm the claim does not imply external truth access.
- Confirm `CLAIMS.md`, `REPLICATION.md`, and `docs/product_readiness_manifest.json` support the wording.

Do not release README, changelog, marketing, or issue-template copy that expands beyond `CLAIMS.md`.

## 8. Tag and release handoff

Only tag after local gates, release evidence, readiness summary, and CI parity are green:

- Tag the exact commit that produced the passing evidence.
- Attach or store `release-evidence.json` with the release review.
- Release notes summarize user-facing changes.
- Known limitations are stated plainly.
- Support docs and issue templates are visible from the repository.

## 9. Package publishing

Package artifacts are built by `.github/workflows/package-publish.yml` on version tags and manual runs.

Publishing policy:

- Tag pushes build distributions and run `twine check`.
- Publishing is manual-only through `workflow_dispatch`.
- Use `target=testpypi` and `publish=true` before attempting `target=pypi`.
- Configure PyPI Trusted Publishing environments named `testpypi` and `pypi` before publishing.
- Do not publish packages when release readiness is blocked.

After publishing:

- Confirm the release page points to the correct tag.
- Confirm the tag points to the intended commit.
- Confirm package URLs and documentation links resolve.

## 10. Failure policy

If any required gate fails or readiness reports blockers:

- Do not publish a tag.
- Do not describe the build as release-ready.
- Fix the failing gate or narrow the release scope.
- Regenerate `release-evidence.json`.
- Re-run `scripts/release_readiness.py`.

The release is ready only when the evidence file passes and readiness reports `Status: ready` with `Blockers: none`.
