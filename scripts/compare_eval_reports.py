#!/usr/bin/env python
"""Compare two ManifoldGuard offline evaluation JSON reports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence


SUMMARY_KEYS = (
    "total_cases",
    "passed_cases",
    "failed_cases",
    "expected_emit",
    "expected_block",
    "actual_emit",
    "actual_block",
    "candidate_evaluations",
    "safe_candidate_evaluations",
    "blocked_candidate_evaluations",
)
CASE_FIELDS = (
    "family",
    "passed",
    "actual_action",
    "actual_emitted_text",
    "actual_candidate_safe",
    "mismatches",
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two ManifoldGuard evaluator JSON reports."
    )
    parser.add_argument(
        "--before",
        required=True,
        type=Path,
        help="Baseline JSON report from manifold-eval.",
    )
    parser.add_argument(
        "--after",
        required=True,
        type=Path,
        help="Candidate JSON report from manifold-eval.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the full JSON diff report to this path.",
    )
    return parser.parse_args(argv)


def load_report(path: Path) -> dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc.msg}") from exc
    if not isinstance(report, dict):
        raise ValueError(f"{path}: expected a JSON object")
    if not isinstance(report.get("summary"), dict):
        raise ValueError(f"{path}: expected a summary object")
    if not isinstance(report.get("cases"), list):
        raise ValueError(f"{path}: expected a cases list")
    return report


def numeric_delta(
    before: dict[str, Any],
    after: dict[str, Any],
    keys: Sequence[str] = SUMMARY_KEYS,
) -> dict[str, dict[str, int | float]]:
    deltas: dict[str, dict[str, int | float]] = {}
    for key in keys:
        before_value = before.get(key, 0)
        after_value = after.get(key, 0)
        if not isinstance(before_value, (int, float)):
            before_value = 0
        if not isinstance(after_value, (int, float)):
            after_value = 0
        if before_value != after_value:
            deltas[key] = {
                "before": before_value,
                "after": after_value,
                "delta": after_value - before_value,
            }
    return deltas


def case_index(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for index, case in enumerate(report.get("cases", []), start=1):
        if not isinstance(case, dict):
            raise ValueError(f"cases[{index}]: expected a case object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError(f"cases[{index}]: expected a non-empty string id")
        indexed[case_id] = case
    return indexed


def case_snapshot(case: dict[str, Any]) -> dict[str, Any]:
    return {field: case.get(field) for field in CASE_FIELDS}


def compare_cases(
    before_cases: dict[str, dict[str, Any]],
    after_cases: dict[str, dict[str, Any]],
) -> dict[str, list[Any]]:
    before_ids = set(before_cases)
    after_ids = set(after_cases)
    added = sorted(after_ids - before_ids)
    removed = sorted(before_ids - after_ids)
    changed = []
    for case_id in sorted(before_ids & after_ids):
        before_snapshot = case_snapshot(before_cases[case_id])
        after_snapshot = case_snapshot(after_cases[case_id])
        if before_snapshot != after_snapshot:
            changed.append(
                {
                    "id": case_id,
                    "before": before_snapshot,
                    "after": after_snapshot,
                }
            )
    return {
        "added": added,
        "removed": removed,
        "changed": changed,
    }


def family_status(
    family: str,
    before_families: dict[str, Any],
    after_families: dict[str, Any],
) -> str:
    if family not in before_families:
        return "added"
    if family not in after_families:
        return "removed"
    return "changed"


def compare_families(
    before_summary: dict[str, Any],
    after_summary: dict[str, Any],
) -> dict[str, Any]:
    before_families = before_summary.get("families", {})
    after_families = after_summary.get("families", {})
    if not isinstance(before_families, dict):
        before_families = {}
    if not isinstance(after_families, dict):
        after_families = {}

    family_deltas: dict[str, Any] = {}
    for family in sorted(set(before_families) | set(after_families)):
        before_metrics = before_families.get(family, {})
        after_metrics = after_families.get(family, {})
        if not isinstance(before_metrics, dict):
            before_metrics = {}
        if not isinstance(after_metrics, dict):
            after_metrics = {}
        delta = numeric_delta(before_metrics, after_metrics)
        if delta or family not in before_families or family not in after_families:
            family_deltas[family] = {
                "status": family_status(family, before_families, after_families),
                "metrics": delta,
            }
    return family_deltas


def compare_reports(before_path: Path, after_path: Path) -> dict[str, Any]:
    before = load_report(before_path)
    after = load_report(after_path)
    summary_delta = numeric_delta(before["summary"], after["summary"])
    family_delta = compare_families(before["summary"], after["summary"])
    case_changes = compare_cases(case_index(before), case_index(after))
    changed = bool(
        summary_delta
        or family_delta
        or case_changes["added"]
        or case_changes["removed"]
        or case_changes["changed"]
    )
    return {
        "schema_version": "1.0",
        "before": str(before_path),
        "after": str(after_path),
        "status": "changed" if changed else "unchanged",
        "summary_delta": summary_delta,
        "family_delta": family_delta,
        "case_changes": case_changes,
        "counts": {
            "added_cases": len(case_changes["added"]),
            "removed_cases": len(case_changes["removed"]),
            "changed_cases": len(case_changes["changed"]),
            "changed_families": len(family_delta),
            "changed_summary_metrics": len(summary_delta),
        },
    }


def format_text(report: dict[str, Any], *, max_cases: int = 20) -> str:
    counts = report["counts"]
    lines = [
        "ManifoldGuard Evaluation Report Diff",
        "",
        f"Status: {report['status']}",
        f"Before: {report['before']}",
        f"After: {report['after']}",
        "Case changes: "
        f"added={counts['added_cases']} "
        f"removed={counts['removed_cases']} "
        f"changed={counts['changed_cases']}",
        f"Family changes: {counts['changed_families']}",
        "",
        "Summary deltas:",
    ]
    if report["summary_delta"]:
        for key, values in report["summary_delta"].items():
            lines.append(
                f"- {key}: {values['before']} -> {values['after']} "
                f"({values['delta']:+})"
            )
    else:
        lines.append("- none")

    lines.extend(["", "Changed cases:"])
    changed_cases = report["case_changes"]["changed"]
    if changed_cases:
        for case in changed_cases[:max_cases]:
            before = case["before"]
            after = case["after"]
            lines.append(
                f"- {case['id']}: passed {before.get('passed')} -> "
                f"{after.get('passed')}; action {before.get('actual_action')} -> "
                f"{after.get('actual_action')}"
            )
        remaining = len(changed_cases) - max_cases
        if remaining > 0:
            lines.append(f"- ... {remaining} more changed case(s)")
    else:
        lines.append("- none")

    if report["case_changes"]["added"]:
        lines.extend(["", "Added cases:"])
        for case_id in report["case_changes"]["added"][:max_cases]:
            lines.append(f"- {case_id}")
    if report["case_changes"]["removed"]:
        lines.extend(["", "Removed cases:"])
        for case_id in report["case_changes"]["removed"][:max_cases]:
            lines.append(f"- {case_id}")

    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    report = compare_reports(args.before, args.after)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_text(report), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
