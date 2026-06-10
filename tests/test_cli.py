import json
import sys

from mbt_ai_tools import regulate_candidates
from mbt_ai_tools.cli import build_regulation_report, format_regulation_text, main


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


def test_cli_regulation_json_report_can_write_output(monkeypatch, capsys, tmp_path):
    output_path = tmp_path / "report.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "mbt-check",
            "--reference",
            "The capital of France is Paris.",
            "--candidate",
            "The capital of France is Paris.",
            "--no-embeddings",
            "--format",
            "json",
            "--output",
            str(output_path),
        ],
    )

    main()

    assert capsys.readouterr().out == ""
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["action"] == "emit"
    assert report["emitted_text"] == "The capital of France is Paris."


def test_cli_batch_jsonl_report(monkeypatch, capsys, tmp_path):
    input_path = tmp_path / "batch.jsonl"
    output_path = tmp_path / "batch-report.jsonl"
    input_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "france-capital",
                        "references": ["The capital of France is Paris."],
                        "candidates": [
                            "The capital of France is London.",
                            "The capital of France is Paris.",
                        ],
                    }
                ),
                json.dumps(
                    {
                        "id": "negation",
                        "reference": "Water is liquid at room temperature.",
                        "candidate": "Water is not liquid at room temperature.",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "mbt-check",
            "--input-jsonl",
            str(input_path),
            "--no-embeddings",
            "--output",
            str(output_path),
        ],
    )

    main()

    assert capsys.readouterr().out == ""
    reports = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
    ]
    assert [report["id"] for report in reports] == ["france-capital", "negation"]
    assert reports[0]["action"] == "emit"
    assert reports[0]["emitted_index"] == 1
    assert reports[1]["action"] == "block"
    assert "negated_positive_support_clamp" in reports[1]["evaluations"][0]["clamps"]


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


def test_format_regulation_text_matches_existing_cli_shape():
    result = regulate_candidates(
        [
            "The capital of France is London.",
            "The capital of France is Paris.",
        ],
        ["The capital of France is Paris."],
        use_embeddings=False,
    )

    output = format_regulation_text(build_regulation_report(result))

    assert output.startswith("EMIT | The capital of France is Paris. | score=0.0000\n")
    assert "[0] blocked | score=" in output
    assert "[1] safe | score=0.0000 | clamps=exact_reference_member" in output
