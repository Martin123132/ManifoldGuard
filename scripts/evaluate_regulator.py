#!/usr/bin/env python
"""Compatibility wrapper for the ManifoldGuard offline evaluator."""

from __future__ import annotations

import sys

from mbt_ai_tools.eval import (
    CASE_FAMILY_PREFIXES,
    DEFAULT_CORPUS,
    PACKAGE_CORPUS,
    REPO_CORPUS,
    candidate_diagnostic,
    candidate_diagnostics,
    case_family,
    evaluate_case,
    evaluate_corpus,
    expected_bool_list,
    format_text,
    main,
    parse_args,
    read_corpus,
    summarize_cases,
    summarize_families,
    summarize_group,
    text_list,
)


__all__ = [
    "CASE_FAMILY_PREFIXES",
    "DEFAULT_CORPUS",
    "PACKAGE_CORPUS",
    "REPO_CORPUS",
    "candidate_diagnostic",
    "candidate_diagnostics",
    "case_family",
    "evaluate_case",
    "evaluate_corpus",
    "expected_bool_list",
    "format_text",
    "main",
    "parse_args",
    "read_corpus",
    "summarize_cases",
    "summarize_families",
    "summarize_group",
    "text_list",
]


if __name__ == "__main__":
    sys.exit(main())
