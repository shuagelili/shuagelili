# Listing Record Schema

Read this reference before drafting or auditing a structured Listing record.

## Required branches

```text
listing_record
├── context
├── evidence_ledger[]
├── product_fact_ledger[]
├── scenarios[]
├── review_objection_keyword_matrix
├── keyword_controls
├── keyword_source_ledger[]
├── keyword_strategy
├── bullet_copy_plan[]
├── description_voice_map
├── attribute_inventory[]
├── variant_listing_matrix
├── publishable_fields
├── publishable_claim_map[]
├── chinese_explanation
└── qa
```

`context` stores mode, resolved marketplace, ASIN roles, and field limits. Configure per-field limits under `context.limits.<field>` as an integer maximum or `{ "min": 0, "max": 100, "count_unit": "unicode_code_points", "source_ref": "..." }`; `count_unit` supports `unicode_code_points`, `utf8_bytes`, or `utf16_code_units`. A missing `count_unit` defaults to Unicode code points. Record the authoritative marketplace/category source when overriding defaults. Defaults are title 75 characters, description 1,500-2,000 characters, and Highlights 125 characters; they are workflow defaults, not universal Amazon policy. `evidence_ledger` stores `id`, `claim`, `value`, `source_type`, `source_ref`, `scope`, and `status`. `product_fact_ledger` stores `id`, `attribute`, `value`, `unit`, `variant`, `ownership`, `source_evidence_ids`, `status`, `disposition`, and `customer_fields_allowed`.

Each scenario stores `id`, `audience`, `trigger_or_problem`, `task`, `product_mechanism`, `outcome`, and `evidence_ids`.

The review matrix contains `status`, review themes, purchase objections, keyword intents, and links. Keyword intents keep separate `intent_stage`, `intent_type`, and `intent_family` values. Keyword controls keep negative keywords separate from forbidden terms.

The variant matrix contains `status`, parent data, children, and `field_scope_map`. A single ASIN uses `not_applicable`; a family uses `complete` and at least two distinct children.

`publishable_fields` contains the final customer copy: title alternatives, Highlights, exactly five bullets, description, use guide, frontend keywords, backend terms, image text/plan, and A+ text/modules. `publishable_claim_map` links every populated field to fact IDs, evidence IDs, and optional scenario IDs.

`keyword_source_ledger` is the audit trail for every keyword candidate considered, including rejected candidates and duplicate rows. Each entry stores `candidate_id`, exact `raw_term`, `normalized_term`, `source_type`, pinpoint `source_ref`, valid `evidence_ids`, `marketplace`, `metric` (`name`, `value`, `unit`, `period`, and scope when available), `brand_terms_detected` with ownership (`own`, `competitor`, or `unknown`), `brand_terms_removed`, `canonical_keyword_id`, `duplicate_action` (`canonical`, `merged_into`, or `excluded`), `eligibility`, `decision_reason`, and `selected_fields`. A candidate merged into another term points to the canonical keyword ID; an excluded candidate has no retained keyword placement. Keep the source value intact and explain every transformation. Record unavailable values as null with a reason. Do not compare or aggregate demand across incompatible marketplaces, metric definitions, units, scopes, or periods.

`keyword_strategy` records `status` (`complete` or `not_available`), `primary_keyword_id`, `required_frontend_keyword_ids`, retained keywords, and `title_selection`. Each retained keyword stores `id`, canonical `term`, `search_volume` (or null when unavailable), `source_ref`, `source_candidate_ids`, `demand_source_candidate_id`, eligibility, and supporting own-product fact IDs. `source_candidate_ids` must point to the raw candidates that support the canonical term; `demand_source_candidate_id` identifies the exact row whose metric supplies `search_volume`.

For a complete strategy, `title_selection` stores `review_status: human_reviewed`, the selected keyword ID (matching `primary_keyword_id`), `selected_fit` (`relevance: relevant`, `naturalness: natural`), a `selection_rationale`, and `higher_demand_terms_not_selected`. Compare only source rows with matching marketplace, metric name, unit, period, scope, and comparison group. Every comparable source row with greater measured demand than the selected term must appear in `higher_demand_terms_not_selected` with its `candidate_id`, `title_relevance`, `naturalness`, `reason_code`, and explanation. Supported reason codes are `not_relevant_to_product`, `awkward_localization`, `unsupported_claim`, `redundant_with_selected_term`, `title_length_or_readability`, `marketplace_language_mismatch`, and `other`. The selected keyword phrase must appear in the title, but need not lead it. The validator checks completeness and consistency of the review record; a human must assess actual relevance and naturalness. `required_frontend_keyword_ids` lists high-demand terms selected for title/bullet coverage. Never invent search volume. `not_available` requires a reason.

`bullet_copy_plan` contains exactly five entries keyed by `bullet_index` (0-4). Each stores `what`, `who`, `why`, relevant `keyword_ids`, and valid evidence IDs. It is planning metadata, not customer-facing copy; the visible bullet remains one coherent sentence in the existing required format.

`description_voice_map` stores `status: complete` and evidence-linked `question_answer_pairs` for `product_identity`, `audience`, `usage`, and `contents_or_compatibility`. Every `answer_excerpt` must occur verbatim in the description. The map makes voice-oriented answers auditable; it does not establish or guarantee Alexa indexing or placement.

`attribute_inventory` mirrors every `product_fact_ledger` entry by `fact_id`, `attribute`, and `value`, and records `keyword_forms`, `disposition`, and either `mapped_fields` or an `omission_reason`. Reconcile the fact ledger against all user-provided product materials; a validator can verify ledger-to-inventory completeness, not detect attributes omitted from the ledger.

## Invariants

1. Generate customer copy from the record; do not draft directly from raw competitor prose.
2. Every publishable field has evidence and product-fact links. Unsupported claims are omitted and recorded in `chinese_explanation`.
3. Facts with `competitor_only`, `analysis_only`, `inferred`, or `to_confirm` status cannot authorize customer copy.
4. Competitor evidence is never relabelled as an own-product fact.
5. Parent/shared fields use shared facts only. Child fields use only shared facts plus the matching child facts.
6. Internal fields such as status, evidence IDs, source references, unresolved items, and correction logs never render in customer copy.
7. The final HTML must render every populated field exactly once inside `data-copy-field="publishable_fields.<name>"`; HTML is a render target and never a second source of claims.
8. Every retained keyword traces through `source_candidate_ids` to a raw source row, and its demand value matches the explicitly identified `demand_source_candidate_id`. Source candidates retain normalized/brand-cleaning/dedup decisions and reasons.
9. Title keyword choice prioritizes demand only after relevance and naturalness review; every comparable higher-demand term not selected has a documented reason. The selected phrase appears in the title without a forced first-position requirement.

## Review and keyword linkage

For each accepted row, connect: review signal -> purchase objection -> keyword intent -> verified response fact -> customer-facing response field. A keyword without a verified product response is an opportunity, not a claim. Missing review data uses `not_available` or `hypothesis`; never invent review frequency or sentiment.

## Field metadata

Before HTML rendering, preserve the final text, measured count, scenario IDs, and evidence IDs for each publishable field. Each bullet also records its header, primary benefit, scenario ID, keyword IDs, and evidence IDs outside the visible copy.
