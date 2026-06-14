# Security Policy

ManifoldGuard is an inference-time regulator library and CLI. Security reports should focus on behavior that could cause unsafe execution, misleading audit output, dependency confusion, packaging risk, or accidental exposure of private input data.

## Supported Versions

The active supported line is the current `main` branch and the latest published release candidate or release tag.

## Reporting a Vulnerability

Please report security issues privately to the project maintainer before opening a public issue.

Include:

- A short description of the issue.
- A minimal reproduction command or script.
- The install mode used: core or `.[embeddings]`.
- Whether the issue requires optional embedding dependencies.
- Any affected CLI output format: text, JSON, Markdown, or CSV.
- Expected impact and any known workaround.

If no private contact is available, open a GitHub issue with limited detail and mark it as a security-sensitive report request. Do not include exploit payloads, private data, tokens, model credentials, or proprietary corpora in public issues.

## Security Boundaries

ManifoldGuard does not execute candidate text as code. Candidate and reference text should still be treated as untrusted input when integrating the CLI into larger automation.

Recommended integration practices:

- Pass inputs through files or argument arrays rather than shell-concatenated strings.
- Keep audit artifacts free of secrets and private personal data.
- Avoid uploading proprietary references or candidates to public CI logs.
- Use `--no-embeddings` for deterministic offline validation.
- Pin dependency versions in production environments.

## Dependency Model

The core install is designed to remain lightweight and offline-first. Embedding-backed behavior is optional through:

```bash
python -m pip install -e .[embeddings]
```

Security-sensitive deployments should review optional transitive dependencies before enabling embedding-backed operation.
