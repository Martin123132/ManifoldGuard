# ManifoldGuard Roadmap

This roadmap keeps development grounded in reference-bounded behavior. It is a
working plan, not a public guarantee.

## Current release baseline

- `manifold-guard==0.1.4` is published to PyPI.
- Core regulation remains offline-first when `use_embeddings=False` or
  `--no-embeddings` is selected.
- EXP22 is closed at `18 / 18` for the checked seed cases.
- EXP23 is closed locally at `18 / 18` for the checked seed cases on the
  `0.1.4` development track.

## Next development track

EXP24 should guide the `0.1.5` cycle. Keep EXP23 as a closed milestone corpus
and use EXP24 to find the next small, stable failure family.

Recommended order:

- measure the EXP24 baseline
- choose the clearest failing family with minimal API risk
- promote focused tests for that family
- rerun EXP24 and record the before/after evidence
- leave public claims tied to release evidence, not exploratory pass rates

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
