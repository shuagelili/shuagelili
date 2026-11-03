#!/usr/bin/env python3
"""Validate keyword placement, bullet strategy, voice map, backend terms, and attributes."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable


VOICE_TYPES = {"product_identity", "audience", "usage", "contents_or_compatibility"}
TITLE_ALTERNATIVE_REASONS = {
    "not_relevant_to_product", "awkward_localization", "unsupported_claim",
    "redundant_with_selected_term", "title_length_or_readability",
    "marketplace_language_mismatch", "other",
}
FIELD_KEYS = {"title", "title_a", "title_b", "highlights", "bullets", "bullet_points", "description", "use_guide", "frontend_keywords", "backend_keywords", "image_text", "image_plan", "a_plus_text", "a_plus_modules"}
STOPWORDS = {"a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "into", "is", "it", "of", "on", "or", "the", "this", "to", "with", "de", "des", "du", "la", "le", "les", "un", "une", "et", "pour", "avec", "en", "sur"}


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).casefold()
    return "".join(ch for ch in value if not unicodedata.combining(ch))


def tokens(value: str) -> list[str]:
    return re.findall(r"[\w]+", norm(value), flags=re.UNICODE)


def term_in_text(term: str, text: str) -> bool:
    phrase = tokens(term)
    haystack = tokens(text)
    if not phrase or len(phrase) > len(haystack):
        return False
    return any(haystack[i:i + len(phrase)] == phrase for i in range(len(haystack) - len(phrase) + 1))


def strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        if value.strip():
            yield value.strip()
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for key in ("text", "copy", "content", "value", "body"):
            if key in value:
                yield from strings(value[key])


def bullet_body(value: Any) -> str:
    text = value if isinstance(value, str) else next(iter(strings(value)), "")
    match = re.fullmatch(r"\s*【[^】]+】 : (.+?)\s*", text, flags=re.DOTALL)
    return match.group(1) if match else ""


def add(findings: list[dict[str, str]], code: str, path: str, message: str, **extra: str) -> None:
    item = {"code": code, "path": path, "message": message}
    item.update(extra)
    findings.append(item)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Validate listing keyword, copy-plan, voice-answer, and attribute coverage.")
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
    fields = record.get("publishable_fields") if isinstance(record.get("publishable_fields"), dict) else {}
    keyword_strategy = record.get("keyword_strategy")
    if not isinstance(keyword_strategy, dict) or keyword_strategy.get("status") not in {"complete", "not_available"}:
        add(findings, "missing_keyword_strategy", "keyword_strategy", "status must be complete or not_available")
        keyword_strategy = {}
    keywords = keyword_strategy.get("keywords", [])
    if not isinstance(keywords, list):
        add(findings, "invalid_keyword_list", "keyword_strategy.keywords", "keywords must be a list")
        keywords = []
    keyword_by_id: dict[str, dict[str, Any]] = {}
    product_facts = record.get("product_fact_ledger", [])
    if not isinstance(product_facts, list):
        product_facts = []
    fact_by_id = {str(item.get("id")): item for item in product_facts if isinstance(item, dict) and item.get("id")}
    evidence_ledger = record.get("evidence_ledger", [])
    if not isinstance(evidence_ledger, list):
        evidence_ledger = []
    evidence_ids = {str(item.get("id")) for item in evidence_ledger if isinstance(item, dict) and item.get("id")}
    seen_terms: set[str] = set()
    source_ledger = record.get("keyword_source_ledger")
    source_by_id: dict[str, dict[str, Any]] = {}
    if strategy_status := keyword_strategy.get("status"):
        if strategy_status == "complete":
            if not isinstance(source_ledger, list) or not source_ledger:
                add(findings, "missing_keyword_source_ledger", "keyword_source_ledger", "complete keyword strategy requires row-level source and processing records")
                source_ledger = []
            for index, candidate in enumerate(source_ledger):
                path = f"keyword_source_ledger[{index}]"
                if not isinstance(candidate, dict):
                    add(findings, "invalid_keyword_source_candidate", path, "source candidate must be an object")
                    continue
                candidate_id = str(candidate.get("candidate_id", "")).strip()
                required = ("raw_term", "normalized_term", "source_type", "source_ref", "evidence_ids", "marketplace", "metric", "brand_terms_detected", "brand_terms_removed", "canonical_keyword_id", "duplicate_action", "eligibility", "decision_reason", "selected_fields")
                missing = [key for key in required if key not in candidate]
                if not candidate_id or candidate_id in source_by_id:
                    add(findings, "invalid_keyword_candidate_id", f"{path}.candidate_id", "candidate_id is required and must be unique")
                if missing:
                    add(findings, "incomplete_keyword_source_candidate", path, "source candidate is missing required traceability fields", missing=", ".join(missing))
                if not str(candidate.get("raw_term", "")).strip():
                    add(findings, "keyword_source_without_raw_term", f"{path}.raw_term", "preserve the exact term as supplied by the source")
                if not str(candidate.get("normalized_term", "")).strip():
                    add(findings, "keyword_source_without_normalized_term", f"{path}.normalized_term", "record the normalized form used for comparison and deduplication")
                if not str(candidate.get("source_ref", "")).strip() or not str(candidate.get("source_type", "")).strip():
                    add(findings, "keyword_source_without_location", path, "record source type and a pinpoint source reference such as workbook, sheet, and row")
                if not str(candidate.get("marketplace", "")).strip():
                    add(findings, "keyword_source_without_marketplace", f"{path}.marketplace", "record the marketplace or mark it unknown with a decision reason")
                metric = candidate.get("metric")
                if not isinstance(metric, dict) or not all(str(metric.get(key, "")).strip() for key in ("name", "unit", "period")) or "value" not in metric:
                    add(findings, "incomplete_keyword_metric_context", f"{path}.metric", "record metric name, value, unit, and reporting period; use null when unavailable")
                if candidate.get("duplicate_action") not in {"canonical", "merged_into", "excluded"}:
                    add(findings, "invalid_keyword_duplicate_action", f"{path}.duplicate_action", "use canonical, merged_into, or excluded")
                if not str(candidate.get("decision_reason", "")).strip():
                    add(findings, "keyword_candidate_without_decision_reason", f"{path}.decision_reason", "record why the candidate was retained, merged, or excluded")
                if not isinstance(candidate.get("evidence_ids"), list) or not candidate.get("evidence_ids") or not set(map(str, candidate.get("evidence_ids", []))).issubset(evidence_ids):
                    add(findings, "keyword_source_missing_evidence", f"{path}.evidence_ids", "source candidate must link to valid evidence ledger IDs")
                if not isinstance(candidate.get("selected_fields"), list):
                    add(findings, "invalid_keyword_field_placement", f"{path}.selected_fields", "selected_fields must be a list; use an empty list when not placed")
                if candidate_id:
                    source_by_id[candidate_id] = candidate
    for index, item in enumerate(keywords):
        path = f"keyword_strategy.keywords[{index}]"
        if not isinstance(item, dict):
            add(findings, "invalid_keyword_entry", path, "keyword entry must be an object")
            continue
        identifier = str(item.get("id", "")).strip()
        term = str(item.get("term", "")).strip()
        source_ref = str(item.get("source_ref", "")).strip()
        if not identifier or not term or not source_ref:
            add(findings, "incomplete_keyword_entry", path, "id, term, and source_ref are required")
            continue
        key = " ".join(tokens(term))
        if identifier in keyword_by_id:
            add(findings, "duplicate_keyword_id", path, "keyword id must be unique", id=identifier)
        if key in seen_terms:
            add(findings, "duplicate_keyword_term", path, "normalized keyword term must be unique", term=term)
        seen_terms.add(key)
        keyword_by_id[identifier] = item
        candidate_ids = item.get("source_candidate_ids")
        if not isinstance(candidate_ids, list) or not candidate_ids:
            add(findings, "keyword_missing_source_candidate_link", f"{path}.source_candidate_ids", "each retained keyword must link to one or more source candidate IDs")
            candidate_ids = []
        else:
            for candidate_id in map(str, candidate_ids):
                candidate = source_by_id.get(candidate_id)
                if not candidate:
                    add(findings, "keyword_source_candidate_not_found", f"{path}.source_candidate_ids", "keyword references an unknown source candidate", candidate_id=candidate_id)
                elif str(candidate.get("canonical_keyword_id", "")) != identifier:
                    add(findings, "keyword_canonical_link_mismatch", f"keyword_source_ledger[{candidate_id}].canonical_keyword_id", "source candidate must point back to this canonical keyword", keyword_id=identifier)
                elif candidate.get("duplicate_action") not in {"canonical", "merged_into"}:
                    add(findings, "excluded_candidate_linked_as_keyword", f"keyword_source_ledger[{candidate_id}].duplicate_action", "excluded candidates cannot support a retained keyword")
                if candidate:
                    metric = candidate.get("metric")
                    if isinstance(metric, dict) and metric.get("name") == "search_volume" and isinstance(metric.get("value"), (int, float)) and item.get("search_volume") != metric.get("value"):
                        add(findings, "keyword_metric_value_mismatch", f"{path}.search_volume", "retained keyword demand must match its linked source record", candidate_id=candidate_id)
        demand_source_id = str(item.get("demand_source_candidate_id", "")).strip()
        if not demand_source_id or demand_source_id not in list(map(str, candidate_ids)):
            add(findings, "keyword_missing_demand_source", f"{path}.demand_source_candidate_id", "identify which linked source row supplies the selected demand metric")
        else:
            demand_source = source_by_id.get(demand_source_id)
            demand_metric = demand_source.get("metric", {}) if isinstance(demand_source, dict) else {}
            if not isinstance(demand_metric, dict) or demand_metric.get("name") != "search_volume" or demand_metric.get("value") != item.get("search_volume"):
                add(findings, "keyword_demand_source_mismatch", f"{path}.demand_source_candidate_id", "selected demand source must provide the recorded search_volume value")
        volume = item.get("search_volume")
        if volume is not None and (not isinstance(volume, (int, float)) or isinstance(volume, bool) or not math.isfinite(volume) or volume < 0):
            add(findings, "invalid_search_volume", path, "search_volume must be a non-negative number or null")
        if item.get("eligible") is True and volume is None:
            add(findings, "missing_keyword_demand", path, "eligible keyword requires a measured search_volume")
        if item.get("eligible") is True:
            fact_ids = item.get("product_fact_ids", [])
            if not isinstance(fact_ids, list) or not fact_ids:
                add(findings, "keyword_missing_product_fact", path, "eligible keyword requires supporting own-product fact IDs")
            else:
                for fact_id in fact_ids:
                    fact = fact_by_id.get(str(fact_id))
                    if not fact or fact.get("ownership") not in {"own", "shared"} or fact.get("status") in {"inferred", "to_confirm"}:
                        add(findings, "keyword_unsupported_by_product", path, "eligible keyword must map to a verified own-product fact", fact_id=str(fact_id))

    strategy_status = keyword_strategy.get("status")
    if strategy_status == "complete":
        primary_id = str(keyword_strategy.get("primary_keyword_id", "")).strip()
        primary = keyword_by_id.get(primary_id)
        title_selection = keyword_strategy.get("title_selection")
        title_selection_path = "keyword_strategy.title_selection"
        if not isinstance(title_selection, dict):
            add(findings, "missing_title_selection_review", title_selection_path, "record the human-reviewed relevance and naturalness decision for the title keyword")
            title_selection = {}
        if title_selection.get("review_status") != "human_reviewed":
            add(findings, "title_selection_not_human_reviewed", f"{title_selection_path}.review_status", "title relevance and naturalness require explicit human review")
        if str(title_selection.get("selected_keyword_id", "")).strip() != primary_id:
            add(findings, "title_selection_primary_mismatch", f"{title_selection_path}.selected_keyword_id", "selected_keyword_id must match keyword_strategy.primary_keyword_id")
        selected_fit = title_selection.get("selected_fit")
        if not isinstance(selected_fit, dict) or selected_fit.get("relevance") != "relevant" or selected_fit.get("naturalness") != "natural":
            add(findings, "selected_title_keyword_fails_fit", f"{title_selection_path}.selected_fit", "the selected title keyword must be reviewed as relevant and natural")
        if not str(title_selection.get("selection_rationale", "")).strip():
            add(findings, "missing_title_selection_rationale", f"{title_selection_path}.selection_rationale", "explain why this keyword best fits the title while prioritizing demand")

        alternatives = title_selection.get("higher_demand_terms_not_selected", [])
        if not isinstance(alternatives, list):
            add(findings, "invalid_title_alternatives", f"{title_selection_path}.higher_demand_terms_not_selected", "higher_demand_terms_not_selected must be a list")
            alternatives = []
        alternatives_by_candidate: dict[str, dict[str, Any]] = {}
        for index, alternative in enumerate(alternatives):
            path = f"{title_selection_path}.higher_demand_terms_not_selected[{index}]"
            if not isinstance(alternative, dict):
                add(findings, "invalid_title_alternative", path, "each alternative must be an object")
                continue
            candidate_id = str(alternative.get("candidate_id", "")).strip()
            candidate = source_by_id.get(candidate_id)
            if not candidate_id or candidate_id in alternatives_by_candidate or not candidate:
                add(findings, "invalid_title_alternative_candidate", f"{path}.candidate_id", "candidate_id must reference a unique keyword source row")
                continue
            alternatives_by_candidate[candidate_id] = alternative
            if alternative.get("title_relevance") not in {"relevant", "partially_relevant", "not_relevant"}:
                add(findings, "missing_alternative_relevance_review", f"{path}.title_relevance", "record the human assessment of title relevance")
            if alternative.get("naturalness") not in {"natural", "awkward"}:
                add(findings, "missing_alternative_naturalness_review", f"{path}.naturalness", "record whether the phrase reads naturally in the target marketplace")
            if alternative.get("reason_code") not in TITLE_ALTERNATIVE_REASONS or not str(alternative.get("reason", "")).strip():
                add(findings, "missing_alternative_reason", path, "provide a reason code and explanation for not selecting this higher-demand term")

        if not primary:
            add(findings, "missing_primary_keyword", "keyword_strategy.primary_keyword_id", "complete keyword strategy requires a valid primary keyword")
        elif primary.get("eligible") is not True:
            add(findings, "ineligible_primary_keyword", "keyword_strategy.primary_keyword_id", "primary keyword must be marked eligible")
        else:
            title = next((str(fields[k]) for k in ("title", "title_a", "title_b") if isinstance(fields.get(k), str)), "")
            if title and not term_in_text(str(primary.get("term", "")), title):
                add(findings, "primary_keyword_missing_from_title", "publishable_fields.title", "selected title keyword phrase must appear in the title", keyword=str(primary.get("term", "")))

            def metric_group(candidate: dict[str, Any]) -> tuple[Any, ...]:
                metric = candidate.get("metric", {})
                source_family = str(candidate.get("source_ref", "")).split(":", 1)[0]
                return (
                    candidate.get("marketplace"), metric.get("name"), metric.get("unit"),
                    metric.get("period"), metric.get("scope"), metric.get("comparison_group", source_family),
                )

            primary_source = source_by_id.get(str(primary.get("demand_source_candidate_id", "")))
            required_alternative_ids: set[str] = set()
            if primary_source and isinstance(primary.get("search_volume"), (int, float)):
                for candidate_id, candidate in source_by_id.items():
                    metric = candidate.get("metric", {})
                    value = metric.get("value") if isinstance(metric, dict) else None
                    if (
                        candidate.get("canonical_keyword_id") != primary_id
                        and candidate.get("duplicate_action") != "excluded"
                        and isinstance(value, (int, float)) and not isinstance(value, bool)
                        and metric_group(candidate) == metric_group(primary_source)
                        and value > primary["search_volume"]
                    ):
                        required_alternative_ids.add(candidate_id)
            missing_alternatives = sorted(required_alternative_ids - set(alternatives_by_candidate))
            for candidate_id in missing_alternatives:
                add(findings, "higher_demand_term_without_reason", title_selection_path, "each comparable higher-demand source term must have a documented title decision", candidate_id=candidate_id)
        required_frontend_ids = keyword_strategy.get("required_frontend_keyword_ids", [])
        if not isinstance(required_frontend_ids, list):
            add(findings, "invalid_required_frontend_keyword_ids", "keyword_strategy.required_frontend_keyword_ids", "required_frontend_keyword_ids must be a list")
            required_frontend_ids = []
        frontend_copy = " ".join([str(fields.get("title", fields.get("title_a", fields.get("title_b", ""))))] + [bullet_body(item) for item in fields.get("bullets", []) if isinstance(fields.get("bullets"), list)])
        for keyword_id in required_frontend_ids:
            keyword = keyword_by_id.get(str(keyword_id))
            if not keyword or keyword.get("eligible") is not True:
                add(findings, "invalid_required_frontend_keyword", "keyword_strategy.required_frontend_keyword_ids", "required frontend keyword must be eligible and present in keyword_strategy", id=str(keyword_id))
            elif not term_in_text(str(keyword.get("term", "")), frontend_copy):
                add(findings, "required_frontend_keyword_unused", "publishable_fields.title", "selected high-demand frontend keyword must appear in the title or one of the five bullets", keyword=str(keyword.get("term", "")))
    elif strategy_status == "not_available" and not str(keyword_strategy.get("reason", "")).strip():
        add(findings, "keyword_unavailability_unexplained", "keyword_strategy.reason", "record why keyword volume data is unavailable")

    bullets = fields.get("bullets", fields.get("bullet_points"))
    plans = record.get("bullet_copy_plan")
    if not isinstance(bullets, list) or len(bullets) != 5:
        add(findings, "missing_five_bullets", "publishable_fields.bullets", "five bullets are required for strategy validation")
        bullets = bullets if isinstance(bullets, list) else []
    if not isinstance(plans, list) or len(plans) != 5:
        add(findings, "missing_bullet_copy_plan", "bullet_copy_plan", "exactly five What-Who-Why plans are required")
        plans = plans if isinstance(plans, list) else []
    plan_by_index: dict[int, dict[str, Any]] = {}
    for index, plan in enumerate(plans):
        path = f"bullet_copy_plan[{index}]"
        if not isinstance(plan, dict):
            add(findings, "invalid_bullet_plan", path, "bullet plan must be an object")
            continue
        bullet_index = plan.get("bullet_index")
        if not isinstance(bullet_index, int) or bullet_index < 0 or bullet_index >= len(bullets) or bullet_index in plan_by_index:
            add(findings, "invalid_bullet_plan_index", path, "bullet_index must uniquely map to a bullet from 0 to 4")
            continue
        plan_by_index[bullet_index] = plan
        for part in ("what", "who", "why"):
            if not str(plan.get(part, "")).strip():
                add(findings, "missing_what_who_why", f"{path}.{part}", "What, Who, and Why must all be recorded")
        plan_evidence = plan.get("evidence_ids", [])
        if not isinstance(plan_evidence, list) or not plan_evidence or not set(map(str, plan_evidence)).issubset(evidence_ids):
            add(findings, "bullet_plan_missing_evidence", f"{path}.evidence_ids", "each bullet plan requires valid evidence IDs")
        body = bullet_body(bullets[bullet_index])
        if not body:
            add(findings, "unparseable_bullet_body", f"publishable_fields.bullets[{bullet_index}]", "bullet body must follow the existing required format")
            continue
        sentence_boundaries = re.findall(r"[.!?。！？][\"'”’)]*\s+(?=[\w\"'“‘])", body, flags=re.UNICODE)
        if sentence_boundaries:
            add(findings, "multiple_bullet_sentences", f"publishable_fields.bullets[{bullet_index}]", "bullet body must be a single sentence")
        if not re.search(r"[.!?。！？][\"'”’)]*\s*$", body):
            add(findings, "bullet_missing_sentence_ending", f"publishable_fields.bullets[{bullet_index}]", "bullet body must be one complete sentence")
        keyword_ids = plan.get("keyword_ids", [])
        if not isinstance(keyword_ids, list):
            add(findings, "invalid_bullet_keyword_ids", f"{path}.keyword_ids", "keyword_ids must be a list")
            keyword_ids = []
        if strategy_status == "complete" and not keyword_ids:
            add(findings, "bullet_without_keyword", f"{path}.keyword_ids", "each bullet must map at least one selected, evidenced keyword")
        for keyword_id in keyword_ids:
            keyword = keyword_by_id.get(str(keyword_id))
            if not keyword:
                add(findings, "unknown_bullet_keyword", f"{path}.keyword_ids", "bullet references an unknown keyword id", id=str(keyword_id))
            elif keyword.get("eligible") is not True:
                add(findings, "ineligible_bullet_keyword", f"{path}.keyword_ids", "bullet cannot target an ineligible keyword", id=str(keyword_id))
            elif not term_in_text(str(keyword.get("term", "")), body):
                add(findings, "bullet_keyword_not_used", f"publishable_fields.bullets[{bullet_index}]", "mapped keyword phrase must appear in its bullet body", keyword=str(keyword.get("term", "")))
    for bullet_index in range(5):
        if bullet_index not in plan_by_index:
            add(findings, "unmapped_bullet_plan", f"publishable_fields.bullets[{bullet_index}]", "every bullet requires a What-Who-Why strategy record")

    backend = fields.get("backend_keywords")
    frontend = fields.get("frontend_keywords")
    if "frontend_keywords" not in fields:
        add(findings, "missing_frontend_keywords", "publishable_fields.frontend_keywords", "frontend keyword field must be present")
    backend_terms = list(strings(backend))
    frontend_terms = list(strings(frontend))
    if "backend_keywords" not in fields:
        add(findings, "missing_backend_keywords", "publishable_fields.backend_keywords", "backend keyword field must be present")
    if not backend_terms:
        add(findings, "missing_backend_keywords", "publishable_fields.backend_keywords", "provide backend search terms, or record an explicit no-eligible-terms reason")
        if not str(record.get("backend_keyword_unavailability_reason", "")).strip():
            add(findings, "missing_backend_reason", "backend_keyword_unavailability_reason", "explain if no eligible backend terms exist")
    else:
        front_texts = [str(value) for key, value in fields.items() if key != "backend_keywords" for value in strings(value)] + frontend_terms
        raw_backend_terms: list[str] = []
        for value in backend_terms:
            raw_backend_terms.extend(part.strip() for part in re.split(r"[,;\n]+", value) if part.strip())
        for index, term in enumerate(raw_backend_terms):
            meaningful = [token for token in tokens(term) if token not in STOPWORDS]
            if not meaningful:
                add(findings, "backend_term_without_content", f"publishable_fields.backend_keywords[{index}]", "backend term must contain a meaningful search token")
            for front in front_texts:
                if term_in_text(term, front):
                    add(findings, "backend_frontend_duplicate", f"publishable_fields.backend_keywords[{index}]", "backend search phrase must not repeat a phrase already used in frontend copy", term=term)
                    break

    description = next((str(fields[k]) for k in ("description",) if isinstance(fields.get(k), str)), "")
    voice_map = record.get("description_voice_map")
    if not isinstance(voice_map, dict) or voice_map.get("status") != "complete":
        add(findings, "missing_voice_description_map", "description_voice_map", "description requires a completed voice-search Q&A map")
        voice_map = {}
    qa_pairs = voice_map.get("question_answer_pairs", [])
    found_types: set[str] = set()
    for index, pair in enumerate(qa_pairs if isinstance(qa_pairs, list) else []):
        path = f"description_voice_map.question_answer_pairs[{index}]"
        if not isinstance(pair, dict):
            add(findings, "invalid_voice_pair", path, "question-answer entry must be an object")
            continue
        kind = str(pair.get("question_type", ""))
        excerpt = str(pair.get("answer_excerpt", "")).strip()
        found_types.add(kind)
        if not excerpt or excerpt not in description:
            add(findings, "voice_excerpt_not_in_description", path, "answer excerpt must appear verbatim in the product description")
        linked = pair.get("evidence_ids", [])
        if not isinstance(linked, list) or not linked or not set(map(str, linked)).issubset(evidence_ids):
            add(findings, "voice_answer_missing_evidence", path, "each voice answer requires valid evidence IDs")
    for kind in sorted(VOICE_TYPES - found_types):
        add(findings, "missing_voice_question_type", "description_voice_map.question_answer_pairs", "voice map must cover product identity, audience, use, and contents or compatibility", question_type=kind)

    facts = product_facts
    inventory = record.get("attribute_inventory")
    if not isinstance(inventory, list):
        add(findings, "missing_attribute_inventory", "attribute_inventory", "provide an explicit inventory for all product attributes")
        inventory = []
    facts_by_id = {str(item.get("id")): item for item in facts if isinstance(item, dict) and item.get("id")}
    inventory_by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(inventory):
        path = f"attribute_inventory[{index}]"
        if not isinstance(item, dict):
            add(findings, "invalid_attribute_inventory_entry", path, "attribute inventory entry must be an object")
            continue
        fact_id = str(item.get("fact_id", "")).strip()
        fact = facts_by_id.get(fact_id)
        if not fact_id or not fact:
            add(findings, "unknown_attribute_fact", path, "attribute entry must reference a product_fact_ledger id")
            continue
        if fact_id in inventory_by_id:
            add(findings, "duplicate_attribute_fact", path, "each product fact must appear only once", fact_id=fact_id)
        inventory_by_id[fact_id] = item
        if norm(str(item.get("attribute", ""))) != norm(str(fact.get("attribute", ""))) or norm(str(item.get("value", ""))) != norm(str(fact.get("value", ""))):
            add(findings, "attribute_inventory_mismatch", path, "attribute and value must match the linked product fact", fact_id=fact_id)
        if not isinstance(item.get("keyword_forms"), list) or not item.get("keyword_forms"):
            add(findings, "missing_attribute_keyword_forms", f"{path}.keyword_forms", "record customer search wording for each attribute")
        disposition = str(item.get("disposition", ""))
        if disposition != str(fact.get("disposition", "")):
            add(findings, "attribute_disposition_mismatch", path, "inventory disposition must match the linked product fact", fact_id=fact_id)
        if disposition == "publishable" and not item.get("mapped_fields"):
            add(findings, "unmapped_product_attribute", path, "publishable attribute must map to one or more listing fields")
        if disposition != "publishable" and not str(item.get("omission_reason", "")).strip():
            add(findings, "attribute_omission_unexplained", path, "non-publishable attribute requires a reason in Chinese explanation")
    for fact_id in sorted(set(facts_by_id) - set(inventory_by_id)):
        add(findings, "product_attribute_missing_from_inventory", "attribute_inventory", "every product fact must appear in the attribute inventory", fact_id=fact_id)
    for fact_id in sorted(set(inventory_by_id) - set(facts_by_id)):
        add(findings, "extra_attribute_inventory_entry", "attribute_inventory", "inventory cannot reference a fact absent from the product fact ledger", fact_id=fact_id)

    findings.sort(key=lambda item: (item.get("path", ""), item.get("code", ""), item.get("fact_id", ""), item.get("term", "")))
    result = {
        "status": "PASS" if not findings else "FAIL",
        "finding_count": len(findings),
        "findings": findings,
        "rules": {
            "title": "prioritize measured demand only after human review confirms title relevance and naturalness; document each comparable higher-demand term not selected",
            "bullets": "five bullets each map What-Who-Why and evidenced keyword IDs; deterministic check flags multiple sentence boundaries",
            "voice_description": "four structured answer types must be evidenced and their excerpts must occur in the description; semantics require human review",
            "backend_keywords": "backend phrases must not duplicate phrases in frontend copy",
            "attribute_inventory": "every product_fact_ledger entry must be listed, mapped, or have an omission reason",
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
