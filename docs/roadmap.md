# ManifoldGuard Roadmap

This roadmap keeps development grounded in reference-bounded behavior. It is a
working plan, not a public guarantee.

## Current release baseline

- `manifold-guard==0.1.3` is published to PyPI.
- Core regulation remains offline-first when `use_embeddings=False` or
  `--no-embeddings` is selected.
- EXP22 is closed at `18 / 18` for the checked seed cases.
- EXP23 is closed locally at `18 / 18` for the checked seed cases on the
  `0.1.4` development track.

## Next development track

The next cycle should start from a fresh challenge seed rather than expanding
EXP23 in place. Keep EXP23 as a closed milestone corpus and use the next seed
to find a small, stable failure family.

Recommended order:

- broader range and unit-bound paraphrases
- conditional support with multiple antecedents
- nested exception chains with more than one excluded subgroup
- relation binding across compact summaries
- all-bad near misses that reuse every reference token

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
