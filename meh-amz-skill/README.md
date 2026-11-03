# meh-amz-skill

面向 Amazon 卖家的竞品分析、Listing 撰写与质量审查工作流。默认按“提供竞品与关键词资料 → 编写 Listing → 验收 Listing”的日常顺序工作，并将依据、中文说明、客户可见文案和 QA 结果整理到一份 HTML 报告中。

## 适用场景

- 根据竞品 ASIN、商品链接和流量关键词分析竞品及搜索机会。
- 根据自有产品资料撰写或优化目标站点的 Listing。
- 检查已有 Listing 的字段格式、事实依据、关键词使用、变体边界和客户可见文案。
- 在需要时补充前台健康检查、七张图片规划或 A+ 文案。

可以直接调用 `$meh-amz-skill`，并附上你已有的资料。仅要求审查时可提供现有 Listing；不需要为了调用而补齐所有类型的输入。

## 日常工作流程

1. **提供资料**：提供竞品 ASIN/网址、流量关键词或关键词表、目标站点，以及自有产品的真实参数和材料。请明确标记自有商品与竞品；没有的数据不会被推测成产品事实或搜索量。
2. **撰写 Listing**：依据已核实的产品事实、竞品观察和关键词意图，撰写目标站点文案，并映射购物场景、产品属性和使用任务。按请求可包含标题、Highlights、五点、描述、前台/后台搜索词、使用指南、七图计划及 A+ 文案。
3. **审查 Listing**：先生成结构化 `listing_record.json` 并运行确定性验证，再根据通过验证的记录渲染 HTML；渲染后再次验证 HTML 中的客户可见文案。需要确认上线页面状态时，再追加前台健康检查。

## 主要规则

- **事实与竞品隔离**：客户可见文案只能使用有依据的自有产品事实。竞品属性和未证实信息不能写成自有产品承诺；内部审查问题放在中文说明、证据或 QA 中。
- **五点格式**：正好五点，每点使用 `【全大写小标题】 : 内容`，保留英文半角冒号及两侧各一个空格。正文为一句通顺的当地语言文案，按 What-Who-Why 规划，聚焦一个主要利益点，并在相关且自然时使用有数据支持的关键词。
- **字段约束**：工作流默认标题不超过 75 字符、Highlights 不超过 125 字符、产品描述为 1,500–2,000 字符。实际站点/类目规则已核实时，应使用相应配置覆盖默认值，并记录来源；默认值不代表 Amazon 对所有站点或类目的已核实政策。
- **Highlights**：可选；只有最终标题少于 75 字符时才使用。以逗号分隔简短特性/利益短语，不写完整句子，不重复标题中的词。
- **关键词**：保留每个候选词的来源和处理记录，区分搜索意图、负面关键词和禁用词。后台词补充前台覆盖，不重复完整短语；没有关键词数据时明确记录缺失，不编造搜索量。
- **场景与语音友好结构**：把不同购物场景映射到相关 Listing 模块。描述应直接回答商品是什么、适合谁、如何使用，以及包含什么或兼容什么；这只改善信息结构，不承诺 Alexa 收录、搜索排名或转化提升。
- **HTML 是交付格式，不是事实来源**：每个已批准的客户可见字段都需在 HTML 中准确呈现。最终交付前重新读取或解析 HTML 并扫描可见文案。

## 目录

- [`SKILL.md`](SKILL.md)：入口、日常流程、强制约束与交付门槛。
- [`references/listing-record-schema.md`](references/listing-record-schema.md)：`listing_record` 数据结构和字段关系。
- [`references/validation-and-qa.md`](references/validation-and-qa.md)：自动验证门槛、检查项和失败解释。
- [`references/output-and-adapters.md`](references/output-and-adapters.md)：工作模式、可选适配器与 HTML 输出结构。
- [`references/experience-first-copy-framework.md`](references/experience-first-copy-framework.md)：场景、体验模式和模块映射。
- [`references/marketplace-evidence.md`](references/marketplace-evidence.md)：站点、页面状态和商品属性的证据要求。
- [`scripts/`](scripts/)：结构化记录、文案、渲染及回归验证脚本。

## 自动验证

在 skill 目录下运行。完整流程先保存 `listing_record.json`，再通过预渲染门槛；仅当预检返回 `PASS` 后渲染 HTML，随后运行交付门槛：

```powershell
python scripts/preflight_listing.py listing_record.json
python scripts/validate_delivery.py listing_record.json final.html --output delivery_validation.json
```

升级验证器或 skill 后运行回归测试：

```powershell
python scripts/test_validators.py
```

单项验证器可帮助定位失败，但单项 `PASS` 不能覆盖汇总门槛的 `FAIL` 或 `ERROR`。交付前必须确认汇总预检和 HTML 交付检查均为 `PASS`。

## 证据边界

当目标站点不明确、竞品页面不可用、关键词表缺失或产品事实存在冲突时，报告应说明证据边界，并把相关事项留在中文说明或 QA 中。不得虚构价格、评分、排名、销量、认证、兼容性或算法权重；不得承诺排名、Alexa 收录或转化提升。前台健康检查依赖实际可用的站点/页面证据，不能用推断替代。
