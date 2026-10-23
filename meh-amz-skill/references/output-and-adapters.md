# Output Contract and Adapters

Read this reference when selecting a mode, using an adapter skill, or rendering the final deliverable.

## Mode router

- `teardown`: competitor intelligence and gap analysis;
- `create`: new product Listing from verified facts;
- `optimize`: improve an existing own Listing;
- `health-check` / `recheck`: add live front-end health evidence;
- `review`: audit only, without inventing replacement copy.

Default route is competitor analysis -> Listing writing -> Listing review. Do not expand into strategic briefs, Q&A, variant strategy, or 30-day operations unless requested or required by the input.

## Adapter boundary

Use `amazon-listing-optimization` for keyword tiers, coverage matrices, competitive gaps, and diagnostics. Use `zach-listing-health-checker` for front-end health snapshots, offer/ZIP evidence, search visibility, and rechecks. Use `boothzoo-amazon-listing-optimizer` for strategic briefs, review intelligence, objection handling, optional Q&A, compliance, and refresh recommendations.

The base skill keeps authority over marketplace limits, evidence status, customer-copy rules, and product facts. Do not import unsupported algorithm weights, ranking guarantees, conversion claims, or inferred product attributes.

## Customer copy contract

All customer-visible fields are localized and paste-ready. Internal review wording belongs only in Chinese explanation, evidence, scene matrices, QA, or correction logs. The five bullets must begin at the first visible character with the exact format:

```text
【UPPERCASE LOCALIZED BENEFIT OR PAIN-POINT HEADER】 : Localized content.
```

## HTML contract

Return one complete UTF-8 HTML document with `<html lang="...">`, semantic headings, escaped user content, accessible tables, and readable styling. Keep this order unless a section is not applicable:

1. site configuration, inputs, and evidence boundary;
2. mode and strategic brief, if requested;
3. competitor teardown;
4. keyword and opportunity analysis;
5. scene coverage and AI-shopping semantic structure;
6. localized Listing copy with Chinese explanation;
7. buyer Q&A or objection handling, if requested;
8. use guide;
9. seven-image plan;
10. A+ text, if requested;
11. health snapshot, if requested;
12. QA, compliance, and correction log;
13. unresolved items and next steps.

Keep evidence, calculations, inferences, recommendations, and unresolved conflicts visibly separate from customer copy. Completion states are `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`.
