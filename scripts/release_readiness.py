#!/usr/bin/env python
"""Summarize ManifoldGuard release readiness from manifest and evidence files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:  # pragma: no cover - Python <3.11 compatibility
    tomllib = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print an operator-friendly ManifoldGuard release readiness summary."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "docs" / "product_readiness_manifest.json",
        help="Path to product readiness manifest.",
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=PROJECT_ROOT / "pyproject.toml",
        help="Path to pyproject.toml.",
    )
    parser.add_argument(
        "--changelog",
        type=Path,
        default=PROJECT_ROOT / "CHANGELOG.md",
        help="Path to changelog.",
    )
    parser.add_argument(
        "--evidence",
        type=Path,
        help="Optional release evidence JSON produced by scripts/release_evidence.py.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_pyproject_version(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    if tomllib is not None:
        data = tomllib.loads(text)
        version = data.get("project", {}).get("version")
        return str(version) if version else None

    in_project = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]"):
            in_project = line == "[project]"
            continue
        if in_project:
            match = re.match(r"version\s*=\s*['\"]([^'\"]+)['\"]", line)
            if match:
                return match.group(1)
    return None


def changelog_has_version(path: Path, version: str | None) -> bool:
    if not version:
        return False
    text = path.read_text(encoding="utf-8")
    return bool(re.search(rf"^\s*##\s+{re.escape(version)}\b", text, re.MULTILINE))


def summarize_evidence(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "path": None,
            "status": "not_provided",
            "summary": None,
        }
    if not path.exists():
        return {
            "path": str(path),
            "status": "missing",
            "summary": None,
        }
    evidence = load_json(path)
    summary = evidence.get("summary") if isinstance(evidence, dict) else None
    status = summary.get("status") if isinstance(summary, dict) else "invalid"
    gates = evidence.get("gates", []) if isinstance(evidence, dict) else []
    return {
        "path": str(path),
        "status": str(status),
        "summary": summary,
        "gates": [
            {
                "name": gate.get("name"),
                "status": gate.get("status"),
                "returncode": gate.get("returncode"),
            }
            for gate in gates
            if isinstance(gate, dict)
        ],
    }


def install_mode_blockers(install_modes: Any) -> list[str]:
    if not isinstance(install_modes, list):
        return ["manifest install_modes must be a list"]

    by_name = {
        mode.get("name"): mode
        for mode in install_modes
        if isinstance(mode, dict) and mode.get("name")
    }
    blockers: list[str] = []
    if "core" not in by_name:
        blockers.append("core install mode is missing")
    elif "--no-deps" not in str(by_name["core"].get("command", "")):
        blockers.append("core install mode must use --no-deps")

    if "embeddings" not in by_name:
        blockers.append("embeddings install mode is missing")
    elif ".[embeddings]" not in str(by_name["embeddings"].get("command", "")):
        blockers.append("embeddings install mode must use .[embeddings]")
    return blockers


def build_readiness_report(
    *,
    manifest_path: Path,
    pyproject_path: Path,
    changelog_path: Path,
    evidence_path: Path | None = None,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    project = manifest.get("project", {})
    manifest_version = project.get("package_version") if isinstance(project, dict) else None
    pyproject_version = parse_pyproject_version(pyproject_path)
    evidence = summarize_evidence(evidence_path)

    blockers: list[str] = []
    if not manifest_version:
        blockers.append("manifest project.package_version is missing")
    if not pyproject_version:
        blockers.append("pyproject version is missing")
    if manifest_version and pyproject_version and manifest_version != pyproject_version:
        blockers.append(
            f"version mismatch: manifest={manifest_version}, pyproject={pyproject_version}"
        )
    if not changelog_has_version(changelog_path, str(manifest_version) if manifest_version else None):
        blockers.append(f"CHANGELOG.md is missing a release heading for {manifest_version}")

    blockers.extend(install_mode_blockers(manifest.get("install_modes")))

    support_boundaries = manifest.get("support_boundaries", [])
    if not any("not a universal fact checker" in str(item).lower() for item in support_boundaries):
        blockers.append("support boundaries must state ManifoldGuard is not a universal fact checker")

    if evidence["status"] == "not_provided":
        blockers.append("release evidence file was not provided")
    elif evidence["status"] == "missing":
        blockers.append(f"release evidence file is missing: {evidence['path']}")
    elif evidence["status"] != "passed":
        blockers.append(f"release evidence status is {evidence['status']}")

    return {
        "schema_version": "1.0",
        "status": "ready" if not blockers else "blocked",
        "project": {
            "name": project.get("name") if isinstance(project, dict) else None,
            "public_name": project.get("public_name") if isinstance(project, dict) else None,
            "repository": project.get("repository") if isinstance(project, dict) else None,
            "manifest_version": manifest_version,
            "pyproject_version": pyproject_version,
            "changelog_has_version": changelog_has_version(
                changelog_path,
                str(manifest_version) if manifest_version else None,
            ),
        },
        "install_modes": manifest.get("install_modes", []),
        "support_boundaries": support_boundaries,
        "evidence": evidence,
        "blockers": blockers,
    }


def format_text(report: dict[str, Any]) -> str:
    project = report["project"]
    lines = [
        "ManifoldGuard Release Readiness",
        "",
        f"Status: {report['status']}",
        f"Project: {project.get('public_name') or project.get('name')}",
        f"Version: manifest={project.get('manifest_version')} pyproject={project.get('pyproject_version')}",
        f"Changelog entry: {'yes' if project.get('changelog_has_version') else 'no'}",
        f"Evidence: {report['evidence']['status']}",
        "",
        "Install modes:",
    ]
    for mode in report.get("install_modes", []):
        if isinstance(mode, dict):
            lines.append(f"- {mode.get('name')}: {mode.get('command')}")

    lines.extend(["", "Support boundaries:"])
    for boundary in report.get("support_boundaries", []):
        lines.append(f"- {boundary}")

    lines.extend(["", "Blockers:"])
    if report["blockers"]:
        lines.extend(f"- {blocker}" for blocker in report["blockers"])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_readiness_report(
        manifest_path=args.manifest,
        pyproject_path=args.pyproject,
        changelog_path=args.changelog,
        evidence_path=args.evidence,
    )
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_text(report), end="")
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    sys.exit(main())
