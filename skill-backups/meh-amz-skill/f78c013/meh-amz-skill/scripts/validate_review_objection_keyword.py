#!/usr/bin/env python3
"""Validate the Review -> purchase objection -> keyword-intent matrix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STATUSES = {"complete", "hypothesis", "not_available"}
ROW_STATUSES = {"verified", "hypothesis", "to_confirm"}
SENTIMENTS = {"positive", "negative", "mixed", "neutral"}
INTENT_STAGES = {"discovery", "problem_solving", "comparison", "transactional", "gift_seasonal", "post_purchase"}
INTENT_TYPES = {"informational", "problem_solving", "comparison", "transactional", "gift_seasonal"}
INTENT_FAMILIES = {
    "core_product", "feature_attribute", "use_case", "problem_solving", "audience",
    "compatibility", "comparison", "transactional", "gift_seasonal", "maintenance", "post_purchase",
}
FIELD_NAMES = {
    "title_a", "title_b", "title", "highlights", "bullets", "bullet_points", "description",
    "use_guide", "frontend_keywords", "backend_keywords", "image_text", "image_plan", "a_plus_text", "a_plus_modules",
}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def add(findings: list[dict[str, str]], code: str, path: str, message: str, **extra: str) -> None:
    item = {"code": code, "path": path, "message": message}
    item.update(extra)
    findings.append(item)


def unique_ids(items: Any, kind: str, findings: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(items, list):
        add(findings, f"missing_{kind}", kind, f"{kind} must be a list")
        return result
    for index, item in enumerate(items):
        path = f"{kind}[{index}]"
        if not isinstance(item, dict):
            add(findings, f"invalid_{kind[:-1]}", path, "entry must be an object")
            continue
        identifier = str(item.get("id", "")).strip()
        if not identifier:
            add(findings, f"missing_{kind[:-1]}_id", path, "id is required")
            continue
        if identifier in result:
            add(findings, f"duplicate_{kind[:-1]}_id", path, "id must be unique", id=identifier)
        result[identifier] = item
    return result


def check_ids(findings: list[dict[str, str]], values: Any, known: dict[str, Any], code: str, path: str) -> None:
    for identifier in as_list(values):
        identifier = str(identifier).strip()
        if identifier and identifier not in known:
            add(findings, code, path, "references an unknown id", id=identifier)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Validate Review, purchase-objection, and keyword-intent linkage.")
    parser.add_argument("json_path", type=Path)
    args = parser.parse_args()
    try:
        record = json.loads(args.json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    if not isinstance(record, dict):
        print(json.dumps({"status": "ERROR", "error": "JSON root must be an object"}, ensure_ascii=False, indent=2))
        return 2

    matrix = record.get("review_objection_keyword_matrix")
    findings: list[dict[str, str]] = []
    if not isinstance(matrix, dict):
        add(findings, "missing_matrix", "review_objection_keyword_matrix", "matrix must be an object")
        matrix = {}
    status = matrix.get("status")
    if status not in STATUSES:
        add(findings, "invalid_matrix_status", "review_objection_keyword_matrix.status", "status must be complete, hypothesis, or not_available")

    evidence = {}
    if isinstance(record.get("evidence_ledger"), list):
        evidence = {str(item.get("id")): item for item in record["evidence_ledger"] if isinstance(item, dict) and item.get("id")}
    facts = {}
    if isinstance(record.get("product_fact_ledger"), list):
        facts = {str(item.get("id")): item for item in record["product_fact_ledger"] if isinstance(item, dict) and item.get("id")}

    review_themes = unique_ids(matrix.get("review_themes", []), "review_themes", findings)
    objections = unique_ids(matrix.get("purchase_objections", []), "purchase_objections", findings)
    keywords = unique_ids(matrix.get("keyword_intents", []), "keyword_intents", findings)
    links = unique_ids(matrix.get("links", []), "links", findings)

    if status == "not_available":
        if review_themes or objections or keywords or links:
            add(findings, "unexpected_matrix_rows", "review_objection_keyword_matrix", "not_available matrix must not contain analytical rows")
    else:
        if status == "complete" and (not review_themes or not objections or not keywords or not links):
            add(findings, "incomplete_matrix", "review_objection_keyword_matrix", "complete matrix requires review themes, objections, keyword intents, and links")

    for identifier, theme in review_themes.items():
        path = f"review_themes.{identifier}"
        for required in ("theme", "sentiment", "evidence_ids"):
            if required not in theme:
                add(findings, "missing_review_theme_field", path, "required field is missing", field=required)
        if theme.get("sentiment") not in SENTIMENTS:
            add(findings, "invalid_review_sentiment", path, "unsupported sentiment", value=str(theme.get("sentiment")))
        check_ids(findings, theme.get("evidence_ids"), evidence, "unknown_review_evidence", path)
        if status == "complete" and not as_list(theme.get("evidence_ids")):
            add(findings, "review_theme_without_evidence", path, "complete review themes require evidence_ids")

    for identifier, objection in objections.items():
        path = f"purchase_objections.{identifier}"
        for required in ("objection", "severity", "evidence_ids", "response_fact_ids", "response_fields"):
            if required not in objection:
                add(findings, "missing_objection_field", path, "required field is missing", field=required)
        check_ids(findings, objection.get("evidence_ids"), evidence, "unknown_objection_evidence", path)
        check_ids(findings, objection.get("response_fact_ids"), facts, "unknown_objection_fact", path)
        for field in as_list(objection.get("response_fields")):
            if str(field) not in FIELD_NAMES:
                add(findings, "invalid_objection_response_field", path, "response field is not a customer-facing field", field=str(field))

    for identifier, keyword in keywords.items():
        path = f"keyword_intents.{identifier}"
        for required in ("keyword", "intent_stage", "intent_type", "intent_family", "source_ref", "evidence_status"):
            if required not in keyword:
                add(findings, "missing_keyword_intent_field", path, "required field is missing", field=required)
        if keyword.get("intent_stage") not in INTENT_STAGES:
            add(findings, "invalid_keyword_intent_stage", path, "unsupported intent_stage", value=str(keyword.get("intent_stage")))
        if keyword.get("intent_type") not in INTENT_TYPES:
            add(findings, "invalid_keyword_intent_type", path, "unsupported intent_type", value=str(keyword.get("intent_type")))
        if keyword.get("intent_family") not in INTENT_FAMILIES:
            add(findings, "invalid_keyword_intent_family", path, "unsupported intent_family", value=str(keyword.get("intent_family")))
        if keyword.get("evidence_status") not in {"verified", "calculated", "inferred", "to_confirm"}:
            add(findings, "invalid_keyword_evidence_status", path, "unsupported evidence_status", value=str(keyword.get("evidence_status")))

    for identifier, link in links.items():
        path = f"links.{identifier}"
        for required in ("review_theme_ids", "objection_ids", "keyword_intent_ids", "intent_summary", "response_fact_ids", "response_fields", "status"):
            if required not in link:
                add(findings, "missing_matrix_link_field", path, "required field is missing", field=required)
        check_ids(findings, link.get("review_theme_ids"), review_themes, "unknown_link_review_theme", path)
        check_ids(findings, link.get("objection_ids"), objections, "unknown_link_objection", path)
        check_ids(findings, link.get("keyword_intent_ids"), keywords, "unknown_link_keyword_intent", path)
        check_ids(findings, link.get("response_fact_ids"), facts, "unknown_link_fact", path)
        if link.get("status") not in ROW_STATUSES:
            add(findings, "invalid_matrix_link_status", path, "unsupported row status", value=str(link.get("status")))
        if status == "complete" and not all(as_list(link.get(key)) for key in ("review_theme_ids", "objection_ids", "keyword_intent_ids", "response_fact_ids", "response_fields")):
            add(findings, "incomplete_matrix_link", path, "complete row requires review, objection, keyword, fact, and response-field links")
        for field in as_list(link.get("response_fields")):
            if str(field) not in FIELD_NAMES:
                add(findings, "invalid_matrix_response_field", path, "response field is not a customer-facing field", field=str(field))

    findings.sort(key=lambda item: (item.get("path", ""), item.get("code", ""), item.get("id", ""), item.get("field", "")))
    result = {
        "status": "PASS" if not findings else "FAIL",
        "finding_count": len(findings),
        "findings": findings,
        "counts": {"review_themes": len(review_themes), "objections": len(objections), "keyword_intents": len(keywords), "links": len(links)},
        "rules": {
            "joint_linkage": "accepted rows link review evidence, purchase resistance, keyword intent, verified product facts, and response fields",
            "no_fabricated_prevalence": "review frequency and severity require supplied evidence; unavailable data stays not_available or hypothesis",
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
