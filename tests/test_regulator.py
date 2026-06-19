import builtins

import numpy as np
import pytest

from mbt_ai_tools import evaluate_candidate, extract_relations, regulate_candidates


def test_mixed_candidate_pool_emits_supported_candidate_without_embeddings():
    references = [
        "The capital of France is Paris.",
        "Paris is the capital city of France.",
    ]

    result = regulate_candidates(
        [
            "The capital of France is London.",
            "The capital of France is Paris.",
        ],
        references,
        use_embeddings=False,
    )

    assert result.action == "emit"
    assert result.emitted_text == "The capital of France is Paris."
    assert result.evaluations[0].safe_to_emit is False
    assert "known_participant_unsupported_relation_clamp" in result.evaluations[0].clamp_summary


def test_all_bad_candidate_pool_blocks_without_embeddings():
    references = ["The capital of France is Paris."]

    result = regulate_candidates(
        [
            "The capital of France is London.",
            "The capital of France is Lyon.",
            "The capital of France is Berlin.",
        ],
        references,
        use_embeddings=False,
    )

    assert result.action == "block"
    assert result.emitted_text is None


def test_relation_direction_and_shared_subject_coordination():
    references = [
        "Photosynthesis releases oxygen.",
        "Photosynthesis stores light energy.",
    ]

    assert ("photosynthesis", "release", "oxygen") in extract_relations(
        "Photosynthesis releases oxygen and stores light energy."
    )
    valid = evaluate_candidate(
        "Photosynthesis releases oxygen and stores light energy.",
        references,
        use_embeddings=False,
    )
    invalid = evaluate_candidate(
        "Photosynthesis converts oxygen into carbon dioxide and water.",
        references,
        use_embeddings=False,
    )

    assert valid.safe_to_emit is True
    assert invalid.safe_to_emit is False
    assert "known_participant_unsupported_relation_clamp" in invalid.clamp_summary


def test_negated_contraction_is_blocked_without_explicit_token_overlap():
    evaluation = evaluate_candidate(
        "Water isn't liquid at room temperature.",
        ["Water is liquid at room temperature."],
        use_embeddings=False,
    )

    assert evaluation.safe_to_emit is False
    assert "negated_positive_support_clamp" in evaluation.clamp_summary


def test_negated_auxiliary_verb_is_blocked():
    evaluation = evaluate_candidate(
        "The Sun does not orbit the Earth.",
        ["The Sun orbits the Earth."],
        use_embeddings=False,
    )

    assert evaluation.safe_to_emit is False
    assert "negated_positive_support_clamp" in evaluation.clamp_summary


def test_negated_contraction_without_space_is_normalized():
    evaluation = evaluate_candidate(
        "The Sun doesn't orbit the Earth.",
        ["The Sun orbits the Earth."],
        use_embeddings=False,
    )

    assert evaluation.safe_to_emit is False
    assert "negated_positive_support_clamp" in evaluation.clamp_summary


def test_negation_on_unrelated_clause_should_not_block_when_relation_not_supported():
    evaluation = evaluate_candidate(
        "Water is a liquid at room temperature and this is not the.",
        ["Water is liquid at room temperature."],
        use_embeddings=False,
    )

    assert "negated_positive_support_clamp" not in evaluation.clamp_summary
    assert evaluation.safe_to_emit is True


def test_negated_future_modal_is_blocked():
    evaluation = evaluate_candidate(
        "The Sun will not orbit the Earth.",
        ["The Sun orbits the Earth."],
        use_embeddings=False,
    )

    assert evaluation.safe_to_emit is False
    assert "negated_positive_support_clamp" in evaluation.clamp_summary


def test_negated_has_no_is_blocked():
    evaluation = evaluate_candidate(
        "Earth has no atmosphere.",
        ["Earth has an atmosphere."],
        use_embeddings=False,
    )

    assert evaluation.safe_to_emit is False
    assert "negated_positive_support_clamp" in evaluation.clamp_summary


def test_missing_sentence_transformers_dependency_is_communicated_in_regulator(monkeypatch):
    original_import = builtins.__import__

    def import_without_sentence_transformers(
        name, globals=None, locals=None, fromlist=(), level=0
    ):
        if name == "sentence_transformers":
            raise ModuleNotFoundError(
                "No module named 'sentence_transformers'", name="sentence_transformers"
            )
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", import_without_sentence_transformers)
    from mbt_ai_tools.mbt.embeddings import load_embedder

    load_embedder.cache_clear()

    with pytest.raises(ModuleNotFoundError, match="sentence-transformers is required"):
        evaluate_candidate("Water is liquid.", ["Water is liquid."])


def test_negated_positive_support_clamp():
    evaluation = evaluate_candidate(
        "Water is not liquid at room temperature.",
        ["Water is liquid at room temperature."],
        use_embeddings=False,
    )

    assert evaluation.safe_to_emit is False
    assert "negated_positive_support_clamp" in evaluation.clamp_summary


