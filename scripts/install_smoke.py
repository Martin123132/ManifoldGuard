"""Smoke-check an installed ManifoldGuard wheel.

Run this from an environment where the package has already been installed from
a wheel or package index. The script intentionally imports the public package
and calls installed console entry points instead of relying on editable-source
paths.
"""

from __future__ import annotations

import subprocess
import sys


def run(command: list[str]) -> str:
    """Run a command and fail with useful output if it exits non-zero."""
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stderr.write(f"Command failed: {' '.join(command)}\n")
        if completed.stdout:
            sys.stderr.write(f"stdout:\n{completed.stdout}\n")
        if completed.stderr:
            sys.stderr.write(f"stderr:\n{completed.stderr}\n")
        raise SystemExit(completed.returncode)
    return completed.stdout.strip()


def check_python_api() -> None:
    """Verify offline regulation works from the installed public API."""
    from mbt_ai_tools import regulate_candidates

    references = ["The capital of France is Paris."]
    candidates = [
        "The capital of France is London.",
        "The capital of France is Paris.",
    ]
    result = regulate_candidates(candidates, references, use_embeddings=False)

    if result.action != "emit":
        raise SystemExit(f"Expected emit action, got: {result.action!r}")
    if result.emitted_text != candidates[1]:
        raise SystemExit(
            "Expected safe Paris candidate, got: "
            f"{result.emitted_text!r}"
        )


def main() -> int:
    check_python_api()
    check_version = run(["manifold-check", "--version"])
    eval_version = run(["manifold-eval", "--version"])

    print("Install smoke passed.")
    print(f"manifold-check: {check_version}")
    print(f"manifold-eval: {eval_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
