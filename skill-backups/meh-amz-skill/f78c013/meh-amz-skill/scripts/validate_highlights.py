#!/usr/bin/env python3
"""Validate Amazon Highlights as a title-overflow phrase string."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any


WORD_RE = re.compile(r"[\wÀ-ÖØ-öø-ÿ]+", re.UNICODE)
SENTENCE_END = re.compile(r"[.!?。！？]\s*$")


def normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold()


def words(value: str) -> set[str]:
    return {token for token in WORD_RE.findall(normalize(value)) if len(token) > 1}


def add(findings: list[dict[str, Any]], code: str, path: str, message: str, **extra: Any) -> None:
    item: dict[str, Any] = {"code": code, "path": path, "message": message}
    item.update(extra)
    findings.append(item)


def title_values(fields: dict[str, Any]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for key in ("title", "title_a", "title_b"):
        value = fields.get(key)
        if isinstance(value, str) and value.strip():
            result.append((key, value.strip()))
    return result


def selected_title(fields: dict[str, Any], record: dict[str, Any], titles: list[tuple[str, str]]) -> tuple[str, str] | None:
    context = record.get("context")
    selected = context.get("selected_title_field") if isinstance(context, dict) else None
    if isinstance(selected, str):
        for key, value in titles:
            if key == selected:
                return key, value
    for key in ("title", "title_a", "title_b"):
        for title_key, value in titles:
            if title_key == key:
                return title_key, value
    return None


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Validate comma-separated Amazon Highlights.")
    parser.add_argument("json_path", type=Path)
    args = parser.parse_args()
    try:
        record = json.loads(args.json_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
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
    titles = title_values(fields)
    display_title = selected_title(fields, record, titles)
    highlight = fields.get("highlights")
    if highlight is None or (isinstance(highlight, str) and not highlight.strip()):
        result = {"status": "PASS", "finding_count": 0, "findings": [], "rules": {"optional": "Highlights may be omitted"}}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    path = "publishable_fields.highlights"
    if display_title is None:
        add(findings, "missing_title_for_highlights", path, "Highlights require a final title for display and overlap checks")
    if not isinstance(highlight, str):
        add(findings, "highlights_must_be_string", path, "Highlights must be one comma-separated phrase string")
        highlight_text = ""
    else:
        highlight_text = highlight.strip()
    if highlight_text:
        count = len(highlight_text)
        if count > 125:
            add(findings, "highlights_above_maximum", path, "Highlights must be no more than 125 characters", characters=count, maximum=125)
        if not re.search(r",", highlight_text):
            add(findings, "highlights_not_comma_separated", path, "Highlights must contain comma-separated phrases")
        phrases = [part.strip() for part in highlight_text.split(",")]
        if any(not phrase for phrase in phrases):
            add(findings, "empty_highlight_phrase", path, "comma-separated Highlights phrases must not be empty")
        if len(phrases) < 2:
            add(findings, "insufficient_highlight_phrases", path, "Highlights must contain at least two short phrases")
        for index, phrase in enumerate(phrases):
            if SENTENCE_END.search(phrase):
                add(findings, "complete_sentence_style", f"{path}[{index}]", "Highlights must be short phrases, not complete sentence-style text")
        for title_key, title in titles:
            overlap = words(highlight_text) & words(title)
            if overlap:
                add(findings, "title_word_overlap", path, "Highlights must not repeat words already used in the product title", title_field=title_key, words=", ".join(sorted(overlap)))
    findings.sort(key=lambda item: (item.get("path", ""), item.get("code", ""), item.get("title_field", "")))
    result = {
        "status": "PASS" if not findings else "FAIL",
        "finding_count": len(findings),
        "findings": findings,
        "measurements": {"characters": len(highlight_text) if highlight_text else 0, "phrases": len([x for x in highlight_text.split(",") if x.strip()]) if highlight_text else 0},
        "rules": {
            "display": "Highlights are allowed only when the final product title is under 75 characters",
            "format": "one string containing at least two comma-separated short phrases",
            "maximum": "125 characters including spaces and commas",
            "overlap": "no repeated words between Highlights and any final title field",
            "sentence_style": "terminal sentence punctuation is rejected",
        },
    }
    if display_title and len(display_title[1]) >= 75 and highlight_text:
        add(result["findings"], "highlights_not_displayable", path, "Highlights must be omitted when the selected product title reaches 75 characters", title_field=display_title[0], title_length=len(display_title[1]))
        result["finding_count"] = len(result["findings"])
        result["status"] = "FAIL"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
