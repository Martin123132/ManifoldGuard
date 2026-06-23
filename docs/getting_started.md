# Getting Started with ManifoldGuard

This guide is for people who want to use, understand, or extend ManifoldGuard
for their own reference-bounded checks.

ManifoldGuard does not try to know external truth. It compares candidate
outputs against references you supply and blocks candidates that drift from
that reference structure.

## Public and legacy names

Use `ManifoldGuard` as the public product name and install it as
`manifold-guard`.

The Python import path remains `mbt_ai_tools` for compatibility with earlier
project versions. Prefer `manifold-check` and `manifold-eval` for new CLI
usage; `mbt-check` and `mbt-eval` remain compatibility aliases for existing
automation.

## Install

For normal offline use:

```bash
python -m pip install manifold-guard
```

For optional embedding-backed behavior:

```bash
python -m pip install "manifold-guard[embeddings]"
```

For source checkout development:

```bash
python -m pip install -e . --no-deps
python -m pip install numpy scipy
```

## Mental model

Think of each run as three inputs:

- trusted references
- candidate outputs
- a decision policy

The output is either:

- `emit`: at least one candidate stayed inside the supplied reference structure
- `block`: every candidate was unsafe

In offline mode, ManifoldGuard mainly checks:

- exact reference membership
- protected numbers, units, and entities
- relation drift
- role swaps
- unsupported negation
- supported negative evidence
- overclaim language

## First CLI check

```bash
manifold-check \
  --reference "The capital of France is Paris." \
  --candidate "The capital of France is London." \
  --candidate "The capital of France is Paris." \
  --no-embeddings
```

Expected shape:

```text
EMIT | The capital of France is Paris. | score=0.0000
```

Add explanations:

```bash
manifold-check \
  --reference "The capital of France is Paris." \
  --candidate "The capital of France is London." \
  --candidate "The capital of France is Paris." \
  --no-embeddings \
  --explain
```

## First Python check

```python
from mbt_ai_tools import regulate_candidates

references = ["The capital of France is Paris."]
candidates = [
    "The capital of France is London.",
    "The capital of France is Paris.",
]

result = regulate_candidates(candidates, references, use_embeddings=False)

print(result.action)
print(result.emitted_text)
for evaluation in result.evaluations:
    print(evaluation.safe_to_emit, evaluation.clamp_summary)
```

## Batch checks

Create a JSONL file with one case per line:

```json
{"id":"france-capital","references":["The capital of France is Paris."],"candidates":["The capital of France is London.","The capital of France is Paris."]}
```

A starter template is available at:

```text
examples/personal_corpus_template.jsonl
```

Run:

```bash
manifold-check \
  --input-jsonl batch.jsonl \
  --no-embeddings \
  --format markdown \
  --output audit.md
```

Use `--format json` for automation and `--format csv` for spreadsheet review.

## Choosing references

Good references are:

- specific
- scoped
- short enough to audit
- explicit about negatives when negatives matter
- split into multiple statements when relations are independent

Example:

```text
The archive contains public records.
The archive does not contain passwords.
```

Avoid using vague references such as:

```text
The archive is safe and complete.
```

Vague references make it harder to decide whether a candidate drifted.

## Extending for personal use

The easiest extension path is data-first:

- add cases to your own JSONL corpus
- start from `examples/personal_corpus_template.jsonl` if helpful
- run `manifold-eval --corpus your-corpus.jsonl`
- inspect failures with `scripts/build_eval_replay_pack.py`
- promote stable cases into tests only after expected behavior is clear

For code changes, useful starting files are:

- `mbt_ai_tools/mbt/regulator.py`: offline relation, literal, negation, and scoring logic
- `mbt_ai_tools/cli.py`: CLI flags and report rendering
- `examples/build_regression_corpus.py`: frozen public corpus builder
- `examples/build_challenge_corpus.py`: exploratory challenge corpus builder
- `tests/test_regulator.py`: focused regulator behavior tests
- `tests/test_cli.py`: CLI/report behavior tests

Keep new behavior reference-bounded. If a change depends on knowing external
truth, it probably belongs outside ManifoldGuard or needs explicit references.

## Common mistakes

- Expecting ManifoldGuard to fact-check without references.
- Treating EXP21 challenge pass rates as public release claims.
- Using embedding mode in CI in a way that downloads models.
- Adding broad claims to docs before adding reproducible evidence.
- Putting unrelated facts into one long reference instead of multiple focused
  reference statements.

## Where to go next

- `README.md`: project overview and quick commands
- `docs/report_schema.md`: report fields and output contracts
- `docs/benchmark.md`: evidence tiers and public claim boundaries
- `docs/exp21_challenge.md`: challenge corpus workflow
- `docs/extending.md`: extension paths for personal corpora and code changes
- `CLAIMS.md`: supported and unsupported public claims
