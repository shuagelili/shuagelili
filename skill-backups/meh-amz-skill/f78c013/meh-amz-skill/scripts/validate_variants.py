#!/usr/bin/env python3
"""Validate parent/child Listing scope and variant-specific fact isolation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


STATUSES = {"complete", "not_applicable"}
FIELD_SCOPES = {"parent", "shared", "child"}


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def add(findings: list[dict[str, str]], code: str, path: str, message: str, **extra: str) -> None:
    result = {"code": code, "path": path, "message": message}
    result.update(extra)
    findings.append(result)


def ids(value: Any) -> set[str]:
    return {str(item).strip() for item in as_list(value) if str(item).strip()}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Validate parent/child Amazon Listing variant logic.")
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

    findings: list[dict[str, str]] = []
    matrix = record.get("variant_listing_matrix")
    if not isinstance(matrix, dict):
        add(findings, "missing_variant_matrix", "variant_listing_matrix", "variant_listing_matrix must be an object")
        matrix = {}
    status = matrix.get("status")
    if status not in STATUSES:
        add(findings, "invalid_variant_status", "variant_listing_matrix.status", "status must be complete or not_applicable")

    parent = matrix.get("parent") if isinstance(matrix.get("parent"), dict) else {}
    children_raw = matrix.get("children", [])
    field_map_raw = matrix.get("field_scope_map", [])
    children: dict[str, dict[str, Any]] = {}
    child_asins: set[str] = set()
    facts = {}
    if isinstance(record.get("product_fact_ledger"), list):
        facts = {str(item.get("id")): item for item in record["product_fact_ledger"] if isinstance(item, dict) and item.get("id")}
    keyword_intents: dict[str, dict[str, Any]] = {}
    matrix_keywords = record.get("review_objection_keyword_matrix")
    if isinstance(matrix_keywords, dict) and isinstance(matrix_keywords.get("keyword_intents"), list):
        keyword_intents = {str(item.get("id")): item for item in matrix_keywords["keyword_intents"] if isinstance(item, dict) and item.get("id")}

    if status == "not_applicable":
        if parent or children_raw or field_map_raw:
            add(findings, "unexpected_variant_data", "variant_listing_matrix", "not_applicable variant matrix must not contain parent, child, or field-scope data")
    else:
        for required in ("id", "variation_theme", "shared_fact_ids", "shared_keyword_intent_ids", "shared_field_paths"):
            if required not in parent:
                add(findings, "missing_parent_variant_field", "variant_listing_matrix.parent", "required field is missing", field=required)
        if not str(parent.get("variation_theme", "")).strip():
            add(findings, "empty_variation_theme", "variant_listing_matrix.parent.variation_theme", "variation_theme is required")
        shared_fact_ids = ids(parent.get("shared_fact_ids"))
        for fact_id in sorted(shared_fact_ids):
            if fact_id not in facts:
                add(findings, "unknown_shared_fact", "variant_listing_matrix.parent.shared_fact_ids", "references an unknown product fact", id=fact_id)
            elif str(facts[fact_id].get("variant", "")).strip() not in {"", "shared", "all", "parent"}:
                add(findings, "variant_specific_fact_marked_shared", "variant_listing_matrix.parent.shared_fact_ids", "variant-specific fact cannot be shared by the parent", id=fact_id)
        for keyword_id in sorted(ids(parent.get("shared_keyword_intent_ids"))):
            if keyword_id not in keyword_intents:
                add(findings, "unknown_shared_keyword_intent", "variant_listing_matrix.parent.shared_keyword_intent_ids", "references an unknown keyword intent", id=keyword_id)

        if not isinstance(children_raw, list):
            add(findings, "invalid_variant_children", "variant_listing_matrix.children", "children must be a list")
            children_raw = []
        if len(children_raw) < 2:
            add(findings, "insufficient_variant_children", "variant_listing_matrix.children", "complete variant matrix requires at least two children")
        signatures: dict[tuple[tuple[str, str], ...], str] = {}
        for index, child in enumerate(children_raw):
            path = f"variant_listing_matrix.children[{index}]"
            if not isinstance(child, dict):
                add(findings, "invalid_variant_child", path, "child must be an object")
                continue
            child_id = str(child.get("id", "")).strip()
            if not child_id:
                add(findings, "missing_variant_child_id", path, "child id is required")
                continue
            if child_id in children:
                add(findings, "duplicate_variant_child_id", path, "child id must be unique", id=child_id)
            asin = str(child.get("asin", "")).strip()
            if asin:
                if asin in child_asins:
                    add(findings, "duplicate_variant_child_asin", path, "child ASIN must be unique", asin=asin)
                child_asins.add(asin)
            attributes = child.get("variation_attributes")
            if not isinstance(attributes, dict) or not attributes:
                add(findings, "missing_variant_attributes", path, "child requires variation_attributes")
                attributes = {}
            signature = tuple(sorted((str(key), str(value).strip()) for key, value in attributes.items() if str(value).strip()))
            if signature in signatures:
                add(findings, "duplicate_variant_signature", path, "variation attributes duplicate another child", previous_id=signatures[signature])
            if signature:
                signatures[signature] = child_id
            fact_ids = ids(child.get("fact_ids"))
            keyword_ids = ids(child.get("keyword_intent_ids"))
            field_paths = ids(child.get("field_paths"))
            for fact_id in sorted(fact_ids):
                if fact_id not in facts:
                    add(findings, "unknown_child_fact", path, "child references an unknown product fact", id=fact_id)
                elif str(facts[fact_id].get("variant", "")).strip() not in {"", "shared", "all", child_id}:
                    add(findings, "child_fact_variant_mismatch", path, "child fact is assigned to a different variant", id=fact_id)
            for keyword_id in sorted(keyword_ids):
                if keyword_id not in keyword_intents:
                    add(findings, "unknown_child_keyword_intent", path, "child references an unknown keyword intent", id=keyword_id)
                elif str(keyword_intents[keyword_id].get("variant_id", "")).strip() not in {"", "shared", child_id}:
                    add(findings, "child_keyword_variant_mismatch", path, "child keyword intent is assigned to a different variant", id=keyword_id)
            if not field_paths:
                add(findings, "missing_variant_field_paths", path, "child requires field_paths for variant-specific copy")
            if fact_ids & shared_fact_ids:
                add(findings, "fact_scope_overlap", path, "child fact_ids overlap parent shared_fact_ids")
            children[child_id] = {"raw": child, "fact_ids": fact_ids, "keyword_intent_ids": keyword_ids, "field_paths": field_paths}

        if not isinstance(field_map_raw, list):
            add(findings, "invalid_variant_field_scope_map", "variant_listing_matrix.field_scope_map", "field_scope_map must be a list")
            field_map_raw = []
        mapped_paths: set[str] = set()
        for index, mapping in enumerate(field_map_raw):
            path = f"variant_listing_matrix.field_scope_map[{index}]"
            if not isinstance(mapping, dict):
                add(findings, "invalid_variant_field_scope", path, "field scope entry must be an object")
                continue
            field_path = str(mapping.get("field_path", "")).strip()
            scope = mapping.get("scope")
            child_ids = ids(mapping.get("child_ids"))
            fact_ids = ids(mapping.get("fact_ids"))
            if not field_path:
                add(findings, "missing_variant_field_path", path, "field_path is required")
            if field_path in mapped_paths:
                add(findings, "duplicate_variant_field_path", path, "field_path must be unique", field_path=field_path)
            mapped_paths.add(field_path)
            if scope not in FIELD_SCOPES:
                add(findings, "invalid_variant_field_scope_value", path, "scope must be parent, shared, or child", value=str(scope))
            if scope in {"parent", "shared"} and child_ids:
                add(findings, "shared_field_has_child_scope", path, "parent/shared fields cannot list child_ids")
            if scope == "child":
                if len(child_ids) != 1:
                    add(findings, "child_field_scope_cardinality", path, "child field scope must identify exactly one child")
                for child_id in child_ids:
                    if child_id not in children:
                        add(findings, "unknown_field_scope_child", path, "field scope references an unknown child", id=child_id)
                    elif not fact_ids.issubset(shared_fact_ids | children[child_id]["fact_ids"]):
                        add(findings, "child_field_fact_leakage", path, "child field uses a fact outside shared facts or that child")
            if scope in {"parent", "shared"} and not fact_ids.issubset(shared_fact_ids):
                add(findings, "shared_field_fact_leakage", path, "parent/shared field uses a child-specific or unknown fact")

        for field_path in ids(parent.get("shared_field_paths")):
            if field_path not in mapped_paths:
                add(findings, "unmapped_shared_field", "variant_listing_matrix.parent.shared_field_paths", "shared field has no scope mapping", field_path=field_path)
        for child_id, child_data in children.items():
            for field_path in child_data["field_paths"]:
                if field_path not in mapped_paths:
                    add(findings, "unmapped_child_field", f"variant_listing_matrix.children.{child_id}.field_paths", "child field has no scope mapping", field_path=field_path)

        claim_map = record.get("publishable_claim_map", [])
        if isinstance(claim_map, list):
            for index, claim in enumerate(claim_map):
                if not isinstance(claim, dict):
                    continue
                field_path = str(claim.get("field_path", "")).strip()
                fact_ids = ids(claim.get("fact_ids"))
                if field_path and field_path not in mapped_paths:
                    add(findings, "unscoped_variant_claim", f"publishable_claim_map[{index}]", "publishable claim has no variant field scope mapping", field_path=field_path)
                if field_path in mapped_paths:
                    mapping = next(item for item in field_map_raw if isinstance(item, dict) and item.get("field_path") == field_path)
                    scope = mapping.get("scope")
                    allowed = ids(mapping.get("fact_ids"))
                    if not fact_ids.issubset(allowed):
                        add(findings, "variant_claim_fact_leakage", f"publishable_claim_map[{index}]", "claim map uses facts outside the field scope", field_path=field_path)

    findings.sort(key=lambda item: (item.get("path", ""), item.get("code", ""), item.get("id", ""), item.get("field_path", "")))
    result = {
        "status": "PASS" if not findings else "FAIL",
        "finding_count": len(findings),
        "findings": findings,
        "counts": {"children": len(children), "child_asins": len(child_asins)},
        "rules": {
            "shared_facts": "parent/shared fields may use only facts declared shared across the variant family",
            "child_isolation": "child fields may use only facts assigned to that child",
            "variant_identity": "each child requires distinct variation attributes and field paths",
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
