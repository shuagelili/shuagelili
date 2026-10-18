---
name: meh-amz-skill
description: Use when a user provides an Amazon ASIN, product URL, competitor listing, keyword workbook, or existing listing and needs marketplace-specific competitor intelligence, listing creation or optimization, health acceptance, or a bilingual HTML deliverable.
---

# Amazon Marketplace Intelligence and 10X Listing

This skill is the primary workflow for evidence-backed Amazon competitor teardown and localized listing work. Its contract remains one self-contained HTML file containing marketplace configuration, evidence, analysis, customer-facing copy, QA, and correction history. The integrations below add optional diagnostics without replacing that contract.

## Daily workflow

Use this short route by default:

1. **提供资料**：竞品 ASIN/网址、流量关键词或 Excel、目标站点、自己产品的真实参数。若优化旧 Listing，再标明自己的 ASIN 为 own_listing；竞品标明为 competitor。
2. **写 Listing**：先拆解竞品和关键词，再生成当地语言的标题、Highlights、五点、描述、前台/后台关键词、七图计划，并附中文说明。
3. **审查 Listing**：对最终文案做字段限制、关键词、What-Who-Why、属性来源、竞品属性隔离、合规和图片一致性检查；用户要求上线验收时，再追加前台健康快照。

默认按 **竞品分析 → Listing 编写 → Listing 审查** 执行。除非用户明确要求，不单独展开战略简报、Q&A、变体策略或 30 天运营建议。

### 强制写作风格

五点不是普通参数罗列。只要输出 Listing 五点，每一条必须严格使用以下可粘贴格式：

【小标题】: 内容

其中必须使用英文半角冒号，冒号紧接在 】 后面；小标题是具体利益或痛点，内容通常为 2-3 句，依次呈现买家场景/痛点、产品机制或结构、对目标用户的具体结果。示例：

【No More Frozen-Together Slices】: Tired of wrestling with a solid block of frozen bread? The individual-slot design keeps slices separated from the start, so home bakers can take only what they need without thawing the entire loaf.

每条必须保留 【...】: 这一前缀，不能改成无标题句子、普通项目符号、全大写 feature label、破折号标题或 标题 - 内容。标题必须具体、可感知、面向买家；禁止泛化标题如 【High Quality】、【Premium Material】，除非后文紧接着给出可验证的具体结果。五点必须覆盖不同购物场景，并自然回答 What、Who、Why。

如果生成的五点中任何一条不符合 ^【[^】]+]:.+ 的结构，或缺少“场景/痛点 → 机制 → 结果”链条，视为 QA FAIL，必须重写后再交付。最终 HTML 中的五点复制区必须保留该格式，不得由模板、表格或渲染过程去掉小标题。

### 三层场景化与 AI 购物语义

Listing 生成必须把信息组织成三种互补维度：

1. **购物场景呈现**：明确买家在什么时刻、为谁、遇到什么问题、希望完成什么任务。至少覆盖 3 个不同场景，例如日常使用、特定人群/家庭、收纳/准备/送礼或季节性场景；只能使用真实产品适用场景。
2. **基础拓展信息**：补充买家决策所需的规格、容量、尺寸、材质、兼容性、使用步骤、清洁维护、包装内容和限制。未知信息标记 待确认，不能用推断填充。
3. **完整商品信息结构化**：把核心产品词、属性、功能、对象、使用场景、结果、限制和证据来源映射到标题、五点、描述、前台关键词、后台词、图片和可选 Q&A，形成可扫描的结构化信息。

将这三层用于 AI 购物理解时，只把它作为内容组织原则，不宣称具体平台算法权重或排名保证。描述和可选 Q&A 应优先回答“这是什么、适合谁、什么时候用、怎么用、有什么限制、购买前要确认什么”，并保持事实可验证。

### 全 Listing 场景覆盖矩阵

场景化必须贯穿所有 Listing 模块，不得只放在五点。先从已验证的产品事实中提取 3-5 个场景，再把场景分配到不同字段；同一场景可以重复出现，但每次承担的语义任务必须不同。

