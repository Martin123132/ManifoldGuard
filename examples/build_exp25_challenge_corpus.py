"""Build the exploratory EXP25 ManifoldGuard challenge corpus seed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path(__file__).with_name("exp25_challenge_corpus.jsonl")


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

    temporal_role_binding = [
        (
            "valve_pump",
            "Sol repaired the pump before Mira inspected the valve.",
            [
                "Mira repaired the pump before Sol inspected the valve.",
                "Sol repaired the pump before Mira inspected the valve.",
            ],
            [False, True],
        ),
        (
            "draft_review",
            "Ana approved draft B after Jo rejected draft A.",
            [
                "Ana rejected draft A after Jo approved draft B.",
                "Jo rejected draft A before Ana approved draft B.",
            ],
            [False, True],
        ),
        (
            "vial_sequence",
            "Iris sealed vial 2 after Noor labeled vial 1.",
            [
                "Noor sealed vial 2 after Iris labeled vial 1.",
                "Noor labeled vial 1 before Iris sealed vial 2.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in temporal_role_binding:
        cases.append(
            challenge_case(
                f"exp25_temporal_role_binding_{key}_case",
                [reference],
                candidates,
                safe,
                notes="Temporal paraphrases should preserve actor, object, and before/after direction.",
            )
        )

    nested_conditionals = [
        (
            "badge_room",
            "If the badge is valid, then if the room is unlocked, the robot enters.",
            [
                "The robot enters when the badge is valid.",
                "The robot enters when the badge is valid and the room is unlocked.",
            ],
            [False, True],
        ),
        (
            "sensor_alarm",
            "If sensor A is armed, then if sensor B is silent, the alarm stays off.",
            [
                "The alarm stays off when sensor B is silent.",
                "The alarm stays off when sensor A is armed and sensor B is silent.",
            ],
            [False, True],
        ),
        (
            "verified_owner",
            "If the account is verified, then if the requester is an owner, export is allowed.",
            [
                "Verified viewers may export.",
                "Verified owners may export.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in nested_conditionals:
        cases.append(
            challenge_case(
                f"exp25_nested_conditionals_{key}_case",
                [reference],
                candidates,
                safe,
                notes="Nested conditions should not collapse into a single antecedent or looser role.",
            )
        )

    quantifier_thresholds = [
        (
            "reviewer_release",
            "At least two reviewers must approve before release.",
            [
                "One reviewer approval is enough for release.",
                "Release requires approval from two or more reviewers.",
            ],
            [False, True],
        ),
        (
            "failed_checks",
            "No more than one failed check is allowed.",
            [
                "Two failed checks are allowed.",
                "At most one failed check is allowed.",
            ],
            [False, True],
        ),
        (
            "signature_count",
            "Exactly three signatures are required.",
            [
                "Two signatures are required.",
                "Three signatures are required.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in quantifier_thresholds:
        cases.append(
            challenge_case(
                f"exp25_quantifier_thresholds_{key}_case",
                [reference],
                candidates,
                safe,
                notes="Quantifier and threshold paraphrases should preserve minimum, maximum, and exact counts.",
            )
        )

    dimension_binding = [
        (
            "container_weight_volume",
            "The container weighs 3 kg and holds 2 liters.",
            [
                "The container weighs 2 kg and holds 3 liters.",
                "The container weighs 3 kg and holds 2 liters.",
            ],
            [False, True],
        ),
        (
            "drone_range_payload",
            "The drone flies 12 km and carries 4 kg.",
            [
                "The drone flies 4 km and carries 12 kg.",
                "The drone flies 12 km and carries 4 kg.",
            ],
            [False, True],
        ),
        (
            "battery_power_duration",
            "The battery charges at 20 watts and lasts 5 hours.",
            [
                "The battery charges at 5 watts and lasts 20 hours.",
                "The battery charges at 20 watts and lasts 5 hours.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in dimension_binding:
        cases.append(
            challenge_case(
                f"exp25_dimension_binding_{key}_case",
                [reference],
                candidates,
                safe,
                notes="Compact numeric summaries should keep values bound to the right dimension and attribute.",
            )
        )

    scoped_exceptions = [
        (
            "export_formats",
            "The exporter supports CSV except encrypted CSV; JSON is supported.",
            [
                "Encrypted CSV is supported.",
                "JSON is supported, but encrypted CSV is not.",
            ],
            [False, True],
        ),
        (
            "staff_access",
            "All staff may enter except visitors and contractors; auditors may enter with escort.",
            [
                "Visitors may enter with escort.",
                "Visitors and contractors may not enter, and auditors may enter with escort.",
            ],
            [False, True],
        ),
        (
            "medicine_approval",
            "The medicine is approved for adults except pregnant adults; adolescents are not approved.",
            [
                "Pregnant adults are approved.",
                "Adults are approved except pregnant adults, and adolescents are not approved.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in scoped_exceptions:
        cases.append(
            challenge_case(
                f"exp25_scoped_exceptions_{key}_case",
                [reference],
                candidates,
                safe,
                notes="Exception scopes should stay attached to the right allowed class and denied class.",
            )
        )

    all_bad_token_reuse = [
        (
            "route_docks",
            "Route A goes to dock 4; Route B goes to dock 7.",
            [
                "Route A goes to dock 7 and Route B goes to dock 4.",
                "Dock 4 goes to Route B.",
            ],
        ),
        (
            "service_deploy",
            "Only Team Blue may deploy service X; Team Red may monitor it.",
            [
                "Team Red may deploy service X.",
                "Service X may deploy Team Blue.",
            ],
        ),
        (
            "freezer_limits",
            "Freezer A must stay below -10 C; Freezer B must stay above 2 C.",
            [
                "Freezer A must stay above 2 C and Freezer B below -10 C.",
                "Freezer B must stay below -10 C.",
            ],
        ),
    ]
    for key, reference, candidates in all_bad_token_reuse:
        cases.append(
            challenge_case(
                f"exp25_all_bad_token_reuse_{key}_case",
                [reference],
                candidates,
                [False] * len(candidates),
                notes="Every candidate reuses reference-like tokens but should still be blocked.",
            )
        )

    return cases


def main() -> None:
    cases = build_cases()
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        for case in cases:
            handle.write(json.dumps(case, sort_keys=True) + "\n")
    print(f"Wrote {len(cases)} cases to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
