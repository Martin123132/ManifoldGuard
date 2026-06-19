from __future__ import annotations

import importlib.util
import json
from pathlib import Path


PASSING_CORPUS = """\
{"id":"france-capital","references":["The capital of France is Paris."],"candidates":["The capital of France is London.","The capital of France is Paris."],"expected_action":"emit","expected_emitted_text":"The capital of France is Paris.","expected_candidate_safe":[false,true]}
{"id":"unsupported-negation","reference":"Water is liquid at room temperature.","candidate":"Water is not liquid at room temperature.","expected_action":"block","expected_candidate_safe":[false]}
"""


def load_evaluate_regulator_module():
    module_path = (
        Path(__file__).resolve().parent.parent / "scripts" / "evaluate_regulator.py"
    )
    spec = importlib.util.spec_from_file_location("evaluate_regulator", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_evaluate_regulator_passes_expected_corpus(tmp_path: Path):
    evaluate_regulator = load_evaluate_regulator_module()
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(PASSING_CORPUS, encoding="utf-8")

    report = evaluate_regulator.evaluate_corpus(corpus)

    assert report["status"] == "passed"
    assert report["summary"]["total_cases"] == 2
    assert report["summary"]["passed_cases"] == 2
    assert report["summary"]["failed_cases"] == 0
    assert report["summary"]["actual_emit"] == 1
    assert report["summary"]["actual_block"] == 1
    assert report["summary"]["families"]["france-capital"]["passed_cases"] == 1
    assert report["summary"]["families"]["unsupported-negation"]["passed_cases"] == 1
    assert report["cases"][0]["candidate_diagnostics"][0]["safe_to_emit"] is False
    assert "protected_entity" in report["cases"][0]["candidate_diagnostics"][0]["clamp_summary"]
    assert report["cases"][1]["candidate_diagnostics"][0]["safe_to_emit"] is False
    assert "negated_positive_support_clamp" in report["cases"][1]["candidate_diagnostics"][0]["clamp_summary"]
    assert "Failures:\n- none" in evaluate_regulator.format_text(report)


def test_evaluate_regulator_groups_underscore_case_families():
    evaluate_regulator = load_evaluate_regulator_module()

    assert evaluate_regulator.case_family("capital_entity_swap_france") == "capital_entity_swap"
    assert evaluate_regulator.case_family("numeric_drift_mars_2025") == "numeric_drift"
    assert evaluate_regulator.case_family("unsupported_negation_water") == "unsupported_negation"
    assert (
        evaluate_regulator.case_family("challenge_supported_negation_trial_children")
        == "challenge_supported_negation"
    )
    assert (
        evaluate_regulator.case_family("challenge_all_bad_near_miss_capitals_close")
        == "challenge_all_bad_near_miss"
    )
    assert (
        evaluate_regulator.case_family("challenge_relation_composition_library_archive")
        == "challenge_relation_composition"
    )
    assert evaluate_regulator.case_family("short_case") == "short_case"


def test_evaluate_regulator_reports_mismatches(tmp_path: Path):
    evaluate_regulator = load_evaluate_regulator_module()
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        PASSING_CORPUS.replace('"expected_action":"emit"', '"expected_action":"block"', 1),
        encoding="utf-8",
    )

    report = evaluate_regulator.evaluate_corpus(corpus)

    assert report["status"] == "failed"
    assert report["summary"]["failed_cases"] == 1
    assert report["cases"][0]["passed"] is False
    assert "action expected 'block', got 'emit'" in report["cases"][0]["mismatches"]
    assert "clamps: 0=protected_entity" in evaluate_regulator.format_text(report)


def test_evaluate_regulator_filters_by_family(tmp_path: Path):
    evaluate_regulator = load_evaluate_regulator_module()
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(PASSING_CORPUS, encoding="utf-8")

    report = evaluate_regulator.evaluate_corpus(
        corpus,
        families=["unsupported-negation"],
    )

    assert report["status"] == "passed"
    assert report["case_filters"]["families"] == ["unsupported-negation"]
    assert report["case_filters"]["selected_cases"] == 1
    assert report["summary"]["total_cases"] == 1
    assert report["summary"]["actual_block"] == 1
    assert report["cases"][0]["id"] == "unsupported-negation"


