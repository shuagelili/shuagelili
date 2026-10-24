---
name: meh-amz-skill
description: Use when a user provides an Amazon ASIN, product URL, competitor listing, keyword workbook, or existing listing and needs marketplace-specific competitor intelligence, Listing creation or optimization, health acceptance, or a bilingual HTML deliverable.
---

# Amazon Marketplace Intelligence and Listing

This skill produces an evidence-backed Amazon competitor analysis, localized Listing package, and QA record in one complete bilingual HTML document. Keep the workflow focused on the user's requested mode.

## Daily workflow

Use this route by default:

1. **提供资料**：竞品 ASIN/网址、流量关键词或 Excel、目标站点、自己产品的真实参数。自己的 ASIN 标为 `own_listing`，竞品标为 `competitor`。
2. **写 Listing**：基于已验证事实、竞品差异和关键词意图，生成当地语言标题、Highlights、五点、描述、前台/后台关键词、使用指南、七图计划和可选 A+ 文案，并附中文说明。
3. **审查 Listing**：运行确定性验证器，检查字段限制、五点格式、证据来源、竞品属性隔离、关键词控制、客户可见文案和变体边界。用户要求上线验收时，再运行前台健康检查。

Default route is competitor analysis -> Listing writing -> Listing review. Read [references/output-and-adapters.md](references/output-and-adapters.md) for mode routing and adapter boundaries.

## Non-negotiable customer-copy rules

Every customer-visible field must contain only verified, publishable product information. Internal review language belongs only in Chinese explanation, evidence, scene matrices, QA, or correction logs.

Do not put the following in title, Highlights, bullets, description, use guide, frontend keywords, backend terms, image text, or A+ text: `待确认`, `仍需确认`, `待核实`, `推断`, `假设`, `未知`, `无法验证`, `可能`, `建议确认`, `listing-stale`, `BLOCKED`, `TBD`, `TBC`, `unverified`, `inferred`, `unknown`, `placeholder`, or equivalent wording.

When a fact cannot safely support customer copy, omit it from the visible field and record the gap in Chinese explanation.

### Five bullets

Whenever bullets are produced, output exactly five entries. Every entry must begin at the first visible character with:

```text
【全大写小标题】 : 内容
```

Rules:

- the text inside `【】` is fully uppercase, including localized accented letters;
- use the English half-width colon and exactly one space on both sides;
- use a specific buyer benefit or pain-point header, not generic labels such as `【HIGH QUALITY】`;
- write the chain buyer scene or pain -> product mechanism -> concrete outcome;
- keep one primary benefit per bullet and cover different verified shopping scenes.

Example:

```text
【CALENDRIER DE L'AVENT FOOTBALL 2026】 : Idéal pour les passionnés de football, ce calendrier rend le compte à rebours inoubliable.
```

The exact format is enforced by `validate_bullets.py`; do not rely on visual formatting or prose assertions.

### Description and field limits

The product description target is 1,500-2,000 characters. Default limits are title at most 75 characters and Highlights at most 125 characters per item, subject to verified marketplace/category overrides. The saved text is measured by the deterministic limits validator.

## Three semantic dimensions

Organize the Listing across all modules using three dimensions:

1. **Shopping scenes**: who uses it, when, what problem occurs, what task is being completed, and what outcome is expected.
2. **Foundational product information**: verified specifications, capacity, dimensions, material, compatibility, contents, use steps, care, and limitations.
3. **Complete structured product information**: map product noun, attributes, functions, audience, use cases, outcomes, limitations, and evidence into title, Highlights, bullets, description, search terms, guide, images, and A+.

Use at least three distinct verified scenes when the product supports them. Do not claim a platform algorithm weight, ranking guarantee, or conversion uplift merely because the content is structured for AI shopping.

## Experience-first copy

Before drafting customer-visible copy, classify the product's primary experience mode: festive ritual, task completion, problem solving, daily comfort, display and atmosphere, exploration and learning, or portable/outdoor use. A festive product can be framed around a ritual or shared seasonal experience; an ordinary product should be framed around the task, pain point, routine, or completed outcome that its verified mechanism supports. Do not force a holiday narrative onto a non-seasonal product.

Build each shopping scene as `buyer situation -> problem or desire -> verified product mechanism -> completed task -> concrete outcome`. Map distinct scenes across title, Highlights, bullets, description, use guide, keywords, images, and A+. Use at least three genuinely different scenes when the product supports them, and keep one primary benefit per bullet. Read [references/experience-first-copy-framework.md](references/experience-first-copy-framework.md) for mode selection, scene coverage, bullet architecture, description flow, and image/A+ mapping.

## Evidence and structured record

Before drafting visible copy, create a `listing_record`. It is the source of truth for the final HTML. At minimum it contains:

