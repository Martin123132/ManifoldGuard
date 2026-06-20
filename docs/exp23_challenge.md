# EXP23 Challenge Corpus

EXP23 is the exploratory challenge surface after the `v0.1.3` release and the
closed EXP22 seed.

EXP22 is intentionally left as a milestone corpus. EXP23 starts the `0.1.4`
development track with harder probes around range bounds, conditionals, nested
exceptions, ordinal slots, aggregates, and all-bad near misses.

## Scope

The EXP23 seed lives at:

```text
examples/exp23_challenge_corpus.jsonl
```

The builder lives at:

```text
examples/build_exp23_challenge_corpus.py
```

The initial seed probes:

- numeric range and bound scope
- conditional and only-if style support
- nested exceptions and subgroup exclusions
- ordinal, ranked, and stage-slot bindings
- aggregate count and grouped-value bindings
- all-bad near misses

These cases are development probes, not public benchmark claims. A low pass
rate is useful if it exposes stable failure modes worth turning into geometry,
relation, negation, or reporting improvements.

Initial local baseline after seed creation: `7 / 18`.

The clearest first failure families are ordinal binding and nested exceptions.

## Regenerate the corpus

```bash
python examples/build_exp23_challenge_corpus.py
```

## Evaluate EXP23

```bash
manifold-eval \
  --corpus examples/exp23_challenge_corpus.jsonl \
  --format json \
  --output exp23-evaluation.json
```

Narrow to one family:

```bash
manifold-eval \
  --corpus examples/exp23_challenge_corpus.jsonl \
  --family exp23_range_bounds \
  --output exp23-range-bounds.json
```

Build a replay pack:

```bash
python scripts/build_eval_replay_pack.py \
  --evaluation exp23-evaluation.json \
  --corpus examples/exp23_challenge_corpus.jsonl \
  --output exp23-replay.md
```

## Promotion boundary

Use EXP23 to find the next reliable improvement boundary.

Promote an EXP23 case only when:

- the expected behavior is unambiguous from the supplied references
- the behavior maps to a stable product guarantee
- the case has focused tests or frozen corpus coverage
- public docs avoid implying external fact-checking
- release evidence and `CLAIMS.md` agree with the promoted scope

Until then, EXP23 remains a private-development style challenge surface for
finding the next useful failures.
