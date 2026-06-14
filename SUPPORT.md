# Support

This project supports ManifoldGuard as a reference-bound output regulator. It is not support for general fact checking, arbitrary model evaluation, or external truth verification.

## Best Places to Start

- `README.md` for installation, CLI usage, and the project overview.
- `docs/report_schema.md` for JSON, Markdown, and CSV report contracts.
- `docs/product_readiness_manifest.json` for supported install modes, CLI formats, CI policy, and support boundaries.
- `CLAIMS.md` for the public claim scope.
- `REPLICATION.md` for reproducing the public result.

## When Opening an Issue

Include:

- The exact command or Python snippet.
- The install mode: core or `.[embeddings]`.
- The value of `manifold-check --version`.
- Whether `--no-embeddings` or `use_embeddings=False` was used.
- Minimal references and candidates that reproduce the behavior.
- The actual output and expected output.
- Relevant report format: text, JSON, Markdown, CSV, or Python API.

## Supported Questions

Good issue topics:

- A candidate is emitted or blocked unexpectedly against supplied references.
- A documented CLI mode behaves inconsistently.
- A report schema field is missing, unstable, or unclear.
- Offline-first install behavior regresses.
- Optional embedding dependency handling is confusing or broken.
- Public docs overstate or understate the supported claim.

Out-of-scope topics:

- Asking ManifoldGuard to determine external truth without references.
- Claims about untested private datasets without reproducible evidence.
- Network/model download failures outside the optional embedding path.
- Requests to hide or bypass regulator clamps.

## Response Expectations

This is an early release-candidate project. Reports with minimal reproductions and clear expected behavior will be easiest to triage.
