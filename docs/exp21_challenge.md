# EXP21 Challenge Corpus

The EXP21 challenge corpus is an exploratory development probe for harder
reference-bounded regulation cases. It is intentionally separate from the
frozen public regression corpus used for release evidence.

Use it to stress ManifoldGuard behavior before promoting cases into the frozen
offline regression suite.

## Scope

The challenge corpus lives at:

```text
examples/challenge_corpus.jsonl
```

The corpus currently probes:

- supported negative evidence
- negation scope binding
- temporal value binding
- alias binding
- relation composition
- qualifier overclaims
- all-bad near misses

These cases are development probes. Do not use EXP21 pass rates as public
performance claims unless the release evidence and claims register explicitly
promote them.

## Regenerate the corpus

```bash
python examples/build_challenge_corpus.py
```

## Evaluate the challenge corpus

```bash
manifold-eval \
  --corpus examples/challenge_corpus.jsonl \
  --output challenge-evaluation.json
```

Narrow to one family:

```bash
manifold-eval \
  --corpus examples/challenge_corpus.jsonl \
  --family challenge_negation_scope \
  --output challenge-negation-scope.json
```

Export only failures:

```bash
manifold-eval \
  --corpus examples/challenge_corpus.jsonl \
  --failures-only \
  --format json \
  --output challenge-failures.json
```

## Build a replay pack

Replay packs turn evaluator JSON plus corpus rows into compact debugging
material for review.

```bash
python scripts/build_eval_replay_pack.py \
  --evaluation challenge-evaluation.json \
  --corpus examples/challenge_corpus.jsonl \
  --include-passed \
  --output challenge-replay.md
```

Build a replay pack for one family:

```bash
python scripts/build_eval_replay_pack.py \
  --evaluation challenge-evaluation.json \
  --corpus examples/challenge_corpus.jsonl \
  --family challenge_relation_composition \
  --include-passed \
  --output challenge-relation-composition-replay.md
```

## Compare evaluator runs

Use saved evaluator reports to see whether a regulator change improved,
regressed, or moved behavior across families.

```bash
python scripts/compare_eval_reports.py \
  --before old-challenge-evaluation.json \
  --after challenge-evaluation.json
```

## Promotion policy

Challenge cases should be promoted into frozen regression evidence only when:

- the case represents a stable product guarantee
- expected behavior is unambiguous from supplied references
- the case is covered by focused tests or corpus validation
- docs avoid implying external truth access
- `CLAIMS.md` and release evidence agree with the new scope

Until then, EXP21 remains a development surface for finding the next useful
geometry, relation, negation, and reporting improvements.