| 模块 | 场景化任务 | 必须呈现的内容 |
|---|---|---|
| 标题 | 快速识别核心使用任务 | 核心产品词 + 一个最高价值场景或适用对象；只使用能帮助搜索识别的短语，不牺牲可读性 |
| Highlights | 补充标题未容纳的场景 | 用短语补充第二场景、使用时机、对象、兼容性或结果；不重复标题中的主要词 |
| 五点 | 展开购买理由 | 每点绑定一个不同场景，写出痛点、机制和结果；至少覆盖日常任务、特定对象/人群、收纳/准备/效率等场景中的已验证部分 |
| 产品描述 | 还原完整使用旅程 | 按“使用前情境 → 使用方式 → 使用中结果 → 使用后收益 → 限制/注意事项”组织，覆盖至少 3 个具体场景 |
| 前台搜索关键词 | 覆盖场景搜索意图 | 包含已验证的对象词、任务词、时机词、问题词和结果词；按关键词证据排序，不把场景词当成产品事实 |
| 后台搜索词 | 补充自然语言长尾 | 补充前台未出现的场景长尾、同义表达和问题句式；排除无证据场景、竞品品牌和重复词 |
| 产品使用指南 | 让买家知道何时、如何使用 | 至少提供准备、操作、取用/收纳、清洁维护和限制说明；每一步说明适用场景或预期结果 |
| 图片文本 | 用视觉证明场景 | 为每张图指定人物/对象、环境、动作、前后状态和要证明的事实；图中文字不得创造文案中没有证据的场景 |
| A+ 文本建议 | 扩展决策和比较语义 | 提供模块标题、场景副标题、功能解释、对比维度和购买前疑问；A+ 建议仍需与已验证产品属性一致 |

至少为每个最终 Listing 输出一张“场景覆盖矩阵”，列出场景、目标用户、触发问题、产品机制、结果、出现模块和证据来源。若某场景只有推断依据，标记为 推断 或 待确认，不得写成确定性卖点。

## Compatibility boundary

Use the other skills as optional adapters, not as competing workflows:

| Adapter | Add to this skill | Do not import blindly |
|---|---|---|
| amazon-listing-optimization | create/optimize mode, keyword tiers, coverage matrix, competitive gap table, tone choice, 8-dimension diagnostic | its 200-character title and 500-character bullet defaults; this skill's resolved marketplace/category limits win |
| zach-listing-health-checker | front-end health snapshot, offer/ZIP evidence, search visibility, page-status and recheck states | its Markdown report contract or any unsupported site fallback |
| boothzoo-amazon-listing-optimizer | strategic brief, review-intelligence prompts, objection handling, optional Q&A, compliance scan, variant/review/refresh recommendations | unsupported A9/Rufus weights, conversion uplift claims, 150–200-character title defaults, or inferred product facts |

The existing meh-amz-skill rules have priority over adapter suggestions. User-supplied product facts and verified authoritative evidence have priority over competitor copy, inferred keywords, and model assumptions.

## Mode router

Choose the narrowest mode that satisfies the request, then keep the full HTML contract. When the request combines modes, use the combined route explicitly: competitor teardown first, then create/optimize, then optional health-check, then QA.

| Mode | Trigger | Required output additions |
|---|---|---|
| teardown | competitor ASIN/URL or market research request | competitor teardown, evidence labels, opportunity matrix |
| create | new product/listing requested | copy-ready localized fields, keyword coverage, product-attribute inventory |
| optimize | existing listing, ASIN, or rewrite request | before/after copy, gap analysis, score deltas, preserved strengths |
| health-check | user asks whether a live ASIN is visible, purchasable, or healthy | Zach-compatible front-end snapshot and action list; do not rewrite facts from the snapshot |
| recheck | user supplies a prior report or asks to verify a fix | compare the same marketplace, ZIP, timestamp context, and fields; show changed/unchanged/unknown |

If several modes apply, use teardown → create/optimize → optional health-check → QA. A health snapshot never becomes proof of product specifications, and a copy rewrite cannot claim to fix offer-level problems such as Buy Box, stock, or delivery.

## Inputs and source priority

Collect or identify these inputs before analysis:

