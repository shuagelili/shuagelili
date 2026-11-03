#!/usr/bin/env python3
"""Validate product facts and competitor-attribute isolation.

The validator is intentionally deterministic. It checks that publishable copy
is linked to an explicit product fact and evidence, and that competitor-only
evidence/facts never authorize a customer-facing field.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


EVIDENCE_REQUIRED = ("id", "claim", "value", "source_type", "source_ref", "scope", "status")
FACT_REQUIRED = ("id", "attribute", "value", "ownership", "source_evidence_ids", "status", "disposition")
VALID_SOURCE_TYPES = {"user", "authoritative_page", "workbook", "health_snapshot", "competitor", "inference"}
VALID_SCOPES = {"product", "variant", "offer", "marketplace", "competitor"}
VALID_STATUSES = {"verified", "calculated", "inferred", "to_confirm"}
VALID_OWNERSHIP = {"own", "shared", "competitor_only", "unknown"}
VALID_DISPOSITIONS = {"publishable", "analysis_only", "to_confirm"}
CUSTOMER_FIELDS = {
    "title_a", "title_b", "title", "highlights", "bullets", "bullet_points",
    "description", "use_guide", "frontend_keywords", "backend_keywords",
    "image_text", "image_plan", "a_plus_text", "a_plus_modules",
}


def issue(code: str, path: str, message: str, **extra: str) -> dict[str, str]:
    result = {"code": code, "path": path, "message": message}
    result.update(extra)
    return result


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def iter_dicts(value: Any, path: str) -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        yield path, value
        for key in sorted(value):
            yield from iter_dicts(value[key], f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from iter_dicts(item, f"{path}[{index}]")


def ids_at(value: Any, keys: set[str]) -> set[str]:
    found: set[str] = set()
    for _, item in iter_dicts(value, "$"):
        for key in keys:
            raw = item.get(key)
            for identifier in as_list(raw):
                if isinstance(identifier, str) and identifier.strip():
                    found.add(identifier.strip())
    return found


def field_key(path: str) -> str:
    path = path.split(".", 2)[-1]
    return path.split("[", 1)[0]


def allowed_for_field(allowed: Any, path: str) -> bool:
    values = [str(item).strip() for item in as_list(allowed) if str(item).strip()]
    if "*" in values:
        return True
    key = field_key(path)
    return any(item == key or item == path or path.startswith(item + ".") for item in values)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Validate product facts and competitor-attribute isolation.")
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
    evidence_entries = record.get("evidence_ledger")
    fact_entries = record.get("product_fact_ledger")
    if not isinstance(evidence_entries, list):
        findings.append(issue("missing_evidence_ledger", "evidence_ledger", "evidence_ledger must be a list"))
        evidence_entries = []
    if not isinstance(fact_entries, list):
        findings.append(issue("missing_product_fact_ledger", "product_fact_ledger", "product_fact_ledger must be a list"))
        fact_entries = []

    evidence_by_id: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(evidence_entries):
        path = f"evidence_ledger[{index}]"
        if not isinstance(entry, dict):
            findings.append(issue("invalid_evidence_entry", path, "evidence entry must be an object"))
            continue
        missing = [key for key in EVIDENCE_REQUIRED if key not in entry]
        if missing:
            findings.append(issue("missing_evidence_field", path, "required evidence fields are missing", fields=",".join(missing)))
        identifier = str(entry.get("id", "")).strip()
        if not identifier:
            findings.append(issue("missing_evidence_id", path, "evidence id is required"))
            continue
        if identifier in evidence_by_id:
            findings.append(issue("duplicate_evidence_id", path, "evidence id must be unique", id=identifier))
        evidence_by_id[identifier] = entry
        if entry.get("source_type") not in VALID_SOURCE_TYPES:
            findings.append(issue("invalid_evidence_source_type", path, "unsupported source_type", value=str(entry.get("source_type"))))
        if entry.get("scope") not in VALID_SCOPES:
            findings.append(issue("invalid_evidence_scope", path, "unsupported scope", value=str(entry.get("scope"))))
        if entry.get("status") not in VALID_STATUSES:
            findings.append(issue("invalid_evidence_status", path, "unsupported status", value=str(entry.get("status"))))

    fact_by_id: dict[str, dict[str, Any]] = {}
    for index, fact in enumerate(fact_entries):
        path = f"product_fact_ledger[{index}]"
        if not isinstance(fact, dict):
            findings.append(issue("invalid_product_fact", path, "product fact must be an object"))
            continue
        missing = [key for key in FACT_REQUIRED if key not in fact]
        if missing:
            findings.append(issue("missing_product_fact_field", path, "required product fact fields are missing", fields=",".join(missing)))
        identifier = str(fact.get("id", "")).strip()
        if not identifier:
            findings.append(issue("missing_product_fact_id", path, "product fact id is required"))
            continue
        if identifier in fact_by_id:
            findings.append(issue("duplicate_product_fact_id", path, "product fact id must be unique", id=identifier))
        fact_by_id[identifier] = fact
        ownership = fact.get("ownership")
        disposition = fact.get("disposition")
        if ownership not in VALID_OWNERSHIP:
            findings.append(issue("invalid_fact_ownership", path, "unsupported ownership", value=str(ownership)))
        if disposition not in VALID_DISPOSITIONS:
            findings.append(issue("invalid_fact_disposition", path, "unsupported disposition", value=str(disposition)))
        if fact.get("status") not in VALID_STATUSES:
            findings.append(issue("invalid_fact_status", path, "unsupported status", value=str(fact.get("status"))))
        for evidence_id in as_list(fact.get("source_evidence_ids")):
            evidence_id = str(evidence_id).strip()
            if evidence_id and evidence_id not in evidence_by_id:
                findings.append(issue("unknown_fact_evidence", path, "product fact references an unknown evidence id", id=evidence_id))
            if evidence_id in evidence_by_id:
                evidence = evidence_by_id[evidence_id]
                if evidence.get("scope") == "competitor" or evidence.get("source_type") == "competitor":
                    if ownership != "competitor_only":
                        findings.append(issue("competitor_evidence_misclassified", path, "competitor evidence must produce competitor_only ownership", id=evidence_id))

    publishable = record.get("publishable_fields")
    if not isinstance(publishable, dict):
        findings.append(issue("missing_publishable_fields", "publishable_fields", "publishable_fields must be an object"))
        publishable = {}
    claim_map = record.get("publishable_claim_map")
    if claim_map is not None and not isinstance(claim_map, list):
        findings.append(issue("invalid_publishable_claim_map", "publishable_claim_map", "publishable_claim_map must be a list"))
        claim_map = []

    links_by_path: dict[str, dict[str, set[str]]] = {}
    for index, link in enumerate(claim_map or []):
        path = f"publishable_claim_map[{index}]"
        if not isinstance(link, dict) or not link.get("field_path"):
            findings.append(issue("invalid_claim_link", path, "claim link requires field_path"))
            continue
        field_path = str(link["field_path"])
        if field_path in links_by_path:
            findings.append(issue("duplicate_claim_link", path, "field_path must appear only once", field_path=field_path))
        links_by_path[field_path] = {
            "evidence_ids": {str(x).strip() for x in as_list(link.get("evidence_ids")) if str(x).strip()},
            "fact_ids": {str(x).strip() for x in as_list(link.get("fact_ids")) if str(x).strip()},
        }

    used_fact_ids: set[str] = set()
    for key, value in publishable.items():
        if key not in CUSTOMER_FIELDS:
            findings.append(issue("unknown_publishable_field", f"publishable_fields.{key}", "customer field is not in the allowlist"))
        path = f"publishable_fields.{key}"
        link = links_by_path.get(path)
        if link is None:
            findings.append(issue("missing_claim_map_entry", path, "publishable field requires an explicit publishable_claim_map entry"))
        evidence_ids = set(link["evidence_ids"]) if link else ids_at(value, {"evidence_ids", "evidence_id"})
        fact_ids = set(link["fact_ids"]) if link else ids_at(value, {"fact_ids", "product_fact_ids", "product_fact_id"})
        used_fact_ids.update(fact_ids)
        if not evidence_ids or not fact_ids:
            findings.append(issue("missing_publishable_claim_links", path, "each publishable field requires evidence_ids and fact_ids"))
        for evidence_id in sorted(evidence_ids):
            evidence = evidence_by_id.get(evidence_id)
            if evidence is None:
                findings.append(issue("unknown_publishable_evidence", path, "publishable field references unknown evidence id", id=evidence_id))
            elif evidence.get("scope") == "competitor" or evidence.get("source_type") == "competitor":
                findings.append(issue("competitor_evidence_in_customer_field", path, "competitor evidence cannot authorize customer-facing copy", id=evidence_id))
        for fact_id in sorted(fact_ids):
            fact = fact_by_id.get(fact_id)
            if fact is None:
                findings.append(issue("unknown_publishable_fact", path, "publishable field references unknown product fact id", id=fact_id))
                continue
            if fact.get("ownership") == "competitor_only" or fact.get("disposition") == "analysis_only":
                findings.append(issue("competitor_only_fact_in_customer_field", path, "competitor-only or analysis-only fact cannot enter customer-facing copy", id=fact_id))
            if fact.get("status") in {"inferred", "to_confirm"}:
                findings.append(issue("unverified_fact_in_customer_field", path, "inferred or to_confirm product fact cannot authorize customer-facing copy", id=fact_id))
            if not allowed_for_field(fact.get("customer_fields_allowed"), key):
                findings.append(issue("fact_not_allowed_in_customer_field", path, "product fact does not authorize this customer field", id=fact_id))

    for fact_id, fact in sorted(fact_by_id.items()):
        if fact.get("disposition") == "publishable" and fact_id not in used_fact_ids:
            findings.append(issue("unmapped_publishable_fact", f"product_fact_ledger.{fact_id}", "publishable product fact is not linked to any customer field", id=fact_id))

    findings.sort(key=lambda item: (item.get("path", ""), item.get("code", ""), item.get("id", ""), item.get("message", "")))
    result = {
        "status": "PASS" if not findings else "FAIL",
        "finding_count": len(findings),
        "findings": findings,
        "counts": {"evidence": len(evidence_by_id), "product_facts": len(fact_by_id), "claim_links": len(links_by_path)},
        "rules": {
            "fact_ledger": "every product fact has an owner, disposition, status, and evidence links",
            "publishable_links": "every customer-facing field has product fact and evidence links",
            "competitor_isolation": "competitor-scoped evidence and competitor-only facts cannot authorize customer-facing copy",
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
