from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def load_compare_module():
    module_path = (
        Path(__file__).resolve().parent.parent / "scripts" / "compare_eval_reports.py"
    )
    spec = importlib.util.spec_from_file_location("compare_eval_reports", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def report(*, passed: bool = True, action: str = "emit") -> dict:
    failed_cases = 0 if passed else 1
    passed_cases = 1 if passed else 0
    return {
        "schema_version": "1.0",
        "summary": {
            "total_cases": 1,
            "passed_cases": passed_cases,
            "failed_cases": failed_cases,
            "expected_emit": 1,
            "expected_block": 0,
            "actual_emit": 1 if action == "emit" else 0,
            "actual_block": 1 if action == "block" else 0,
            "candidate_evaluations": 2,
            "safe_candidate_evaluations": 1 if action == "emit" else 0,
            "blocked_candidate_evaluations": 1 if action == "emit" else 2,
            "families": {
                "france-capital": {
                    "total_cases": 1,
                    "passed_cases": passed_cases,
                    "failed_cases": failed_cases,
                    "expected_emit": 1,
                    "expected_block": 0,
                    "actual_emit": 1 if action == "emit" else 0,
                    "actual_block": 1 if action == "block" else 0,
                    "candidate_evaluations": 2,
                    "safe_candidate_evaluations": 1 if action == "emit" else 0,
                    "blocked_candidate_evaluations": 1 if action == "emit" else 2,
                }
            },
        },
        "cases": [
            {
                "id": "france-capital",
                "family": "france-capital",
                "passed": passed,
                "actual_action": action,
                "actual_emitted_text": "Paris" if action == "emit" else None,
                "actual_candidate_safe": [False, action == "emit"],
                "mismatches": [] if passed else ["action expected 'emit', got 'block'"],
            }
        ],
    }


def write_report(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_compare_eval_reports_detects_unchanged_reports(tmp_path: Path):
    compare_eval_reports = load_compare_module()
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    write_report(before, report())
    write_report(after, report())

    diff = compare_eval_reports.compare_reports(before, after)

    assert diff["status"] == "unchanged"
    assert diff["counts"]["changed_cases"] == 0
    assert diff["summary_delta"] == {}
    assert "Status: unchanged" in compare_eval_reports.format_text(diff)


def test_compare_eval_reports_detects_summary_and_case_changes(tmp_path: Path):
    compare_eval_reports = load_compare_module()
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    write_report(before, report())
    write_report(after, report(passed=False, action="block"))

    diff = compare_eval_reports.compare_reports(before, after)

    assert diff["status"] == "changed"
    assert diff["summary_delta"]["failed_cases"] == {
        "before": 0,
        "after": 1,
        "delta": 1,
    }
    assert diff["family_delta"]["france-capital"]["status"] == "changed"
    assert diff["counts"]["changed_cases"] == 1
    assert diff["case_changes"]["changed"][0]["id"] == "france-capital"


def test_compare_eval_reports_main_writes_json_output(tmp_path: Path, capsys):
    compare_eval_reports = load_compare_module()
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    output = tmp_path / "diff.json"
    write_report(before, report())
    write_report(after, report(passed=False, action="block"))

    result = compare_eval_reports.main(
        [
            "--before",
            str(before),
            "--after",
            str(after),
            "--output",
            str(output),
        ]
    )

    captured = capsys.readouterr()
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert result == 0
    assert saved["status"] == "changed"
    assert "ManifoldGuard Evaluation Report Diff" in captured.out