- The user's own ASIN or URL, when optimizing an existing listing, explicitly labelled as own_listing.
- Competitor ASINs or URLs, explicitly labelled as competitor; never infer the role from position in a list. Preserve parent/child, pack, bundle, and variant roles for every ASIN.
- Target marketplace/country, or a marketplace URL.
- Traffic-keyword Excel workbook or actual sheet content. Read real columns and retain sheet/row/date references.
- Brand name, or [Brand] for analysis-only placeholders.
- Target selling-price range, if supplied; never invent a competitor price.
- Actual product parameters supplied by the user or verified from an authoritative source.
- Optional: current listing copy, CTR/CVR/ACOS/Brand Analytics data, review themes, competitor ASINs, tone, category, compliance constraints, and requested output language.

Apply this source order to every claim:

1. User-supplied product facts and documents.
2. Authoritative marketplace/product evidence captured for the resolved site.
3. User-provided keyword workbook metrics.
4. Front-end health snapshot for time/ZIP/offer state only.
5. Competitor observations for comparison and keyword discovery.
6. Analyst inference, clearly labelled.

If a required input is missing, state the gap and continue only with evidenced portions. Never fabricate a product attribute, keyword volume, rank, price, review count, image detail, certification, Buy Box, delivery promise, or competitor claim. If user-supplied product parameters conflict with the own listing page, preserve both values, label the conflict listing-stale / 待确认, and recommend updating the listing or verifying the parameter before using it in final copy.

## Dynamic marketplace configuration

Resolve the target marketplace before reading evidence or writing copy. Show the resolved configuration near the top of the HTML and apply it to page access, keyword interpretation, language, image text, and QA.

1. An explicit marketplace or URL wins. If an ASIN and URL conflict, use the explicit marketplace and record the conflict.
2. Supported defaults for the health adapter are: US amazon.com/90001/en-US/USD; UK amazon.co.uk/SW1A 1AA/en-GB/GBP; DE amazon.de/10115/de-DE/EUR; FR amazon.fr/75001/fr-FR/EUR; IT amazon.it/00100/it-IT/EUR; ES amazon.es/28001/es-ES/EUR; CA amazon.ca/M5V 2T6/en-CA/CAD; JP amazon.co.jp/100-0001/ja-JP/JPY; MX amazon.com.mx/06600/es-MX/MXN; AU amazon.com.au/2000/en-AU/AUD.
3. For any other country, identify the domain, language, currency, and postal code from authoritative evidence. If the health adapter cannot execute that site, mark health status BLOCKED rather than falling back to US/France or guessing.
4. Record postal-code source, retrieval time, locale, currency, login/personalization limitations, and any unresolved language choice.

The default deliverable remains: title alternatives at most 75 characters, highlights at most 125 characters, five bullets, product description 1,500-2,000 characters, separate frontend/backend keyword fields, and a seven-image plan. Treat these as this skill's template defaults, not universal Amazon limits. User instructions and verified category/marketplace rules override them; record the override and the measurement unit. If verified facts cannot support 1,500 characters without repetition or invention, keep the description shorter and mark the gap rather than padding it.

When no brand is supplied, [Brand] may appear only in analysis tables. Omit it from final copy and mark the brand field 待确认.

## Evidence and marketplace rules

1. Keep observed, calculated, inferred, recommended, and 待确认 facts visibly separate.
2. A blocked page, snippet, incomplete export, or one ZIP snapshot is not proof of live price, rating, review count, BSR, stock, search rank, or global availability.
3. ASIN-level page evidence does not prove offer-level ownership, Buy Box, inventory, or delivery. Record seller, fulfillment, ZIP, and timestamp separately.
4. Use the workbook as the source of truth for keyword metrics. Preserve original keyword, metric name, date, sheet, and row. Do not call estimated traffic share category market share.
5. Competitor-only features, certifications, materials, sizes, guarantees, images, and claims stay out of the user's listing unless present in verified product parameters.
6. Keep product lines and variants separate. Do not globally negate a term because it is irrelevant to one child ASIN.
7. Do not assert exact A9/Rufus weighting or conversion uplift. Describe placement as a testable hypothesis unless the user supplies measured evidence.

## Workflow

### 1. Preflight and strategic brief