def test_supported_reference_negation_blocks_positive_counterclaim():
    result = regulate_candidates(
        [
            "The dataset contains city names and phone numbers.",
            "The dataset contains city names but no phone numbers.",
        ],
        ["The dataset contains city names but does not contain phone numbers."],
        use_embeddings=False,
    )

    assert result.action == "emit"
    assert result.emitted_text == "The dataset contains city names but no phone numbers."
    assert result.evaluations[0].safe_to_emit is False
    assert "negated_reference_relation_clamp" in result.evaluations[0].clamp_summary
    assert result.evaluations[1].safe_to_emit is True
    assert "negated_positive_support_clamp" not in result.evaluations[1].clamp_summary


def test_supported_reference_negation_keeps_exact_negative_reference_safe():
    evaluation = evaluate_candidate(
        "Mars has two moons and does not have a dense ring system.",
        ["Mars has two moons and does not have a dense ring system."],
        use_embeddings=False,
    )

    assert evaluation.safe_to_emit is True
    assert "exact_reference_member" in evaluation.clamp_summary
    assert "negated_positive_support_clamp" not in evaluation.clamp_summary
    assert "negated_reference_relation_clamp" not in evaluation.clamp_summary


def test_exclusion_supports_equivalent_negative_candidate():
    result = regulate_candidates(
        [
            "The trial included adults and children.",
            "The trial included adults and did not include children.",
        ],
        ["The trial included adults and excluded children."],
        use_embeddings=False,
    )

    assert result.action == "emit"
    assert result.emitted_text == "The trial included adults and did not include children."
    assert result.evaluations[0].safe_to_emit is False
    assert "negated_reference_relation_clamp" in result.evaluations[0].clamp_summary
    assert result.evaluations[1].safe_to_emit is True


def test_temporal_year_value_swap_is_blocked():
    result = regulate_candidates(
        [
            "In 2020, rainfall was 45 mm and in 2021 it was 30 mm.",
            "Rainfall was 30 mm in 2020 and 45 mm in 2021.",
        ],
        ["In 2020, rainfall was 30 mm. In 2021, rainfall was 45 mm."],
        use_embeddings=False,
    )

    assert result.action == "emit"
    assert result.emitted_text == "Rainfall was 30 mm in 2020 and 45 mm in 2021."
    assert result.evaluations[0].safe_to_emit is False
    assert "known_participant_unsupported_relation_clamp" in result.evaluations[0].clamp_summary
    assert result.evaluations[1].safe_to_emit is True


def test_temporal_version_binding_swap_is_blocked():
    result = regulate_candidates(
        [
            "Version 1.2 added import support and version 1.3 added export support.",
            "Version 1.2 added export support and version 1.3 added import support.",
        ],
        ["Version 1.2 added export support. Version 1.3 added import support."],
        use_embeddings=False,
    )

    assert result.action == "emit"
    assert result.emitted_text == (
        "Version 1.2 added export support and version 1.3 added import support."
    )
    assert result.evaluations[0].safe_to_emit is False
    assert result.evaluations[1].safe_to_emit is True


def test_temporal_start_end_date_swap_is_blocked():
    result = regulate_candidates(
        [
            "The lease starts on August 31 and ends on March 1.",
            "The lease starts on March 1 and ends on August 31.",
        ],
        ["The lease starts on March 1 and ends on August 31."],
        use_embeddings=False,
    )

    assert result.action == "emit"
    assert result.emitted_text == "The lease starts on March 1 and ends on August 31."
    assert result.evaluations[0].safe_to_emit is False
    assert result.evaluations[1].safe_to_emit is True


def test_relation_composition_shared_subject_chain_is_blocked():
    references = [
        "Photosynthesis uses carbon dioxide.",
        "Photosynthesis releases oxygen.",
        "Photosynthesis stores chemical energy.",
    ]

    assert ("photosynthesis", "use", "carbon dioxide") in extract_relations(
        "Photosynthesis uses carbon dioxide, releases oxygen, and stores chemical energy."
    )
    assert ("photosynthesis", "release", "oxygen") in extract_relations(
        "Photosynthesis uses carbon dioxide, releases oxygen, and stores chemical energy."
    )
    result = regulate_candidates(
        [
            "Photosynthesis releases carbon dioxide and uses oxygen.",
            "Photosynthesis uses carbon dioxide, releases oxygen, and stores chemical energy.",
        ],
        references,
        use_embeddings=False,
    )

    assert result.action == "emit"
    assert result.emitted_text == (
        "Photosynthesis uses carbon dioxide, releases oxygen, and stores chemical energy."
    )
    assert result.evaluations[0].safe_to_emit is False
    assert "known_participant_unsupported_relation_clamp" in result.evaluations[0].clamp_summary
    assert result.evaluations[1].safe_to_emit is True


