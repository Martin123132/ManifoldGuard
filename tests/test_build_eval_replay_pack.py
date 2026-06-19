from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def load_replay_module():
    module_path = (
        Path(__file__).resolve().parent.parent / "scripts" / "build_eval_replay_pack.py"
    )
    spec = importlib.util.spec_from_file_location("build_eval_replay_pack", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_corpus(path: Path) -> None:
    rows = [
        {
            "id": "france-capital",
            "references": ["The capital of France is Paris."],
            "candidates": [
                "The capital of France is London.",
                "The capital of France is Paris.",
            ],
            "expected_action": "emit",
            "expected_emitted_text": "The capital of France is Paris.",
            "expected_candidate_safe": [False, True],
        },
        {
            "id": "water-negation",
            "reference": "Water is liquid at room temperature.",
            "candidate": "Water is not liquid at room temperature.",
            "expected_action": "block",
            "expected_candidate_safe": [False],
        },
    ]
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def evaluation_report() -> dict:
    return {
        "schema_version": "1.0",
        "status": "failed",
        "cases": [
            {
                "id": "france-capital",
                "family": "france-capital",
                "passed": True,
                "expected_action": "emit",
                "actual_action": "emit",
                "expected_emitted_text": "The capital of France is Paris.",
                "actual_emitted_text": "The capital of France is Paris.",
                "expected_candidate_safe": [False, True],
                "actual_candidate_safe": [False, True],
                "mismatches": [],
                "candidate_diagnostics": [
                    {
                        "index": 0,
                        "clamp_summary": ["protected_entity"],
                        "literal_score": 1.0,
                    }
                ],
            },
            {
                "id": "water-negation",
                "family": "unsupported-negation",
                "passed": False,
                "expected_action": "block",
                "actual_action": "emit",
                "expected_candidate_safe": [False],
                "actual_candidate_safe": [True],
                "mismatches": ["action expected 'block', got 'emit'"],
                "candidate_diagnostics": [
                    {
                        "index": 0,
                        "clamp_summary": [],
                        "literal_score": 0.0,
                    }
                ],
            },
        ],
    }


def test_replay_pack_defaults_to_failed_cases(tmp_path: Path):
    replay = load_replay_module()
    corpus = tmp_path / "corpus.jsonl"
    evaluation = tmp_path / "evaluation.json"
    write_corpus(corpus)
    write_json(evaluation, evaluation_report())

    pack = replay.build_replay_pack(corpus_path=corpus, evaluation_path=evaluation)

    assert pack["summary"]["selected_cases"] == 1
    assert pack["cases"][0]["id"] == "water-negation"
    assert pack["cases"][0]["references"] == [
        "Water is liquid at room temperature."
    ]
    assert pack["cases"][0]["candidates"] == [
        "Water is not liquid at room temperature."
    ]


def test_replay_pack_exact_case_id_includes_passed_case(tmp_path: Path):
    replay = load_replay_module()
    corpus = tmp_path / "corpus.jsonl"
    evaluation = tmp_path / "evaluation.json"
    write_corpus(corpus)
    write_json(evaluation, evaluation_report())

    pack = replay.build_replay_pack(
        corpus_path=corpus,
        evaluation_path=evaluation,
        case_ids=["france-capital"],
    )

    assert pack["summary"]["selected_cases"] == 1
    assert pack["cases"][0]["id"] == "france-capital"
    assert pack["cases"][0]["passed"] is True


def test_replay_pack_main_writes_markdown(tmp_path: Path, capsys):
    replay = load_replay_module()
    corpus = tmp_path / "corpus.jsonl"
    evaluation = tmp_path / "evaluation.json"
    output = tmp_path / "replay.md"
    write_corpus(corpus)
    write_json(evaluation, evaluation_report())

    result = replay.main(
        [
            "--corpus",
            str(corpus),
            "--evaluation",
            str(evaluation),
            "--output",
            str(output),
        ]
    )

    captured = capsys.readouterr()
    rendered = output.read_text(encoding="utf-8")
    assert result == 0
    assert captured.out == ""
    assert "# ManifoldGuard Evaluation Replay Pack" in rendered
    assert "## water-negation" in rendered
    assert "action expected 'block', got 'emit'" in rendered
