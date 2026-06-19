# EXP22 Challenge Corpus

EXP22 is the next exploratory challenge surface after the `v0.1.2` release and
the closed EXP21 seed.

EXP21 is intentionally left as a milestone corpus. EXP22 starts a broader and
rougher development track for `0.1.3`.

## Scope

The EXP22 seed lives at:

```text
examples/exp22_challenge_corpus.jsonl
```

The builder lives at:

```text
examples/build_exp22_challenge_corpus.py
```

The initial seed probes:

- coreference and compact role binding
- comparative direction binding
- exception and exclusion scope
- unit binding with repeated numbers
- temporal before/after order
- all-bad near misses

These cases are development probes, not public benchmark claims. A low pass
rate is useful if it exposes stable failure modes worth turning into geometry,
relation, negation, or reporting improvements.

## Regenerate the corpus

```bash
python examples/build_exp22_challenge_corpus.py
```

## Evaluate EXP22

```bash
manifold-eval \
  --corpus examples/exp22_challenge_corpus.jsonl \
  --format json \
  --output exp22-evaluation.json
```

Narrow to one family:

```bash
manifold-eval \
  --corpus examples/exp22_challenge_corpus.jsonl \
  --family exp22_comparative_binding \
  --output exp22-comparative-binding.json
```

Build a replay pack:

```bash
python scripts/build_eval_replay_pack.py \
  --evaluation exp22-evaluation.json \
  --corpus examples/exp22_challenge_corpus.jsonl \
  --include-passed \
  --output exp22-replay.md
```

## Development policy

Use EXP22 to find the next reliable improvement boundary.

Promote an EXP22 case only when:

- the expected behavior is unambiguous from the supplied references
- the behavior maps to a stable product guarantee
- the case has focused tests or frozen corpus coverage
- public docs avoid implying external fact-checking
- release evidence and `CLAIMS.md` agree with the promoted scope

Until then, EXP22 remains a private-development style challenge surface for
finding the next useful failures.