def test_evaluate_regulator_filters_by_case_id(tmp_path: Path):
    evaluate_regulator = load_evaluate_regulator_module()
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(PASSING_CORPUS, encoding="utf-8")

    report = evaluate_regulator.evaluate_corpus(
        corpus,
        case_ids=["france-capital"],
    )

    assert report["status"] == "passed"
    assert report["case_filters"]["case_ids"] == ["france-capital"]
    assert report["summary"]["total_cases"] == 1
    assert report["summary"]["actual_emit"] == 1
    assert report["cases"][0]["id"] == "france-capital"


def test_evaluate_regulator_failures_only_reports_only_failing_cases(tmp_path: Path):
    evaluate_regulator = load_evaluate_regulator_module()
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        PASSING_CORPUS.replace('"expected_action":"emit"', '"expected_action":"block"', 1),
        encoding="utf-8",
    )

    report = evaluate_regulator.evaluate_corpus(corpus, failures_only=True)

    assert report["status"] == "failed"
    assert report["summary"]["total_cases"] == 2
    assert report["summary"]["failed_cases"] == 1
    assert report["case_filters"]["failures_only"] is True
    assert report["case_filters"]["reported_cases"] == 1
    assert [case["id"] for case in report["cases"]] == ["france-capital"]


def test_evaluate_regulator_rejects_invalid_candidate_safety(tmp_path: Path):
    evaluate_regulator = load_evaluate_regulator_module()
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(
        '{"id":"bad","reference":"A.","candidate":"A.","expected_candidate_safe":["yes"]}\n',
        encoding="utf-8",
    )

    try:
        evaluate_regulator.evaluate_corpus(corpus)
    except ValueError as exc:
        assert "expected_candidate_safe" in str(exc)
    else:
        raise AssertionError("Expected invalid candidate safety to raise ValueError")


def test_evaluate_regulator_main_writes_json_output(tmp_path: Path, capsys):
    evaluate_regulator = load_evaluate_regulator_module()
    corpus = tmp_path / "corpus.jsonl"
    output = tmp_path / "evaluation.json"
    corpus.write_text(PASSING_CORPUS, encoding="utf-8")

    result = evaluate_regulator.main(
        [
            "--corpus",
            str(corpus),
            "--output",
            str(output),
        ]
    )

    captured = capsys.readouterr()
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert result == 0
    assert saved["status"] == "passed"
    assert saved["summary"]["total_cases"] == 2
    assert "ManifoldGuard Offline Regression Evaluation" in captured.out


def test_evaluate_regulator_main_lists_families(tmp_path: Path, capsys):
    evaluate_regulator = load_evaluate_regulator_module()
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(PASSING_CORPUS, encoding="utf-8")

    result = evaluate_regulator.main(
        [
            "--corpus",
            str(corpus),
            "--list-families",
        ]
    )

    captured = capsys.readouterr()
    assert result == 0
    assert "ManifoldGuard Offline Regression Families" in captured.out
    assert "- france-capital: cases=1 passed=1 failed=0" in captured.out
    assert "- unsupported-negation: cases=1 passed=1 failed=0" in captured.out


def test_package_evaluator_matches_script_interface(tmp_path: Path, capsys):
    from mbt_ai_tools import eval as package_eval

    corpus = tmp_path / "corpus.jsonl"
    output = tmp_path / "package-evaluation.json"
    corpus.write_text(PASSING_CORPUS, encoding="utf-8")

    result = package_eval.main(
        [
            "--corpus",
            str(corpus),
            "--output",
            str(output),
        ]
    )

    captured = capsys.readouterr()
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert result == 0
    assert saved["status"] == "passed"
    assert saved["summary"]["families"]["france-capital"]["passed_cases"] == 1
    assert "Status: passed" in captured.out


def test_package_evaluator_default_corpus_is_bundled():
    from mbt_ai_tools import eval as package_eval

    assert package_eval.DEFAULT_CORPUS.exists()
    assert package_eval.DEFAULT_CORPUS.name == "regression_corpus.jsonl"


def test_mbt_eval_console_script_is_registered():
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"

    assert 'manifold-eval = "mbt_ai_tools.eval:main"' in pyproject.read_text(
        encoding="utf-8"
    )
    assert 'mbt-eval = "mbt_ai_tools.eval:main"' in pyproject.read_text(
        encoding="utf-8"
    )
