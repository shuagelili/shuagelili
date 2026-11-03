#!/usr/bin/env python3
"""Preflight deterministic limits for saved customer-facing Listing fields."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


DEFAULT_LIMITS: dict[str, dict[str, Any]] = {
    "title": {"max": 75},
    "title_a": {"max": 75},
    "title_b": {"max": 75},
    "description": {"min": 1500, "max": 2000},
    "highlights": {"max": 125},
}
COUNT_UNITS = {"unicode_code_points", "utf8_bytes", "utf16_code_units"}
STANDARD_FIELDS = (
    "title", "title_a", "title_b", "highlights", "bullets", "bullet_points",
    "description", "frontend_keywords", "backend_keywords", "use_guide",
    "image_text", "a_plus_text",
)


def configure_stdout() -> None:
    stream = getattr(sys, "stdout", None)
    if stream is not None and hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


def add(findings: list[dict[str, Any]], code: str, path: str, message: str, **extra: Any) -> None:
    findings.append({"code": code, "path": path, "message": message, **extra})


def as_text(value: Any, path: str, findings: list[dict[str, Any]]) -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from as_text(item, f"{path}[{index}]", findings)
    elif isinstance(value, dict):
        for key in ("text", "copy", "content", "value", "body"):
            if isinstance(value.get(key), str):
                yield f"{path}.{key}", value[key]
                return
        add(findings, "unmeasurable_field", path, "customer-facing field must contain text or a text-bearing list/object")
    elif value is not None:
        add(findings, "invalid_field_type", path, "customer-facing field must be text, list, or text-bearing object")


def count_text(text: str, unit: str) -> int:
    if unit == "utf8_bytes":
        return len(text.encode("utf-8"))
    if unit == "utf16_code_units":
        return len(text.encode("utf-16-le")) // 2
    return len(text)


def resolve_limit(record: dict[str, Any], field: str, findings: list[dict[str, Any]]) -> dict[str, Any]:
    context = record.get("context")
    limits = context.get("limits", {}) if isinstance(context, dict) else {}
    configured = limits.get(field) if isinstance(limits, dict) else None
    if configured is None:
        configured = DEFAULT_LIMITS.get(field, {})
    if isinstance(configured, int) and not isinstance(configured, bool):
        configured = {"max": configured}
    if not isinstance(configured, dict):
        add(findings, "invalid_limit_config", f"context.limits.{field}", "limit must be an integer or an object with min/max")
        return {"count_unit": "unicode_code_points", "source_ref": None}

    result: dict[str, Any] = {key: configured[key] for key in ("min", "max") if key in configured}
    result["count_unit"] = configured.get("count_unit", "unicode_code_points")
    result["source_ref"] = configured.get("source_ref")
    for key in ("min", "max"):
        if key in result and (not isinstance(result[key], int) or isinstance(result[key], bool) or result[key] < 0):
            add(findings, "invalid_limit_value", f"context.limits.{field}.{key}", "limit values must be non-negative integers")
            result.pop(key)
    if result["count_unit"] not in COUNT_UNITS:
        add(findings, "invalid_count_unit", f"context.limits.{field}.count_unit", "count_unit must be unicode_code_points, utf8_bytes, or utf16_code_units")
        result["count_unit"] = "unicode_code_points"
    if "min" in result and "max" in result and result["min"] > result["max"]:
        add(findings, "invalid_limit_range", f"context.limits.{field}", "minimum must not exceed maximum", minimum=result["min"], maximum=result["max"])
        result.pop("min")
        result.pop("max")
    return result


def main() -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Preflight deterministic Listing field limits before rendering.")
    parser.add_argument("json_path", type=Path, help="UTF-8 listing_record.json")
    args = parser.parse_args()
    try:
        record = json.loads(args.json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    if not isinstance(record, dict):
        print(json.dumps({"status": "ERROR", "error": "JSON root must be an object"}, ensure_ascii=False, indent=2))
        return 2

    findings: list[dict[str, Any]] = []
    context = record.get("context")
    if not isinstance(context, dict) or not str(context.get("marketplace", "")).strip():
        add(findings, "missing_limit_marketplace", "context.marketplace", "resolve the target marketplace before field preflight")
    fields = record.get("publishable_fields")
    if not isinstance(fields, dict):
        add(findings, "missing_publishable_fields", "publishable_fields", "publishable_fields must be an object")
        fields = {}
    if not any(field in fields for field in ("title", "title_a", "title_b")):
        add(findings, "missing_title", "publishable_fields", "at least one title, title_a, or title_b is required")
    if "description" not in fields:
        add(findings, "missing_description", "publishable_fields.description", "product description is required")

    limit_map = context.get("limits", {}) if isinstance(context, dict) else {}
    field_names = list(dict.fromkeys([*STANDARD_FIELDS, *(limit_map.keys() if isinstance(limit_map, dict) else [])]))
    measurements: list[dict[str, Any]] = []
    for field in field_names:
        if field not in fields:
            continue
        limits = resolve_limit(record, field, findings)
        for path, text in as_text(fields[field], f"publishable_fields.{field}", findings):
            unit = limits["count_unit"]
            count = count_text(text, unit)
            measurements.append({
                "field": field, "path": path, "count": count, "count_unit": unit,
                "limits": {key: limits[key] for key in ("min", "max") if key in limits},
                "source_ref": limits.get("source_ref"),
            })
            if "min" in limits and count < limits["min"]:
                add(findings, "below_minimum", path, "field is shorter than the configured minimum", count=count, count_unit=unit, minimum=limits["min"])
            if "max" in limits and count > limits["max"]:
                add(findings, "above_maximum", path, "field exceeds the configured maximum", count=count, count_unit=unit, maximum=limits["max"])

    findings.sort(key=lambda item: (item.get("path", ""), item.get("code", "")))
    result = {
        "status": "PASS" if not findings else "FAIL", "stage": "pre_render_field_limits",
        "finding_count": len(findings), "findings": findings, "measurements": measurements,
        "rules": {
            "configured_limits": "context.limits.<field> supports integer max or min/max with count_unit and source_ref",
            "default_limits": "title 75, description 1500-2000, Highlights 125; other common fields are measured and limited when configured",
            "count_units": sorted(COUNT_UNITS),
            "fail_closed": "unresolved marketplace, malformed limits, and out-of-range counts fail preflight",
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
