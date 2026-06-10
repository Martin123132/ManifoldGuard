# MBT-5 Report Schema

`mbt-check --format json` emits one JSON object for a single regulation run.
`mbt-check --input-jsonl ...` emits one JSON object per input line.

## Single Report

Top-level fields:

- `action`: `emit` or `block`.
- `emitted_text`: emitted candidate text, or `null` when blocked.
- `emitted_index`: zero-based emitted candidate index, or `null` when blocked.
- `emitted_score`: emitted candidate regulator score, or `null` when blocked.
- `evaluations`: per-candidate evaluation objects.

Each evaluation contains:

- `index`: zero-based candidate index.
- `text`: candidate text.
- `status`: `safe` or `blocked`.
- `safe_to_emit`: boolean emit eligibility.
- `pred_hallucinated`: boolean regulator prediction.
- `regulator_score`: final ranking score.
- `mbt5_shock`: semantic geometry shock score.
- `threshold`: active geometry threshold.
- `literal_score`: literal drift score.
- `clamps`: clamp names applied to the candidate.
- `relations`: extracted candidate relation tuples.
- `negated_relations`: extracted negated relation tuples.
- `exact_reference_member`: whether candidate exactly matches a reference after normalization.
- `token_shock`: optional token shock entries when `--token-shock` is used.

## Batch Input JSONL

Each non-empty line must be a JSON object with:

- `references`: string or list of strings.
- `candidates`: string or list of strings.
- `id`: optional caller-provided identifier copied into the output line.

Singular aliases `reference` and `candidate` are accepted for one-item inputs.

## Batch Output JSONL

Batch output uses the same report fields as single JSON output and adds:

- `line`: one-based input line number.
- `id`: copied from the input when present.
- `references`: normalized list of reference strings used for that line.
