from __future__ import annotations

import importlib.util
from pathlib import Path


class FakeResult:
    def __init__(self, returncode: int):
        self.returncode = returncode


def load_release_check_module():
    module_path = Path(__file__).resolve().parent.parent / "scripts" / "release_check.py"
    spec = importlib.util.spec_from_file_location("release_check", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_release_check_builds_evidence_then_readiness_commands():
    release_check = load_release_check_module()

    commands = release_check.build_release_check_commands(
        output=Path("release-evidence.json"),
        max_output_chars=123,
    )

    assert commands[0]["label"] == "release evidence"
    assert commands[0]["command"][1:] == [
        "scripts/release_evidence.py",
        "--run",
        "--output",
        "release-evidence.json",
        "--max-output-chars",
        "123",
    ]
    assert commands[1]["label"] == "release readiness"
    assert commands[1]["command"][1:] == [
        "scripts/release_readiness.py",
        "--evidence",
        "release-evidence.json",
    ]


def test_release_check_runs_commands_in_order(tmp_path: Path):
    release_check = load_release_check_module()
    calls = []

    def runner(command, *, cwd, check):
        calls.append((command, cwd, check))
        return FakeResult(0)

    result = release_check.run_release_check(
        output=Path("evidence.json"),
        max_output_chars=50,
        project_root=tmp_path,
        runner=runner,
    )

    assert result == 0
    assert [call[0][1] for call in calls] == [
        "scripts/release_evidence.py",
        "scripts/release_readiness.py",
    ]
    assert all(call[1] == tmp_path for call in calls)
    assert all(call[2] is False for call in calls)


def test_release_check_stops_on_failed_evidence(tmp_path: Path):
    release_check = load_release_check_module()
    calls = []

    def runner(command, *, cwd, check):
        calls.append(command)
        return FakeResult(7)

    result = release_check.run_release_check(
        output=Path("evidence.json"),
        max_output_chars=50,
        project_root=tmp_path,
        runner=runner,
    )

    assert result == 7
    assert len(calls) == 1
