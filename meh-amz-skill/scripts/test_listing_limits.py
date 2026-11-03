#!/usr/bin/env python3
"""Regression tests for configurable, deterministic Listing field preflight."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def run_case(script: Path, record: dict[str, Any], expected: int) -> tuple[bool, dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="meh-amz-limits-") as directory:
        path = Path(directory) / "listing_record.json"
        path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(script), str(path)], capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}, check=False,
        )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {"status": "ERROR", "stderr": result.stderr, "stdout": result.stdout}
        return result.returncode == expected, payload


def main() -> int:
    script = Path(__file__).resolve().with_name("validate_listing_limits.py")
    base = {"context": {"marketplace": "US"}, "publishable_fields": {
        "title": "Bread freezer box", "description": "Verified product details. " * 65,
        "bullets": ["one", "two"], "backend_keywords": "bread storage",
    }}
    cases: dict[str, tuple[dict[str, Any], int]] = {"defaults_measure_all_fields": (base, 0)}

    byte_limit = copy.deepcopy(base)
    byte_limit["publishable_fields"]["backend_keywords"] = "éé"
    byte_limit["context"]["limits"] = {"backend_keywords": {
        "max": 3, "count_unit": "utf8_bytes", "source_ref": "seller-provided limit"}}
    cases["configured_utf8_byte_limit"] = (byte_limit, 1)

    invalid_range = copy.deepcopy(base)
    invalid_range["context"]["limits"] = {"title": {"min": 80, "max": 75}}
    cases["invalid_min_max_range"] = (invalid_range, 1)

    invalid_unit = copy.deepcopy(base)
    invalid_unit["context"]["limits"] = {"title": {"max": 75, "count_unit": "guesses"}}
    cases["unsupported_count_unit"] = (invalid_unit, 1)

    bool_limit = copy.deepcopy(base)
    bool_limit["context"]["limits"] = {"title": {"max": True}}
    cases["boolean_is_not_a_limit"] = (bool_limit, 1)

    char_limit = copy.deepcopy(base)
    char_limit["publishable_fields"]["bullets"] = ["éé"]
    char_limit["context"]["limits"] = {"bullets": {"max": 1, "count_unit": "unicode_code_points"}}
    cases["list_entries_are_measured_individually"] = (char_limit, 1)

    unresolved_market = copy.deepcopy(base)
    del unresolved_market["context"]["marketplace"]
    cases["unresolved_marketplace"] = (unresolved_market, 1)

    outputs = {name: run_case(script, record, expected) for name, (record, expected) in cases.items()}
    expected_findings = {
        "configured_utf8_byte_limit": "above_maximum",
        "invalid_min_max_range": "invalid_limit_range",
        "unsupported_count_unit": "invalid_count_unit",
        "boolean_is_not_a_limit": "invalid_limit_value",
        "list_entries_are_measured_individually": "above_maximum",
        "unresolved_marketplace": "missing_limit_marketplace",
    }
    for name, code in expected_findings.items():
        findings = outputs[name][1].get("findings", [])
        outputs[name] = (outputs[name][0] and any(item.get("code") == code for item in findings), outputs[name][1])
    failed = [name for name, (passed, _) in outputs.items() if not passed]
    print(json.dumps({"status": "PASS" if not failed else "FAIL", "cases": {
        name: {"passed": passed, **payload} for name, (passed, payload) in outputs.items()
    }, "failed_cases": failed}, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
