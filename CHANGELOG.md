# Changelog

## Unreleased

- Added CLI JSON regulation reports with emitted candidate index, per-candidate scores, clamp summaries, relations, and negated relations.
- Added optional CLI token-shock reporting controls for regulation reports.
- Added `--output` for writing CLI output to files.
- Added `--input-jsonl` for batch regulation reports.
- Added `--summary` and `--fail-on-block` for CI-friendly batch guard usage.
- Documented the JSON report schema under `docs/`.
- Added a CLI JSON report demo under `examples/`.
- Updated GitHub Actions dependencies to Node 24-compatible major versions.

## 0.1.0 Release Candidate - 2026-06-10

- Kept the default package install offline-first by moving `sentence-transformers` behind the optional `.[embeddings]` extra.
- Added CI coverage for both dependency modes: full offline core tests and deterministic embeddings-mode smoke tests.
- Added clearer missing-dependency guidance for embedding-backed paths.
- Hardened unsupported negation handling across contractions, auxiliary verbs, future modals, and `has no` forms.
- Added configurable `token_shock_map` controls for `max_samples`, `top_k`, and output ordering.
- Documented install modes consistently across README, replication notes, and claims scope.
- Verified the local focused and full suites with `25 passed` and `26 passed`.
