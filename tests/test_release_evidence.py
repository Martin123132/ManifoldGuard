from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_release_evidence_module():
    module_path = (
        Path(__file__).resolve().parent.parent / "scripts" / "release_evidence.py"
    )
    spec = importlib.util.spec_from_file_location("release_evidence", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_release_evidence_dry_run_records_planned_gates(tmp_path: Path):
    release_evidence = load_release_evidence_module()
    gates = [
        {
            "name": "example_gate",
            "description": "Example gate.",
            "command": [sys.executable, "-c", "print('should not run')"],
            "display": "python -c example",
        }
    ]

    report = release_evidence.build_release_evidence(
        run=False,
        gates=gates,
        project_root=tmp_path,
        generated_at="2026-06-12T00:00:00+00:00",
    )

    assert report["schema_version"] == "1.0"
    assert report["mode"] == "dry_run"
    assert report["summary"] == {
        "failed": 0,
        "not_run": 1,
        "passed": 0,
        "status": "dry_run",
        "total": 1,
    }
    assert report["gates"][0]["name"] == "example_gate"
    assert report["gates"][0]["command"] == "python -c example"
    assert report["gates"][0]["status"] == "not_run"
    assert report["gates"][0]["returncode"] is None


def test_release_evidence_run_records_success_and_failure(tmp_path: Path):
    release_evidence = load_release_evidence_module()
    gates = [
        {
            "name": "passing_gate",
            "description": "Passing gate.",
            "command": [sys.executable, "-c", "print('ok')"],
        },
        {
            "name": "failing_gate",
            "description": "Failing gate.",
            "command": [sys.executable, "-c", "import sys; print('bad'); sys.exit(3)"],
        },
    ]

    report = release_evidence.build_release_evidence(
        run=True,
        gates=gates,
        project_root=tmp_path,
        max_output_chars=20,
        generated_at="2026-06-12T00:00:00+00:00",
    )

    assert report["mode"] == "run"
    assert report["summary"]["status"] == "failed"
    assert report["summary"]["passed"] == 1
    assert report["summary"]["failed"] == 1
    assert report["gates"][0]["status"] == "passed"
    assert report["gates"][0]["returncode"] == 0
    assert "ok" in report["gates"][0]["stdout_tail"]
    assert report["gates"][1]["status"] == "failed"
    assert report["gates"][1]["returncode"] == 3


def test_release_evidence_empty_gate_list_is_partial_free(tmp_path: Path):
    release_evidence = load_release_evidence_module()

    report = release_evidence.build_release_evidence(
        run=False,
        gates=[],
        project_root=tmp_path,
        generated_at="2026-06-12T00:00:00+00:00",
    )

    assert report["gates"] == []
    assert report["summary"] == {
        "failed": 0,
        "not_run": 0,
        "passed": 0,
        "status": "dry_run",
        "total": 0,
    }
