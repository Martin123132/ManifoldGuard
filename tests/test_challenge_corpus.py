import json
from pathlib import Path


CORPUS_PATH = Path(__file__).resolve().parents[1] / "examples" / "challenge_corpus.jsonl"


def _load_cases():
    with CORPUS_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def test_challenge_corpus_structure_is_valid():
    cases = list(_load_cases())
    case_ids = [case["id"] for case in cases]
    required_prefixes = {
        "challenge_supported_negation",
        "challenge_negation_scope",
        "challenge_temporal_scope",
        "challenge_relation_composition",
        "challenge_qualifier_overclaim",
        "challenge_all_bad_near_miss",
    }

    assert len(cases) >= 30
    assert len(case_ids) == len(set(case_ids))
    for prefix in required_prefixes:
        assert any(case_id.startswith(f"{prefix}_") for case_id in case_ids)

    for case in cases:
        assert case["id"].startswith("challenge_")
        assert case["expected_action"] in {"emit", "block"}
        assert isinstance(case["challenge_notes"], str)
        assert case["challenge_notes"]
        assert isinstance(case["references"], list)
        assert all(isinstance(reference, str) for reference in case["references"])
        assert isinstance(case["candidates"], list)
        assert all(isinstance(candidate, str) for candidate in case["candidates"])
        assert len(case["candidates"]) == len(case["expected_candidate_safe"])
        assert all(isinstance(value, bool) for value in case["expected_candidate_safe"])

        safe_candidates = [
            candidate
            for candidate, safe in zip(
                case["candidates"],
                case["expected_candidate_safe"],
            )
            if safe
        ]
        if case["expected_action"] == "emit":
            assert safe_candidates
            assert case["expected_emitted_text"] == safe_candidates[0]
        else:
            assert not safe_candidates
            assert case["expected_emitted_text"] is None
