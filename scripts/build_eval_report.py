#!/usr/bin/env python
"""Build a Markdown evaluation report from ManifoldGuard offline corpus metrics."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from mbt_ai_tools.eval import evaluate_corpus


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "evaluation_report.md"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a Markdown report from ManifoldGuard offline evaluator JSON."
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Existing regulator-evaluation JSON artifact. If omitted, run the packaged evaluator.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Markdown report output path.",
    )
    parser.add_argument(
        "--generated-at",
        help="UTC timestamp for deterministic tests or release notes.",
    )
    return parser.parse_args(argv)


def load_report(path: Path | None) -> dict[str, Any]:
    if path is None:
        return evaluate_corpus()
    return json.loads(path.read_text(encoding="utf-8"))


def markdown_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return lines


def build_markdown(report: dict[str, Any], *, generated_at: str | None = None) -> str:
    summary = report["summary"]
    timestamp = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    families = summary.get("families", {})
    family_rows = [
        [
            family,
            metrics["total_cases"],
            metrics["passed_cases"],
            metrics["failed_cases"],
            metrics["actual_emit"],
            metrics["actual_block"],
        ]
        for family, metrics in sorted(families.items())
    ]

    lines = [
        "# ManifoldGuard Offline Evaluation Report",
        "",
        f"Generated at: `{timestamp}`",
        "",
        "## Summary",
        "",
        f"- Status: `{report['status']}`",
        f"- Corpus: `{report['corpus']}`",
        f"- Mode: `{report['mode']}`",
        f"- Cases: `{summary['total_cases']}`",
        f"- Passed: `{summary['passed_cases']}`",
        f"- Failed: `{summary['failed_cases']}`",
        f"- Expected actions: emit=`{summary['expected_emit']}` block=`{summary['expected_block']}`",
        f"- Actual actions: emit=`{summary['actual_emit']}` block=`{summary['actual_block']}`",
        f"- Candidate evaluations: total=`{summary['candidate_evaluations']}` safe=`{summary['safe_candidate_evaluations']}` blocked=`{summary['blocked_candidate_evaluations']}`",
        "",
        "## Taxonomy",
        "",
    ]
    lines.extend(
        markdown_table(
            ["Family", "Cases", "Passed", "Failed", "Actual emit", "Actual block"],
            family_rows,
        )
    )

    failures = [case for case in report.get("cases", []) if not case.get("passed")]
    lines.extend(["", "## Failures", ""])
    if failures:
        for case in failures:
            lines.append(f"- `{case['id']}`: {'; '.join(case.get('mismatches', []))}")
            diagnostics = case.get("candidate_diagnostics", [])
            if diagnostics:
                for candidate in diagnostics:
                    clamps = ", ".join(candidate.get("clamp_summary", []))
                    safe = candidate.get("safe_to_emit")
                    lines.append(
                        f"  - candidate `{candidate.get('index')}` "
                        f"safe=`{safe}` clamps=`{clamps}`"
                    )
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    report = load_report(args.input)
    content = build_markdown(report, generated_at=args.generated_at)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    print(f"Wrote evaluation report to {args.output}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
