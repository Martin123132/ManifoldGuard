#!/usr/bin/env python
"""Generate release evidence for ManifoldGuard quality gates."""

from __future__ import annotations

import argparse
import json
import platform
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_GATES = [
    {
        "name": "pytest_full",
        "description": "Full Python test suite.",
        "command": [sys.executable, "-m", "pytest", "-q"],
        "display": "python -m pytest -q",
    },
    {
        "name": "docs_quality_full",
        "description": "Manifest, docs, workflow, and report schema quality checks.",
        "command": [sys.executable, "scripts/docs_quality.py"],
        "display": "python scripts/docs_quality.py",
    },
    {
        "name": "examples_fresh",
        "description": "Committed examples match current offline CLI output.",
        "command": [sys.executable, "scripts/validate_examples.py"],
        "display": "python scripts/validate_examples.py",
    },
    {
        "name": "regression_corpus_eval",
        "description": "Frozen public corpus matches expected offline regulator behavior.",
        "command": [sys.executable, "scripts/evaluate_regulator.py"],
        "display": "python scripts/evaluate_regulator.py",
    },
    {
        "name": "preflight_full",
        "description": "Combined docs-quality and pytest preflight.",
        "command": [sys.executable, "scripts/preflight.py"],
        "display": "python scripts/preflight.py",
    },
    {
        "name": "preflight_docs_only",
        "description": "Docs-only preflight path used by embeddings-mode CI smoke checks.",
        "command": [sys.executable, "scripts/preflight.py", "--docs-only"],
        "display": "python scripts/preflight.py --docs-only",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a JSON evidence report for ManifoldGuard release gates."
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute gates. Without this flag, emit a dry-run evidence plan.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON evidence to this path instead of stdout.",
    )
    parser.add_argument(
        "--max-output-chars",
        type=int,
        default=4000,
        help="Maximum stdout/stderr tail characters stored per gate.",
    )
    return parser.parse_args()


def load_project_metadata(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    manifest_path = project_root / "docs" / "product_readiness_manifest.json"
    if not manifest_path.exists():
        return {}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    project = manifest.get("project", {})
    if not isinstance(project, dict):
        return {}
    return {
        "name": project.get("name"),
        "public_name": project.get("public_name"),
        "package_version": project.get("package_version"),
        "repository": project.get("repository"),
    }


def command_label(command: Iterable[str], display: str | None = None) -> str:
    if display:
        return display
    return shlex.join(str(part) for part in command)


def text_tail(value: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if len(value) <= limit:
        return value
    return value[-limit:]


def dry_run_gate(gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": gate["name"],
        "description": gate.get("description", ""),
        "command": command_label(gate["command"], gate.get("display")),
        "status": "not_run",
        "returncode": None,
        "duration_seconds": None,
        "stdout_tail": "",
        "stderr_tail": "",
    }


def run_gate(
    gate: dict[str, Any],
    *,
    project_root: Path = PROJECT_ROOT,
    max_output_chars: int = 4000,
) -> dict[str, Any]:
    started = time.perf_counter()
    result = subprocess.run(
        gate["command"],
        cwd=project_root,
        check=False,
        capture_output=True,
        text=True,
    )
    duration = time.perf_counter() - started
    return {
        "name": gate["name"],
        "description": gate.get("description", ""),
        "command": command_label(gate["command"], gate.get("display")),
        "status": "passed" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "duration_seconds": round(duration, 3),
        "stdout_tail": text_tail(result.stdout, max_output_chars),
        "stderr_tail": text_tail(result.stderr, max_output_chars),
    }


def summarize_gates(gates: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {
        "total": len(gates),
        "passed": sum(1 for gate in gates if gate["status"] == "passed"),
        "failed": sum(1 for gate in gates if gate["status"] == "failed"),
        "not_run": sum(1 for gate in gates if gate["status"] == "not_run"),
    }
    if counts["failed"]:
        status = "failed"
    elif counts["not_run"] == counts["total"]:
        status = "dry_run"
    elif counts["not_run"]:
        status = "partial"
    else:
        status = "passed"
    return {**counts, "status": status}


def build_release_evidence(
    *,
    run: bool,
    gates: list[dict[str, Any]] | None = None,
    project_root: Path = PROJECT_ROOT,
    max_output_chars: int = 4000,
    generated_at: str | None = None,
) -> dict[str, Any]:
    selected_gates = DEFAULT_GATES if gates is None else gates
    gate_results = [
        run_gate(gate, project_root=project_root, max_output_chars=max_output_chars)
        if run
        else dry_run_gate(gate)
        for gate in selected_gates
    ]
    return {
        "schema_version": "1.0",
        "generated_at": generated_at
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "run" if run else "dry_run",
        "project": load_project_metadata(project_root),
        "environment": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "summary": summarize_gates(gate_results),
        "gates": gate_results,
    }


def main() -> int:
    args = parse_args()
    evidence = build_release_evidence(
        run=args.run,
        max_output_chars=args.max_output_chars,
    )
    payload = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
        print(f"Wrote release evidence to {args.output}")
    else:
        print(payload, end="")
    return 1 if evidence["summary"]["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
