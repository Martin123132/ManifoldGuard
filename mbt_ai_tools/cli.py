import argparse
import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .mbt.regulator import regulate_candidates
from .mbt.stability import classify_entropy, confidence_score
from .mbt.tokens import token_shock_map


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MBT-5 geometry-only confidence probe and v11 candidate regulator."
    )
    parser.add_argument(
        "text",
        nargs="?",
        help='Text or blank-line separated responses to score, e.g. `mbt-check "answer a\n\nanswer b"`',
    )
    parser.add_argument(
        "--reference",
        "-r",
        action="append",
        default=[],
        help="Reference statement. Repeat to build a reference manifold for candidate regulation.",
    )
    parser.add_argument(
        "--candidate",
        "-c",
        action="append",
        default=[],
        help="Candidate output to regulate. Repeat for candidate selection; emits best safe candidate or BLOCK.",
    )
    parser.add_argument(
        "--input-jsonl",
        type=Path,
        help="Batch regulation input JSONL. Each line needs references and candidates fields.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Write command output to a file instead of stdout.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Append a batch summary JSON object when using --input-jsonl.",
    )
    parser.add_argument(
        "--fail-on-block",
        action="store_true",
        help="Exit with status 2 when a regulation run blocks.",
    )
    parser.add_argument(
        "--no-embeddings",
        action="store_true",
        help="Run only literal/relation/negation clamps without semantic embeddings.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format for regulation reports.",
    )
    parser.add_argument(
        "--token-shock",
        action="store_true",
        help="Include token-level shock scores for each candidate in regulation mode.",
    )
    parser.add_argument(
        "--token-shock-max-samples",
        type=int,
        default=None,
        help="Maximum number of token-removal variants to score when --token-shock is used.",
    )
    parser.add_argument(
        "--token-shock-top-k",
        type=int,
        default=None,
        help="Return only the highest-shock tokens when --token-shock is used.",
    )
    parser.add_argument(
        "--token-shock-order",
        choices=("token", "score"),
        default="score",
        help="Order token shock output by original token position or descending score.",
    )
    args = parser.parse_args()

    if args.input_jsonl:
        if args.reference or args.candidate or args.text:
            parser.error("--input-jsonl cannot be combined with positional text, --reference, or --candidate")
        try:
            reports = list(
                build_batch_reports(
                    args.input_jsonl,
                    use_embeddings=not args.no_embeddings,
                    include_token_shock=args.token_shock,
                    token_shock_max_samples=args.token_shock_max_samples,
                    token_shock_top_k=args.token_shock_top_k,
                    token_shock_order=args.token_shock_order,
                )
            )
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
        output_items = reports[:]
        if args.summary:
            output_items.append(build_batch_summary(reports))
        content = "".join(f"{json.dumps(report, sort_keys=True)}\n" for report in output_items)
        _emit_output(content, args.output)
        return 2 if args.fail_on_block and any(report["action"] == "block" for report in reports) else 0

    if args.reference or args.candidate:
        candidates = args.candidate or ([args.text] if args.text else [])
        if not args.reference:
            parser.error("--reference is required when using --candidate regulation mode")
        if not candidates:
            parser.error("provide at least one --candidate or positional text in regulation mode")

        result = regulate_candidates(
            candidates,
            args.reference,
            use_embeddings=not args.no_embeddings,
        )
        report = build_regulation_report(
            result,
            include_token_shock=args.token_shock,
            token_shock_max_samples=args.token_shock_max_samples,
            token_shock_top_k=args.token_shock_top_k,
            token_shock_order=args.token_shock_order,
        )
        if args.format == "json":
            content = f"{json.dumps(report, indent=2, sort_keys=True)}\n"
        else:
            content = format_regulation_text(report)
        _emit_output(content, args.output)
        return 2 if args.fail_on_block and report["action"] == "block" else 0

    if args.text is None:
        parser.error("text is required unless --candidate is supplied")

    score = confidence_score(args.text)
    label, _ = classify_entropy(score)

    _emit_output(f"{label} | Internal Entropy: {score:.4f}\n", args.output)
    return 0


