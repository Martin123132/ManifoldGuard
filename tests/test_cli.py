import json
import sys

from mbt_ai_tools import regulate_candidates
from mbt_ai_tools.cli import build_regulation_report, main


def test_cli_regulation_json_report_without_embeddings(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "mbt-check",
            "--reference",
            "The capital of France is Paris.",
            "--candidate",
            "The capital of France is London.",
            "--candidate",
            "The capital of France is Paris.",
            "--no-embeddings",
            "--format",
            "json",
        ],
    )

    main()

    report = json.loads(capsys.readouterr().out)
    assert report["action"] == "emit"
    assert report["emitted_text"] == "The capital of France is Paris."
    assert report["emitted_index"] == 1
    assert report["evaluations"][0]["status"] == "blocked"
    assert "known_participant_unsupported_relation_clamp" in report["evaluations"][0]["clamps"]
    assert report["evaluations"][1]["status"] == "safe"


def test_build_regulation_report_can_include_token_shock(monkeypatch):
    calls = []

    def fake_token_shock_map(text, *, max_samples=None, top_k=None, order="token"):
        calls.append((text, max_samples, top_k, order))
        return [("London", 12.5)]

    monkeypatch.setattr("mbt_ai_tools.cli.token_shock_map", fake_token_shock_map)
    result = regulate_candidates(
        [
            "The capital of France is London.",
            "The capital of France is Paris.",
        ],
        ["The capital of France is Paris."],
        use_embeddings=False,
    )

    report = build_regulation_report(
        result,
        include_token_shock=True,
        token_shock_max_samples=4,
        token_shock_top_k=1,
        token_shock_order="score",
    )

    assert calls == [
        ("The capital of France is London.", 4, 1, "score"),
        ("The capital of France is Paris.", 4, 1, "score"),
    ]
    assert report["evaluations"][0]["token_shock"] == [
        {"token": "London", "shock": 12.5}
    ]
