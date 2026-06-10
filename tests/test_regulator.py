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
