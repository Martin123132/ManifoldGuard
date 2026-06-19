# ManifoldGuard Explain Report Example

This example shows the opt-in `--explain` path for a simple offline regulation
run. Explanations are intended to make each candidate decision easier to audit
without changing ManifoldGuard's default report shape.

## Command

```bash
manifold-check \
  --reference "The capital of France is Paris." \
  --candidate "The capital of France is London." \
  --candidate "The capital of France is Paris." \
  --no-embeddings \
  --explain
```

## Example output

```text
EMIT | The capital of France is Paris. | score=0.0000
[0] blocked | score=0.0000 | clamps=known_participant_unsupported_relation_clamp|guarded_known_participant_unsupported_relation_clamp|exp19b_guarded_patch_clamp
    explain | Blocked because these guards fired: known_participant_unsupported_relation_clamp, guarded_known_participant_unsupported_relation_clamp, exp19b_guarded_patch_clamp.
    reason | known_participant_unsupported_relation_clamp | Candidate uses known reference participants in an unsupported relation.
    reason | guarded_known_participant_unsupported_relation_clamp | Guarded relation recall confirmed unsupported known-participant drift.
    reason | exp19b_guarded_patch_clamp | Guarded relation patch lineage marked this candidate as unsupported.
[1] safe | score=0.0000 | clamps=exact_reference_member
    explain | Safe because the candidate exactly matches a supplied reference.
    reason | exact_reference_member | Candidate exactly matches a supplied reference after normalization.
```

## Notes

- `--explain` is available for text, JSON, and Markdown regulation reports.
- CSV keeps the stable candidate-row columns; use JSON or Markdown when you need
  structured explanation details.
- Explanations summarize the regulator guards that fired. They do not turn
  ManifoldGuard into an external fact checker.
