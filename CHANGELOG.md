# Changelog

## 0.1.0 Release Candidate - 2026-06-10

- Kept the default package install offline-first by moving `sentence-transformers` behind the optional `.[embeddings]` extra.
- Added CI coverage for both dependency modes: full offline core tests and deterministic embeddings-mode smoke tests.
- Added clearer missing-dependency guidance for embedding-backed paths.
- Hardened unsupported negation handling across contractions, auxiliary verbs, future modals, and `has no` forms.
- Added configurable `token_shock_map` controls for `max_samples`, `top_k`, and output ordering.
- Documented install modes consistently across README, replication notes, and claims scope.
- Verified the local focused and full suites with `25 passed` and `26 passed`.
