"""Build the exploratory EXP24 ManifoldGuard challenge corpus seed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path(__file__).with_name("exp24_challenge_corpus.jsonl")


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

    multi_antecedent_conditionals = [
        (
            "card_pin_door",
            "If the card is active and the PIN is correct, the door opens.",
            [
                "The door opens when the card is active.",
                "The door opens when the card is active and the PIN is correct.",
            ],
            [False, True],
        ),
        (
            "valve_pressure_pump",
            "If the valve is open and pressure is below 5 bar, the pump starts.",
            [
                "The pump starts when pressure is below 5 bar.",
                "The pump starts when the valve is open and pressure is below 5 bar.",
            ],
            [False, True],
        ),
        (
            "admin_owner_export",
            "If the user is an admin or owner, export is allowed.",
            [
                "Viewers may export the file.",
                "Admins and owners may export the file.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in multi_antecedent_conditionals:
        cases.append(
            challenge_case(
                f"exp24_multi_antecedent_conditionals_{key}",
                [reference],
                candidates,
                safe,
                notes="Multi-condition support should not collapse into single-condition or unrelated-role support.",
            )
        )

    alias_permission = [
        (
            "rao_invoice",
            "Mira Rao, also called Dr. Rao, may approve invoices. Lee may view invoices.",
            [
                "Lee may approve invoices.",
                "Dr. Rao may approve invoices.",
            ],
            [False, True],
        ),
        (
            "maintainer_merge",
            "The maintainer is Alex Chen. Alex Chen can merge releases.",
            [
                "Jordan can merge releases.",
                "The maintainer can merge releases.",
            ],
            [False, True],
        ),
        (
            "backup_restart",
            "Device A is the backup unit. The backup unit may restart the router.",
            [
                "Device B may restart the router.",
                "Device A may restart the router.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in alias_permission:
        cases.append(
            challenge_case(
                f"exp24_alias_permission_{key}",
                [reference],
                candidates,
                safe,
                notes="Alias and role bindings should preserve which actor has each permission.",
            )
        )

    unit_range_paraphrases = [
        (
            "tank_liters",
            "The tank holds at most 2 liters.",
            [
                "The tank holds 2500 milliliters.",
                "The tank holds up to 2000 milliliters.",
            ],
            [False, True],
        ),
        (
            "cable_centimeters",
            "The cable must be shorter than 3 meters.",
            [
                "The cable may be 300 centimeters long.",
                "The cable must be less than 300 centimeters long.",
            ],
            [False, True],
        ),
        (
            "service_window",
            "The service window starts at 09:00 and ends before 17:00.",
            [
                "The service window includes 17:00.",
                "The service window runs from 09:00 until before 17:00.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in unit_range_paraphrases:
        cases.append(
            challenge_case(
                f"exp24_unit_range_paraphrases_{key}",
                [reference],
                candidates,
                safe,
                notes="Unit, endpoint, and inclusive/exclusive bound paraphrases should preserve numeric scope.",
            )
        )

    exception_chains = [
        (
            "employee_entry",
            "All employees may enter except contractors and interns; security may enter after hours.",
            [
                "Contractors may enter.",
                "Contractors and interns may not enter, and security may enter after hours.",
            ],
            [False, True],
        ),
        (
            "image_formats",
            "The importer accepts images except SVG and animated GIFs; it accepts PNG.",
            [
                "The importer accepts SVG files.",
                "The importer accepts PNG files but not SVG or animated GIFs.",
            ],
            [False, True],
        ),
        (
            "clinic_visitors",
            "The clinic treats adults except walk-ins and unregistered visitors.",
            [
                "The clinic treats all adults including walk-ins.",
                "The clinic treats adults except walk-ins and unregistered visitors.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in exception_chains:
        cases.append(
            challenge_case(
                f"exp24_exception_chains_{key}",
                [reference],
                candidates,
                safe,
                notes="Multiple exclusions should stay attached to the same allowed class.",
            )
        )

    compact_binding = [
        (
            "store_revenue",
            "North store revenue was 10 and South store revenue was 20.",
            [
                "North store revenue was 20 and South store revenue was 10.",
                "North store revenue was 10 and South store revenue was 20.",
            ],
            [False, True],
        ),
        (
            "model_hardware",
            "Model A uses CPU and Model B uses GPU.",
            [
                "Model A uses GPU and Model B uses CPU.",
                "Model A uses CPU and Model B uses GPU.",
            ],
            [False, True],
        ),
        (
            "sensor_monitoring",
            "Sensor red monitors heat and sensor blue monitors humidity.",
            [
                "Sensor red monitors humidity and sensor blue monitors heat.",
                "Sensor red monitors heat and sensor blue monitors humidity.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in compact_binding:
        cases.append(
            challenge_case(
                f"exp24_compact_binding_{key}",
                [reference],
                candidates,
                safe,
                notes="Compact summaries should keep values, devices, and attributes bound to the correct participant.",
            )
        )

    all_bad_token_reuse = [
        (
            "ledger_reuse",
            "Only Team Red may edit the ledger; Team Blue may view it.",
            [
                "Team Red may view the ledger and Team Blue may edit it.",
                "The ledger may edit Team Red.",
            ],
        ),
        (
            "switch_reuse",
            "If the switch is off, the motor stops; if the switch is on, the motor runs.",
            [
                "The motor stops when the switch is on.",
                "The motor runs when the switch is off.",
            ],
        ),
        (
            "dose_reuse",
            "The dose must be at least 5 mg and below 10 mg.",
            [
                "A 4 mg dose is allowed.",
                "A 10 mg dose is allowed.",
            ],
        ),
    ]
    for key, reference, candidates in all_bad_token_reuse:
        cases.append(
            challenge_case(
                f"exp24_all_bad_token_reuse_{key}",
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
