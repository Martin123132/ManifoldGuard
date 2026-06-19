"""Offline regression evaluation for ManifoldGuard."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from mbt_ai_tools import __version__
from mbt_ai_tools.mbt.regulator import regulate_candidates
from mbt_ai_tools.mbt.regulator import CandidateEvaluation


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_CORPUS = Path(__file__).resolve().parent / "data" / "regression_corpus.jsonl"
REPO_CORPUS = PROJECT_ROOT / "examples" / "regression_corpus.jsonl"
DEFAULT_CORPUS = PACKAGE_CORPUS if PACKAGE_CORPUS.exists() else REPO_CORPUS
CASE_FAMILY_PREFIXES = (
    "capital_entity_swap",
    "capital_all_bad",
    "capital_reverse_paraphrase",
    "capital_supported_paraphrase",
    "coordinated_relation",
    "copular_relation",
    "exact_reference_member",
    "noncopular_relation",
    "numeric_drift",
    "overclaim",
    "unit_drift",
    "unsupported_negation",
    "challenge_alias_binding",
    "challenge_all_bad_near_miss",
    "challenge_negation_scope",
    "challenge_qualifier_overclaim",
    "challenge_relation_composition",
    "challenge_supported_negation",
    "challenge_temporal_scope",
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run deterministic offline ManifoldGuard regulator evaluation."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=DEFAULT_CORPUS,
        help="JSONL corpus with references, candidates, and expected outputs.",
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
        help="Write the full JSON evaluation report to this path.",
    )
    parser.add_argument(
        "--family",
        action="append",
        dest="families",
        default=[],
        help="Only evaluate cases from this family. Repeat to include multiple families.",
    )
    parser.add_argument(
        "--case-id",
        action="append",
        dest="case_ids",
        default=[],
        help="Only evaluate an exact case id. Repeat to include multiple cases.",
    )
    parser.add_argument(
        "--failures-only",
        action="store_true",
        help="Only include failing cases in the reported case list.",
    )
    parser.add_argument(
        "--list-families",
        action="store_true",
        help="List evaluated corpus families and exit.",
    )
    parser.add_argument(
        "--max-failures",
        type=int,
        default=10,
        help="Maximum failure details shown in text output.",
    )
    return parser.parse_args(argv)


def case_family(case_id: str) -> str:
    for prefix in CASE_FAMILY_PREFIXES:
        if case_id == prefix or case_id.startswith(f"{prefix}_"):
            return prefix
    parts = case_id.split("_")
    if len(parts) <= 2:
        return case_id
    return "_".join(parts[:-1])


def text_list(
    item: dict[str, Any],
    *,
    plural_key: str,
    singular_key: str,
    path: Path,
    line_number: int,
) -> list[str]:
    if plural_key in item:
        value = item[plural_key]
    elif singular_key in item:
        value = item[singular_key]
    else:
        raise ValueError(
            f"{path}:{line_number}: expected '{plural_key}' or '{singular_key}'"
        )

    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list) and all(isinstance(entry, str) for entry in value):
        values = value
    else:
        raise ValueError(
            f"{path}:{line_number}: '{plural_key}'/'{singular_key}' must be text or a list of text"
        )

    values = [entry.strip() for entry in values if entry.strip()]
    if not values:
        raise ValueError(
            f"{path}:{line_number}: '{plural_key}'/'{singular_key}' must not be empty"
        )
    return values


def expected_bool_list(
    item: dict[str, Any],
    *,
    key: str,
    path: Path,
    line_number: int,
) -> list[bool] | None:
    if key not in item:
        return None
    value = item[key]
    if not isinstance(value, list) or not all(isinstance(entry, bool) for entry in value):
        raise ValueError(f"{path}:{line_number}: '{key}' must be a list of booleans")
    return value


def relation_record(relation: tuple[str, str, str]) -> dict[str, str]:
    subject, predicate, object_ = relation
    return {
        "subject": subject,
        "predicate": predicate,
        "object": object_,
    }


def candidate_diagnostic(
    evaluation: CandidateEvaluation,
    *,
    index: int,
) -> dict[str, Any]:
    literal_drift = evaluation.literal_drift
    return {
        "index": index,
        "text": evaluation.text,
        "safe_to_emit": evaluation.safe_to_emit,
        "pred_hallucinated": evaluation.pred_hallucinated,
        "regulator_score": evaluation.regulator_score,
        "mbt5_shock": evaluation.mbt5_shock,
        "threshold": evaluation.threshold,
        "literal_score": evaluation.literal_score,
        "clamp_summary": list(evaluation.clamp_summary),
        "exact_reference_member": evaluation.exact_reference_member,
        "relations": [
            relation_record(relation) for relation in evaluation.relations
        ],
        "negated_relations": [
            relation_record(relation) for relation in evaluation.negated_relations
        ],
        "literal_drift": {
            "novel_numbers": list(literal_drift.novel_numbers),
            "novel_units": list(literal_drift.novel_units),
            "novel_entities": list(literal_drift.novel_entities),
            "novel_content": list(literal_drift.novel_content),
        },
    }


def candidate_diagnostics(
    evaluations: Sequence[CandidateEvaluation],
) -> list[dict[str, Any]]:
    return [
        candidate_diagnostic(evaluation, index=index)
        for index, evaluation in enumerate(evaluations)
    ]


def evaluate_case(
    item: dict[str, Any],
    *,
    path: Path,
    line_number: int,
) -> dict[str, Any]:
    case_id = str(item.get("id") or f"line-{line_number}")
    references = text_list(
        item,
        plural_key="references",
        singular_key="reference",
        path=path,
        line_number=line_number,
    )
    candidates = text_list(
        item,
        plural_key="candidates",
        singular_key="candidate",
        path=path,
        line_number=line_number,
    )
    expected_action = item.get("expected_action")
    expected_emitted_text = item.get("expected_emitted_text")
    expected_candidate_safe = expected_bool_list(
        item,
        key="expected_candidate_safe",
        path=path,
        line_number=line_number,
    )

    result = regulate_candidates(candidates, references, use_embeddings=False)
    actual_candidate_safe = [
        evaluation.safe_to_emit for evaluation in result.evaluations
    ]

    mismatches: list[str] = []
    if expected_action is not None and result.action != expected_action:
        mismatches.append(
            f"action expected {expected_action!r}, got {result.action!r}"
        )
    if expected_emitted_text is not None and result.emitted_text != expected_emitted_text:
        mismatches.append(
            f"emitted_text expected {expected_emitted_text!r}, got {result.emitted_text!r}"
        )
    if (
        expected_candidate_safe is not None
        and actual_candidate_safe != expected_candidate_safe
    ):
        mismatches.append(
            "candidate safety expected "
            f"{expected_candidate_safe!r}, got {actual_candidate_safe!r}"
        )

    return {
        "id": case_id,
        "family": case_family(case_id),
        "line": line_number,
        "expected_action": expected_action,
        "actual_action": result.action,
        "expected_emitted_text": expected_emitted_text,
        "actual_emitted_text": result.emitted_text,
        "expected_candidate_safe": expected_candidate_safe,
        "actual_candidate_safe": actual_candidate_safe,
        "candidate_diagnostics": candidate_diagnostics(result.evaluations),
        "candidate_count": len(candidates),
        "passed": not mismatches,
        "mismatches": mismatches,
    }


def read_corpus(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
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
            cases.append(evaluate_case(item, path=path, line_number=line_number))
    return cases


def summarize_group(cases: list[dict[str, Any]]) -> dict[str, Any]:
    failed_cases = [case for case in cases if not case["passed"]]
    candidate_evaluations = sum(case["candidate_count"] for case in cases)
    safe_candidate_evaluations = sum(
        sum(1 for value in case["actual_candidate_safe"] if value)
        for case in cases
    )
    return {
        "total_cases": len(cases),
        "passed_cases": len(cases) - len(failed_cases),
        "failed_cases": len(failed_cases),
        "expected_emit": sum(1 for case in cases if case["expected_action"] == "emit"),
        "expected_block": sum(1 for case in cases if case["expected_action"] == "block"),
        "actual_emit": sum(1 for case in cases if case["actual_action"] == "emit"),
        "actual_block": sum(1 for case in cases if case["actual_action"] == "block"),
        "candidate_evaluations": candidate_evaluations,
        "safe_candidate_evaluations": safe_candidate_evaluations,
        "blocked_candidate_evaluations": candidate_evaluations
        - safe_candidate_evaluations,
    }


def summarize_families(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    families = sorted({case["family"] for case in cases})
    return {
        family: summarize_group([case for case in cases if case["family"] == family])
        for family in families
    }


def summarize_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        **summarize_group(cases),
        "families": summarize_families(cases),
    }


def normalized_filters(values: Sequence[str] | None) -> list[str]:
    if values is None:
        return []
    return [value.strip() for value in values if value.strip()]


def filter_evaluated_cases(
    cases: list[dict[str, Any]],
    *,
    families: Sequence[str] | None = None,
    case_ids: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    family_filters = set(normalized_filters(families))
    case_id_filters = set(normalized_filters(case_ids))
    selected_cases = cases
    if family_filters:
        selected_cases = [
            case for case in selected_cases if case["family"] in family_filters
        ]
    if case_id_filters:
        selected_cases = [
            case for case in selected_cases if case["id"] in case_id_filters
        ]
    return selected_cases


def evaluate_corpus(
    path: Path = DEFAULT_CORPUS,
    *,
    families: Sequence[str] | None = None,
    case_ids: Sequence[str] | None = None,
    failures_only: bool = False,
) -> dict[str, Any]:
    all_cases = read_corpus(path)
    selected_cases = filter_evaluated_cases(
        all_cases,
        families=families,
        case_ids=case_ids,
    )
    reported_cases = (
        [case for case in selected_cases if not case["passed"]]
        if failures_only
        else selected_cases
    )
    summary = summarize_cases(selected_cases)
    return {
        "schema_version": "1.0",
        "corpus": str(path),
        "mode": "offline",
        "status": "passed" if summary["failed_cases"] == 0 else "failed",
        "case_filters": {
            "families": normalized_filters(families),
            "case_ids": normalized_filters(case_ids),
            "failures_only": failures_only,
            "selected_cases": len(selected_cases),
            "reported_cases": len(reported_cases),
        },
        "summary": summary,
        "cases": reported_cases,
    }


def format_family_list(report: dict[str, Any]) -> str:
    lines = ["ManifoldGuard Offline Regression Families", ""]
    families = report["summary"]["families"]
    if not families:
        lines.append("- none")
    else:
        for family, metrics in families.items():
            lines.append(
                f"- {family}: cases={metrics['total_cases']} "
                f"passed={metrics['passed_cases']} failed={metrics['failed_cases']}"
            )
    return "\n".join(lines) + "\n"


def format_text(report: dict[str, Any], *, max_failures: int = 10) -> str:
    summary = report["summary"]
    lines = [
        "ManifoldGuard Offline Regression Evaluation",
        "",
        f"Status: {report['status']}",
        f"Corpus: {report['corpus']}",
        f"Cases: {summary['total_cases']}",
        f"Passed: {summary['passed_cases']}",
        f"Failed: {summary['failed_cases']}",
        f"Expected actions: emit={summary['expected_emit']} block={summary['expected_block']}",
        f"Actual actions: emit={summary['actual_emit']} block={summary['actual_block']}",
        "Candidate evaluations: "
        f"total={summary['candidate_evaluations']} "
        f"safe={summary['safe_candidate_evaluations']} "
        f"blocked={summary['blocked_candidate_evaluations']}",
        "",
        "Taxonomy:",
    ]
    for family, metrics in summary["families"].items():
        lines.append(
            f"- {family}: cases={metrics['total_cases']} "
            f"passed={metrics['passed_cases']} failed={metrics['failed_cases']} "
            f"actual_emit={metrics['actual_emit']} actual_block={metrics['actual_block']}"
        )

    lines.extend(["", "Failures:"])
    failures = [case for case in report["cases"] if not case["passed"]]
    if failures:
        for case in failures[:max_failures]:
            clamp_summary = "; ".join(
                f"{candidate['index']}={','.join(candidate['clamp_summary'])}"
                for candidate in case.get("candidate_diagnostics", [])
            )
            suffix = f" | clamps: {clamp_summary}" if clamp_summary else ""
            lines.append(f"- {case['id']}: {'; '.join(case['mismatches'])}{suffix}")
        remaining = len(failures) - max_failures
        if remaining > 0:
            lines.append(f"- ... {remaining} more failure(s)")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    report = evaluate_corpus(
        args.corpus,
        families=args.families,
        case_ids=args.case_ids,
        failures_only=args.failures_only,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.list_families:
        if args.format == "json":
            print(
                json.dumps(
                    {
                        "case_filters": report["case_filters"],
                        "families": report["summary"]["families"],
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print(format_family_list(report), end="")
        return 0
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_text(report, max_failures=args.max_failures), end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