def test_relation_composition_cross_subject_verb_swap_is_blocked():
    result = regulate_candidates(
        [
            "Libraries preserve records and archives lend books.",
            "Libraries lend books and archives preserve records.",
        ],
        [
            "Libraries lend books.",
            "Archives preserve records.",
        ],
        use_embeddings=False,
    )

    assert result.action == "emit"
    assert result.emitted_text == "Libraries lend books and archives preserve records."
    assert result.evaluations[0].safe_to_emit is False
    assert "known_participant_unsupported_relation_clamp" in result.evaluations[0].clamp_summary
    assert result.evaluations[1].safe_to_emit is True


def test_relation_composition_transform_swap_is_blocked():
    result = regulate_candidates(
        [
            "Evaporation turns vapor into liquid water and condensation turns liquid water into vapor.",
            "Evaporation turns liquid water into vapor and condensation turns vapor into liquid water.",
        ],
        [
            "Evaporation turns liquid water into vapor.",
            "Condensation turns vapor into liquid water.",
        ],
        use_embeddings=False,
    )

    assert result.action == "emit"
    assert result.emitted_text == (
        "Evaporation turns liquid water into vapor and condensation turns vapor into liquid water."
    )
    assert result.evaluations[0].safe_to_emit is False
    assert "known_participant_unsupported_relation_clamp" in result.evaluations[0].clamp_summary
    assert result.evaluations[1].safe_to_emit is True


@pytest.mark.parametrize(
    "reference,candidate",
    [
        ("Water is liquid at room temperature.", "Water is not liquid at room temperature."),
        ("Water is liquid at room temperature.", "Water isn't liquid at room temperature."),
        ("The Sun orbits the Earth.", "The Sun does not orbit the Earth."),
        ("The Sun orbits the Earth.", "The Sun doesn't orbit the Earth."),
        ("The Sun orbits the Earth.", "The Sun will not orbit the Earth."),
        ("Earth has an atmosphere.", "Earth has no atmosphere."),
        ("Plants use sunlight.", "Plants do not use sunlight."),
        ("Plants use sunlight.", "Plants won't use sunlight."),
        ("DNA contains genes.", "DNA cannot contain genes."),
        ("Mammals need oxygen.", "Mammals shouldn't need oxygen."),
    ],
)
def test_negations_without_embeddings_remain_blocked(reference, candidate):
    evaluation = evaluate_candidate(
        candidate,
        [reference],
        use_embeddings=False,
    )

    assert evaluation.safe_to_emit is False
    assert "negated_positive_support_clamp" in evaluation.clamp_summary


def test_multi_word_relation_direction_swap_is_blocked():
    evaluation = evaluate_candidate(
        "Sunlight uses solar panels.",
        ["Solar panels use sunlight."],
        use_embeddings=False,
    )

    assert evaluation.safe_to_emit is False
    assert "known_participant_unsupported_relation_clamp" in evaluation.clamp_summary


@pytest.mark.parametrize(
    "reference,candidate",
    [
        ("The model output is a candidate result.", "The model output is the final truth."),
        (
            "The method has preliminary support.",
            "The method is complete and experimentally verified.",
        ),
        ("The answer is a candidate result.", "The answer is automatically the final answer."),
    ],
)
def test_overclaim_boundaries_block_without_embeddings(reference, candidate):
    evaluation = evaluate_candidate(
        candidate,
        [reference],
        use_embeddings=False,
    )

    assert evaluation.safe_to_emit is False
    assert "overclaim_flag" in evaluation.clamp_summary


def test_supported_capital_paraphrase_reference_no_false_relation_clamp():
    evaluation = evaluate_candidate(
        "Paris is the capital city of France.",
        ["The capital of France is Paris."],
        use_embeddings=False,
    )

    assert evaluation.safe_to_emit is True
    assert "known_participant_unsupported_relation_clamp" not in evaluation.clamp_summary


def test_regulate_candidates_with_embedded_manifold_smoke(monkeypatch):
    def fake_embed_texts(texts, *args, **kwargs):
        outputs = []
        for text in texts:
            if text == "The capital of France is Paris.":
                outputs.append(np.array([0.0, 0.0, 0.0]))
            else:
                outputs.append(np.array([4.0, 0.0, 0.0]))
        return np.asarray(outputs)

    monkeypatch.setattr("mbt_ai_tools.mbt.regulator.embed_texts", fake_embed_texts)

    result = regulate_candidates(
        ["The capital of France is Paris.", "The capital of France is London."],
        ["The capital of France is Paris."],
    )

    assert result.action == "emit"
    assert result.emitted_text == "The capital of France is Paris."


def test_multi_word_capital_relations_are_not_truncated():
    assert ("mexico", "capital", "mexico city") in extract_relations(
        "The capital of Mexico is Mexico City."
    )
    assert ("argentina", "capital", "buenos aires") in extract_relations(
        "Buenos Aires is the capital city of Argentina."
    )
