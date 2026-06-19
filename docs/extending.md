# Extending ManifoldGuard

This guide is for people who want to adapt ManifoldGuard for personal projects,
private corpora, or focused research experiments.

The safest extension path is data-first: add examples, evaluate behavior, and
only then change regulator code if the gap is clear.

## Extension paths

### 1. Personal corpus

Use this when you want ManifoldGuard to check your own domain references.

Start from:

```text
examples/personal_corpus_template.jsonl
```

Run:

```bash
manifold-eval --corpus my-corpus.jsonl --output my-evaluation.json
```

This path is best for:

- private notes
- project-specific guardrails
- domain examples
- local experiments
- deciding whether a behavior is stable enough for tests

### 2. Challenge corpus

Use this when you are probing harder future behavior.

Start from:

```text
examples/build_challenge_corpus.py
examples/challenge_corpus.jsonl
```

Challenge cases should remain separate from public release claims until they are
stable, documented, and intentionally promoted.

### 3. Focused tests

Use this when expected behavior is already clear.

Good starting files:

```text
tests/test_regulator.py
tests/test_cli.py
tests/test_challenge_corpus.py
```

Focused tests should be small and readable. Each one should explain one behavior
that the tool must keep.

### 4. Regulator code

Use this only after a data or test case shows a specific gap.

Main files:

```text
mbt_ai_tools/mbt/regulator.py
mbt_ai_tools/cli.py
mbt_ai_tools/mbt/tokens.py
mbt_ai_tools/mbt/geometry.py
```

Keep the behavior reference-bounded. ManifoldGuard should compare candidates to
supplied references, not silently rely on external truth.

## Adding a new relation guard

Recommended workflow:

1. Add one or two corpus examples showing the failure.
2. Add a focused test in `tests/test_regulator.py`.
3. Extend relation extraction or clamp logic in `mbt_ai_tools/mbt/regulator.py`.
4. Confirm the candidate that should pass still passes.
5. Document the new scope in `CHANGELOG.md` and relevant docs.

Prefer narrow relation patterns over broad parsing rules. A small auditable
pattern is better than a clever rule that creates hidden false positives.

## Adding a report or CLI feature

Recommended workflow:

1. Add the flag or report field in `mbt_ai_tools/cli.py`.
2. Keep default output stable unless the change is intentionally breaking.
3. Add focused tests in `tests/test_cli.py`.
4. Update `docs/report_schema.md` when report fields change.
5. Add or update an example under `examples/`.

For optional fields, prefer opt-in flags such as `--explain` or `--token-shock`.

## Adding public claims

Do not add a public claim just because a new example passes.

A public claim needs:

- a named corpus or ledger
- exact commands
- exact counts or metrics
- a clear offline or embedding mode
- agreement with `CLAIMS.md`
- no implication of external truth access

Use `docs/benchmark.md` to decide whether a result is release evidence or only
a development probe.

## Keeping personal changes private

If your corpus contains private facts, keep it outside the public repository.

Useful pattern:

```bash
manifold-eval --corpus path/to/private-corpus.jsonl --output private-evaluation.json
```

Do not commit:

- private references
- customer data
- proprietary documents
- secrets
- direct personal contact/payment details

## Good extension habits

- Keep references short and explicit.
- Split independent facts into separate references.
- Add negative references when absence matters.
- Keep examples deterministic.
- Separate development probes from release evidence.
- Prefer readable guards over broad magic.
- Record limitations before marketing claims.

## Quick decision table

| Goal | Best starting point |
| --- | --- |
| Try ManifoldGuard on private facts | `examples/personal_corpus_template.jsonl` |
| Stress harder future behavior | `examples/challenge_corpus.jsonl` |
| Fix a known regulator edge case | `tests/test_regulator.py` |
| Improve CLI/report output | `tests/test_cli.py` and `mbt_ai_tools/cli.py` |
| Add public evidence | `docs/benchmark.md` and `CLAIMS.md` |
