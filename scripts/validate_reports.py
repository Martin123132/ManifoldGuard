#!/usr/bin/env python
"""Validate MBT-5 report JSON artifacts against the JSON schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate MBT-5 report JSON and JSONL artifacts against a JSON schema."
    )
    parser.add_argument(
        "--schema",
        default="docs/report_schema.json",
        help="Path to JSON schema file.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="One or more JSON or JSONL report files.",
    )
    return parser.parse_args()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def iter_report_objects(path: Path):
    if path.suffix.lower() == ".jsonl":
        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            yield line_number, json.loads(raw_line)
        return
    yield 1, load_json(path)


def main() -> int:
    args = parse_args()
    try:
        from jsonschema import validate
    except ImportError as exc:
        raise SystemExit(
            "jsonschema is not installed. Install it before running this script."
        ) from exc

    schema = load_json(Path(args.schema))
    total_errors = 0
    for file_name in args.files:
        path = Path(file_name)
        for line_number, payload in iter_report_objects(path):
            try:
                validate(instance=payload, schema=schema)
            except Exception as exc:  # pragma: no cover - explicit runtime behavior
                total_errors += 1
                if path.suffix.lower() == ".jsonl":
                    location = f"{path}:{line_number}"
                else:
                    location = str(path)
                print(f"Schema validation failed for {location}: {exc}")
    if total_errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
