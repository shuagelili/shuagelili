#!/usr/bin/env python3
"""Validate the exact five-bullet customer-copy format."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


FORMAT = re.compile(r"^【([^】]+)】 : (.+)$", re.DOTALL)


def add(findings: list[dict[str, str]], code: str, path: str, message: str, **extra: str) -> None:
    item = {"code": code, "path": path, "message": message}
    item.update(extra)
    findings.append(item)


def uppercase_header(header: str) -> bool:
    # For scripts without letter case, upper() is unchanged and therefore valid.
    return header == header.upper()


def parse_bullet(value: Any, path: str, findings: list[dict[str, str]]) -> str:
    if isinstance(value, str):
        match = FORMAT.fullmatch(value.strip())
        if not match:
            add(findings, "invalid_bullet_format", path, "bullet must match 【UPPERCASE HEADER】 : content")
            return ""
        header, body = match.groups()
    elif isinstance(value, dict):
        rendered = value.get("text") or value.get("content") or value.get("copy")
        header_value = value.get("header")
        if isinstance(rendered, str) and FORMAT.fullmatch(rendered.strip()):
            match = FORMAT.fullmatch(rendered.strip())
            assert match is not None
            header, body = match.groups()
        else:
            header = str(header_value or "").strip()
            if header.startswith("【") and header.endswith("】"):
                header = header[1:-1].strip()
            body = str(rendered or "").strip()
            if not header or not body:
                add(findings, "incomplete_bullet_object", path, "structured bullet requires header and text/content/copy")
                return ""
    else:
        add(findings, "invalid_bullet_type", path, "bullet must be a string or structured object")
        return ""

    if not uppercase_header(header):
        add(findings, "bullet_header_not_uppercase", path, "all cased letters inside 【】 must be uppercase", header=header)
    if not body.strip():
        add(findings, "empty_bullet_content", path, "bullet content must not be empty")
    return header


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Validate Amazon five-bullet formatting deterministically.")
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
    fields = record.get("publishable_fields") if isinstance(record.get("publishable_fields"), dict) else record
    bullets = fields.get("bullets") if isinstance(fields, dict) else None
    if bullets is None and isinstance(fields, dict):
        bullets = fields.get("bullet_points")
    findings: list[dict[str, str]] = []
    if not isinstance(bullets, list):
        add(findings, "missing_bullets", "publishable_fields.bullets", "bullets must be a list")
        bullets = []
    if len(bullets) != 5:
        add(findings, "bullet_count", "publishable_fields.bullets", "exactly five bullets are required", count=str(len(bullets)))
    headers: dict[str, int] = {}
    for index, bullet in enumerate(bullets):
        header = parse_bullet(bullet, f"publishable_fields.bullets[{index}]", findings)
        key = header.casefold().strip()
        if key:
            if key in headers:
                add(findings, "duplicate_bullet_header", f"publishable_fields.bullets[{index}]", "bullet headers must be distinct", previous_index=str(headers[key]))
            headers[key] = index
    findings.sort(key=lambda item: (item.get("path", ""), item.get("code", ""), item.get("header", "")))
    result = {
        "status": "PASS" if not findings else "FAIL",
        "finding_count": len(findings),
        "findings": findings,
        "rules": {"format": "【UPPERCASE HEADER】 : content", "count": "exactly five bullets"},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
