#!/usr/bin/env python3
"""Validate that rendered HTML contains the approved publishable fields."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


FIELD_KEYS = {
    "title_a", "title_b", "title", "highlights", "bullets", "bullet_points",
    "description", "use_guide", "frontend_keywords", "backend_keywords",
    "image_text", "image_plan", "a_plus_text", "a_plus_modules",
}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
BLOCK_TAGS = {"address", "article", "blockquote", "div", "dl", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "li", "main", "ol", "p", "section", "table", "tr", "ul"}


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def normalize(value: str) -> str:
    value = html.unescape(value).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", value).strip().casefold()


def iter_copy(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(iter_copy(item))
        return result
    if isinstance(value, dict):
        for key in ("text", "copy", "content", "value", "body"):
            if isinstance(value.get(key), (str, list, dict)):
                return iter_copy(value[key])
    return []


class CopyFieldParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.active: list[tuple[int, str, list[str]]] = []
        self.fields: dict[str, str] = {}
        self.marker_counts: dict[str, int] = {}
        self.ignored = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        if tag.lower() in {"script", "style", "template"}:
            self.ignored += 1
        marker = attrs_map.get("data-copy-field")
        if tag.lower() in VOID_TAGS:
            return
        if tag.lower() in BLOCK_TAGS:
            for _, _, chunks in self.active:
                chunks.append(" ")
        self.depth += 1
        if marker:
            self.marker_counts[marker] = self.marker_counts.get(marker, 0) + 1
            self.active.append((self.depth, marker, []))

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in VOID_TAGS:
            return
        if self.active and self.active[-1][0] == self.depth:
            depth, marker, chunks = self.active.pop()
            self.fields[marker] = normalize(" ".join(chunks))
        if tag.lower() in BLOCK_TAGS:
            for _, _, chunks in self.active:
                chunks.append(" ")
        if tag.lower() in {"script", "style", "template"} and self.ignored:
            self.ignored -= 1
        self.depth = max(0, self.depth - 1)

    def handle_data(self, data: str) -> None:
        if self.ignored:
            return
        for index in range(len(self.active)):
            self.active[index][2].append(data)


def main() -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Validate approved Listing copy against rendered HTML.")
    parser.add_argument("json_path", type=Path)
    parser.add_argument("html_path", type=Path)
    args = parser.parse_args()
    try:
        record = json.loads(args.json_path.read_text(encoding="utf-8"))
        html_text = args.html_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    if not isinstance(record, dict):
        print(json.dumps({"status": "ERROR", "error": "JSON root must be an object"}, ensure_ascii=False, indent=2))
        return 2
    fields = record.get("publishable_fields")
    findings: list[dict[str, str]] = []
    if not isinstance(fields, dict):
        findings.append({"code": "missing_publishable_fields", "path": "publishable_fields", "message": "publishable_fields must be an object"})
        fields = {}
    parser_obj = CopyFieldParser()
    parser_obj.feed(html_text)
    rendered = parser_obj.fields
    for marker, count in sorted(parser_obj.marker_counts.items()):
        if count > 1:
            findings.append({"code": "duplicate_render_marker", "path": marker, "message": "each publishable field must have exactly one data-copy-field marker", "count": str(count)})
    for key, value in fields.items():
        if key not in FIELD_KEYS:
            findings.append({"code": "unknown_publishable_field", "path": f"publishable_fields.{key}", "message": "field is not in the render contract"})
            continue
        marker = f"publishable_fields.{key}"
        if marker not in rendered:
            findings.append({"code": "missing_render_marker", "path": marker, "message": "HTML must contain data-copy-field marker"})
            continue
        visible = rendered[marker]
        expected_text = normalize(" ".join(iter_copy(value)))
        if expected_text != visible:
            findings.append({"code": "rendered_copy_mismatch", "path": marker, "message": "marked HTML field must exactly match approved publishable text; added, changed, or missing text is not allowed"})
    findings.sort(key=lambda item: (item["path"], item["code"]))
    result = {
        "status": "PASS" if not findings else "FAIL",
        "finding_count": len(findings),
        "findings": findings,
        "rendered_fields": sorted(rendered),
        "rules": {
            "marker": "each populated publishable field must use data-copy-field=publishable_fields.<name>",
            "source_of_truth": "rendered HTML must contain the final text from listing_record.publishable_fields",
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