def build_regulation_report(
    result,
    *,
    include_token_shock: bool = False,
    token_shock_max_samples: Optional[int] = None,
    token_shock_top_k: Optional[int] = None,
    token_shock_order: str = "score",
) -> Dict[str, Any]:
    emitted_index = None
    if result.emitted is not None:
        emitted_index = next(
            (
                index
                for index, evaluation in enumerate(result.evaluations)
                if evaluation is result.emitted
            ),
            None,
        )

    evaluations = []
    for index, evaluation in enumerate(result.evaluations):
        item: Dict[str, Any] = {
            "index": index,
            "text": evaluation.text,
            "status": "safe" if evaluation.safe_to_emit else "blocked",
            "safe_to_emit": evaluation.safe_to_emit,
            "pred_hallucinated": evaluation.pred_hallucinated,
            "regulator_score": evaluation.regulator_score,
            "mbt5_shock": evaluation.mbt5_shock,
            "threshold": evaluation.threshold,
            "literal_score": evaluation.literal_score,
            "clamps": list(evaluation.clamp_summary),
            "relations": list(evaluation.relations),
            "negated_relations": list(evaluation.negated_relations),
            "exact_reference_member": evaluation.exact_reference_member,
        }
        if include_token_shock:
            item["token_shock"] = [
                {"token": token, "shock": score}
                for token, score in token_shock_map(
                    evaluation.text,
                    max_samples=token_shock_max_samples,
                    top_k=token_shock_top_k,
                    order=token_shock_order,
                )
            ]
        evaluations.append(item)

    return {
        "action": result.action,
        "emitted_text": result.emitted_text,
        "emitted_index": emitted_index,
        "emitted_score": None
        if emitted_index is None
        else evaluations[emitted_index]["regulator_score"],
        "evaluations": evaluations,
    }


def build_batch_reports(
    input_jsonl: Path,
    *,
    use_embeddings: bool = True,
    include_token_shock: bool = False,
    token_shock_max_samples: Optional[int] = None,
    token_shock_top_k: Optional[int] = None,
    token_shock_order: str = "score",
) -> Iterable[Dict[str, Any]]:
    with input_jsonl.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                item = json.loads(raw_line)
            except JSONDecodeError as exc:
                raise ValueError(
                    f"{input_jsonl}:{line_number}: invalid JSON: {exc.msg}"
                ) from exc
            if not isinstance(item, dict):
                raise ValueError(f"{input_jsonl}:{line_number}: expected a JSON object")

            references = _text_list(item, "references", "reference", input_jsonl, line_number)
            candidates = _text_list(item, "candidates", "candidate", input_jsonl, line_number)
            result = regulate_candidates(
                candidates,
                references,
                use_embeddings=use_embeddings,
            )
            report = build_regulation_report(
                result,
                include_token_shock=include_token_shock,
                token_shock_max_samples=token_shock_max_samples,
                token_shock_top_k=token_shock_top_k,
                token_shock_order=token_shock_order,
            )
            report["line"] = line_number
            report["references"] = references
            if "id" in item:
                report["id"] = item["id"]
            yield report


def build_batch_summary(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    safe_candidates = sum(
        1
        for report in reports
        for evaluation in report["evaluations"]
        if evaluation["safe_to_emit"]
    )
    blocked_candidates = sum(
        1
        for report in reports
        for evaluation in report["evaluations"]
        if not evaluation["safe_to_emit"]
    )
    return {
        "record_type": "summary",
        "total": len(reports),
        "emitted": sum(1 for report in reports if report["action"] == "emit"),
        "blocked": sum(1 for report in reports if report["action"] == "block"),
        "safe_candidates": safe_candidates,
        "blocked_candidates": blocked_candidates,
    }


def format_regulation_text(report: Dict[str, Any]) -> str:
    if report["action"] == "block":
        lines = ["BLOCK | no safe candidate"]
    else:
        lines = [
            f"EMIT | {report['emitted_text']} | score={report['emitted_score']:.4f}"
        ]

    for evaluation in report["evaluations"]:
        clamps = "|".join(evaluation["clamps"])
        lines.append(
            f"[{evaluation['index']}] {evaluation['status']} | "
            f"score={evaluation['regulator_score']:.4f} | clamps={clamps}"
        )
        for token in evaluation.get("token_shock", []):
            lines.append(f"    token_shock | {token['token']} | shock={token['shock']:.4f}")
    return "\n".join(lines) + "\n"


def _text_list(
    item: Dict[str, Any],
    plural_key: str,
    singular_key: str,
    input_jsonl: Path,
    line_number: int,
) -> List[str]:
    value = item.get(plural_key, item.get(singular_key))
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list) and all(isinstance(entry, str) for entry in value):
        values = value
    else:
        raise ValueError(
            f"{input_jsonl}:{line_number}: {plural_key} must be a string or list of strings"
        )
    if not values:
        raise ValueError(f"{input_jsonl}:{line_number}: {plural_key} cannot be empty")
    return values


def _emit_output(content: str, output_path: Optional[Path]) -> None:
    if output_path is None:
        print(content, end="")
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
