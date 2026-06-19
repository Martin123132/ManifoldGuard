"""Build the exploratory EXP22 ManifoldGuard challenge corpus seed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path(__file__).with_name("exp22_challenge_corpus.jsonl")


def challenge_case(
    case_id: str,
    references: list[str],
    candidates: list[str],
    expected_candidate_safe: list[bool],
    *,
    notes: str,
) -> dict[str, Any]:
    if len(candidates) != len(expected_candidate_safe):
        raise ValueError(f"{case_id}: candidate safety length mismatch")
    safe_indexes = [index for index, safe in enumerate(expected_candidate_safe) if safe]
    expected_action = "emit" if safe_indexes else "block"
    expected_emitted_text = candidates[safe_indexes[0]] if safe_indexes else None
    return {
        "id": case_id,
        "references": references,
        "candidates": candidates,
        "expected_action": expected_action,
        "expected_emitted_text": expected_emitted_text,
        "expected_candidate_safe": expected_candidate_safe,
        "challenge_notes": notes,
    }


def build_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    coreference_binding = [
        (
            "parser_review",
            "Ada wrote the parser. Linus reviewed the parser.",
            [
                "Linus wrote the parser and Ada reviewed it.",
                "Ada wrote the parser and Linus reviewed it.",
            ],
            [False, True],
        ),
        (
            "valve_tanks",
            "The blue valve feeds Tank A. The red valve feeds Tank B.",
            [
                "The red valve feeds Tank A and the blue valve feeds Tank B.",
                "The blue valve feeds Tank A and the red valve feeds Tank B.",
            ],
            [False, True],
        ),
        (
            "supervision_chain",
            "Maya supervises Kim. Kim supervises Omar.",
            [
                "Omar supervises Kim and Kim supervises Maya.",
                "Maya supervises Kim and Kim supervises Omar.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in coreference_binding:
        cases.append(
            challenge_case(
                f"exp22_coreference_binding_{key}",
                [reference],
                candidates,
                safe,
                notes="Role bindings should survive compact paraphrase and pronoun-like reuse.",
            )
        )

    comparative_binding = [
        (
            "plan_cost",
            "Plan A costs 40 dollars. Plan B costs 55 dollars.",
            [
                "Plan B is cheaper than Plan A.",
                "Plan A is cheaper than Plan B.",
            ],
            [False, True],
        ),
        (
            "model_latency",
            "Model X has 80 ms latency. Model Y has 120 ms latency.",
            [
                "Model Y is faster than Model X.",
                "Model X is faster than Model Y.",
            ],
            [False, True],
        ),
        (
            "battery_capacity",
            "Battery Alpha stores 3000 mAh. Battery Beta stores 2500 mAh.",
            [
                "Battery Beta has higher capacity than Battery Alpha.",
                "Battery Alpha has higher capacity than Battery Beta.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in comparative_binding:
        cases.append(
            challenge_case(
                f"exp22_comparative_binding_{key}",
                [reference],
                candidates,
                safe,
                notes="Comparative claims must preserve numeric direction and participant binding.",
            )
        )

    exception_scope = [
        (
            "weekday_closure",
            "The museum is open every weekday except Monday.",
            [
                "The museum is open on Monday.",
                "The museum is closed on Monday and open on other weekdays.",
            ],
            [False, True],
        ),
        (
            "shipping_regions",
            "The service ships to Europe and Asia, but not Brazil.",
            [
                "The service ships to Brazil.",
                "The service ships to Europe and Asia but not Brazil.",
            ],
            [False, True],
        ),
        (
            "file_formats",
            "The importer accepts CSV and JSON files, except encrypted JSON.",
            [
                "The importer accepts encrypted JSON files.",
                "The importer accepts CSV and JSON files but not encrypted JSON.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in exception_scope:
        cases.append(
            challenge_case(
                f"exp22_exception_scope_{key}",
                [reference],
                candidates,
                safe,
                notes="Exceptions and exclusions should not be collapsed into positive support.",
            )
        )

    unit_conversion = [
        (
            "temperature_units",
            "The incubator is set to 37 degrees Celsius.",
            [
                "The incubator is set to 37 degrees Fahrenheit.",
                "The incubator is set to 37 degrees Celsius.",
            ],
            [False, True],
        ),
        (
            "storage_units",
            "The backup archive is 4 GB.",
            [
                "The backup archive is 4 MB.",
                "The backup archive is 4 GB.",
            ],
            [False, True],
        ),
        (
            "distance_units",
            "The cable length is 12 meters.",
            [
                "The cable length is 12 centimeters.",
                "The cable length is 12 meters.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in unit_conversion:
        cases.append(
            challenge_case(
                f"exp22_unit_binding_{key}",
                [reference],
                candidates,
                safe,
                notes="Same numbers with changed units should remain unsafe.",
            )
        )

    temporal_order = [
        (
            "approval_deployment",
            "The feature was approved before deployment.",
            [
                "The feature was deployed before approval.",
                "The feature was approved before deployment.",
            ],
            [False, True],
        ),
        (
            "backup_migration",
            "The backup completed after the migration.",
            [
                "The backup completed before the migration.",
                "The backup completed after the migration.",
            ],
            [False, True],
        ),
        (
            "inspection_launch",
            "The inspection happened before launch and the repair happened after launch.",
            [
                "The repair happened before launch and the inspection happened after launch.",
                "The inspection happened before launch and the repair happened after launch.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in temporal_order:
        cases.append(
            challenge_case(
                f"exp22_temporal_order_{key}",
                [reference],
                candidates,
                safe,
                notes="Before/after order should not be reversed or rebound across events.",
            )
        )

    all_bad_near_miss = [
        (
            "double_swap",
            "The left pump feeds Boiler 1. The right pump feeds Boiler 2.",
            [
                "The left pump feeds Boiler 2.",
                "The right pump feeds Boiler 1.",
                "Boiler 1 feeds the left pump.",
            ],
        ),
        (
            "negated_exception",
            "The form requires a signature and does not require a witness.",
            [
                "The form requires a witness and does not require a signature.",
                "The form does not require a signature.",
            ],
        ),
        (
            "alias_role",
            "Dr. Rao, also called Mira Rao, signed the report.",
            [
                "Dr. Chen signed the report.",
                "The report signed Mira Rao.",
            ],
        ),
    ]
    for key, reference, candidates in all_bad_near_miss:
        cases.append(
            challenge_case(
                f"exp22_all_bad_near_miss_{key}",
                [reference],
                candidates,
                [False] * len(candidates),
                notes="Every candidate is close to the reference but should still be blocked.",
            )
        )

    return cases


def main() -> None:
    cases = build_cases()
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        for case in cases:
            handle.write(json.dumps(case, ensure_ascii=True, separators=(",", ":")))
            handle.write("\n")
    candidate_count = sum(len(case["candidates"]) for case in cases)
    print(f"wrote {len(cases)} cases / {candidate_count} candidates to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
