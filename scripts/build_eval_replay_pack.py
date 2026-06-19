#!/usr/bin/env python
"""Build replay packs from ManifoldGuard evaluation reports and corpora."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CORPUS = PROJECT_ROOT / "examples" / "regression_corpus.jsonl"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a compact replay pack for evaluator cases."
    )
    parser.add_argument(
        "--evaluation",
        required=True,
        type=Path,
        help="JSON report produced by manifold-eval or scripts/evaluate_regulator.py.",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=DEFAULT_CORPUS,
        help="JSONL corpus used to produce the evaluation report.",
    )
    parser.add_argument(
        "--case-id",
        action="append",
        dest="case_ids",
        default=[],
        help="Include an exact case id. Repeat to include multiple cases.",
    )
    parser.add_argument(
        "--family",
        action="append",
        dest="families",
        default=[],
        help="Include cases from this family. Repeat to include multiple families.",
    )
    parser.add_argument(
        "--include-passed",
        action="store_true",
        help="Include passed cases too. By default only failing cases are replayed.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the replay pack to this path instead of stdout.",
    )
    return parser.parse_args(argv)


def normalize_filters(values: Sequence[str] | None) -> list[str]:
    if values is None:
        return []
    return [value.strip() for value in values if value.strip()]


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return payload


def list_text(
    item: dict[str, Any],
    *,
    plural_key: str,
    singular_key: str,
) -> list[str]:
    value = item.get(plural_key, item.get(singular_key, []))
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = [entry for entry in value if isinstance(entry, str)]
    else:
        values = []
    return [entry.strip() for entry in values if entry.strip()]


def load_corpus(path: Path) -> dict[str, dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                item = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc.msg}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            case_id = str(item.get("id") or f"line-{line_number}")
            cases[case_id] = {
                "id": case_id,
                "line": line_number,
                "references": list_text(
                    item,
                    plural_key="references",
                    singular_key="reference",
                ),
                "candidates": list_text(
                    item,
                    plural_key="candidates",
                    singular_key="candidate",
                ),
                "expected_action": item.get("expected_action"),
                "expected_emitted_text": item.get("expected_emitted_text"),
                "expected_candidate_safe": item.get("expected_candidate_safe"),
            }
    return cases


def load_evaluation(path: Path) -> dict[str, Any]:
    evaluation = load_json(path)
    if not isinstance(evaluation.get("cases"), list):
        raise ValueError(f"{path}: expected a cases list")
    return evaluation


def selected_eval_cases(
    evaluation: dict[str, Any],
    *,
    families: Sequence[str] | None = None,
    case_ids: Sequence[str] | None = None,
    include_passed: bool = False,
) -> list[dict[str, Any]]:
    family_filters = set(normalize_filters(families))
    case_id_filters = set(normalize_filters(case_ids))
    explicit_cases = bool(case_id_filters)
    selected: list[dict[str, Any]] = []
    for case in evaluation["cases"]:
        if not isinstance(case, dict):
            continue
        case_id = case.get("id")
        family = case.get("family")
        if case_id_filters and case_id not in case_id_filters:
            continue
        if family_filters and family not in family_filters:
            continue
        if not include_passed and not explicit_cases and case.get("passed") is True:
            continue
        selected.append(case)
    return selected


def replay_case(
    eval_case: dict[str, Any],
    corpus_cases: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    case_id = str(eval_case.get("id", ""))
    corpus_case = corpus_cases.get(case_id, {})
    return {
        "id": case_id,
        "family": eval_case.get("family"),
        "corpus_line": corpus_case.get("line"),
        "corpus_found": bool(corpus_case),
        "passed": eval_case.get("passed"),
        "expected_action": eval_case.get(
            "expected_action",
            corpus_case.get("expected_action"),
        ),
        "actual_action": eval_case.get("actual_action"),
        "expected_emitted_text": eval_case.get(
            "expected_emitted_text",
            corpus_case.get("expected_emitted_text"),
        ),
        "actual_emitted_text": eval_case.get("actual_emitted_text"),
        "expected_candidate_safe": eval_case.get(
            "expected_candidate_safe",
            corpus_case.get("expected_candidate_safe"),
        ),
        "actual_candidate_safe": eval_case.get("actual_candidate_safe"),
        "mismatches": list(eval_case.get("mismatches") or []),
        "references": list(corpus_case.get("references") or []),
        "candidates": list(corpus_case.get("candidates") or []),
        "candidate_diagnostics": list(eval_case.get("candidate_diagnostics") or []),
    }


def build_replay_pack(
    *,
    corpus_path: Path = DEFAULT_CORPUS,
    evaluation_path: Path,
    families: Sequence[str] | None = None,
    case_ids: Sequence[str] | None = None,
    include_passed: bool = False,
) -> dict[str, Any]:
    corpus_cases = load_corpus(corpus_path)
    evaluation = load_evaluation(evaluation_path)
    selected_cases = selected_eval_cases(
        evaluation,
        families=families,
        case_ids=case_ids,
        include_passed=include_passed,
    )
    replay_cases = [replay_case(case, corpus_cases) for case in selected_cases]
    return {
        "schema_version": "1.0",
        "corpus": str(corpus_path),
        "evaluation": str(evaluation_path),
        "source_status": evaluation.get("status"),
        "filters": {
            "families": normalize_filters(families),
            "case_ids": normalize_filters(case_ids),
            "include_passed": include_passed,
            "default_selection": "failures_only",
        },
        "summary": {
            "selected_cases": len(replay_cases),
            "missing_corpus_cases": sum(
                1 for case in replay_cases if not case["corpus_found"]
            ),
        },
        "cases": replay_cases,
    }


def diagnostic_by_index(case: dict[str, Any]) -> dict[int, dict[str, Any]]:
    diagnostics: dict[int, dict[str, Any]] = {}
    for diagnostic in case.get("candidate_diagnostics", []):
        if not isinstance(diagnostic, dict):
            continue
        index = diagnostic.get("index")
        if isinstance(index, int):
            diagnostics[index] = diagnostic
    return diagnostics


def format_markdown(pack: dict[str, Any]) -> str:
    lines = [
        "# ManifoldGuard Evaluation Replay Pack",
        "",
        f"Evaluation: `{pack['evaluation']}`",
        f"Corpus: `{pack['corpus']}`",
        f"Source status: `{pack.get('source_status')}`",
        f"Selected cases: {pack['summary']['selected_cases']}",
        f"Missing corpus cases: {pack['summary']['missing_corpus_cases']}",
        "",
    ]
    if not pack["cases"]:
        lines.append("No cases selected.")
        return "\n".join(lines) + "\n"

    for case in pack["cases"]:
        lines.extend(
            [
                f"## {case['id']}",
                "",
                f"Family: `{case.get('family')}`",
                f"Passed: `{case.get('passed')}`",
                f"Expected action: `{case.get('expected_action')}`",
                f"Actual action: `{case.get('actual_action')}`",
                f"Expected emitted text: `{case.get('expected_emitted_text')}`",
                f"Actual emitted text: `{case.get('actual_emitted_text')}`",
                "",
                "### Mismatches",
            ]
        )
        mismatches = case.get("mismatches") or []
        if mismatches:
            lines.extend(f"- {mismatch}" for mismatch in mismatches)
        else:
            lines.append("- none")

        lines.extend(["", "### References"])
        references = case.get("references") or []
        if references:
            lines.extend(f"{index}. {reference}" for index, reference in enumerate(references, start=1))
        else:
            lines.append("- missing from corpus")

        lines.extend(["", "### Candidates"])
        candidates = case.get("candidates") or []
        diagnostics = diagnostic_by_index(case)
        if candidates:
            for index, candidate in enumerate(candidates):
                safe_values = case.get("actual_candidate_safe") or []
                safe = safe_values[index] if index < len(safe_values) else None
                diagnostic = diagnostics.get(index, {})
                clamps = ", ".join(diagnostic.get("clamp_summary") or [])
                lines.append(f"{index}. safe={safe} `{candidate}`")
                if clamps:
                    lines.append(f"   Clamps: `{clamps}`")
                if diagnostic.get("literal_score") is not None:
                    lines.append(f"   Literal score: `{diagnostic['literal_score']}`")
        else:
            lines.append("- missing from corpus")
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    pack = build_replay_pack(
        corpus_path=args.corpus,
        evaluation_path=args.evaluation,
        families=args.families,
        case_ids=args.case_ids,
        include_passed=args.include_passed,
    )
    if args.format == "json":
        rendered = json.dumps(pack, indent=2, sort_keys=True) + "\n"
    else:
        rendered = format_markdown(pack)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
