from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def load_build_eval_report_module():
    module_path = (
        Path(__file__).resolve().parent.parent / "scripts" / "build_eval_report.py"
    )
    spec = importlib.util.spec_from_file_location("build_eval_report", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def sample_report() -> dict:
    return {
        "schema_version": "1.0",
        "corpus": "example.jsonl",
        "mode": "offline",
        "status": "passed",
        "summary": {
            "total_cases": 2,
            "passed_cases": 2,
            "failed_cases": 0,
            "expected_emit": 1,
            "expected_block": 1,
            "actual_emit": 1,
            "actual_block": 1,
            "candidate_evaluations": 3,
            "safe_candidate_evaluations": 1,
            "blocked_candidate_evaluations": 2,
            "families": {
                "capital_entity_swap": {
                    "total_cases": 1,
                    "passed_cases": 1,
                    "failed_cases": 0,
                    "actual_emit": 1,
                    "actual_block": 0,
                },
                "unsupported_negation": {
                    "total_cases": 1,
                    "passed_cases": 1,
                    "failed_cases": 0,
                    "actual_emit": 0,
                    "actual_block": 1,
                },
            },
        },
        "cases": [
            {
                "id": "capital_entity_swap_france",
                "passed": True,
                "mismatches": [],
            }
        ],
    }


def test_build_markdown_includes_summary_and_taxonomy():
    build_eval_report = load_build_eval_report_module()

    content = build_eval_report.build_markdown(
        sample_report(),
        generated_at="2026-06-14T00:00:00+00:00",
    )

    assert "# ManifoldGuard Offline Evaluation Report" in content
    assert "Status: `passed`" in content
    assert "| capital_entity_swap | 1 | 1 | 0 | 1 | 0 |" in content
    assert "| unsupported_negation | 1 | 1 | 0 | 0 | 1 |" in content
    assert "- none" in content


def test_build_eval_report_main_writes_output_from_json(tmp_path: Path, capsys):
    build_eval_report = load_build_eval_report_module()
    report_path = tmp_path / "regulator-evaluation.json"
    output_path = tmp_path / "evaluation_report.md"
    report_path.write_text(json.dumps(sample_report()), encoding="utf-8")

    result = build_eval_report.main(
        [
            "--input",
            str(report_path),
            "--output",
            str(output_path),
            "--generated-at",
            "2026-06-14T00:00:00+00:00",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert output_path.exists()
    assert "Wrote evaluation report" in captured.out
    assert "Generated at: `2026-06-14T00:00:00+00:00`" in output_path.read_text(
        encoding="utf-8"
    )
