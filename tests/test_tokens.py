import builtins

import pytest
import numpy as np

from mbt_ai_tools import token_shock_map
from mbt_ai_tools.mbt.embeddings import load_embedder


def test_token_shock_map_top_k_prefers_highest_scores(monkeypatch):
    def fake_embed_texts(texts, *args, **kwargs):
        outputs = []
        for text in texts:
            if text == "alpha beta gamma delta":
                outputs.append(np.array([0.0, 0.0, 0.0]))
            elif text == "beta gamma delta":
                outputs.append(np.array([2.0, 0.0, 0.0]))  # remove alpha
            elif text == "alpha gamma delta":
                outputs.append(np.array([1.0, 0.0, 0.0]))  # remove beta
            elif text == "alpha beta delta":
                outputs.append(np.array([3.0, 0.0, 0.0]))  # remove gamma
            elif text == "alpha beta gamma":
                outputs.append(np.array([4.0, 0.0, 0.0]))  # remove delta
            else:
                raise AssertionError(f"unexpected variant: {text}")
        return np.asarray(outputs)

    monkeypatch.setattr("mbt_ai_tools.mbt.tokens.embed_texts", fake_embed_texts)

    assert token_shock_map("alpha beta gamma delta", top_k=2, order="token") == [
        ("gamma", 9.0),
        ("delta", 16.0),
    ]

    assert token_shock_map("alpha beta gamma delta", top_k=2, order="score") == [
        ("delta", 16.0),
        ("gamma", 9.0),
    ]


def test_token_shock_map_invalid_order_rejected():
    with pytest.raises(ValueError, match="order must be 'token' or 'score'"):
        token_shock_map("alpha beta", order="invalid")


def test_token_shock_map_max_samples_keeps_single_middle_token_for_short_text(monkeypatch):
    def fake_embed_texts(texts, *args, **kwargs):
        outputs = []
        for text in texts:
            if text == "alpha beta gamma":
                outputs.append(np.array([0.0, 0.0, 0.0]))
            elif text == "alpha gamma":
                outputs.append(np.array([2.5, 0.0, 0.0]))
            else:
                raise AssertionError(f"unexpected variant: {text}")
        return np.asarray(outputs)

    monkeypatch.setattr("mbt_ai_tools.mbt.tokens.embed_texts", fake_embed_texts)

    assert token_shock_map("alpha beta gamma", max_samples=1, order="token") == [("beta", 6.25)]


def test_missing_sentence_transformers_dependency_is_communicated(monkeypatch):
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
    load_embedder.cache_clear()

    with pytest.raises(ModuleNotFoundError, match="sentence-transformers is required"):
        load_embedder()
