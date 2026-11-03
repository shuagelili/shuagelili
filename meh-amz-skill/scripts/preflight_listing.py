#!/usr/bin/env python3
"""Run the complete structured Listing QA gate before HTML rendering."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Validate listing_record.json before generating any customer-facing deliverable.")
    parser.add_argument("json_path", type=Path, help="UTF-8 listing_record.json")
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args()
    if not args.json_path.is_file():
        print(json.dumps({"status": "ERROR", "stage": "pre_render", "error": f"listing record not found: {args.json_path}"}, ensure_ascii=False, indent=2))
        return 2

    script_dir = Path(__file__).resolve().parent
    try:
        completed = subprocess.run(
            [sys.executable, str(script_dir / "validate_listing_record.py"), str(args.json_path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=args.timeout, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "ERROR", "stage": "pre_render", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    try:
        aggregate: dict[str, Any] = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        print(json.dumps({"status": "ERROR", "stage": "pre_render", "error": f"aggregate validator returned invalid JSON: {exc}", "stderr": completed.stderr}, ensure_ascii=False, indent=2))
        return 2

    limits_check = aggregate.get("checks", {}).get("listing_limits", {}).get("result", {})
    status = "PASS" if completed.returncode == 0 and aggregate.get("status") == "PASS" else ("ERROR" if completed.returncode == 2 or aggregate.get("status") == "ERROR" else "FAIL")
    result = {
        "status": status, "stage": "pre_render", "input": str(args.json_path),
        "html_rendered": False, "aggregate": aggregate,
        "field_preflight": limits_check,
        "next_step": "Render HTML from the approved listing_record only after PASS." if status == "PASS" else "Revise the record and rerun preflight; do not render or deliver it.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else (2 if status == "ERROR" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
