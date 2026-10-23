# Validation and QA

Read this reference before final delivery or when a deterministic check fails.

## Automatic gate

Run from the skill directory or resolve the absolute script path:

```powershell
python scripts/validate_listing_record.py listing_record.json --output qa_validation.json
python scripts/test_validators.py
```

The aggregate gate runs fact-ledger isolation, review-objection-keyword linkage, keyword controls, variants, bullet format, customer-copy scanning, and field limits. Every child must return `PASS` for aggregate `PASS`. Missing scripts, invalid child JSON, timeouts, and exit code 2 produce aggregate `ERROR`; any child `FAIL` produces aggregate `FAIL` and exit code 1.

The regression script verifies that a clean record exits 0, while legacy bullet formatting, customer-visible internal review wording, and a description shorter than 1,500 characters exit 1. It checks actual exit codes and `failed_checks`.

## Individual checks

```powershell
python scripts/validate_fact_ledger.py listing_record.json
python scripts/validate_review_objection_keyword.py listing_record.json
python scripts/validate_keyword_controls.py listing_record.json
python scripts/validate_variants.py listing_record.json
python scripts/validate_bullets.py listing_record.json
python scripts/validate_listing_limits.py listing_record.json
python scripts/scan_customer_copy.py listing_record.json
```

Use individual scripts to locate a failure; their separate PASS results never override an aggregate failure.

## QA gates

Check the final saved text, not an earlier draft:

- five bullets use `【UPPERCASE HEADER】 : content`, with an ASCII colon and one space on both sides;
- bullets cover at least three distinct verified scenes and do not repeat one benefit;
- title, Highlights, description, frontend terms, backend terms, image text, use guide, and A+ text stay within resolved limits and field rules;
- description follows the buyer journey and does not merely copy the bullets;
- every supplied product attribute is mapped to a publishable field or a Chinese unresolved item;
- negative keywords and forbidden terms stay in their declared scopes;
- competitor attributes, ASINs, prices, promotions, seller/logistics states, placeholders, and unsupported claims do not enter customer copy;
- customer-copy scanner returns PASS with zero findings;
- scene coverage maps verified scenes across title, Highlights, bullets, description, search fields, guide, images, and A+;
- the final HTML is reopened or parsed and its visible copy is rescanned.

Use `PASS`, `FAIL`, `待确认`, or `BLOCKED`. Do not turn an unresolved or blocked state into a pass.
