# Quality Gates

These gates define what "product standard" means for MBT-5 work. A change does not need every gate for every commit, but release candidates should satisfy all applicable gates.

## Gate 1: Offline-First Reliability

MBT-5 must remain useful without optional embedding dependencies.

Evidence:

- `use_embeddings=False` works through the Python API.
- `--no-embeddings` works through the CLI.
- Core tests do not require network access or model downloads.
- Base install behavior is documented.

## Gate 2: Deterministic Regression Coverage

Regulator changes must be covered by stable examples.

Evidence:

- Focused tests cover new clamps or scoring behavior.
- Regression corpus examples are deterministic.
- Committed CLI output examples are checked with `python scripts/validate_examples.py`.
- Frozen corpus expectations are evaluated with `python scripts/evaluate_regulator.py`.
- Installed evaluator command `mbt-eval` exposes the same offline corpus check.
- Package data includes the default corpus used by `mbt-eval`.
- Frozen corpus metrics include taxonomy summaries by case family for release triage.
- `docs/evaluation_report.md` can be regenerated from `regulator-evaluation.json`.
- Expected blocks and emits are explained by reference structure.
- Edge cases include at least one safe candidate and one all-bad abstention path when relevant.

## Gate 3: Report Contract Stability

Report formats are product surfaces.

Evidence:

- JSON fields are documented in `docs/report_schema.md`.
- Machine-readable contract is in `docs/report_schema.json`.
- Markdown output remains readable for audits.
- CSV output remains one row per candidate evaluation.
- Exit codes remain documented.
- Token-shock requires embedding-backed dependencies and is disabled in strict offline (`--no-embeddings`) mode by CLI validation.
- Breaking report changes are called out in `CHANGELOG.md`.
- Local schema validation uses `scripts/docs_quality.py` (and `scripts/validate_reports.py` for focused fixture checks).

## Gate 4: Optional Dependency Discipline

Embedding-backed behavior must stay opt-in.

Evidence:

- `sentence-transformers` stays under `.[embeddings]`.
- Missing dependency errors suggest either installing extras or using offline mode.
- CI smoke checks avoid model downloads.
- Token-shock behavior is tested without making embeddings a default install requirement.

## Gate 5: Claim Discipline

MBT-5 regulates against supplied references. It does not know external truth.

Evidence:

- Claims are scoped to frozen ledgers, public corpora, or explicitly supplied references.
- README and `CLAIMS.md` stay aligned.
- New public claims include reproducible commands or data.
- Docs avoid universal fact-checker language.

## Gate 6: User-Facing Ergonomics

Users should be able to install, run, inspect, and report issues without guessing.

Evidence:

- CLI help exposes supported flags.
- `mbt-check --version` works.
- README includes common commands.
- Examples exist for batch input and report output.
- GitHub issue templates request enough reproduction detail.

## Gate 7: Release Traceability

Every release should be reconstructable from public evidence.

Evidence:

- `CHANGELOG.md` names user-visible changes.
- Release checklist is complete.
- `RELEASE_PROCESS.md` documents the maintainer release sequence from install modes through evidence, readiness, CI parity, and tagging.
- Preflight parity is verified for both install modes:
  - `python scripts/preflight.py` (core path)
  - `python scripts/preflight.py --docs-only` (embeddings path)
- GitHub Actions pass on the release commit or tag.
- Package metadata points to the correct repository.
- Package URL metadata is kept aligned between `pyproject.toml` and `docs/product_readiness_manifest.json`.
- Installed distribution version is consistent with release identity (`project.package_version` and `pyproject.toml`).
- Installability is validated in CI with both `python -m pip install -e . --no-deps` and `python -m pip install -e .[embeddings]` smoke checks.
- Product manifest validates install-mode contracts (core + embeddings definitions and CI policy modes).
- Release evidence can be generated with `python scripts/release_evidence.py --run --output release-evidence.json`.
- Release readiness can be summarized with `python scripts/release_readiness.py --evidence release-evidence.json`.
- The combined release process can be run with `python scripts/release_check.py --output release-evidence.json`.
- Core CI uploads the generated release evidence JSON and regulator evaluation JSON as workflow artifacts.
- Support boundaries are clear in docs and issue templates.
- `scripts/preflight.py` is run before release for combined checks and should reproduce locally.

## Gate 8: Package Publishing Safety

Publishing packages must be explicit and reversible during release-candidate validation.

Evidence:

- Distribution artifacts build on release tags.
- `twine check` passes before any publish step.
- Trusted Publishing setup values are documented in `docs/package_publishing.md`.
- Package-index install and smoke commands are documented in `docs/package_installation.md`.
- PyPI publishing requires manual workflow dispatch with `publish=true`.
- TestPyPI is used before PyPI.
- Trusted Publishing environments are named `testpypi` and `pypi`.
- No package publish happens from a blocked release readiness report.
