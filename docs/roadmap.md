# ManifoldGuard Roadmap

This roadmap keeps development grounded in reference-bounded behavior. It is a
working plan, not a public guarantee.

## Current release baseline

- `manifold-guard==0.1.3` is published to PyPI.
- Core regulation remains offline-first when `use_embeddings=False` or
  `--no-embeddings` is selected.
- EXP22 is closed at `18 / 18` for the checked seed cases.

## Next development track

EXP23 should guide the `0.1.4` cycle. The first priority is to measure the new
seed and identify the smallest stable failure family.

Recommended order:

- range and bound scope
- conditional support scope
- nested exception handling
- ordinal and ranked-slot binding
- aggregate count binding
- all-bad near-miss blocking

## Product hardening

- Keep default installs lightweight and offline-first.
- Keep optional embeddings explicit through `.[embeddings]`.
- Add new guards only when they are explainable from supplied references.
- Prefer challenge-corpus seeds before changing regulator behavior.
- Keep public claims tied to reproducible release evidence.

## Release rhythm

- Open each cycle with an unreleased changelog section.
- Add a new exploratory seed before broad regulator changes.
- Close each promoted family with focused tests.
- Publish only after local validation, CI, TestPyPI smoke, and PyPI smoke.
