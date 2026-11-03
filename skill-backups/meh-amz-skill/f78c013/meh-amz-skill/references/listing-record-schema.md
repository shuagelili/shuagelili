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

`context` stores mode, marketplace, ASIN roles, and resolved field limits. `evidence_ledger` stores `id`, `claim`, `value`, `source_type`, `source_ref`, `scope`, and `status`. `product_fact_ledger` stores `id`, `attribute`, `value`, `unit`, `variant`, `ownership`, `source_evidence_ids`, `status`, `disposition`, and `customer_fields_allowed`.

Each scenario stores `id`, `audience`, `trigger_or_problem`, `task`, `product_mechanism`, `outcome`, and `evidence_ids`.

The review matrix contains `status`, review themes, purchase objections, keyword intents, and links. Keyword intents keep separate `intent_stage`, `intent_type`, and `intent_family` values. Keyword controls keep negative keywords separate from forbidden terms.

The variant matrix contains `status`, parent data, children, and `field_scope_map`. A single ASIN uses `not_applicable`; a family uses `complete` and at least two distinct children.

`publishable_fields` contains the final customer copy: title alternatives, Highlights, exactly five bullets, description, use guide, frontend keywords, backend terms, image text/plan, and A+ text/modules. `publishable_claim_map` links every populated field to fact IDs, evidence IDs, and optional scenario IDs.

`keyword_strategy` records `status` (`complete` or `not_available`), `primary_keyword_id`, `required_frontend_keyword_ids`, and retained keywords. Each keyword stores `id`, `term`, measured `search_volume` (or null when ineligible), `source_ref`, eligibility, and supporting own-product fact IDs. A complete strategy selects the highest-volume eligible and relevant term as the title lead. `required_frontend_keyword_ids` lists high-demand terms selected for title/bullet coverage. Never invent search volume. `not_available` requires a reason.

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

## Review and keyword linkage

For each accepted row, connect: review signal -> purchase objection -> keyword intent -> verified response fact -> customer-facing response field. A keyword without a verified product response is an opportunity, not a claim. Missing review data uses `not_available` or `hypothesis`; never invent review frequency or sentiment.

## Field metadata

Before HTML rendering, preserve the final text, measured count, scenario IDs, and evidence IDs for each publishable field. Each bullet also records its header, primary benefit, scenario ID, keyword IDs, and evidence IDs outside the visible copy.
