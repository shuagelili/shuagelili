#!/usr/bin/env python3
"""Gate final delivery: structured record -> aggregate QA -> rendered HTML."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def emit(payload: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")


def run(command: list[str], timeout: float) -> tuple[int, dict[str, Any]]:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 2, {"status": "ERROR", "error": str(exc)}
    try:
        payload = json.loads(completed.stdout) if completed.stdout.strip() else {"status": "ERROR", "error": "validator produced no JSON"}
    except json.JSONDecodeError as exc:
        payload = {"status": "ERROR", "error": f"validator produced invalid JSON: {exc}"}
    return completed.returncode, payload


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Require listing_record, aggregate QA, and HTML render validation before delivery.")
    parser.add_argument("json_path", type=Path)
    parser.add_argument("html_path", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()
    if not args.json_path.is_file() or not args.html_path.is_file():
        payload = {"status": "ERROR", "error": "listing_record.json and rendered HTML are both required", "gate": "pre_render_and_delivery"}
        emit(payload, args.output)
        return 2
    script_dir = Path(__file__).resolve().parent
    aggregate_exit, aggregate = run([sys.executable, str(script_dir / "validate_listing_record.py"), str(args.json_path)], args.timeout)
    if aggregate_exit != 0 or aggregate.get("status") != "PASS":
        payload = {"status": "FAIL" if aggregate_exit == 1 else "ERROR", "gate": "aggregate_validation", "aggregate": aggregate, "render": {"status": "SKIPPED", "reason": "aggregate QA must pass before render validation"}}
        emit(payload, args.output)
        return aggregate_exit if aggregate_exit in {1, 2} else 2
    render_exit, render = run([sys.executable, str(script_dir / "validate_render_contract.py"), str(args.json_path), str(args.html_path)], args.timeout)
    status = "PASS" if render_exit == 0 and render.get("status") == "PASS" else ("FAIL" if render_exit == 1 else "ERROR")
    payload = {"status": status, "gate": "delivery", "aggregate": aggregate, "render": render, "input": {"listing_record": str(args.json_path), "html": str(args.html_path)}}
    emit(payload, args.output)
    return 0 if status == "PASS" else render_exit


if __name__ == "__main__":
    raise SystemExit(main())
