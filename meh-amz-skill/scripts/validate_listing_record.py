#!/usr/bin/env python3
"""Run every deterministic Listing validator and return one aggregate result."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


CHECKS = (
    ("fact_ledger", "validate_fact_ledger.py"),
    ("review_objection_keyword", "validate_review_objection_keyword.py"),
    ("keyword_controls", "validate_keyword_controls.py"),
    ("variants", "validate_variants.py"),
    ("bullets", "validate_bullets.py"),
    ("customer_copy", "scan_customer_copy.py"),
    ("listing_limits", "validate_listing_limits.py"),
)


def configure_stdout() -> None:
    stream = getattr(sys, "stdout", None)
    if stream is not None and hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


def emit(result: dict[str, Any], output: Path | None) -> None:
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(payload, end="")
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")


def main() -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Run the complete deterministic Amazon Listing QA pipeline.")
    parser.add_argument("json_path", type=Path, help="UTF-8 listing_record.json")
    parser.add_argument("--output", type=Path, help="Optional path for the aggregate JSON result")
    parser.add_argument("--timeout", type=float, default=120.0, help="Per-check timeout in seconds")
    args = parser.parse_args()

    if not args.json_path.is_file():
        result = {"status": "ERROR", "error": f"input file not found: {args.json_path}", "checks": {}}
        emit(result, args.output)
        return 2

    script_dir = Path(__file__).resolve().parent
    checks: dict[str, dict[str, Any]] = {}
    orchestration_errors: list[str] = []
    for name, script_name in CHECKS:
        script_path = script_dir / script_name
        if not script_path.is_file():
            checks[name] = {"status": "ERROR", "error": f"validator script not found: {script_path}"}
            orchestration_errors.append(name)
            continue
        try:
            completed = subprocess.run(
                [sys.executable, str(script_path), str(args.json_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                timeout=args.timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            checks[name] = {"status": "ERROR", "error": str(exc)}
            orchestration_errors.append(name)
            continue

        stdout = completed.stdout.strip()
        try:
            child = json.loads(stdout) if stdout else {"status": "ERROR", "error": "validator produced no JSON"}
        except json.JSONDecodeError as exc:
            child = {"status": "ERROR", "error": f"validator produced invalid JSON: {exc}", "raw_stdout": stdout[:2000]}
        child_status = child.get("status") if isinstance(child, dict) else "ERROR"
        checks[name] = {
            "script": script_name,
            "exit_code": completed.returncode,
            "status": child_status,
            "result": child,
        }
        if completed.stderr.strip():
            checks[name]["stderr"] = completed.stderr.strip()[:2000]
        if completed.returncode == 2 or child_status == "ERROR":
            orchestration_errors.append(name)

    failed = [name for name, check in checks.items() if check.get("status") != "PASS"]
    if orchestration_errors:
        status = "ERROR"
        exit_code = 2
    elif failed:
        status = "FAIL"
        exit_code = 1
    else:
        status = "PASS"
        exit_code = 0
    result = {
        "status": status,
        "input": str(args.json_path),
        "checks_run": list(checks),
        "failed_checks": failed,
        "orchestration_errors": orchestration_errors,
        "checks": checks,
        "rules": {
            "aggregate_gate": "PASS requires every deterministic validator to return PASS",
            "fail_closed": "missing scripts, invalid child JSON, timeouts, and exit code 2 produce ERROR",
        },
    }
    emit(result, args.output)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
