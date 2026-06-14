# Pull Request

## Summary

Describe the change and why it moves ManifoldGuard toward a better reference-bound regulator or product surface.

## Type of Change

- [ ] Regulator behavior
- [ ] CLI/reporting
- [ ] Regression corpus
- [ ] Documentation
- [ ] Packaging/release/CI
- [ ] Governance/support

## Offline-First Checklist

- [ ] Core behavior still works with `--no-embeddings` / `use_embeddings=False`.
- [ ] Optional embedding behavior remains behind `.[embeddings]`.
- [ ] No routine validation path requires model downloads.

## Product Surface Checklist

- [ ] User-facing behavior is documented.
- [ ] Report schema changes are reflected in `docs/report_schema.md`.
- [ ] Support contract changes are reflected in `docs/product_readiness_manifest.json`.
- [ ] `CHANGELOG.md` records user-visible changes.

## Claim Discipline

- [ ] This PR does not claim ManifoldGuard is a universal fact checker.
- [ ] Any performance or safety claim is tied to reproducible commands, corpora, or frozen ledgers.
- [ ] Claim wording remains aligned with `CLAIMS.md`.

## Tests

List commands run, or explain why validation was not run.

```text

```