State the selected mode, marketplace configuration, inputs received, data gaps, and evidence boundaries. When useful, add a concise strategic brief covering keyword clusters, positioning angle, buyer objection, use-case/Rufus hypothesis, compliance constraints, and any A/B test variable. Label every hypothesis.

The preflight table must list ASIN roles explicitly as own_listing, competitor, or reference_only and state the resolved field limits used for this report. If a workbook is supplied but no health keywords are named, use only the primary/title-tier terms for search visibility checks; do not search every workbook row.

### 2. Competitor deep teardown

Analyze the target ASIN or URL in the resolved customer language, with concise Chinese explanation for every major section. Cover:

- title structure: brand, core noun, differentiators, use case, audience, and keyword order;
- five bullets: What-Who-Why coverage, claims, benefits, objections, and keyword placement;
- image strategy: count and observable role, product visibility, infographic/lifestyle balance, and missing proof;
- user pain points and purchase reasons, separating review evidence from analyst inference;
- parameter completeness and ambiguous specifications;
- workbook traffic keywords with source and priority tiers;
- positioning gap matrix: competitor claims, your verified facts, and defensible gaps.

Include source notes and confidence for each competitor section. If live access is unavailable, provide a re-check list instead of filling live metrics.

### 3. Keyword and conversion modules

Use these as additive diagnostics for create and optimize:

- Keyword tiers: primary/title, secondary/bullets, tertiary/description, long-tail/backend. Preserve volume/date/source; inferred terms are marked 推断.
- Coverage matrix: keyword × title/highlights/bullets/description/frontend/backend, with exact phrase/variant match and a source column. Report coverage percentage without treating it as a ranking guarantee.
- Competitive gap: show what competitors use, what the user's listing uses, and what verified product facts can defensibly own. Never fill a gap with a competitor-only claim.
- Review intelligence: if review themes exist, map positive themes to benefits and complaints to objection handling. Without review data, mark the module as a hypothesis.
- Optional Q&A: provide up to five buyer-voice questions and honest answers only when requested or when the listing needs FAQ/objection coverage. Q&A is supplemental content, not a replacement for the required fields.
- Tone: professional, friendly, urgent, or luxury only when compatible with category and compliance; default to professional.

### 4. 10X listing package

Write customer-facing copy in the resolved marketplace language/locale and place a concise Chinese explanation beside it. The final HTML is bilingual in this sense: localized copy is paste-ready, while Chinese is the internal explanation and audit layer.

- Title: two alternatives, measured after localization. Put the primary core term early and add one verified high-value use case, user, or task when space allows. Use only verified facts and workbook-supported terms. If no brand exists, omit the brand segment.
- Highlights: a comma-separated phrase line at most 125 characters, shown only when the title is below 75 characters. Use it to add one or more verified secondary scenarios, timing cues, audience cues, compatibility cues, or outcome cues that are absent from the title. Avoid meaningful-word overlap with the final title.
- Five bullets: exactly five, each must begin with the literal structure 【小标题】: 内容. Use a specific localized benefit or pain-point header, then normally write two or three fluent sentences covering buyer situation or pain point, verified product mechanism, and concrete outcome. A question opener is optional. Cover What, Who, and Why naturally without enforcing a fixed sentence order. No price, promotion, logistics, seller information, or unsupported guarantees.
- Product description: 1,500-2,000 characters after final localization. Use localized question-and-answer headings when helpful, cover what it is, who it is for, where/how it is used, why to choose it, care/limits, and what to check before purchase. Organize the body around at least 3 verified usage journeys rather than repeating a feature list: trigger/problem, action, mechanism, result, and boundary. Expand rather than copy bullets. Do not claim Alexa/Rufus indexing. If evidence is insufficient for 1,500 characters, mark 待确认 and explain the missing facts instead of inventing detail.
- Use guide: concise steps for preparation, use, removal or storage, cleaning/maintenance, and limits. Tie each step to a real usage moment and expected result, such as preparing before freezing, taking one serving during a busy morning, or cleaning after use. Do not invent frequency, duration, temperature, or safety instructions.
- Frontend search keywords: report-only field, lowercase and comma-separated, evidence-backed, with title overlap and source shown. Include verified scene-intent terms covering who, when, where, task, problem, and desired result. Do not imply it is a standard Seller Central field.
- Backend search terms: separate field; use the resolved marketplace's verified character/byte limit. Use relevant natural-language scene variants and long-tail task phrases absent from the frontend where possible. Exclude competitor brands, ASINs, irrelevant scenarios, unsupported claims, and duplicate words.
- Seven-image logic: specify image 1 through 7, purpose, scene/content, proof, text boundaries, mobile legibility, and claim risk. Across the sequence, show different verified usage contexts rather than seven abstract feature panels. Keep image 1 marketplace-compliant.
- A+ content text plan: when A+ is requested or materially useful, provide module-by-module text with a scene-led headline, supporting copy, proof point, comparison/decision cue, and evidence source. A+ copy is supplemental and must not introduce an unverified use case or product claim.

