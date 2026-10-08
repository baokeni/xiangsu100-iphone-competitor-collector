# 横向决策报告数据契约

本契约用于需要目标产品设计取舍的横向报告。只了解竞品机制时使用 [探索报告](exploration-report.md)；不要伪造目标产品、页面调整或用 `--allow-legacy` 绕过本契约。仅在用户选择建立长期基线或周期变化跟踪时，使用 [research-cycles.md](research-cycles.md)，不强填改版方案。一次性任务与不同用户的路线走查不要求周期基线或分期快照。横向报告是独立分析层，可引用单竞品报告或直接分析已有材料。使用 `cross-analysis.json`，不改变真机单竞品 `ux-analysis.json` 的 schema v2，也不覆盖原始报告或证据。只有一个观察对象时可登记一个平台/频道并说明范围，不虚构第二个竞品或设备运行记录。先按目标产品的用户决定选维度；不能从竞品页面清单直接生成固定维度。

## 输入

运行 `python3 scripts/render_cross_report.py --analysis cross-analysis.json --output-dir 输出目录`。可先加 `--check-only` 检查数据与证据链接，不写文件。输出为 `cross-decision-report.md` 和 `cross-decision-report.html`。输入 JSON 使用如下字段：

- `title`、`target_product`、`task`、`scope_note`、`limits`：说明研究问题、样本条件与未验证边界。目标产品未实测时必须在 `limits` 明说建议是设计假设。
- 新报告必填 `research_goals: [{id,statement,original_text,revision_source,priority,priority_reason,experience_status}]`；字段含义见[交付契约](research-delivery.md)。`priority` 为 primary/supporting，与体验满意程度分开；认可前版分析不构成满意判断。每个 primary 目标须有对应的 primary 设计决定。默认省略目标将失败；只有显式 `--allow-legacy` 才读取无目标的历史输入，输出带历史提示，不能用于新报告验收。
- 新报告必填 `target_baseline`（status、summary、limits、evidence）；每个维度填写 `target_evidence_ids` 引用目标产品证据编号。缺材料时可明确 unknown 与空数组；已观察项校验来源文件及 SHA256。静态截图不证明连续操作，完整字段见[已有材料入口](research-delivery.md)。
- `platforms`: `[{id,name}]`；`channels`: `[{id,name,platform_id}]`。同平台不同频道分开比较，独立平台数只从 `platforms` 计。每个频道只能指向一个已登记平台。
- `dimensions`: 按研究目标与用户决定排列。新报告每项填写 `goal_id`（指向 `research_goals.id`）、`id`、`user_decision`、`necessary_support`、`comparability`、`priority`（`primary` 或 `supporting`）、`cells` 和 `target_decision`。一个目标可以包含多个页面触点；首页最多突出三项，不限制完整分析维度数量；primary决定不得挂在supporting目标下。研究优先级与最终行动优先级分别记录。
- 每个 `cell` 指向一个 `channel_id`，并写 `status`、`mechanism`、`decision_support`、`friction`、`unknown`、`evidence_refs`。状态只可为 `observed`、`partial`、`not_verified`、`user_excluded`、`not_applicable`。每个维度必须为所有频道填写单元；未验证或排除的单元不填“无此功能”或零分。已观察/局部观察的单元必须有证据。
- `target_decision` 写 `action`（`adopt`、`adapt`、`keep`、`defer`、`reject`）、`judgment`、`conditions`、`minimum_change`、`cost`、`alternative`、`validation`、`falsifier`。采用与调整都只是目标产品建议；不能将竞品表现推断为目标产品的问题已证实。
- 用户需要**设计方案**时，在首页 `primary` 维度加 `design_proposal`：`title`、`placement`、`components`（界面组成）、`interaction`、`key_states`、`screens`（每屏含 `name`、`title`、`blocks[{label,value}]`、`action`）、`evidence_images[{path,caption}]`。示意屏明确标为拟议界面，不能伪装成目标产品当前截图；仅引用逐张审查过的既有竞品图片。报告首页并排展示界面示意与证据截图，技术细节折叠到后文。没有可靠图片时不要编造截图，可保留文本摘要并写明缺口。
- `evidence_refs` 是相对输入 JSON 所在目录的本地文件路径，可指来源索引、原图、快照、事件或研究文档。渲染器检查文件存在和可用材料类型，拒绝代码充当观察证据；若指 `source_evidence_index`，还检查其 `source` 文件存在及哈希一致（相对 source 路径以索引文件目录解析）。文件格式与哈希仍不证明内容相关，交付前需打开来源核对其是否支持具体表述。报告同时给出索引和原图入口，但不自动嵌入可能含敏感信息的截图。
- `detail_report` 可指向完整横向报告，作为第二层。详细流程和图库保留来源；不默认增加定位矩阵或独立机制拆解章节，只有用户明确需要且证据足够时另用相应方法。
- `related_links` 可列出 `[{label,path}]`，在首页醒目连接原横向图文报告、证据图库或研究总览。新试稿不能让原报告入口消失。路径相对 `cross-analysis.json`。
- 可选 `positioning`：`axes` 中恰好两项，每项写 `name` 与 `criteria`；`entries` 为每个频道各写一项 `channel_id`、`status`（`placed`、`partial`、`unpositioned`）、`x`、`y`、`reason`、`evidence_refs`。只有两轴都有证据时才用 `placed`，否则明确待定位；轴依项目选择，不预设价格或信任。
- 可选 `flows`：每个共同任务分支写 `branch` 与 `routes`，每个频道各一项 `channel_id`、`status`（与维度单元相同）、`route`、`evidence_refs`。这里填实际观察到的路由；计划路径不得伪装成已走通。

