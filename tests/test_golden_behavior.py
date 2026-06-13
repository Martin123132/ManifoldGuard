from __future__ import annotations

from mbt_ai_tools.cli import build_regulation_report
from mbt_ai_tools.mbt.regulator import regulate_candidates


def offline_report_snapshot(*, references: list[str], candidates: list[str]) -> dict:
    result = regulate_candidates(candidates, references, use_embeddings=False)
    report = build_regulation_report(result)
    return {
        "action": report["action"],
        "emitted_text": report["emitted_text"],
        "emitted_index": report["emitted_index"],
        "candidate_statuses": [
            evaluation["status"] for evaluation in report["evaluations"]
        ],
    }


def test_core_offline_behavior_golden_snapshot():
    snapshots = [
        {
            "id": "france-capital",
            **offline_report_snapshot(
                references=["The capital of France is Paris."],
                candidates=[
                    "The capital of France is London.",
                    "The capital of France is Paris.",
                ],
            ),
        },
        {
            "id": "unsupported-negation",
            **offline_report_snapshot(
                references=["Water is liquid at room temperature."],
                candidates=["Water is not liquid at room temperature."],
            ),
        },
    ]

    assert snapshots == [
        {
            "id": "france-capital",
            "action": "emit",
            "emitted_text": "The capital of France is Paris.",
            "emitted_index": 1,
            "candidate_statuses": ["blocked", "safe"],
        },
        {
            "id": "unsupported-negation",
            "action": "block",
            "emitted_text": None,
            "emitted_index": None,
            "candidate_statuses": ["blocked"],
        },
    ]
