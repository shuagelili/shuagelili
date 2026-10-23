#!/usr/bin/env python3
"""Run regression fixtures against the complete deterministic Listing QA gate."""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def configure_stdout() -> None:
    stream = getattr(sys, "stdout", None)
    if stream is not None and hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


def valid_record() -> dict[str, Any]:
    description = ("A verified product description for everyday use. " * 36).strip()
    return {
        "evidence_ledger": [{
            "id": "e1", "claim": "product type", "value": "verified box",
            "source_type": "user", "source_ref": "input", "scope": "product", "status": "verified",
        }],
        "product_fact_ledger": [{
            "id": "f1", "attribute": "product_type", "value": "box", "ownership": "own",
            "source_evidence_ids": ["e1"], "status": "verified", "disposition": "publishable",
            "customer_fields_allowed": ["*"]
        }],
        "publishable_fields": {
            "title": "Bread freezer box",
            "bullets": [f"【HEADER {index}】 : Useful customer-facing content for scene {index}." for index in range(1, 6)],
            "description": description,
        },
        "publishable_claim_map": [
            {"field_path": "publishable_fields.title", "fact_ids": ["f1"], "evidence_ids": ["e1"]},
            {"field_path": "publishable_fields.bullets", "fact_ids": ["f1"], "evidence_ids": ["e1"]},
            {"field_path": "publishable_fields.description", "fact_ids": ["f1"], "evidence_ids": ["e1"]},
        ],
        "review_objection_keyword_matrix": {"status": "not_available"},
        "keyword_controls": {"status": "not_available"},
        "variant_listing_matrix": {"status": "not_applicable"},
    }


def run_case(script: Path, record: dict[str, Any], expected: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="meh-amz-validator-") as directory:
        input_path = Path(directory) / "listing_record.json"
        input_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(script), str(input_path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}, check=False,
        )
        payload = json.loads(completed.stdout) if completed.stdout.strip() else {"status": "ERROR", "raw": completed.stderr}
        passed = completed.returncode == expected
        return {"expected_exit": expected, "actual_exit": completed.returncode, "passed": passed, "status": payload.get("status"), "failed_checks": payload.get("failed_checks", [])}


def main() -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Regression-test all deterministic Listing validators.")
    parser.add_argument("--script-dir", type=Path, help="Directory containing validator scripts")
    args = parser.parse_args()
    script_dir = args.script_dir or Path(__file__).resolve().parent
    aggregate = script_dir / "validate_listing_record.py"
    if not aggregate.is_file():
        print(json.dumps({"status": "ERROR", "error": f"missing aggregate validator: {aggregate}"}, ensure_ascii=False, indent=2))
        return 2

    clean = valid_record()
    cases = {"clean": (clean, 0)}
    old_bullet = copy.deepcopy(clean)
    old_bullet["publishable_fields"]["bullets"][0] = "Calendrier de l'Avent Football 2026."
    cases["old_bullet_format"] = (old_bullet, 1)
    copy_violation = copy.deepcopy(clean)
    copy_violation["publishable_fields"]["title"] = "Bread freezer box - TBD"
    cases["customer_copy_violation"] = (copy_violation, 1)
    short_description = copy.deepcopy(clean)
    short_description["publishable_fields"]["description"] = "Too short."
    cases["description_too_short"] = (short_description, 1)

    results = {name: run_case(aggregate, record, expected) for name, (record, expected) in cases.items()}
    failed = [name for name, result in results.items() if not result["passed"]]
    output = {"status": "PASS" if not failed else "FAIL", "cases": results, "failed_cases": failed}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
