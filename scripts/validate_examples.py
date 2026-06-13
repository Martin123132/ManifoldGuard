#!/usr/bin/env python
"""Validate that committed examples match current offline CLI behavior."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mbt_ai_tools.cli import (
    build_batch_reports,
    build_regulation_report,
    format_csv_audit,
    format_markdown_audit,
)
from mbt_ai_tools.mbt.regulator import regulate_candidates


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SINGLE_REFERENCES = ["The capital of France is Paris."]
SINGLE_CANDIDATES = [
    "The capital of France is London.",
    "The capital of France is Paris.",
]


def canonical_json(payload: Any, *, pretty: bool = False) -> str:
    if pretty:
        return json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n"


def json_ready(payload: Any) -> Any:
    return json.loads(canonical_json(payload))


def expected_single_report() -> dict[str, Any]:
    result = regulate_candidates(
        SINGLE_CANDIDATES,
        SINGLE_REFERENCES,
        use_embeddings=False,
    )
    return build_regulation_report(result)


def expected_batch_reports(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    return list(
        build_batch_reports(
            project_root / "examples" / "batch_input.jsonl",
            use_embeddings=False,
        )
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def validate_examples(project_root: Path = PROJECT_ROOT) -> list[str]:
    examples_dir = project_root / "examples"
    failures: list[str] = []

    single_report = expected_single_report()
    single_path = examples_dir / "single_report_example.json"
    if json.loads(single_path.read_text(encoding="utf-8")) != json_ready(single_report):
        failures.append(f"{single_path} does not match current single-report output")

    batch_reports = expected_batch_reports(project_root)
    batch_path = examples_dir / "batch_report_example.jsonl"
    if read_jsonl(batch_path) != [json_ready(report) for report in batch_reports]:
        failures.append(f"{batch_path} does not match current batch JSONL output")

    csv_path = examples_dir / "csv_audit_report.csv"
    expected_csv = format_csv_audit(batch_reports)
    if csv_path.read_text(encoding="utf-8") != expected_csv:
        failures.append(f"{csv_path} does not match current CSV audit output")

    json_demo_path = examples_dir / "cli_json_report.md"
    expected_json_block = canonical_json(single_report, pretty=True).strip()
    if expected_json_block not in json_demo_path.read_text(encoding="utf-8"):
        failures.append(f"{json_demo_path} does not include current JSON output")

    markdown_path = examples_dir / "markdown_audit_report.md"
    expected_markdown = format_markdown_audit(batch_reports).strip()
    if expected_markdown not in markdown_path.read_text(encoding="utf-8"):
        failures.append(f"{markdown_path} does not include current Markdown audit output")

    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate committed example outputs against current offline CLI behavior."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Repository root containing examples/.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    failures = validate_examples(args.project_root)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print("Example fixtures are current.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
