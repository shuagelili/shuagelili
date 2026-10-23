#!/usr/bin/env python3
"""Validate keyword intent classifications, negative keywords, and forbidden terms."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable


CONTROL_STATUSES = {"complete", "not_available"}
MATCH_TYPES = {"exact", "phrase", "broad"}
NEGATIVE_SCOPES = {"ppc", "frontend_keywords", "backend_keywords", "all"}
NEGATIVE_ACTIONS = {"negative_exact", "negative_phrase", "exclude", "review"}
TERM_STATUSES = {"verified", "calculated", "inferred", "to_confirm"}
FORBIDDEN_CATEGORIES = {"competitor_brand", "asin", "internal_review", "unsupported_claim", "regulated", "trademark", "commercial_offer", "other"}
FORBIDDEN_SCOPES = {"customer_copy", "frontend_keywords", "backend_keywords", "ppc", "all"}
TEXT_KEYS = {
    "text", "copy", "content", "value", "header", "title", "headline", "subheadline", "subtitle",
    "body", "caption", "overlay_text", "text_overlay", "supporting_copy", "supporting_text",
    "keyword", "term", "step", "instruction", "action", "result", "note", "warning", "limit",
}
CUSTOMER_FIELDS = {"title_a", "title_b", "title", "highlights", "bullets", "bullet_points", "description", "use_guide", "frontend_keywords", "backend_keywords", "image_text", "image_plan", "a_plus_text", "a_plus_modules"}


def normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def add(findings: list[dict[str, str]], code: str, path: str, message: str, **extra: str) -> None:
    result = {"code": code, "path": path, "message": message}
    result.update(extra)
    findings.append(result)


def iter_copy(value: Any, path: str) -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        if value.strip():
            yield path, value
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            yield from iter_copy(item, f"{path}[{index}]")
        return
    if not isinstance(value, dict):
        return
    for key in sorted(value):
        child = f"{path}.{key}"
        if key in TEXT_KEYS:
            yield from iter_copy(value[key], child)
        elif key in {"steps", "items", "modules", "sections", "bullets", "points"}:
            yield from iter_copy(value[key], child)


def contains_term(text: str, term: str) -> bool:
    normalized_text = normalize(text)
    normalized_term = normalize(term)
    if not normalized_term:
        return False
    if re.search(r"[a-z0-9]", normalized_term) and not re.search(r"[\u4e00-\u9fff]", normalized_term):
        return re.search(rf"(?<![a-z0-9]){re.escape(normalized_term)}(?![a-z0-9])", normalized_text) is not None
    return normalized_term in normalized_text


def unique_terms(items: Any, kind: str, findings: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    if not isinstance(items, list):
        add(findings, f"missing_{kind}", kind, f"{kind} must be a list")
        return result
    normalized_terms: dict[str, str] = {}
    for index, item in enumerate(items):
        path = f"{kind}[{index}]"
        if not isinstance(item, dict):
            add(findings, f"invalid_{kind[:-1]}", path, "entry must be an object")
            continue
        identifier = str(item.get("id", "")).strip()
        term = str(item.get("term", "")).strip()
        if not identifier:
            add(findings, f"missing_{kind[:-1]}_id", path, "id is required")
            continue
        if not term:
            add(findings, "empty_control_term", path, "term is required")
        if identifier in result:
            add(findings, f"duplicate_{kind[:-1]}_id", path, "id must be unique", id=identifier)
        key = normalize(term)
        if key and key in normalized_terms:
            add(findings, "duplicate_control_term", path, "normalized term already exists", previous_id=normalized_terms[key])
        if key:
            normalized_terms[key] = identifier
        result[identifier] = item
    return result


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Validate keyword intent controls and exclusion terms.")
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
    controls = record.get("keyword_controls")
    if not isinstance(controls, dict):
        add(findings, "missing_keyword_controls", "keyword_controls", "keyword_controls must be an object")
        controls = {}
    status = controls.get("status")
    if status not in CONTROL_STATUSES:
        add(findings, "invalid_keyword_controls_status", "keyword_controls.status", "status must be complete or not_available")

    negatives = unique_terms(controls.get("negative_keywords", []), "negative_keywords", findings)
    forbidden = unique_terms(controls.get("forbidden_terms", []), "forbidden_terms", findings)
    if status == "not_available" and (negatives or forbidden):
        add(findings, "unexpected_keyword_controls", "keyword_controls", "not_available controls must not contain terms")

    for identifier, item in negatives.items():
        path = f"negative_keywords.{identifier}"
        for required in ("term", "reason", "source_ref", "match_type", "scope", "action", "status"):
            if required not in item:
                add(findings, "missing_negative_keyword_field", path, "required field is missing", field=required)
        if item.get("match_type") not in MATCH_TYPES:
            add(findings, "invalid_negative_match_type", path, "unsupported match_type", value=str(item.get("match_type")))
        for scope in as_list(item.get("scope")):
            if str(scope) not in NEGATIVE_SCOPES:
                add(findings, "invalid_negative_scope", path, "unsupported scope", value=str(scope))
        if item.get("action") not in NEGATIVE_ACTIONS:
            add(findings, "invalid_negative_action", path, "unsupported action", value=str(item.get("action")))
        if item.get("status") not in TERM_STATUSES:
            add(findings, "invalid_negative_status", path, "unsupported status", value=str(item.get("status")))

    for identifier, item in forbidden.items():
        path = f"forbidden_terms.{identifier}"
        for required in ("term", "category", "applies_to", "reason", "source_ref", "status"):
            if required not in item:
                add(findings, "missing_forbidden_term_field", path, "required field is missing", field=required)
        if item.get("category") not in FORBIDDEN_CATEGORIES:
            add(findings, "invalid_forbidden_category", path, "unsupported category", value=str(item.get("category")))
        for scope in as_list(item.get("applies_to")):
            if str(scope) not in FORBIDDEN_SCOPES:
                add(findings, "invalid_forbidden_scope", path, "unsupported applies_to value", value=str(scope))
        if item.get("status") not in TERM_STATUSES:
            add(findings, "invalid_forbidden_status", path, "unsupported status", value=str(item.get("status")))

    publishable = record.get("publishable_fields") if isinstance(record.get("publishable_fields"), dict) else {}
    for identifier, item in negatives.items():
        scopes = {str(scope) for scope in as_list(item.get("scope"))}
        target_fields = CUSTOMER_FIELDS if "all" in scopes else {scope for scope in scopes if scope in CUSTOMER_FIELDS}
        for field in sorted(target_fields):
            for path, text in iter_copy(publishable.get(field), f"publishable_fields.{field}"):
                if contains_term(text, str(item.get("term", ""))):
                    add(findings, "negative_keyword_in_publishable_field", path, "negative keyword appears in a publishable field", id=identifier, term=str(item.get("term")))

    for identifier, item in forbidden.items():
        scopes = {str(scope) for scope in as_list(item.get("applies_to"))}
        if "all" in scopes or "customer_copy" in scopes:
            target_fields = CUSTOMER_FIELDS
        else:
            target_fields = scopes & CUSTOMER_FIELDS
        for field in sorted(target_fields):
            for path, text in iter_copy(publishable.get(field), f"publishable_fields.{field}"):
                if contains_term(text, str(item.get("term", ""))):
                    add(findings, "forbidden_term_in_publishable_field", path, "forbidden term appears in a publishable field", id=identifier, term=str(item.get("term")))

    matrix = record.get("review_objection_keyword_matrix")
    intents = matrix.get("keyword_intents", []) if isinstance(matrix, dict) else []
    for index, keyword in enumerate(intents if isinstance(intents, list) else []):
        if not isinstance(keyword, dict):
            continue
        term = str(keyword.get("keyword", ""))
        for identifier, item in forbidden.items():
            applies = {str(scope) for scope in as_list(item.get("applies_to"))}
            if "all" in applies or applies & {"frontend_keywords", "backend_keywords", "ppc"}:
                if contains_term(term, str(item.get("term", ""))):
                    add(findings, "forbidden_term_in_keyword_intent", f"review_objection_keyword_matrix.keyword_intents[{index}]", "forbidden term cannot be a positive keyword intent", id=identifier, term=str(item.get("term")))

    findings.sort(key=lambda item: (item.get("path", ""), item.get("code", ""), item.get("id", ""), item.get("term", "")))
    result = {
        "status": "PASS" if not findings else "FAIL",
        "finding_count": len(findings),
        "findings": findings,
        "counts": {"negative_keywords": len(negatives), "forbidden_terms": len(forbidden)},
        "rules": {
            "intent_classification": "keyword intents are classified separately by stage, type, and family",
            "negative_keywords": "negative keywords control targeting and must not enter their scoped publishable fields",
            "forbidden_terms": "forbidden terms are hard exclusions for their declared customer-copy or keyword scopes",
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
