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
    lead = "Bread freezer box is a storage product for home bakers. It is for home bakers who prepare bread ahead. Place slices inside before freezing. The box stores sliced bread for organized freezer use. "
    description = (lead + "A verified product description for everyday use. " * 34).strip()
    return {
        "context": {"marketplace": "US"},
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
            "frontend_keywords": "bread freezer box, home baker",
            "backend_keywords": "compact freezer organizer",
        },
        "keyword_strategy": {"status": "not_available", "reason": "No keyword workbook or measured demand data supplied.", "keywords": []},
        "bullet_copy_plan": [
            {"bullet_index": index, "what": "verified product", "who": "target buyer", "why": f"scene {index} benefit", "keyword_ids": [], "evidence_ids": ["e1"]}
            for index in range(5)
        ],
        "description_voice_map": {
            "status": "complete",
            "question_answer_pairs": [
                {"question_type": "product_identity", "answer_excerpt": "Bread freezer box is a storage product for home bakers.", "evidence_ids": ["e1"]},
                {"question_type": "audience", "answer_excerpt": "It is for home bakers who prepare bread ahead.", "evidence_ids": ["e1"]},
                {"question_type": "usage", "answer_excerpt": "Place slices inside before freezing.", "evidence_ids": ["e1"]},
                {"question_type": "contents_or_compatibility", "answer_excerpt": "The box stores sliced bread for organized freezer use.", "evidence_ids": ["e1"]},
            ],
        },
        "attribute_inventory": [{"fact_id": "f1", "attribute": "product_type", "value": "box", "keyword_forms": ["box"], "disposition": "publishable", "mapped_fields": ["title", "bullets", "description"]}],
        "publishable_claim_map": [
            {"field_path": "publishable_fields.title", "fact_ids": ["f1"], "evidence_ids": ["e1"]},
            {"field_path": "publishable_fields.highlights", "fact_ids": ["f1"], "evidence_ids": ["e1"]},
            {"field_path": "publishable_fields.bullets", "fact_ids": ["f1"], "evidence_ids": ["e1"]},
            {"field_path": "publishable_fields.description", "fact_ids": ["f1"], "evidence_ids": ["e1"]},
            {"field_path": "publishable_fields.frontend_keywords", "fact_ids": ["f1"], "evidence_ids": ["e1"]},
            {"field_path": "publishable_fields.backend_keywords", "fact_ids": ["f1"], "evidence_ids": ["e1"]},
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


def render_html(record: dict[str, Any], *, omit_marker: str | None = None) -> str:
    fields = record["publishable_fields"]
    blocks: list[str] = ["<!doctype html><html><body>"]
    for key, value in fields.items():
        marker = f"publishable_fields.{key}"
        if marker == omit_marker:
            continue
        if isinstance(value, list):
            content = "".join(f"<li>{item}</li>" for item in value)
            blocks.append(f'<section data-copy-field="{marker}"><ul>{content}</ul></section>')
        else:
            blocks.append(f'<section data-copy-field="{marker}">{value}</section>')
    blocks.append("</body></html>")
    return "".join(blocks)


def run_delivery_case(script_dir: Path, record: dict[str, Any], expected: int, *, omit_marker: str | None = None, duplicate_marker: str | None = None, extra_copy: str | None = None) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="meh-amz-delivery-") as directory:
        root = Path(directory)
        input_path = root / "listing_record.json"
        html_path = root / "listing.html"
        input_path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        rendered = render_html(record, omit_marker=omit_marker)
        if omit_marker is None:
            rendered = rendered.replace("</section>", "<br><img alt='proof'></section>", 1)
        if duplicate_marker:
            rendered += f'<section data-copy-field="{duplicate_marker}">duplicate</section>'
        if extra_copy:
            rendered = rendered.replace("</section>", f"{extra_copy}</section>", 1)
        html_path.write_text(rendered, encoding="utf-8")
        completed = subprocess.run([sys.executable, str(script_dir / "validate_delivery.py"), str(input_path), str(html_path)], capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"}, check=False)
        payload = json.loads(completed.stdout) if completed.stdout.strip() else {"status": "ERROR"}
        return {"expected_exit": expected, "actual_exit": completed.returncode, "passed": completed.returncode == expected, "status": payload.get("status"), "gate": payload.get("gate")}


def run_missing_record_case(script_dir: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="meh-amz-missing-record-") as directory:
        root = Path(directory)
        html_path = root / "listing.html"
        html_path.write_text("<html><body>direct HTML without a record</body></html>", encoding="utf-8")
        completed = subprocess.run([sys.executable, str(script_dir / "validate_delivery.py"), str(root / "missing.json"), str(html_path)], capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"}, check=False)
        payload = json.loads(completed.stdout) if completed.stdout.strip() else {"status": "ERROR"}
        return {"expected_exit": 2, "actual_exit": completed.returncode, "passed": completed.returncode == 2, "status": payload.get("status"), "gate": payload.get("gate")}


def run_preflight_case(script_dir: Path, record: dict[str, Any], expected: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="meh-amz-preflight-") as directory:
        path = Path(directory) / "listing_record.json"
        path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        completed = subprocess.run([sys.executable, str(script_dir / "preflight_listing.py"), str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"}, check=False)
        payload = json.loads(completed.stdout) if completed.stdout.strip() else {"status": "ERROR"}
        passed = completed.returncode == expected and payload.get("html_rendered") is False
        return {"expected_exit": expected, "actual_exit": completed.returncode, "passed": passed, "status": payload.get("status"), "stage": payload.get("stage"), "html_rendered": payload.get("html_rendered")}


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
    highlight_overlap = copy.deepcopy(clean)
    highlight_overlap["publishable_fields"]["highlights"] = "Bread storage, easy serving"
    cases["highlight_title_overlap"] = (highlight_overlap, 1)
    highlight_valid = copy.deepcopy(clean)
    highlight_valid["publishable_fields"]["highlights"] = "Individual slots, organized storage, quick serving"
    cases["highlight_valid"] = (highlight_valid, 0)
    highlight_sentence = copy.deepcopy(clean)
    highlight_sentence["publishable_fields"]["highlights"] = "Individual slots, Perfect for busy mornings."
    cases["highlight_sentence_style"] = (highlight_sentence, 1)
    highlight_too_long = copy.deepcopy(clean)
    highlight_too_long["publishable_fields"]["highlights"] = "Individual slots, " + ("extra detail " * 10)
    cases["highlight_too_long"] = (highlight_too_long, 1)
    long_title_highlights = copy.deepcopy(clean)
    long_title_highlights["publishable_fields"]["title"] = "A" * 75
    long_title_highlights["publishable_fields"]["highlights"] = "Separate slots, easy storage"
    cases["highlights_hidden_at_title_limit"] = (long_title_highlights, 1)

    results = {name: run_case(aggregate, record, expected) for name, (record, expected) in cases.items()}
    failed = [name for name, result in results.items() if not result["passed"]]
    delivery_results = {
        "preflight_clean_record": run_preflight_case(script_dir, clean, 0),
        "preflight_rejects_short_description": run_preflight_case(script_dir, short_description, 1),
        "delivery_clean": run_delivery_case(script_dir, clean, 0),
        "delivery_missing_marker": run_delivery_case(script_dir, clean, 1, omit_marker="publishable_fields.bullets"),
        "delivery_duplicate_marker": run_delivery_case(script_dir, clean, 1, duplicate_marker="publishable_fields.title"),
        "delivery_extra_unapproved_copy": run_delivery_case(script_dir, clean, 1, extra_copy="Add an unapproved benefit."),
        "delivery_aggregate_failure": run_delivery_case(script_dir, short_description, 1),
        "delivery_missing_record": run_missing_record_case(script_dir),
    }
    strategy_suite = subprocess.run([sys.executable, str(script_dir / "test_listing_strategy.py")], capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"}, check=False)
    strategy_payload = json.loads(strategy_suite.stdout) if strategy_suite.stdout.strip() else {"status": "ERROR", "stderr": strategy_suite.stderr}
    delivery_results["listing_strategy_regression_suite"] = {"expected_exit": 0, "actual_exit": strategy_suite.returncode, "passed": strategy_suite.returncode == 0 and strategy_payload.get("status") == "PASS", "status": strategy_payload.get("status")}
    limit_suite = subprocess.run([sys.executable, str(script_dir / "test_listing_limits.py")], capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"}, check=False)
    limit_payload = json.loads(limit_suite.stdout) if limit_suite.stdout.strip() else {"status": "ERROR", "stderr": limit_suite.stderr}
    delivery_results["listing_limits_regression_suite"] = {"expected_exit": 0, "actual_exit": limit_suite.returncode, "passed": limit_suite.returncode == 0 and limit_payload.get("status") == "PASS", "status": limit_payload.get("status")}
    delivery_failed = [name for name, result in delivery_results.items() if not result["passed"]]
    output = {"status": "PASS" if not failed and not delivery_failed else "FAIL", "cases": results, "delivery_cases": delivery_results, "failed_cases": failed + delivery_failed}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if not failed and not delivery_failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
