#!/usr/bin/env python
"""Run the canonical ManifoldGuard release check sequence."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class CommandResult:
    returncode: int


CommandRunner = Callable[..., CommandResult]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run ManifoldGuard release evidence generation and readiness checks."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("release-evidence.json"),
        help="Path for release evidence JSON.",
    )
    parser.add_argument(
        "--max-output-chars",
        type=int,
        default=4000,
        help="Maximum stdout/stderr tail characters stored per release evidence gate.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Repository root used as the command working directory.",
    )
    return parser.parse_args(argv)


def quote_command(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in command)


def build_release_check_commands(
    *,
    output: Path,
    max_output_chars: int,
) -> list[dict[str, list[str] | str]]:
    output_arg = str(output)
    max_output_arg = str(max_output_chars)
    return [
        {
            "label": "release evidence",
            "command": [
                sys.executable,
                "scripts/release_evidence.py",
                "--run",
                "--output",
                output_arg,
                "--max-output-chars",
                max_output_arg,
            ],
        },
        {
            "label": "release readiness",
            "command": [
                sys.executable,
                "scripts/release_readiness.py",
                "--evidence",
                output_arg,
            ],
        },
    ]


def run_command(
    command: Sequence[str],
    *,
    label: str,
    project_root: Path,
    runner: CommandRunner = subprocess.run,
) -> int:
    print(f"Running {label}: {quote_command(command)}")
    result = runner(list(command), cwd=project_root, check=False)
    if result.returncode != 0:
        print(f"{label} failed with exit code {result.returncode}.")
    return int(result.returncode)


def run_release_check(
    *,
    output: Path,
    max_output_chars: int,
    project_root: Path = PROJECT_ROOT,
    runner: CommandRunner = subprocess.run,
) -> int:
    for spec in build_release_check_commands(
        output=output,
        max_output_chars=max_output_chars,
    ):
        returncode = run_command(
            spec["command"],  # type: ignore[arg-type]
            label=str(spec["label"]),
            project_root=project_root,
            runner=runner,
        )
        if returncode:
            return returncode

    print(f"Release check completed. Evidence: {output}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    return run_release_check(
        output=args.output,
        max_output_chars=args.max_output_chars,
        project_root=args.project_root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
