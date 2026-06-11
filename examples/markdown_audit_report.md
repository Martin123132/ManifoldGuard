# Markdown Audit Report Demo

This example turns a batch JSONL evaluation into a human-readable audit report.

```bash
mbt-check \
  --input-jsonl examples/batch_input.jsonl \
  --no-embeddings \
  --format markdown \
  --output audit.md
```

Guard-mode audit command:

```bash
mbt-check \
  --input-jsonl examples/batch_input.jsonl \
  --no-embeddings \
  --format markdown \
  --fail-on-block
```

The guard command exits with status `2` when any input row blocks.

Expected report shape:

```markdown
# MBT-5 Audit Report

## Summary

- Total cases: 2
- Emitted: 1
- Blocked: 1
- Safe candidate evaluations: 1
- Blocked candidate evaluations: 2

## Case: france-capital

- Action: emit
- Emitted index: 1
- Emitted text: The capital of France is Paris.

### Candidate Evaluations

#### Candidate 0 - blocked

- Clamps: protected_entity, protected_literal_drift, final_literal_block, content_clamp_flag, known_participant_unsupported_relation_clamp, guarded_known_participant_unsupported_relation_clamp, exp19b_guarded_patch_clamp

## Case: unsupported-negation

- Action: block
- Emitted index: `null`
- Emitted text: `null`
```
