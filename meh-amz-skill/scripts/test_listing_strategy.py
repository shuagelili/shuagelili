#!/usr/bin/env python3
"""Regression tests for keyword, title, bullet, voice, backend, and attribute gates."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def valid_record() -> dict[str, Any]:
    description = (
        "This bread freezer box helps home bakers store sliced sourdough in a tidy way. "
        "Who is it for? It is for home bakers who prepare bread ahead. "
        "How is it used? Place each slice in an individual slot before freezing. "
        "What does it hold? It holds sliced bread for organized freezer storage. "
        + ("The verified box supports a practical kitchen routine. " * 30)
    )
    terms = [
        {"id": "kw1", "term": "bread freezer box", "search_volume": 1200, "source_ref": "keyword-workbook.xlsx:Sheet1", "eligible": True, "product_fact_ids": ["f1"]},
        {"id": "kw2", "term": "home baker", "search_volume": 800, "source_ref": "keyword-workbook.xlsx:Sheet1", "eligible": True, "product_fact_ids": ["f1"]},
        {"id": "kw3", "term": "sourdough storage", "search_volume": 600, "source_ref": "keyword-workbook.xlsx:Sheet1", "eligible": True, "product_fact_ids": ["f1"]},
        {"id": "kw4", "term": "freezer organization", "search_volume": 500, "source_ref": "keyword-workbook.xlsx:Sheet1", "eligible": True, "product_fact_ids": ["f1"]},
        {"id": "kw5", "term": "bread slice holder", "search_volume": 300, "source_ref": "keyword-workbook.xlsx:Sheet1", "eligible": True, "product_fact_ids": ["f1"]},
    ]
    for i, term in enumerate(terms):
        term["source_candidate_ids"] = [f"src{i}"]
        term["demand_source_candidate_id"] = f"src{i}"
    bullets = [
        "【EASY BREAD STORAGE】 : This bread freezer box keeps slices organized for home bakers.",
        "【SOURDOUGH ROUTINE】 : A home baker can use sourdough storage slots to keep slices separated.",
        "【FREEZER ORGANIZATION】 : Sourdough storage helps keep prepared slices arranged.",
        "【INDIVIDUAL SLICES】 : Freezer organization helps keep each portion ready to retrieve.",
        "【PREP AHEAD】 : A bread slice holder supports a practical kitchen routine.",
    ]
    source_ledger = [
        {
            "candidate_id": f"src{i}", "raw_term": term["term"], "normalized_term": term["term"],
            "source_type": "user_workbook", "source_ref": f"keyword-workbook.xlsx:Sheet1:row{i + 1}",
            "evidence_ids": ["e1"], "marketplace": "US", "collected_at": "2026-10-01",
            "metric": {"name": "search_volume", "value": term["search_volume"], "unit": "searches", "period": "monthly"},
            "brand_terms_detected": [], "brand_terms_removed": [], "canonical_keyword_id": term["id"],
            "duplicate_action": "canonical", "eligibility": "eligible", "decision_reason": "Relevant to verified product fact f1.",
            "selected_fields": ["title" if i == 0 else "bullets"], "demand_source_candidate_id": f"src{i}"
        }
        for i, term in enumerate(terms)
    ]
    return {
        "context": {"marketplace": "US"},
        "evidence_ledger": [{"id": "e1", "claim": "product type", "value": "bread freezer box", "source_type": "user", "source_ref": "input", "scope": "product", "status": "verified"}],
        "product_fact_ledger": [{"id": "f1", "attribute": "product_type", "value": "bread freezer box", "ownership": "own", "source_evidence_ids": ["e1"], "status": "verified", "disposition": "publishable"}],
        "keyword_strategy": {
            "status": "complete", "primary_keyword_id": "kw1", "required_frontend_keyword_ids": ["kw1", "kw2", "kw3", "kw4", "kw5"], "keywords": terms,
            "title_selection": {
                "review_status": "human_reviewed", "selected_keyword_id": "kw1",
                "selected_fit": {"relevance": "relevant", "naturalness": "natural"},
                "selection_rationale": "Best relevant phrase for a concise, natural product title.",
                "higher_demand_terms_not_selected": [],
            },
        },
        "keyword_source_ledger": source_ledger,
        "publishable_fields": {
            "title": "Bread freezer box for home bakers",
            "bullets": bullets,
            "description": description,
            "frontend_keywords": "bread freezer box, home baker, sourdough storage",
            "backend_keywords": "compact freezer organizer",
        },
        "bullet_copy_plan": [
            {"bullet_index": i, "what": "bread freezer box", "who": "home bakers", "why": "organized slices", "keyword_ids": [f"kw{i + 1}"], "evidence_ids": ["e1"]}
            for i in range(5)
        ],
        "description_voice_map": {
            "status": "complete",
            "question_answer_pairs": [
                {"question_type": "product_identity", "answer_excerpt": "This bread freezer box helps home bakers store sliced sourdough in a tidy way.", "evidence_ids": ["e1"]},
                {"question_type": "audience", "answer_excerpt": "It is for home bakers who prepare bread ahead.", "evidence_ids": ["e1"]},
                {"question_type": "usage", "answer_excerpt": "Place each slice in an individual slot before freezing.", "evidence_ids": ["e1"]},
                {"question_type": "contents_or_compatibility", "answer_excerpt": "It holds sliced bread for organized freezer storage.", "evidence_ids": ["e1"]},
            ],
        },
        "attribute_inventory": [{"fact_id": "f1", "attribute": "product_type", "value": "bread freezer box", "keyword_forms": ["bread freezer box"], "disposition": "publishable", "mapped_fields": ["title", "bullets", "description"]}],
    }


def run_case(script: Path, record: dict[str, Any], expected: int) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="meh-amz-strategy-") as directory:
        path = Path(directory) / "listing_record.json"
        path.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(script), str(path)], capture_output=True, text=True,
            encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"}, check=False,
        )
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            payload = {"status": "ERROR", "raw": completed.stdout, "stderr": completed.stderr}
        expected_status = "PASS" if expected == 0 else "FAIL"
        return {"passed": completed.returncode == expected and payload.get("status") == expected_status, "actual_exit": completed.returncode, "status": payload.get("status"), "findings": payload.get("findings", [])}


def main() -> int:
    script = Path(__file__).resolve().with_name("validate_listing_strategy.py")
    if not script.is_file():
        print(json.dumps({"status": "FAIL", "error": "strategy validator has not been implemented"}, ensure_ascii=False, indent=2))
        return 1
    clean = valid_record()
    cases: dict[str, tuple[dict[str, Any], int]] = {"clean": (clean, 0)}
    bad_title = copy.deepcopy(clean)
    bad_title["publishable_fields"]["title"] = "Home baker storage container"
    cases["primary_keyword_missing_from_title"] = (bad_title, 1)
    naturally_placed = copy.deepcopy(clean)
    naturally_placed["publishable_fields"]["title"] = "For home bakers: bread freezer box"
    cases["primary_keyword_naturally_placed"] = (naturally_placed, 0)
    bad_bullet = copy.deepcopy(clean)
    bad_bullet["bullet_copy_plan"][0]["who"] = ""
    cases["missing_what_who_why"] = (bad_bullet, 1)
    missing_keyword = copy.deepcopy(clean)
    missing_keyword["bullet_copy_plan"][0]["keyword_ids"] = []
    cases["bullet_without_keyword"] = (missing_keyword, 1)
    repeated_backend = copy.deepcopy(clean)
    repeated_backend["publishable_fields"]["backend_keywords"] = "bread freezer box"
    cases["backend_repeats_frontend_phrase"] = (repeated_backend, 1)
    bad_voice = copy.deepcopy(clean)
    bad_voice["description_voice_map"]["question_answer_pairs"] = bad_voice["description_voice_map"]["question_answer_pairs"][:2]
    cases["incomplete_voice_map"] = (bad_voice, 1)
    missing_attribute = copy.deepcopy(clean)
    missing_attribute["attribute_inventory"] = []
    cases["missing_attribute_inventory_entry"] = (missing_attribute, 1)
    unplaced_required_keyword = copy.deepcopy(clean)
    unplaced_required_keyword["publishable_fields"]["bullets"][0] = "【EASY BREAD STORAGE】 : Slices stay organized for home bakers."
    cases["required_high_demand_keyword_unused"] = (unplaced_required_keyword, 1)
    absent_backend_field = copy.deepcopy(clean)
    del absent_backend_field["publishable_fields"]["backend_keywords"]
    absent_backend_field["backend_keyword_unavailability_reason"] = "No remaining eligible term."
    cases["backend_field_missing"] = (absent_backend_field, 1)
    absent_voice_excerpt = copy.deepcopy(clean)
    absent_voice_excerpt["description_voice_map"]["question_answer_pairs"][0]["answer_excerpt"] = "Not in description."
    cases["voice_excerpt_unmatched"] = (absent_voice_excerpt, 1)
    multiple_sentences = copy.deepcopy(clean)
    multiple_sentences["publishable_fields"]["bullets"][0] = "【EASY BREAD STORAGE】 : This bread freezer box stores slices. It keeps them organized."
    cases["bullet_has_multiple_sentences"] = (multiple_sentences, 1)
    missing_keyword_source = copy.deepcopy(clean)
    missing_keyword_source["keyword_strategy"]["keywords"][0]["source_ref"] = ""
    cases["keyword_without_frequency_source"] = (missing_keyword_source, 1)
    missing_source_ledger = copy.deepcopy(clean)
    del missing_source_ledger["keyword_source_ledger"]
    cases["missing_keyword_source_ledger"] = (missing_source_ledger, 1)
    missing_raw_term = copy.deepcopy(clean)
    missing_raw_term["keyword_source_ledger"][0]["raw_term"] = ""
    cases["keyword_source_without_raw_term"] = (missing_raw_term, 1)
    source_does_not_map = copy.deepcopy(clean)
    source_does_not_map["keyword_source_ledger"][0]["canonical_keyword_id"] = "unknown"
    cases["keyword_source_without_canonical_link"] = (source_does_not_map, 1)
    mismatched_metric = copy.deepcopy(clean)
    mismatched_metric["keyword_strategy"]["keywords"][0]["search_volume"] = 999
    cases["keyword_metric_conflicts_with_source"] = (mismatched_metric, 1)
    higher_demand_not_selected = copy.deepcopy(clean)
    higher_demand_not_selected["keyword_strategy"]["keywords"].append({
        "id": "kw6", "term": "frozen bread storage box", "search_volume": 1800,
        "source_ref": "keyword-workbook.xlsx:Sheet1", "eligible": True, "product_fact_ids": ["f1"],
        "source_candidate_ids": ["src6"], "demand_source_candidate_id": "src6",
    })
    higher_demand_not_selected["keyword_source_ledger"].append({
        "candidate_id": "src6", "raw_term": "frozen bread storage box", "normalized_term": "frozen bread storage box",
        "source_type": "user_workbook", "source_ref": "keyword-workbook.xlsx:Sheet1:row7",
        "evidence_ids": ["e1"], "marketplace": "US", "collected_at": "2026-10-01",
        "metric": {"name": "search_volume", "value": 1800, "unit": "searches", "period": "monthly"},
        "brand_terms_detected": [], "brand_terms_removed": [], "canonical_keyword_id": "kw6",
        "duplicate_action": "canonical", "eligibility": "eligible", "decision_reason": "Relevant phrase, retained for evaluation.",
        "selected_fields": [], "demand_source_candidate_id": "src6",
    })
    higher_demand_not_selected["keyword_strategy"]["title_selection"]["higher_demand_terms_not_selected"] = [{
        "candidate_id": "src6", "title_relevance": "relevant", "naturalness": "awkward",
        "reason_code": "awkward_localization", "reason": "The phrase is less idiomatic in the target marketplace than the selected title wording.",
    }]
    cases["higher_demand_term_has_reviewed_reason"] = (higher_demand_not_selected, 0)
    missing_higher_demand_reason = copy.deepcopy(higher_demand_not_selected)
    missing_higher_demand_reason["keyword_strategy"]["title_selection"]["higher_demand_terms_not_selected"] = []
    cases["higher_demand_term_missing_reason"] = (missing_higher_demand_reason, 1)
    results = {name: run_case(script, record, expected) for name, (record, expected) in cases.items()}
    failed = [name for name, result in results.items() if not result["passed"]]
    output = {"status": "PASS" if not failed else "FAIL", "cases": results, "failed_cases": failed}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
