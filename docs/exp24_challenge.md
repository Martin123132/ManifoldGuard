# EXP24 Challenge Corpus

EXP24 is the exploratory challenge surface after the `v0.1.4` release and the
closed EXP23 seed.

EXP23 is intentionally left as a milestone corpus. EXP24 starts the `0.1.5`
development track with harder probes around multi-antecedent conditionals,
alias-bound permissions, unit/range paraphrases, chained exceptions, compact
relation bindings, and all-bad token-reuse near misses.

## Scope

The EXP24 seed lives at:

```text
examples/exp24_challenge_corpus.jsonl
```

The builder lives at:

```text
examples/build_exp24_challenge_corpus.py
```

The initial seed probes:

- multi-antecedent conditional scope
- alias and role-bound permissions
- unit/range paraphrases and endpoint inclusivity
- chained exceptions with multiple exclusions
- compact value, device, and attribute bindings
- all-bad token-reuse near misses

These cases are development probes, not public benchmark claims. A low pass
rate is useful if it exposes stable failure modes worth turning into geometry,
relation, negation, literal-drift, or reporting improvements.

Initial local baseline after seed creation: `5 / 18`.

First bounded improvement pass: multi-antecedent conditional probes now pass
`3 / 3`, raising the local EXP24 baseline from `5 / 18` to `8 / 18` by
preserving joint condition scope offline.

Remaining zero-pass families after that pass should be unit/range paraphrases
and chained exceptions.

## Regenerate the corpus

```bash
python examples/build_exp24_challenge_corpus.py
```

## Evaluate EXP24

```bash
manifold-eval \
  --corpus examples/exp24_challenge_corpus.jsonl \
  --format json \
  --output exp24-evaluation.json
```

Narrow to the multi-antecedent conditional families:

```bash
manifold-eval \
  --corpus examples/exp24_challenge_corpus.jsonl \
  --family exp24_multi_antecedent_conditionals_card_pin \
  --family exp24_multi_antecedent_conditionals_valve_pressure \
  --family exp24_multi_antecedent_conditionals_admin_owner \
  --output exp24-conditionals.json
```

Build a replay pack:

```bash
python scripts/build_eval_replay_pack.py \
  --evaluation exp24-evaluation.json \
  --corpus examples/exp24_challenge_corpus.jsonl \
  --output exp24-replay.md
```

## Promotion boundary

Use EXP24 to find the next reliable improvement boundary.

Promote an EXP24 case only when:

- the expected behavior is unambiguous from the supplied references
- the behavior maps to a stable product guarantee
- the case has focused tests or frozen corpus coverage
- public docs avoid implying external fact-checking
- release evidence and `CLAIMS.md` agree with the promoted scope

Until then, EXP24 remains a private-development style challenge surface for
finding the next useful failures.
