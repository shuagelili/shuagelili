# Validation and QA

Read this reference before final delivery or when a deterministic check fails.

## Automatic gate

Run from the skill directory or resolve the absolute script path:

```powershell
python scripts/preflight_listing.py listing_record.json
# Render HTML only after preflight PASS.
python scripts/validate_delivery.py listing_record.json final.html --output delivery_validation.json
python scripts/test_validators.py
```

The pre-render gate requires a resolved target marketplace and a saved structured record. It runs the aggregate JSON validators, including field-limit measurements, and emits `html_rendered: false`; render only after `PASS`. The delivery gate requires both the record and rendered HTML, repeats preflight, then compares every marked HTML customer-copy field with `listing_record.publishable_fields`. Every child must return `PASS`, and the HTML render contract must return `PASS`. Missing files, invalid child JSON, timeouts, or skipped render validation produce `ERROR`; any child failure produces `FAIL`.

Field-limit preflight measures title, Highlights, bullets, description, frontend/backend keywords, use guide, image text, and A+ text, plus any additional field with a configured limit. Counts use Unicode code points by default; per-field rules can use UTF-8 bytes or UTF-16 code units. Invalid units, negative/non-integer limits, and minimums above maximums fail. The built-in title, description, and Highlights values are workflow defaults until replaced with a verified marketplace/category limit.

Each populated field must appear exactly once in an element marked `data-copy-field="publishable_fields.<name>"`. The record remains the source of truth; HTML cannot introduce a new claim or silently omit an approved field.

The regression script verifies that a clean record exits 0, while legacy bullet formatting, customer-visible internal review wording, a description shorter than 1,500 characters, and malformed keyword source traceability or field-limit configurations exit 1. It also verifies that preflight passes without rendering on a clean record and rejects a short description. It checks actual exit codes and `failed_checks`.

## Individual checks

```powershell
python scripts/validate_fact_ledger.py listing_record.json
python scripts/validate_review_objection_keyword.py listing_record.json
python scripts/validate_keyword_controls.py listing_record.json
python scripts/validate_variants.py listing_record.json
python scripts/validate_bullets.py listing_record.json
python scripts/validate_listing_limits.py listing_record.json
python scripts/validate_listing_strategy.py listing_record.json
python scripts/scan_customer_copy.py listing_record.json
python scripts/validate_render_contract.py listing_record.json final.html
python scripts/validate_highlights.py listing_record.json
```

Use individual scripts to locate a failure; their separate PASS results never override an aggregate failure.

## QA gates

Check the final saved text, not an earlier draft:

- five bullets use `【UPPERCASE HEADER】 : content`, with an ASCII colon and one space on both sides;
- Highlights, if present, are one comma-separated phrase string under 125 characters, shown only when the selected title is under 75 characters, with no title-word overlap or complete-sentence punctuation;
- bullets cover at least three distinct verified scenes and do not repeat one benefit;
- title, Highlights, description, frontend terms, backend terms, image text, use guide, and A+ text stay within resolved limits and field rules;
- description follows the buyer journey and does not merely copy the bullets;
- every supplied product attribute is mapped to a publishable field or a Chinese unresolved item;
- the title keyword choice prioritizes comparable measured demand only after a human confirms relevance and naturalness; every comparable higher-demand term not selected has a reason, and the chosen phrase appears naturally in the title without a fixed first-position rule;
- every keyword candidate, including excluded and duplicate rows, has exact raw-term/source-row provenance, marketplace and metric context, brand handling, normalization and deduplication decisions, eligibility/reason, and field-placement record;
- each retained canonical keyword links to its supporting source candidate IDs and names the exact demand-source row; the recorded demand matches that row, and unlike metrics are never ranked or combined;
- all five bullets have a What-Who-Why plan, relevant keyword IDs, and one coherent customer-facing sentence;
- backend phrases do not duplicate complete phrases in frontend keywords or other visible copy;
- the description voice map covers product identity, audience, usage, and contents/compatibility with evidence-linked excerpts present in the description;
- every product fact appears in the attribute inventory and is mapped or has a Chinese omission reason; compare the inventory back to original product materials;
- a human reviewer confirms the description directly answers likely spoken questions in natural language; do not claim Alexa indexing or ranking guarantees;
- negative keywords and forbidden terms stay in their declared scopes;
- competitor attributes, ASINs, prices, promotions, seller/logistics states, placeholders, and unsupported claims do not enter customer copy;
- customer-copy scanner returns PASS with zero findings;
- scene coverage maps verified scenes across title, Highlights, bullets, description, search fields, guide, images, and A+;
- the final HTML is reopened or parsed and its visible copy is rescanned.

Use `PASS`, `FAIL`, `待确认`, or `BLOCKED`. Do not turn an unresolved or blocked state into a pass.
