#!/usr/bin/env python3
"""Validate deterministic character limits for customer-facing Listing fields."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


DEFAULT_LIMITS = {
    "title": {"max": 75},
    "title_a": {"max": 75},
    "title_b": {"max": 75},
    "description": {"min": 1500, "max": 2000},
    "highlights": {"max": 125},
}


def configure_stdout() -> None:
    stream = getattr(sys, "stdout", None)
    if stream is not None and hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


def add(findings: list[dict[str, Any]], code: str, path: str, message: str, **extra: Any) -> None:
    item: dict[str, Any] = {"code": code, "path": path, "message": message}
    item.update(extra)
    findings.append(item)


def as_text(value: Any, path: str, findings: list[dict[str, Any]]) -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            yield from as_text(item, f"{path}[{index}]", findings)
        return
    if isinstance(value, dict):
        for key in ("text", "copy", "content", "value", "body"):
            if isinstance(value.get(key), str):
                yield f"{path}.{key}", value[key]
                return
        add(findings, "unmeasurable_field", path, "customer-facing field must contain text or a text-bearing list/object")
        return
    if value is not None:
        add(findings, "invalid_field_type", path, "customer-facing field must be text, list, or text-bearing object")


def resolve_limit(record: dict[str, Any], field: str) -> dict[str, int]:
    limits: dict[str, Any] = {}
    context = record.get("context")
    if isinstance(context, dict) and isinstance(context.get("limits"), dict):
        limits = context["limits"]
    configured = limits.get(field)
    if isinstance(configured, int):
        return {"max": configured}
    if isinstance(configured, dict):
        result: dict[str, int] = {}
        for key in ("min", "max"):
            if isinstance(configured.get(key), int):
                result[key] = configured[key]
        return result or DEFAULT_LIMITS.get(field, {})
    return DEFAULT_LIMITS.get(field, {})


def main() -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Validate deterministic Listing character limits.")
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

    fields = record.get("publishable_fields")
    findings: list[dict[str, Any]] = []
    if not isinstance(fields, dict):
        add(findings, "missing_publishable_fields", "publishable_fields", "publishable_fields must be an object")
        fields = {}

    if not any(field in fields for field in ("title", "title_a", "title_b")):
        add(findings, "missing_title", "publishable_fields", "at least one title, title_a, or title_b is required")
    if "description" not in fields:
        add(findings, "missing_description", "publishable_fields.description", "product description is required")

    measurements: list[dict[str, Any]] = []
    for field in ("title", "title_a", "title_b", "description", "highlights"):
        if field not in fields:
            continue
        limits = resolve_limit(record, field)
        for path, text in as_text(fields[field], f"publishable_fields.{field}", findings):
            count = len(text)
            measurements.append({"field": field, "path": path, "characters": count, "limits": limits})
            if "min" in limits and count < limits["min"]:
                add(findings, "below_minimum", path, "field is shorter than the configured minimum", characters=count, minimum=limits["min"])
            if "max" in limits and count > limits["max"]:
                add(findings, "above_maximum", path, "field exceeds the configured maximum", characters=count, maximum=limits["max"])

    findings.sort(key=lambda item: (item.get("path", ""), item.get("code", "")))
    result = {
        "status": "PASS" if not findings else "FAIL",
        "finding_count": len(findings),
        "findings": findings,
        "measurements": measurements,
        "rules": {
            "description": "1500-2000 characters by default; context.limits.description overrides when explicitly supplied",
            "title": "75 characters maximum by default",
            "highlights": "125 characters maximum per text item by default",
            "counting": "Python Unicode code-point length of the saved UTF-8 text",
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
