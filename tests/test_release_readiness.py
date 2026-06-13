from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def load_release_readiness_module():
    module_path = (
        Path(__file__).resolve().parent.parent / "scripts" / "release_readiness.py"
    )
    spec = importlib.util.spec_from_file_location("release_readiness", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def write_release_files(tmp_path: Path, *, evidence_status: str = "passed") -> Path:
    manifest = {
        "project": {
            "name": "mbt-ai-tools",
            "public_name": "MBT-5 Geometry-Only Output Regulator",
            "package_version": "0.1.0",
            "repository": "https://example.test/repo",
        },
        "install_modes": [
            {
                "name": "core",
                "command": "python -m pip install -e . --no-deps",
            },
            {
                "name": "embeddings",
                "command": "python -m pip install -e .[embeddings]",
            },
        ],
        "support_boundaries": [
            "MBT-5 regulates candidate outputs against supplied reference structure.",
            "MBT-5 is not a universal fact checker.",
        ],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "mbt-ai-tools"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## 0.1.0 Release Candidate - 2026-06-12\n",
        encoding="utf-8",
    )
    evidence = {
        "summary": {
            "status": evidence_status,
            "total": 1,
            "passed": 1 if evidence_status == "passed" else 0,
            "failed": 0 if evidence_status == "passed" else 1,
            "not_run": 0,
        },
        "gates": [
            {
                "name": "pytest_full",
                "status": evidence_status,
                "returncode": 0 if evidence_status == "passed" else 1,
            }
        ],
    }
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    return evidence_path


def test_release_readiness_reports_ready_when_contracts_and_evidence_pass(tmp_path: Path):
    release_readiness = load_release_readiness_module()
    evidence_path = write_release_files(tmp_path)

    report = release_readiness.build_readiness_report(
        manifest_path=tmp_path / "manifest.json",
        pyproject_path=tmp_path / "pyproject.toml",
        changelog_path=tmp_path / "CHANGELOG.md",
        evidence_path=evidence_path,
    )

    assert report["status"] == "ready"
    assert report["blockers"] == []
    assert "Evidence: passed" in release_readiness.format_text(report)
    assert "- none" in release_readiness.format_text(report)


def test_release_readiness_blocks_without_evidence(tmp_path: Path):
    release_readiness = load_release_readiness_module()
    write_release_files(tmp_path)

    report = release_readiness.build_readiness_report(
        manifest_path=tmp_path / "manifest.json",
        pyproject_path=tmp_path / "pyproject.toml",
        changelog_path=tmp_path / "CHANGELOG.md",
    )

    assert report["status"] == "blocked"
    assert "release evidence file was not provided" in report["blockers"]


def test_release_readiness_blocks_failed_evidence_and_version_drift(tmp_path: Path):
    release_readiness = load_release_readiness_module()
    evidence_path = write_release_files(tmp_path, evidence_status="failed")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "mbt-ai-tools"\nversion = "0.2.0"\n',
        encoding="utf-8",
    )

    report = release_readiness.build_readiness_report(
        manifest_path=tmp_path / "manifest.json",
        pyproject_path=tmp_path / "pyproject.toml",
        changelog_path=tmp_path / "CHANGELOG.md",
        evidence_path=evidence_path,
    )

    assert report["status"] == "blocked"
    assert "version mismatch: manifest=0.1.0, pyproject=0.2.0" in report["blockers"]
    assert "release evidence status is failed" in report["blockers"]
