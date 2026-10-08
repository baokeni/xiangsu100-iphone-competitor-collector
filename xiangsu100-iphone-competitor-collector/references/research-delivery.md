# 已有材料、设计交接与版本同步

本流程仅处理本地文件，不调用手机。用户要求分析截图、改报告或检查设计时直接进入对应阶段；缺证据先说明边界，只有新增采集属于当前任务时才走设备流程。

先按本轮用途分流：纯机制探索按 [探索报告](exploration-report.md) 交付，无需改版对象或 cross-analysis.json；以下第 1—3 节适用于设计决策及交接，第 4 节按多产物同步需要使用。

设计决策的最小输入是目标产品、最新研究目标、用户任务与本轮范围、已有文件路径；产品定位或业务条件未知可明写未知。需要设计取舍时，只有截图也可按 [分析方法](analysis-result-design.md) 和 [横向契约](cross-report-contract.md) 生成 `cross-analysis.json` 与图文报告，不补造 manifest、events 或设备信息。交付时提供可打开的 HTML、结构化来源和缺口说明；报告修订只更新受影响产物，设计交接另按第 3 节验收。仅当有多份派生产物需要同步时使用第 4 节清单，不把全套文档当成所有任务的起步门槛。

默认完成本轮材料分析和结论交付，不要求长期跟踪。不同用户路线记录在本轮计划与报告中；用户明确选择周期基线或跨期对比时，才采用 [research-cycles.md](research-cycles.md) 的分期快照。需要目标产品设计取舍时使用下述 cross-analysis.json。

## 1. 当前研究入口

一个项目选定一份 `cross-analysis.json` 作为当前目标、目标产品现状和设计决定的共同入口。竞品原始观察与采集记录保持独立。用户修正目标时保留旧版作为明确标注的历史文件，只修订受影响的目标与结论，不推翻其余已认可内容。

新报告的 `research_goals` 每项包含：

- `id`、`statement`：稳定编号与当前解释。
- `original_text`、`revision_source`：用户原话及修订来源（对话日期/文档位置）。
- `priority`（primary/supporting）、`priority_reason`：本轮优先级与原因。
- `experience_status`（unknown/problem_observed/satisfactory/mixed）：目标产品的体验判断，与优先级分开。认可旧分析不等于现状满意。

每个维度必须有 `goal_id`、`target_evidence_ids`。后者可为空，此时判断只能依赖明确条件，不能声称目标产品已有问题。竞品来源仍在 `cells[].evidence_refs`，验证任务仍在 `target_decision.validation`。

## 2. 静态现状证据

这里的 `target_baseline` 仅表示本轮目标产品的现状证据，不是定期跟踪基线，也不要求上期材料。根字段 `target_baseline`：`status`（unknown/partial/observed）、`summary`、`limits`、`evidence`。无目标产品材料也能继续：填 unknown、空数组及未知边界，不编造现状。

`evidence[]` 每项：

```json
{
  "id": "T01", "source_type": "user_screenshot",
  "page": "文章列表", "object": "样例文章", "state": "默认列表",
  "captured_at": "unknown", "observed": "列表已有收藏入口",
  "limits": "不能确认点击结果与返回状态",
  "continuity": "not_established",
  "path": "sources/list.png", "sha256": "填写原文件SHA256"
}
```

来源类型为 user_screenshot/device_capture/document；时间不明写 unknown，不用导入时间替代采集时间。`continuity=documented` 必须附 `continuity_refs` 路径数组，指向事件或前后状态证据，并人工核对对象一致。哈希只验证来源完整性，不证明内容或流程正确。静态已知、动态未知、效果未测试分别描述；不要重复建议新增已可见的能力。

```sh
python3 scripts/render_cross_report.py --analysis PROJECT/cross-analysis.json --check-only
# 仅历史读取；输出带历史标识，不能用来验收新报告
python3 scripts/render_cross_report.py --analysis ARCHIVE/cross-analysis.json --allow-legacy
```

## 3. 设计交接与成图检查

使用 `design-handoff.json`。路径相对此文件，包含：

- `analysis: {path, sha256}`：本次设计依据的准确版本。
- `scope_goal_ids`、`scope_note`：这张图/原型覆盖的目标与范围，未覆盖页面留在后续任务。
- `regions[]`：每项含 name、dimension_ids、preserve、change、information_priority、data_policy、states、acceptance。
- `acceptance[]: {id, criterion}`：生成前写可判断的检查项，不以“更美观”“已生成”代替。
- 生成后增加 `artifact_review`：path、sha256、reviewer、reviewed_at、effect_validation，以及 `checks[]: {check_id, outcome, note}`。outcome 为 pass/needs_revision/not_verified；必须覆盖全部判据。effect_validation 记录用户效果证据或明确未验证。

`dimension_ids` 自动关联目标、竞品证据、目标现状和验证任务。任务单须说明保留哪些能力、真实字段与示意数据、信息先后、默认/变化/空态等关键状态。成图后打开实际文件，逐目标检查：分类是否同维、价格是否与对象及适用条件对应、信息是否更早可见、文字可读性和必要能力有无丢失；按项目选择判据，不固定首屏比例、卡片数量或字号。仅一张静态图不能验收动态状态。

```sh
python3 scripts/research_delivery.py check-design PROJECT/design-handoff.json
python3 scripts/research_delivery.py check-design PROJECT/design-handoff.json --require-design-pass
```

前者检验记录完整性，允许如实记录待修订；后者只在全部设计检查 pass 时返回成功。任一通过均不代表用户效果已验证。上游分析或成图变化后旧哈希不再有效，必须重审，不直接补写新哈希冒充复查。

进入实现前，另按 [readiness-review.md](readiness-review.md) 记录目标方案和实现条件的实际复核；结构检查通过不替代语义审阅，也不代表已证明用户收益。

## 4. 当前、历史与概念稿

`delivery-manifest.json` 包含 `artifacts[]`，每项为 `id, path, role, dependencies`。role 为 current/historical/concept；dependencies 是输入文件路径数组，包括当前结论、实际引用的证据文件、渲染器和设计任务单等。路径相对此清单。原始采集标 historical；概念设计标 concept 并链接成图检查结果。

依赖图应无环；清单本身不作为产物依赖。按上游到下游重建（结构化输入→图文报告/摘要→总览）。每次实际重建或逐项复核后，才逐个登记：

```sh
python3 scripts/research_delivery.py record PROJECT/delivery-manifest.json --artifact report
python3 scripts/research_delivery.py check-release PROJECT/delivery-manifest.json
```

record 保存更新时间、产物哈希与输入哈希，不代表验收。check-release 重新计算，不依赖手写“完成”；上游或产物变化输出 stale（待更新），缺失为 missing，未登记版本为 pending，历史为 historical。上游已过期时下游也过期。不能对未更新的文件批量 record 来消除错误。

图文报告、目标表、方案摘要和总览应由共同数据读取当前判断；报告有意保留的旧结论在文件与总览入口标历史。不能只换顶部声明却让正文继续写过时的现状判断。交付前对照各页的目标、已知/未知及建议，哈希检查不能替代语义复核。
