#!/usr/bin/env python3
"""Deterministically scan customer-facing Amazon listing copy.

The input is a UTF-8 JSON object containing ``publishable_fields`` and, when
available, ``context``. Only declared customer-copy fields are scanned;
evidence and other internal metadata are never treated as customer text.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable


FIELD_LABELS = {
    "title_a": "Title A", "title_b": "Title B", "title": "Title",
    "highlights": "Highlights", "bullets": "Bullet", "bullet_points": "Bullet",
    "description": "Product description", "use_guide": "Use guide",
    "frontend_keywords": "Frontend search keywords", "backend_keywords": "Backend search terms",
    "image_text": "Image text", "image_plan": "Image text",
    "a_plus_text": "A+ text", "a_plus_modules": "A+ text",
}
CUSTOMER_FIELD_KEYS = tuple(FIELD_LABELS)
TEXT_KEYS = {
    "text", "copy", "content", "value", "header", "title", "headline",
    "subheadline", "subtitle", "body", "caption", "overlay_text", "text_overlay",
    "supporting_copy", "supporting_text", "keyword", "term", "step",
    "instruction", "action", "result", "note", "warning", "limit",
}

INTERNAL_PATTERNS = [
    (r"待确认|仍需确认|待核实|待验证|推断|假设|未知|无法验证|建议确认", "internal_review_language"),
    (r"\blisting[- ]stale\b|\bblocked\b|\bto be confirmed\b", "internal_review_language"),
    (r"\bneeds? confirmation\b|\bpending confirmation\b|\bverification needed\b", "internal_review_language"),
    (r"\bunverified\b|\binferred\b|\bassumption\b|\bunknown\b|\btbd\b|\btbc\b", "internal_review_language"),
    (r"\bplaceholder\b|\bcannot be verified\b|\bnot verified\b", "internal_review_language"),
    (r"可能(?:为|适用|需要|存在)|may be unverified|subject to confirmation", "internal_review_language"),
]
PLACEHOLDER_PATTERNS = [
    (r"\[Brand\]|\[品牌\]|\{\{[^{}\n]{1,80}\}\}|\{[A-Za-z_][A-Za-z0-9_. -]{0,79}\}", "placeholder"),
    (r"\bTODO\b|\bTBD\b|\bTBC\b", "placeholder"),
]
COMMERCIAL_PATTERNS = [
    (r"[$€£¥]\s?\d+(?:[.,]\d{1,2})?", "price_or_currency"),
    (r"\b(?:USD|EUR|GBP|CAD|AUD|JPY|CNY)\s?\d+(?:[.,]\d{1,2})?\b", "price_or_currency"),
    (r"\b(?:coupon|discount|sale price|limited time|free shipping|free delivery|ships? from|sold by|buy box|in stock|out of stock|delivery date|arrives? by)\b", "commercial_or_offer"),
    (r"\b\d{1,3}%\s*(?:off|discount)\b", "commercial_or_offer"),
    (r"优惠券|折扣|促销|包邮|配送日期|卖家|购物车|Buy Box|库存", "commercial_or_offer"),
]
ASIN_PATTERN = re.compile(r"\bB0[A-Z0-9]{8}\b", re.IGNORECASE)


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold()


def iter_text_nodes(value: Any, path: str, *, allow_scalar: bool = True) -> Iterable[tuple[str, str]]:
    """Extract copy nodes while ignoring evidence/count/source metadata."""
    if isinstance(value, str):
        if allow_scalar and value.strip():
            yield path, value
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            yield from iter_text_nodes(item, f"{path}[{index}]", allow_scalar=allow_scalar)
        return
    if not isinstance(value, dict):
        return
    for key in sorted(value):
        item = value[key]
        child = f"{path}.{key}"
        if key in TEXT_KEYS:
            yield from iter_text_nodes(item, child, allow_scalar=True)
        elif isinstance(item, (dict, list)) and key in {"steps", "items", "modules", "sections", "bullets", "points"}:
            yield from iter_text_nodes(item, child, allow_scalar=False)


def customer_fields(record: dict[str, Any]) -> tuple[list[tuple[str, str, str]], list[dict[str, str]]]:
    fields = record.get("publishable_fields")
    if fields is None and isinstance(record.get("fields"), dict):
        fields = record["fields"]
    if fields is None and any(key in record for key in CUSTOMER_FIELD_KEYS):
        # Backward-compatible input form: the publishable-fields object itself.
        fields = {key: record[key] for key in CUSTOMER_FIELD_KEYS if key in record}
    if not isinstance(fields, dict):
        return [], [{"field": "publishable_fields", "code": "missing_publishable_fields", "message": "publishable_fields must be an object"}]

    findings: list[dict[str, str]] = []
    for key in sorted(set(fields) - set(CUSTOMER_FIELD_KEYS)):
        findings.append({
            "field": key, "path": f"publishable_fields.{key}", "code": "unknown_publishable_field",
            "message": "field is not in the customer-copy allowlist; classify it before publishing",
        })

    collected: list[tuple[str, str, str]] = []
    for key in CUSTOMER_FIELD_KEYS:
        if key not in fields:
            continue
        for path, text in iter_text_nodes(fields[key], f"publishable_fields.{key}"):
            label = FIELD_LABELS[key]
            if key in {"bullets", "bullet_points"}:
                match = re.search(r"\[(\d+)\]", path)
                label = f"Bullet {int(match.group(1)) + 1}" if match else "Bullet"
            collected.append((label, path, text))
    return collected, findings


def collect_forbidden_terms(record: dict[str, Any]) -> list[str]:
    terms: set[str] = set()
    for container in (record, record.get("context", {}), record.get("internal", {}), record.get("keyword_controls", {})):
        if not isinstance(container, dict):
            continue
        for key in ("competitor_brands", "competitor_asins", "forbidden_terms", "customer_copy_forbidden_terms"):
            value = container.get(key, [])
            values = [value] if isinstance(value, str) else value if isinstance(value, list) else []
            for item in values:
                if isinstance(item, dict):
                    item = item.get("term", "")
                term = str(item).strip()
                if term:
                    terms.add(term)
    return sorted(terms, key=lambda item: (normalize(item), item))


def excerpt(text: str, start: int, length: int = 80) -> str:
    left = max(0, start - 30)
    right = min(len(text), start + length)
    return text[left:right].replace("\n", " ")


def term_match(text: str, term: str) -> re.Match[str] | None:
    escaped = re.escape(term)
    if re.search(r"[A-Za-z0-9]", term) and not re.search(r"[\u4e00-\u9fff]", term):
        return re.search(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", text, re.IGNORECASE)
    return re.search(escaped, text, re.IGNORECASE)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Scan customer-facing Amazon listing copy deterministically.")
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

    fields, schema_findings = customer_fields(record)
    forbidden_terms = collect_forbidden_terms(record)
    findings: list[dict[str, str]] = list(schema_findings)
    for label, path, text in fields:
        normalized = normalize(text)
        for pattern, code in INTERNAL_PATTERNS + PLACEHOLDER_PATTERNS + COMMERCIAL_PATTERNS:
            match = re.search(pattern, normalized, re.IGNORECASE)
            if match:
                findings.append({"field": label, "path": path, "code": code, "match": match.group(0), "excerpt": excerpt(text, match.start())})
        asin_match = ASIN_PATTERN.search(text)
        if asin_match:
            findings.append({"field": label, "path": path, "code": "asin_in_customer_copy", "match": asin_match.group(0), "excerpt": excerpt(text, asin_match.start())})
        for term in forbidden_terms:
            match = term_match(text, term)
            if match:
                findings.append({"field": label, "path": path, "code": "forbidden_term", "match": term, "excerpt": excerpt(text, match.start(), len(term) + 40)})

    findings.sort(key=lambda item: (item.get("field", ""), item.get("path", ""), item.get("code", ""), item.get("match", "")))
    result = {
        "status": "PASS" if not findings else "FAIL",
        "scanned_fields": len(fields), "finding_count": len(findings), "findings": findings,
        "schema": {"allowed_customer_fields": list(CUSTOMER_FIELD_KEYS), "unknown_fields_fail": True},
        "rules": {
            "internal_review_language": "customer-facing fields must not contain internal evidence or review-status wording",
            "placeholders": "customer-facing fields must not contain placeholders",
            "commercial_or_offer": "customer-facing copy must not contain price, promotion, seller, logistics, or offer-state wording",
            "asin_in_customer_copy": "ASINs must not appear in customer-facing copy",
            "forbidden_term": "configured competitor brands and forbidden terms must not appear",
            "schema": "only explicit publishable customer-copy fields are scanned; unknown fields fail closed",
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