- `context`: mode, resolved marketplace, ASIN roles, and limits;
- `evidence_ledger` and `product_fact_ledger`;
- `scenarios`;
- `review_objection_keyword_matrix`;
- `keyword_controls`;
- `variant_listing_matrix`;
- `publishable_fields`;
- `publishable_claim_map`;
- `chinese_explanation` and `qa`.

Every publishable field needs final text, measured count, scenario IDs, evidence IDs, and a claim-map entry linking at least one own product fact and one evidence item. Every bullet also keeps its header, main benefit, scenario ID, keyword IDs, and evidence IDs outside the visible text.

Use this source priority: user facts and documents -> authoritative marketplace evidence -> user keyword workbook -> front-end health snapshot -> competitor observations -> clearly labelled analyst inference. Never fabricate attributes, metrics, prices, reviews, rankings, certifications, delivery promises, or competitor claims.

Read [references/listing-record-schema.md](references/listing-record-schema.md) for the full schema and ownership invariants. Read [references/marketplace-evidence.md](references/marketplace-evidence.md) before resolving a country, ZIP, currency, offer state, or disputed product attribute.

## Joint buyer analysis

Keep these layers separate and connect them only when evidence supports the link:

`review signal -> purchase objection -> keyword intent -> verified response fact -> Listing response field`

Classify every retained keyword independently by `intent_stage`, `intent_type`, and `intent_family`. Keep negative keywords separate from forbidden terms. A keyword with no verified product response is an opportunity or hypothesis, not a customer-facing claim. When review data is unavailable, use `not_available` or `hypothesis`; never invent frequency, sentiment, or severity.

## Variants

For one ASIN, set `variant_listing_matrix.status` to `not_applicable`. For a parent/child family, keep parent/shared fields limited to shared facts and child fields limited to the matching child facts, keywords, and scenes. Never generalize a child-only size, color, pack count, material, compatibility, review theme, or keyword to the parent without explicit shared evidence.

## Automatic validation

Run the aggregate gate after localization and before HTML rendering:

```powershell
python scripts/validate_listing_record.py listing_record.json --output qa_validation.json
```

It runs fact-ledger isolation, review-objection-keyword linkage, keyword controls, variants, bullet format, customer-copy scanning, and field limits. Every child must return `PASS`; aggregate `PASS` is the only accepted state. Missing scripts, invalid child JSON, timeouts, and exit code 2 produce `ERROR`; any child `FAIL` produces `FAIL` and exit code 1.

After changing a validator or upgrading this skill, run the regression fixtures:

```powershell
python scripts/test_validators.py
```

The regression suite checks a clean record, legacy bullet formatting, internal review wording in customer copy, and a description shorter than 1,500 characters. It asserts actual exit codes, JSON status, and `failed_checks`.

For debugging, the individual checks remain available:

```powershell
python scripts/validate_fact_ledger.py listing_record.json
python scripts/validate_review_objection_keyword.py listing_record.json
python scripts/validate_keyword_controls.py listing_record.json
python scripts/validate_variants.py listing_record.json
python scripts/validate_bullets.py listing_record.json
python scripts/validate_listing_limits.py listing_record.json
python scripts/scan_customer_copy.py listing_record.json
```

Individual PASS results never override an aggregate FAIL or ERROR. Read [references/validation-and-qa.md](references/validation-and-qa.md) for the full QA gate and failure interpretation.

## Deliverable

Return one complete UTF-8 HTML document with semantic headings, escaped user content, accessible tables, and readable styling. Include, when applicable:

1. site configuration, inputs, and evidence boundary;
2. competitor teardown;
3. keyword and opportunity analysis;
4. scene coverage and AI-shopping semantic structure;
5. localized Listing copy with Chinese explanation;
6. use guide;
7. seven-image plan;
8. A+ text;
9. front-end health snapshot;
10. QA, compliance, correction log, unresolved items, and next steps.

Keep evidence, calculations, inferences, recommendations, and unresolved conflicts separate from paste-ready customer copy. Reopen or parse the saved HTML and rescan the final visible text before reporting completion. Use completion states `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`.

Read [references/output-and-adapters.md](references/output-and-adapters.md) for the complete HTML order, mode router, and optional adapter guidance.

## Stop conditions

- unknown marketplace or unsupported health adapter: stop that check and mark it `BLOCKED`;
- missing keyword workbook: continue with evidenced product and competitor analysis, but mark keyword metrics unresolved in Chinese explanation;
- captcha, 404, unavailable page, or incomplete export: report the evidence boundary and do not infer live metrics;
- no verified brand: omit the brand from paste-ready fields;
- unresolved price, Buy Box, inventory, delivery, rating, BSR, or search position: keep it out of product claims;
- unsupported algorithm weights, ranking guarantees, or conversion percentages: label as hypothesis only.
