# Package Publishing Setup

This document records the package publishing setup for `mbt-ai-tools`.

Publishing is intentionally manual-only. The package workflow builds distributions on tags and manual runs, but it publishes only when a maintainer runs the workflow with `publish=true`.

## Current repository setup

GitHub repository:

- Owner: `Martin123132`
- Repository: `Geometry-Only-Control-of-LLM-Output-at-Inference-Time`
- Publishing workflow: `.github/workflows/package-publish.yml`

GitHub environments:

- `testpypi`
- `pypi`

Both environments are required by `.github/workflows/package-publish.yml`.

## Trusted Publishing values

Configure these values on TestPyPI first:

- Project name: `mbt-ai-tools`
- Owner: `Martin123132`
- Repository name: `Geometry-Only-Control-of-LLM-Output-at-Inference-Time`
- Workflow filename: `package-publish.yml`
- Environment name: `testpypi`

Configure these values on PyPI after TestPyPI succeeds:

- Project name: `mbt-ai-tools`
- Owner: `Martin123132`
- Repository name: `Geometry-Only-Control-of-LLM-Output-at-Inference-Time`
- Workflow filename: `package-publish.yml`
- Environment name: `pypi`

PyPI requires the owner, repository name, and workflow filename for GitHub Actions trusted publishers. The environment name is optional in PyPI, but strongly recommended because it lets GitHub apply environment-specific deployment controls.

## If the project already exists on TestPyPI or PyPI

1. Sign in to the package index.
2. Open the `mbt-ai-tools` project.
3. Go to the project publishing settings.
4. Add a GitHub Actions trusted publisher with the values above.
5. Confirm the publisher appears in the project's publishing settings.

## If the project does not exist yet

Use a pending publisher:

1. Sign in to the package index.
2. Open account publishing settings.
3. Add a pending GitHub Actions trusted publisher.
4. Use project name `mbt-ai-tools`.
5. Use the owner, repository name, workflow filename, and environment name listed above.
6. Run the publish workflow when ready.

A pending publisher does not reserve the project name until the first successful publish. Publish to TestPyPI before PyPI.

## Build-only validation

Run the workflow manually without publishing:

```bash
gh workflow run package-publish.yml --ref main -f target=testpypi -f publish=false
```

Expected result:

- Workflow builds wheel and source distribution.
- `twine check dist/*` passes.
- `mbt-dist` artifact is uploaded.
- No package is published.

## Publish sequence

1. Confirm tag CI is green.
2. Confirm release evidence reports `Status: ready`.
3. Confirm `mbt-eval` reports `Status: passed`.
4. Run build-only package workflow with `publish=false`.
5. Configure TestPyPI trusted publisher.
6. Run package workflow with `target=testpypi` and `publish=true`.
7. Install from TestPyPI in a clean environment and run `mbt-check --version` plus `mbt-eval`.
8. Configure PyPI trusted publisher.
9. Run package workflow with `target=pypi` and `publish=true`.

Do not publish when release readiness is blocked.

Package-index install commands are documented in `docs/package_installation.md`.