For every generated block, optionally include a compact annotation with logic, keywords, and data source. Keep annotations outside copy-ready fields so the seller can paste clean text.

#### Field recipes retained from the original workflow

- Title A follows core product term + brand when verified + two core benefits + main use/compatibility. Title B follows verified brand when available + core product term + differentiator/key specification. If no brand is verified, omit the brand segment rather than inserting a placeholder.
- Each bullet follows 【localized benefit or pain-point header】: content, then buyer situation or pain point + product mechanism + outcome, while preserving What → Who → Why, one primary selling point, and one relevant priority keyword. Keep the English half-width colon and header in the final customer-facing text. Headers should be specific and customer-facing, such as 【No More Frozen-Together Slices】; do not use generic labels such as 【High Quality】. Keyword stuffing, repeated claims, and unsupported superlatives are not allowed.
- The description uses localized buyer questions such as what it is, who it is for, where/how it is used, why to choose it, care/limits, and what to check before purchase. This is a readability pattern, not a claim of Alexa or Rufus indexing. Aim for 1,500-2,000 measured characters.
- Backend terms are lowercase where the marketplace permits, separated according to the verified field rule, and measured in characters or UTF-8 bytes as required. Report the limit and measured value.
- The seven-image plan covers image 1 through 7 with purpose, scene, proof, and claim boundaries. Image 1 must follow the resolved marketplace's main-image rules.

### 5. Optional front-end health snapshot

Run this only for health-check/recheck, or when the user explicitly asks for live acceptance. Reuse zach-listing-health-checker scripts when available. Resolve the script's absolute path in the current environment before execution; the command below is illustrative and the Windows interpreter may be python rather than python3:

    python3 skills/zach-listing-health-checker/scripts/fetch_amazon_page.py {ASIN} --site {SITE}
    python3 skills/zach-listing-health-checker/scripts/fetch_amazon_search.py "{keyword}" {ASIN} --site {SITE}

Adapt the JSON into an HTML evidence block with timestamp, site, postal code, page status, and these checks: accessibility, price/promotion, seller/fulfillment, cart/Buy Box, delivery/Prime, category path, BSR, review negatives, and keyword search visibility. Use ok, attention, error, unavailable, captcha, or fetch_failed; missing fields are 待确认. Run search visibility only for user-provided core keywords or primary/title-tier workbook terms. A health snapshot is a time/ZIP/offer observation and must not be written into product copy. If the health section is blocked while copy work succeeds, set the overall state to DONE_WITH_CONCERNS and keep the health section state BLOCKED; use overall BLOCKED only when a required input prevents the requested deliverable.

### 6. QA, scoring, and correction log

Run final QA after localization and after any correction. Measure the final saved text, not an earlier draft. At minimum check:

