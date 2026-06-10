import argparse
import json
from typing import Any, Dict, Optional

from .mbt.regulator import regulate_candidates
from .mbt.stability import classify_entropy, confidence_score
from .mbt.tokens import token_shock_map


def main() -> None:
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
            print(json.dumps(report, indent=2, sort_keys=True))
        elif result.action == "block":
            print("BLOCK | no safe candidate")
            _print_evaluation_lines(report)
        else:
            assert result.emitted is not None
            print(f"EMIT | {result.emitted_text} | score={result.emitted.regulator_score:.4f}")
            _print_evaluation_lines(report)
        return

    if args.text is None:
        parser.error("text is required unless --candidate is supplied")

    score = confidence_score(args.text)
    label, _ = classify_entropy(score)

    print(f"{label} | Internal Entropy: {score:.4f}")


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
        "evaluations": evaluations,
    }


def _print_evaluation_lines(report: Dict[str, Any]) -> None:
    for evaluation in report["evaluations"]:
        clamps = "|".join(evaluation["clamps"])
        print(
            f"[{evaluation['index']}] {evaluation['status']} | "
            f"score={evaluation['regulator_score']:.4f} | clamps={clamps}"
        )
        for token in evaluation.get("token_shock", []):
            print(f"    token_shock | {token['token']} | shock={token['shock']:.4f}")


if __name__ == "__main__":
    main()
