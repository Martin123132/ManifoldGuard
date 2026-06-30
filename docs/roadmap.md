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
- EXP24 is closed locally at `18 / 18` for the checked seed cases on the
  `0.1.5` development track.
- EXP25 is closed locally at `18 / 18` for the checked seed cases and should be
  treated as supporting development evidence, not a public benchmark claim.

## Next release-candidate track

The next bounded work is `0.1.5` release-candidate hardening. Keep EXP24 and
EXP25 as closed milestone corpora, then verify the public release evidence
without broadening product claims.

Recommended order:

- rerun the frozen regression suite and release evidence checks
- confirm EXP24 and EXP25 remain reproducible development evidence
- review `CLAIMS.md`, README, and package metadata for claim/version alignment
- prepare release notes without promoting challenge-corpus pass rates into
  benchmark claims
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