## 阅读与验收

所有当前研究目标都须有对应维度，包括 supporting 目标；缺证据时可写未验证单元与暂缓取舍，仍通过最终总结说明页面范围和补证任务。明确不在本轮范围的目标留在 scope_note/历史记录，不登记为当前目标后静默遗漏。历史 `--allow-legacy` 可兼容目标覆盖不全，但不能作为新报告验收。

`source_evidence_index` 必须有可用的 source 与 64 位十六进制 source_sha256，缺失、格式错误或原件变化均不通过。不要为通过检查补写未复核原件的新哈希；直接引用图片/文档仍检查文件存在，只有登记哈希的索引才做完整性比对。

新报告必填 `redesign_summary`：

- `conclusion`：最后总体判断；`ranking_basis`：本轮排序依据；`not_now`：暂不做什么及原因。
- `items[]`：`id`、`title`、`dimension_ids`、`priority`（P1/P2/P3）、`order`（正整数、唯一）、`stage`（prototype/verify/implement/keep/defer/reject）、`reason`、`depends_on`（方案id数组，无依赖为空）、`validation`、`page_changes`。
- 每个已分析维度至少被一项总结覆盖，可用保持/暂缓结论。通过dimension_ids追溯goal_id、竞品单元和目标产品现状。不要求各级都有事项，不能全写P1回避取舍。
- `page_changes[]`每项必填`page`、`module`、`current`、`change`、`preserve`、`states`、`acceptance`、`target_evidence_ids`。无现状材料时数组为空，current明确未知，change写条件性方案。对保持/暂缓项也指出页面范围、保留内容或待核对项。
- order须符合优先级，前置事项必须存在且顺序更早。prototype/implement不能与维度的keep/defer/reject取舍冲突。stage=implement还需`readiness_evidence_refs`指向结构化、通过且未过期的目标方案验收记录；不能用任意附件或竞品表现推断实现就绪。格式、绑定哈希及命令见 [readiness-review.md](readiness-review.md)。
- 无最终总结、无页面落点、来源编号缺失、依赖顺序冲突将被拒绝。显式历史读取仍可兼容旧输入，不能作为当前交付验收。

HTML/Markdown在分析后生成完整的“最后总结：改版优先级与页面调整”，HTML顶部提供直达链接。图文观察与完整图库继续保留，不用一张文字清单替换原竞品分析。

生成图片/原型后，使用 `design-handoff.json` 逐目标检查实际产物，使用 `delivery-manifest.json` 检查依赖版本。具体命令见[设计与版本验收](research-delivery.md)。这两份文件独立于单竞品 schema v2，历史原始证据不迁移或伪装为新采集。

第一页先显示研究目标与方案的对应、原报告入口和最多三项设计方案，再显示逐维度的并排证据。事实写在 mechanism；效果解释写在 decision_support/friction，并标明推断或测试依据；反例与替代解释写入 friction/unknown；目标产品建议写在 target_decision。每项维度保留可比口径和未知项，不能把未采集写成差评。读者应能回答：服务哪个目标、具体改哪里、竞品证据支持到哪一步、目标产品依赖什么条件、什么结果会推翻建议。结构校验和链接校验不等于分析判断通过，也不等于浏览器视觉验收或真实用户测试。
