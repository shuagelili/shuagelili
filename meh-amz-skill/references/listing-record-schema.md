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

## Invariants

1. Generate customer copy from the record; do not draft directly from raw competitor prose.
2. Every publishable field has evidence and product-fact links. Unsupported claims are omitted and recorded in `chinese_explanation`.
3. Facts with `competitor_only`, `analysis_only`, `inferred`, or `to_confirm` status cannot authorize customer copy.
4. Competitor evidence is never relabelled as an own-product fact.
5. Parent/shared fields use shared facts only. Child fields use only shared facts plus the matching child facts.
6. Internal fields such as status, evidence IDs, source references, unresolved items, and correction logs never render in customer copy.

## Review and keyword linkage

For each accepted row, connect: review signal -> purchase objection -> keyword intent -> verified response fact -> customer-facing response field. A keyword without a verified product response is an opportunity, not a claim. Missing review data uses `not_available` or `hypothesis`; never invent review frequency or sentiment.

## Field metadata

Before HTML rendering, preserve the final text, measured count, scenario IDs, and evidence IDs for each publishable field. Each bullet also records its header, primary benefit, scenario ID, keyword IDs, and evidence IDs outside the visible copy.
