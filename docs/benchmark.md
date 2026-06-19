# Benchmark and Evidence Guide

This guide explains how ManifoldGuard evidence is organized for public release
claims and ongoing development work.

ManifoldGuard is reference-bounded. It evaluates candidate outputs against
supplied reference statements and derived relation structure. It does not check
external truth.

## Evidence tiers

### Tier 1: Frozen public regression corpus

The frozen public regression corpus is the release evidence surface.

Path:

```text
examples/regression_corpus.jsonl
```

Current scope:

```text
Cases: 229
Mode: offline literal / relation / negation / numeric / unit guards
Embeddings: disabled with --no-embeddings or use_embeddings=False
```

Use this corpus for release readiness and public scoped claims.

Run:

```bash
manifold-eval
manifold-eval --output regulator-evaluation.json
python scripts/build_eval_report.py \
  --input regulator-evaluation.json \
  --output docs/evaluation_report.md
```

Expected healthy release result:

```text
Status: passed
Cases: 229
Passed: 229
Failed: 0
```

### Tier 2: EXP21 challenge corpus

The EXP21 challenge corpus is a development probe, not current release
evidence.

Path:

```text
examples/challenge_corpus.jsonl
```

It contains harder cases for:

- supported negative evidence
- negation scope binding
- temporal value binding
- alias binding
- relation composition
- qualifier overclaims
- all-bad near misses

Run:

```bash
manifold-eval \
  --corpus examples/challenge_corpus.jsonl \
  --output challenge-evaluation.json
```

The full EXP21 workflow is documented in `docs/exp21_challenge.md`.

### Tier 3: Focused unit/regression tests

Focused tests protect specific behavior before or after cases move into a
corpus.

Use these for small implementation changes:

```bash
python -m pytest -q tests/test_regulator.py
python -m pytest -q tests/test_cli.py
python -m pytest -q tests/test_challenge_corpus.py
```

## Public claim boundary

Supported public claims should be tied to:

- a named corpus or ledger
- exact commands
- exact case counts or metrics
- explicit offline/embedding mode
- explicit reference-bounded scope

Avoid claims that imply:

- universal fact checking
- access to external truth
- correctness outside supplied references
- broad embedding-mode generalization without separate evidence

## Comparing evidence runs

Compare saved evaluator JSON reports:

```bash
python scripts/compare_eval_reports.py \
  --before old-regulator-evaluation.json \
  --after regulator-evaluation.json
```

Build replay material for selected or failing cases:

```bash
python scripts/build_eval_replay_pack.py \
  --evaluation regulator-evaluation.json \
  --corpus examples/regression_corpus.jsonl \
  --output regression-replay.md
```

## Release checklist

Before a public release:

- Run the frozen public regression corpus.
- Regenerate `docs/evaluation_report.md` from the latest evaluation JSON.
- Confirm docs-quality passes.
- Confirm full offline tests pass.
- Confirm package build and install smoke checks pass.
- Keep EXP21 results separate unless intentionally promoted and documented.
