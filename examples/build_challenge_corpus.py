"""Build the exploratory EXP21 ManifoldGuard challenge corpus seed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OUTPUT_PATH = Path(__file__).with_name("challenge_corpus.jsonl")


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
    safe_indexes = [
        index for index, safe in enumerate(expected_candidate_safe) if safe
    ]
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

    supported_negation = [
        (
            "trial_children",
            "The trial included adults and excluded children.",
            [
                "The trial included adults and children.",
                "The trial included adults and did not include children.",
                "Children were excluded from the trial.",
            ],
            [False, True, True],
        ),
        (
            "mars_rings",
            "Mars has two moons and does not have a dense ring system.",
            [
                "Mars has two moons and a dense ring system.",
                "Mars has two moons and does not have a dense ring system.",
                "Mars lacks a dense ring system.",
            ],
            [False, True, True],
        ),
        (
            "dataset_names",
            "The dataset contains city names but does not contain phone numbers.",
            [
                "The dataset contains city names and phone numbers.",
                "The dataset contains city names but no phone numbers.",
                "The dataset omits city names and contains phone numbers.",
            ],
            [False, True, False],
        ),
        (
            "engine_batteries",
            "The prototype uses a fuel cell and does not use lithium batteries.",
            [
                "The prototype uses lithium batteries.",
                "The prototype uses a fuel cell and no lithium batteries.",
                "The prototype does not use a fuel cell.",
            ],
            [False, True, False],
        ),
        (
            "policy_remote",
            "The policy allows remote work but does not allow overseas payroll.",
            [
                "The policy allows remote work and overseas payroll.",
                "The policy allows remote work but not overseas payroll.",
                "The policy blocks remote work.",
            ],
            [False, True, False],
        ),
        (
            "medicine_children",
            "The medicine is approved for adults and is not approved for children.",
            [
                "The medicine is approved for adults and children.",
                "The medicine is approved for adults, not children.",
                "The medicine is not approved for adults.",
            ],
            [False, True, False],
        ),
    ]
    for key, reference, candidates, safe in supported_negation:
        cases.append(
            challenge_case(
                f"challenge_supported_negation_{key}",
                [reference],
                candidates,
                safe,
                notes="Supported negation should be preserved, not treated as drift.",
            )
        )

    negation_scope = [
        (
            "pressure_temperature",
            "The alarm responds to pressure changes, not temperature changes.",
            [
                "The alarm responds to temperature changes, not pressure changes.",
                "The alarm responds to pressure changes and not temperature changes.",
            ],
            [False, True],
        ),
        (
            "north_south_gate",
            "The north gate opens at 08:00; the south gate does not open until 10:00.",
            [
                "The south gate opens at 08:00 and the north gate opens at 10:00.",
                "The north gate opens at 08:00 and the south gate waits until 10:00.",
            ],
            [False, True],
        ),
        (
            "sensor_humidity",
            "Sensor A measures humidity; Sensor B does not measure humidity.",
            [
                "Sensor B measures humidity and Sensor A does not.",
                "Sensor A measures humidity and Sensor B does not.",
            ],
            [False, True],
        ),
        (
            "committee_vote",
            "The committee approved the budget but did not approve the timeline.",
            [
                "The committee approved the timeline but not the budget.",
                "The committee approved the budget but not the timeline.",
            ],
            [False, True],
        ),
        (
            "machine_axis",
            "Axis X moved during calibration; Axis Y did not move.",
            [
                "Axis Y moved during calibration while Axis X did not.",
                "Axis X moved during calibration while Axis Y did not.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in negation_scope:
        cases.append(
            challenge_case(
                f"challenge_negation_scope_{key}",
                [reference],
                candidates,
                safe,
                notes="Negation scope and participant binding must stay aligned.",
            )
        )

    temporal_scope = [
        (
            "rainfall_years",
            "In 2020, rainfall was 30 mm. In 2021, rainfall was 45 mm.",
            [
                "In 2020, rainfall was 45 mm and in 2021 it was 30 mm.",
                "Rainfall was 30 mm in 2020 and 45 mm in 2021.",
            ],
            [False, True],
        ),
        (
            "office_dates",
            "The Berlin office opened in 2018. The Paris office opened in 2020.",
            [
                "The Paris office opened in 2018 and the Berlin office opened in 2020.",
                "The Berlin office opened in 2018 and the Paris office opened in 2020.",
            ],
            [False, True],
        ),
        (
            "version_changes",
            "Version 1.2 added export support. Version 1.3 added import support.",
            [
                "Version 1.2 added import support and version 1.3 added export support.",
                "Version 1.2 added export support and version 1.3 added import support.",
            ],
            [False, True],
        ),
        (
            "shipments_quarters",
            "Q1 shipments were 12 units. Q2 shipments were 18 units.",
            [
                "Q1 shipments were 18 units and Q2 shipments were 12 units.",
                "Q1 shipments were 12 units and Q2 shipments were 18 units.",
            ],
            [False, True],
        ),
        (
            "contract_dates",
            "The lease starts on March 1 and ends on August 31.",
            [
                "The lease starts on August 31 and ends on March 1.",
                "The lease starts on March 1 and ends on August 31.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in temporal_scope:
        cases.append(
            challenge_case(
                f"challenge_temporal_scope_{key}",
                [reference],
                candidates,
                safe,
                notes="Time-bound facts should not swap values across dates or versions.",
            )
        )

    alias_cases = [
        (
            "ibm",
            "International Business Machines, also called IBM, acquired Red Hat.",
            [
                "Intel acquired Red Hat.",
                "IBM acquired Red Hat.",
                "Red Hat acquired IBM.",
            ],
            [False, True, False],
        ),
        (
            "nyc",
            "New York City, abbreviated NYC, is in New York State.",
            [
                "NYC is in California.",
                "NYC is in New York State.",
                "New York State is in NYC.",
            ],
            [False, True, False],
        ),
        (
            "who",
            "The World Health Organization is abbreviated WHO.",
            [
                "The WTO is abbreviated WHO.",
                "WHO abbreviates the World Health Organization.",
                "The World Health Organization is abbreviated WTO.",
            ],
            [False, True, False],
        ),
        (
            "uk",
            "The United Kingdom, or UK, includes England, Scotland, Wales, and Northern Ireland.",
            [
                "The UK includes England, Scotland, Wales, and Ireland.",
                "The UK includes England, Scotland, Wales, and Northern Ireland.",
            ],
            [False, True],
        ),
        (
            "mit",
            "The Massachusetts Institute of Technology is commonly called MIT.",
            [
                "MIT commonly refers to the Massachusetts Institute of Technology.",
                "MIT commonly refers to the Michigan Institute of Technology.",
            ],
            [True, False],
        ),
    ]
    for key, reference, candidates, safe in alias_cases:
        cases.append(
            challenge_case(
                f"challenge_alias_binding_{key}",
                [reference],
                candidates,
                safe,
                notes="Alias equivalence should help safe paraphrases without allowing entity swaps.",
            )
        )

    relation_composition = [
        (
            "photosynthesis",
            [
                "Photosynthesis uses carbon dioxide.",
                "Photosynthesis releases oxygen.",
                "Photosynthesis stores chemical energy.",
            ],
            [
                "Photosynthesis releases carbon dioxide and uses oxygen.",
                "Photosynthesis uses carbon dioxide, releases oxygen, and stores chemical energy.",
            ],
            [False, True],
        ),
        (
            "battery",
            [
                "A battery stores chemical energy.",
                "A circuit uses electrical energy.",
            ],
            [
                "A battery uses electrical energy and a circuit stores chemical energy.",
                "A battery stores chemical energy and a circuit uses electrical energy.",
            ],
            [False, True],
        ),
        (
            "library_archive",
            [
                "Libraries lend books.",
                "Archives preserve records.",
            ],
            [
                "Libraries preserve records and archives lend books.",
                "Libraries lend books and archives preserve records.",
            ],
            [False, True],
        ),
        (
            "roots_leaves",
            [
                "Roots absorb water.",
                "Leaves exchange gases.",
            ],
            [
                "Roots exchange gases and leaves absorb water.",
                "Roots absorb water and leaves exchange gases.",
            ],
            [False, True],
        ),
        (
            "servers_clients",
            [
                "Servers provide data.",
                "Clients request data.",
            ],
            [
                "Clients provide data and servers request data.",
                "Servers provide data and clients request data.",
            ],
            [False, True],
        ),
        (
            "evaporation_condensation",
            [
                "Evaporation turns liquid water into vapor.",
                "Condensation turns vapor into liquid water.",
            ],
            [
                "Evaporation turns vapor into liquid water and condensation turns liquid water into vapor.",
                "Evaporation turns liquid water into vapor and condensation turns vapor into liquid water.",
            ],
            [False, True],
        ),
    ]
    for key, references, candidates, safe in relation_composition:
        cases.append(
            challenge_case(
                f"challenge_relation_composition_{key}",
                references,
                candidates,
                safe,
                notes="Multiple supported relations must not be recombined with swapped roles.",
            )
        )

    qualifier_cases = [
        (
            "sea_level",
            "Water boils at 100 degrees Celsius at sea level.",
            [
                "Water always boils at 100 degrees Celsius.",
                "At sea level, water boils at 100 degrees Celsius.",
            ],
            [False, True],
        ),
        (
            "pilot_scope",
            "The pilot study found reduced latency in one internal test.",
            [
                "The pilot study proved latency is reduced in all deployments.",
                "The pilot study found reduced latency in one internal test.",
            ],
            [False, True],
        ),
        (
            "sample_scope",
            "The survey included 40 students from one school.",
            [
                "The survey represents all students nationally.",
                "The survey included 40 students from one school.",
            ],
            [False, True],
        ),
        (
            "model_scope",
            "The model matched the validation set used in the report.",
            [
                "The model is guaranteed to match all future data.",
                "The model matched the validation set used in the report.",
            ],
            [False, True],
        ),
        (
            "prototype_scope",
            "The prototype worked during a controlled indoor test.",
            [
                "The prototype is fully proven for all outdoor conditions.",
                "The prototype worked during a controlled indoor test.",
            ],
            [False, True],
        ),
        (
            "clinical_scope",
            "The trial observed improvement in a small adult cohort.",
            [
                "The treatment is proven safe and effective for every patient.",
                "The trial observed improvement in a small adult cohort.",
            ],
            [False, True],
        ),
    ]
    for key, reference, candidates, safe in qualifier_cases:
        cases.append(
            challenge_case(
                f"challenge_qualifier_overclaim_{key}",
                [reference],
                candidates,
                safe,
                notes="Cautious scope should be preserved; universal overclaims should block.",
            )
        )

    all_bad_cases = [
        (
            "capitals_close",
            "The capital of Australia is Canberra.",
            [
                "The capital of Australia is Sydney.",
                "Sydney is the capital city of Australia.",
                "Canberra is the capital city of New Zealand.",
            ],
        ),
        (
            "numbers_close",
            "The sample weighs 5 kg and was stored for 12 hours.",
            [
                "The sample weighs 6 kg and was stored for 12 hours.",
                "The sample weighs 5 kg and was stored for 10 hours.",
                "The sample weighs 6 kg and was stored for 10 hours.",
            ],
        ),
        (
            "relations_close",
            "The Moon orbits Earth and Earth orbits the Sun.",
            [
                "Earth orbits the Moon and the Sun orbits Earth.",
                "The Moon orbits the Sun and Earth orbits the Moon.",
            ],
        ),
        (
            "negation_close",
            "The archive contains records and does not contain passwords.",
            [
                "The archive contains passwords and does not contain records.",
                "The archive does not contain records.",
            ],
        ),
    ]
    for key, reference, candidates in all_bad_cases:
        cases.append(
            challenge_case(
                f"challenge_all_bad_near_miss_{key}",
                [reference],
                candidates,
                [False] * len(candidates),
                notes="All candidates are close to the reference but should still be blocked.",
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
