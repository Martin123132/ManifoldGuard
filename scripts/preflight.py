#!/usr/bin/env python
"""Run combined MBT-5 preflight checks."""

from __future__ import annotations

import argparse
import subprocess
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run consolidated local checks before pushing a change."
    )
    parser.add_argument(
        "--tests-only",
        action="store_true",
        help="Run tests only and skip docs-quality checks.",
    )
    parser.add_argument(
        "--docs-only",
        action="store_true",
        help="Run docs-quality checks only and skip tests.",
    )
    parser.add_argument(
        "--no-schema",
        action="store_true",
        help="Run docs-quality checks without JSON schema validation.",
    )
    return parser.parse_args()


def run_command(command, *, label: str) -> int:
    print(f"Running {label}...")
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        print(f"{label} failed with exit code {result.returncode}.")
    return result.returncode


def main() -> int:
    args = parse_args()
    failures = 0

    if not args.tests_only:
        docs_cmd = [sys.executable, "scripts/docs_quality.py"]
        if args.no_schema:
            docs_cmd.append("--skip-schema")
        failures += run_command(docs_cmd, label="docs-quality checks")

    if not args.docs_only:
        failures += run_command(
            [sys.executable, "-m", "pytest", "-q"],
            label="pytest",
        )

    if failures:
        print(f"Preflight completed with {failures} failed step(s).")
        return 1
    print("Preflight completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
