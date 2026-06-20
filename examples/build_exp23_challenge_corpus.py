"""Build the exploratory EXP23 ManifoldGuard challenge corpus seed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path(__file__).with_name("exp23_challenge_corpus.jsonl")


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

    range_bounds = [
        (
            "charger_voltage",
            "The charger accepts 5 to 9 volts.",
            [
                "The charger accepts 4 to 9 volts.",
                "The charger accepts 5 to 9 volts.",
            ],
            [False, True],
        ),
        (
            "applicant_age",
            "Applicants must be at least 18 and under 65.",
            [
                "Applicants aged 17 are eligible.",
                "Applicants aged 18 through 64 are eligible.",
            ],
            [False, True],
        ),
        (
            "freezer_temperature",
            "The freezer must stay between -20 and -10 degrees Celsius.",
            [
                "The freezer may stay at -5 degrees Celsius.",
                "The freezer must stay between -20 and -10 degrees Celsius.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in range_bounds:
        cases.append(
            challenge_case(
                f"exp23_range_bounds_{key}",
                [reference],
                candidates,
                safe,
                notes="Numeric bounds should preserve closed, open, and between-range scope.",
            )
        )

    conditional_scope = [
        (
            "alarm_lock",
            "If the alarm is armed, the door lock engages.",
            [
                "The door lock always engages.",
                "The door lock engages when the alarm is armed.",
            ],
            [False, True],
        ),
        (
            "encrypted_backup",
            "Backups are uploaded after encryption succeeds and are not uploaded if encryption fails.",
            [
                "Backups are uploaded even if encryption fails.",
                "Backups are uploaded after encryption succeeds.",
            ],
            [False, True],
        ),
        (
            "member_discount",
            "Members get the discount on weekdays, not weekends.",
            [
                "Members get the discount on weekends.",
                "Members get the discount on weekdays.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in conditional_scope:
        cases.append(
            challenge_case(
                f"exp23_conditional_scope_{key}",
                [reference],
                candidates,
                safe,
                notes="Conditioned support should not be emitted as unconditional or opposite-condition support.",
            )
        )

    nested_exceptions = [
        (
            "lab_access",
            "All staff can enter the lab except interns; supervisors can enter after hours.",
            [
                "Interns can enter the lab.",
                "Interns cannot enter the lab, and supervisors can enter after hours.",
            ],
            [False, True],
        ),
        (
            "animated_gif",
            "The importer accepts images except animated GIFs; it accepts static GIFs.",
            [
                "The importer accepts animated GIFs.",
                "The importer accepts static GIFs but not animated GIFs.",
            ],
            [False, True],
        ),
        (
            "clinic_walkins",
            "The clinic treats adults except emergency walk-ins; children require referral.",
            [
                "The clinic treats all adults including emergency walk-ins.",
                "The clinic treats adults except emergency walk-ins.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in nested_exceptions:
        cases.append(
            challenge_case(
                f"exp23_nested_exception_{key}",
                [reference],
                candidates,
                safe,
                notes="Nested exceptions should preserve the excluded subgroup while retaining supported allowances.",
            )
        )

    ordinal_binding = [
        (
            "race_finish",
            "Runner A finished first. Runner B finished second. Runner C finished third.",
            [
                "Runner B finished first and Runner A finished second.",
                "Runner A finished first and Runner B finished second.",
            ],
            [False, True],
        ),
        (
            "priority_labels",
            "Priority 1 is critical. Priority 2 is warning. Priority 3 is informational.",
            [
                "Priority 2 is critical and Priority 1 is warning.",
                "Priority 1 is critical and Priority 2 is warning.",
            ],
            [False, True],
        ),
        (
            "pipeline_stages",
            "The first stage is intake, the second stage is review, and the third stage is approval.",
            [
                "The first stage is review and the second stage is intake.",
                "The first stage is intake and the second stage is review.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in ordinal_binding:
        cases.append(
            challenge_case(
                f"exp23_ordinal_binding_{key}",
                [reference],
                candidates,
                safe,
                notes="Ordinal labels and ranked slots should remain bound to the correct participant or value.",
            )
        )

    aggregate_binding = [
        (
            "sensor_failures",
            "Three of ten sensors failed.",
            [
                "Seven of ten sensors failed.",
                "Three of ten sensors failed.",
            ],
            [False, True],
        ),
        (
            "reviewer_votes",
            "Two reviewers approved and one reviewer rejected.",
            [
                "One reviewer approved and two reviewers rejected.",
                "Two reviewers approved and one reviewer rejected.",
            ],
            [False, True],
        ),
        (
            "trial_groups",
            "The trial enrolled 40 adults and 10 children.",
            [
                "The trial enrolled 10 adults and 40 children.",
                "The trial enrolled 40 adults and 10 children.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in aggregate_binding:
        cases.append(
            challenge_case(
                f"exp23_aggregate_binding_{key}",
                [reference],
                candidates,
                safe,
                notes="Counts, ratios, and grouped totals should preserve value-to-group binding.",
            )
        )

    all_bad_near_miss = [
        (
            "dose_bounds",
            "The safe dose is between 5 and 10 mg.",
            [
                "A 4 mg dose is safe.",
                "An 11 mg dose is safe.",
            ],
        ),
        (
            "switch_motor",
            "If the switch is off, the motor stops.",
            [
                "The motor stops when the switch is on.",
                "The switch stops when the motor is off.",
            ],
        ),
        (
            "ledger_permissions",
            "Only Team Red may edit the ledger; Team Blue may view it.",
            [
                "Team Blue may edit the ledger.",
                "The ledger may edit Team Red.",
            ],
        ),
    ]
    for key, reference, candidates in all_bad_near_miss:
        cases.append(
            challenge_case(
                f"exp23_all_bad_near_miss_{key}",
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
            handle.write(json.dumps(case, sort_keys=True) + "\n")
    print(f"Wrote {len(cases)} cases to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
