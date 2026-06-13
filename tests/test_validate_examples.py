from __future__ import annotations

import importlib.util
from pathlib import Path


BATCH_INPUT = """\
{"id":"france-capital","references":["The capital of France is Paris."],"candidates":["The capital of France is London.","The capital of France is Paris."]}
{"id":"unsupported-negation","reference":"Water is liquid at room temperature.","candidate":"Water is not liquid at room temperature."}
"""


def load_validate_examples_module():
    module_path = (
        Path(__file__).resolve().parent.parent / "scripts" / "validate_examples.py"
    )
    spec = importlib.util.spec_from_file_location("validate_examples", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_validate_examples_passes_for_repo_examples():
    validate_examples = load_validate_examples_module()
    project_root = Path(__file__).resolve().parent.parent

    assert validate_examples.validate_examples(project_root) == []


def test_validate_examples_detects_stale_csv_fixture(tmp_path: Path):
    validate_examples = load_validate_examples_module()
    examples = tmp_path / "examples"
    examples.mkdir()
    (examples / "batch_input.jsonl").write_text(BATCH_INPUT, encoding="utf-8")

    single_report = validate_examples.expected_single_report()
    batch_reports = validate_examples.expected_batch_reports(tmp_path)
    (examples / "single_report_example.json").write_text(
        validate_examples.canonical_json(single_report),
        encoding="utf-8",
    )
    (examples / "batch_report_example.jsonl").write_text(
        "".join(validate_examples.canonical_json(report) for report in batch_reports),
        encoding="utf-8",
    )
    (examples / "csv_audit_report.csv").write_text("stale\n", encoding="utf-8")
    (examples / "cli_json_report.md").write_text(
        validate_examples.canonical_json(single_report, pretty=True),
        encoding="utf-8",
    )
    (examples / "markdown_audit_report.md").write_text(
        validate_examples.format_markdown_audit(batch_reports),
        encoding="utf-8",
    )

    failures = validate_examples.validate_examples(tmp_path)

    assert failures == [
        f"{examples / 'csv_audit_report.csv'} does not match current CSV audit output"
    ]