1. exactly five bullets; every bullet matches ^【[^】]+]:.+, keeps the header and English half-width colon in the copy-ready text, covers a buyer situation, verified mechanism, and outcome, includes What-Who-Why naturally, and develops one main selling point in a short paragraph, normally two or three sentences;
2. five bullets collectively cover at least three distinct verified shopping scenarios and do not repeat the same scene or benefit;
3. title position, formula, no-brand handling, both character counts, and category/site override;
4. highlights display condition, character count, and zero meaningful-word overlap with title;
5. description count 1,500-2,000 characters, prohibited commercial content, localized Q&A structure, sufficient evidence for the length, and no copied bullet sentences;
6. frontend keyword format, source, lowercase/comma rule, title overlap, and report-only label;
7. backend separation, relevance, duplicate removal, and verified character/UTF-8 byte count;
8. attribute inventory mapping every supplied attribute to title, highlights, bullets, description, images, or 待确认;
9. the three semantic dimensions are represented across the listing: shopping scenes, foundational product information, and structured complete-product coverage;
10. the scene coverage matrix maps verified scenes across title, highlights, bullets, description, search fields, guide, images, and A+ text;
11. the title and highlights do not merely repeat the same scene, and the description/use guide add context rather than duplicate bullets;
12. removal of price, promotion, logistics, seller information, competitor brands, duplicate claims, and unsupported claims;
13. seven image slots, mobile/readability notes, and explicit image/claim risks;
14. optional 8-dimension diagnostic: title, bullets, images, A+ content, description, pricing, reviews, SEO coverage;
15. optional compliance scan: medical/health efficacy, superlatives, competitor/trademark terms, environmental claims, child safety, origin, endorsements, materials/food contact, and category certifications;
16. optional health snapshot fields and unchanged/changed/unknown recheck states.

Use PASS, FAIL, 待确认, or BLOCKED. Correct failures before delivery and show original issue, change, reason, and evidence. The HTML limits table must identify which resolved limits were applied and which adapter defaults were rejected. Do not convert 待确认 or BLOCKED into a pass. Q&A and block annotations remain supplemental and must never introduce unsupported claims or replace required fields.

## Copy-ready output formatting

The copy-ready five-bullet block must contain exactly five separate bullet entries. Each entry must begin at the first visible character with a localized header and English half-width colon in this form:

【Localized Benefit or Pain-Point Header】: Localized content.

Do not place numbering, an emoji, an HTML heading, a table cell label, or a Chinese explanation before the header. Put the Chinese rationale in a separate adjacent column or paragraph after the copy-ready text. Before delivery, inspect the rendered HTML and the raw text extracted from the copy-ready block; both must preserve all five headers and colons.

## HTML output contract

Return one complete valid HTML document with UTF-8 metadata, <html lang="...">, semantic headings, escaped user content, accessible tables, and readable styling. Use this stable order; optional sections may be inserted where marked:

1. 站点配置、输入与证据边界
2. 模式与战略简报（optional）
3. 竞品深度拆解
4. 关键词与机会洞察（含 coverage/gap matrix）
5. 场景覆盖矩阵与 AI 购物语义结构
6. 10X Listing（当地语言文案 + 中文解释）
7. 买家问答与异议处理（optional）
8. 产品使用指南
9. 七张图片设置逻辑
10. A+ 文本建议（optional）
11. 前台健康快照（optional）
12. 评分、合规扫描与自检清单
13. 修正记录
14. 运营附加建议：变体、Review、刷新触发器（optional）
15. 待确认事项与下一步

Use tables for limits, evidence, keyword coverage, scores, and correction history. Keep raw evidence, calculations, inferences, recommendations, and listing-stale / 待确认 conflicts visibly distinct. Save as UTF-8, reopen or parse the saved HTML, and recheck all limits against the final text before reporting completion. If the save path is unspecified, use outputs/meh-amz-skill/{ASIN-or-brand}/{YYYY-MM-DD}_{ASIN-or-topic}.html.

## Common mistakes and stop conditions

- Unknown site or unsupported health adapter: stop the unsupported check and mark BLOCKED; do not silently use US/France.
- Missing workbook: continue with product facts and competitor observations, but mark keyword metrics 待确认.
- Captcha, dog page, 404, or unavailable listing: report the page status and re-check path; do not infer live metrics.
- Competitor attribute conflicts with supplied product parameters: keep it in competitor analysis only and mark the gap unownable.
- No brand: never place [Brand] in paste-ready fields.
- Price, Buy Box, inventory, delivery, rating, BSR, and search position: always attach site, ZIP, timestamp, and offer context.
- Exact algorithm weights, ranking guarantees, and conversion percentages: treat as hypotheses unless measured evidence is provided.

Completion states are DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, or BLOCKED, and the HTML must explain the state.
