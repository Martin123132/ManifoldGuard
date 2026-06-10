# CLI JSON Report Demo

This example runs the offline regulation path and emits a structured JSON report.

```bash
mbt-check \
  --reference "The capital of France is Paris." \
  --candidate "The capital of France is London." \
  --candidate "The capital of France is Paris." \
  --no-embeddings \
  --format json
```

Expected shape:

```json
{
  "action": "emit",
  "emitted_index": 1,
  "emitted_text": "The capital of France is Paris.",
  "evaluations": [
    {
      "index": 0,
      "status": "blocked",
      "safe_to_emit": false,
      "text": "The capital of France is London.",
      "clamps": [
        "protected_entity",
        "protected_literal_drift",
        "final_literal_block",
        "content_clamp_flag",
        "known_participant_unsupported_relation_clamp",
        "guarded_known_participant_unsupported_relation_clamp",
        "exp19b_guarded_patch_clamp"
      ]
    },
    {
      "index": 1,
      "status": "safe",
      "safe_to_emit": true,
      "text": "The capital of France is Paris.",
      "clamps": [
        "exact_reference_member"
      ]
    }
  ]
}
```

The actual report also includes numeric scores, extracted relations, negated relations, threshold values, and exact-reference flags.
