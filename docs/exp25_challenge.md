# EXP25 Challenge Corpus

EXP25 is the exploratory challenge surface after the completed EXP24 seed.

EXP24 is intentionally left as a closed development milestone at `18 / 18`.
EXP25 opens the next development track with harder probes around temporal role
binding, nested conditionals, quantifier thresholds, compact dimension binding,
scoped exceptions, and all-bad token-reuse near misses.

## Scope

The EXP25 seed lives at:

```text
examples/exp25_challenge_corpus.jsonl
```

The builder lives at:

```text
examples/build_exp25_challenge_corpus.py
```

The initial seed probes:

- temporal actor, object, and before/after binding
- nested conditional scope
- quantifier, threshold, and exact-count paraphrases
- compact dimension and numeric-value bindings
- scoped exceptions with allowed and denied classes
- all-bad token-reuse near misses

These cases are development probes, not public benchmark claims. A low pass
rate is useful if it exposes stable failure modes worth turning into geometry,
relation, negation, literal-drift, or reporting improvements.

Initial local baseline after seed creation: `1 / 18`.

First bounded improvement pass: compact dimension binding probes now pass
`3 / 3`, raising the local EXP25 baseline from `1 / 18` to `4 / 18` with scoped
weight/volume, range/payload, and power/duration relation bindings.

## Regenerate the corpus

```bash
python examples/build_exp25_challenge_corpus.py
```

## Evaluate EXP25

```bash
manifold-eval \
  --corpus examples/exp25_challenge_corpus.jsonl \
  --format json \
  --output exp25-evaluation.json
```

Narrow to the temporal role-binding families:

```bash
manifold-eval \
  --corpus examples/exp25_challenge_corpus.jsonl \
  --family exp25_temporal_role_binding_valve_pump \
  --family exp25_temporal_role_binding_draft_review \
  --family exp25_temporal_role_binding_vial_sequence \
  --output exp25-temporal-role-binding.json
```

Narrow to the quantifier-threshold families:

```bash
manifold-eval \
  --corpus examples/exp25_challenge_corpus.jsonl \
  --family exp25_quantifier_thresholds_reviewer_release \
  --family exp25_quantifier_thresholds_failed_checks \
  --family exp25_quantifier_thresholds_signature_count \
  --output exp25-quantifier-thresholds.json
```

Build a replay pack:

```bash
python scripts/build_eval_replay_pack.py \
  --evaluation exp25-evaluation.json \
  --corpus examples/exp25_challenge_corpus.jsonl \
  --output exp25-replay.md
```

## Promotion boundary

Use EXP25 to find the next reliable improvement boundary.

Promote an EXP25 case only when:

- the expected behavior is unambiguous from the supplied references
- the behavior maps to a stable product guarantee
- the case has focused tests or frozen corpus coverage
- public docs avoid implying external fact-checking
- release evidence and `CLAIMS.md` agree with the promoted scope

Until then, EXP25 remains a private-development style challenge surface for
finding the next useful failures.
