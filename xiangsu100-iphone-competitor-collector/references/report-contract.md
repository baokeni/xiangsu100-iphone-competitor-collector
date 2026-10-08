# 深度竞品报告契约

本契约用于基于真实单 App 运行证据、需要 UX 建议或设计取舍的报告；纯机制探索使用 [探索报告](exploration-report.md)，不强填建议字段。`research_context.stage` 表示研究成熟度，不表示报告用途。

采集报告不是最终竞品报告。设备会话结束并生成基础操作轨迹后，必须创建 `ux-analysis.json`，通过质量检查，再渲染为最终 `report.md` 和 `report.html`。

## 必需输入

- `manifest.json`
- `events.jsonl`
- 本次引用的 `screenshots/` 文件
- 本次引用的 `snapshots/` 文件
- 用户任务、目标用户、成功标准和授权范围

## `ux-analysis.json` 结构

以 [ux-analysis.schema.json](ux-analysis.schema.json) 为机器校验基线。核心结构：

```json
{
  "schema_version": 2,
  "research_context": {
    "stage": "deepening",
    "target_product": "准备改版的目标产品，可与本次观察的竞品不同",
    "positioning": "已知定位、用户习惯和界面风格；未知则说明",
    "business_constraints": "已知业务目标和约束；未知则说明",
    "core_questions": ["用户收藏后能否顺利继续归类？"],
    "prior_research_provided": true,
    "baseline": [
      {"id": "B01", "kind": "hypothesis", "claim": "收藏后缺少继续归类的入口", "source": "用户预研报告第 2 节"}
    ]
  },
  "research_review": {
    "counterexample_search": "实际检查了哪些替代路径、反例和遗漏；哪些没有覆盖",
    "incremental_value": "本次确认、修正、新发现与未确认的内容如何影响后续判断；没有新增发现时如实说明",
    "items": [
      {
        "baseline_id": "B01",
        "outcome": "revised",
        "assessment": "根据本次证据修正原判断，说明适用范围",
        "counterevidence": "实际反向证据或替代解释；没有发现也需说明检查范围",
        "evidence": ["screenshots/001.png"]
      }
    ]
  },
  "product": {
    "app": "App 名称",
    "platform": "iOS",
    "task": "用户任务",
    "persona": "最小、明确的人物假设",
    "success_criteria": "可观察的完成状态",
    "scope": "本次覆盖范围"
  },
  "executive_summary": {
    "overall": "证据约束下的整体判断",
    "strongest": "最强体验及原因",
    "weakest": "最大问题及原因",
    "top_finding_ids": ["UX-01"]
  },
  "journey": [
    {
      "step_id": "S01",
      "goal": "用户此刻的目标",
      "state": "页面状态",
      "action": "用户动作",
      "evidence": ["screenshots/001.png", "snapshots/001.json"],
      "goal_formation": {"rating": "clear", "analysis": "..."},
      "discoverability": {"rating": "uncertain", "analysis": "..."},
      "meaning_match": {"rating": "clear", "analysis": "..."},
      "progress_feedback": {"rating": "clear", "analysis": "..."},
      "friction": "本步骤的认知或操作成本"
    }
  ],
  "information_architecture": {
    "entry_points": "...",
    "structure": "...",
    "labels": "...",
    "wayfinding": "...",
    "scalability": "...",
    "management_loop": "..."
  },
  "screen_reviews": [
    {
      "screen_id": "P01",
      "name": "关键页面名称",
      "evidence": ["screenshots/001.png"],
      "visual_hierarchy": "...",
      "composition": "...",
      "typography": "...",
      "color": "...",
      "affordance": "...",
      "information_density": "...",
      "feedback": "..."
    }
  ],
  "findings": [
    {
      "id": "UX-01",
      "title": "具体问题标题",
      "severity": "major",
      "dimension": "discoverability",
      "journey_step": "S01",
      "evidence": ["screenshots/002.png"],
      "observation": "证据直接显示的现象",
      "principle": "认知走查、启发式、IA 或视觉原则",
      "user_impact": "对当前任务的具体影响",
      "root_cause": "候选原因（推断）及替代解释，或原因未明和证据缺口",
      "task_barrier": {
        "user_decision": "用户此刻要作出的判断",
        "missing_support": "缺少的信息、反馈或控制",
        "consequence": "对后续用户任务的影响，不是自动化工具的故障"
      },
      "priority_reason": "依据任务影响、证据强度与项目相关性解释关注程度",
      "recommendation": {
        "decision": "adapt",
        "applicability": "适用人群和情境，以及与目标产品定位、习惯、风格的匹配",
        "business_alignment": {
          "basis": "unknown",
          "analysis": "业务收益暂无法确认，说明需要验证什么",
          "source_or_gap": "没有业务指标资料，不能把推测当作事实"
        },
        "complexity_cost": "新增的信息、操作和维护负担",
        "minimum_change": "最小需要改变什么，或为什么保持当前行为",
        "alternative": "备选方案以及当前不采用的原因",
        "change": "具体改变",
        "rationale": "针对哪个候选原因、预计怎样起作用；待验证",
        "tradeoffs": "可能代价或副作用",
        "validation": "验证任务和指标"
      },
      "confidence": "observed"
    }
  ],
  "strengths": [
    {
      "id": "ST-01",
      "title": "具体优势",
      "evidence": ["screenshots/003.png"],
      "analysis": "为什么对用户目标有效",
      "confidence": "observed"
    }
  ],
  "limitations": ["本报告是专家评估，不代表真实用户测试结果。"]
}
```

## 质量门槛

### V2 字段规则

- `stage`：`exploration`（初步探索）或 `deepening`（深化研究），按学生所处阶段判断。
- 无预研时 `prior_research_provided: false`，`baseline` 可以为空，但 `core_questions` 至少一个。不强求一份预研文档。
- 有预研时提取与任务相关的基线，`kind` 为 `evidence`、`hypothesis` 或 `question`；`source` 标明用户材料出处。预研引用与本次采集证据不是一回事。
- 每个基线 ID 必须且只能被复核一次。`outcome` 为 `supported`、`revised`、`contradicted`、`unresolved`；新发现用 `new`，其 `baseline_id` 必须为 `null`。
- 有结论的复核必须引用本次运行中存在的证据。`unresolved` 可使用空 `evidence`，但必须填写 `limitation` 说明缺失状态；不能为通过校验虚构证据。
- `counterexample_search` 记录实际反例与遗漏检查及覆盖边界；每条复核的 `counterevidence` 解释反向证据或替代解释。未找到反例时如实记录，不要求制造反例。
- `incremental_value` 解释本次新增认识。允许没有新发现、没有问题条目；无预研且无新增发现时 `items` 可以为空，但仍要写检查范围和研究所得。
- 每条问题必须填写 `task_barrier` 和 `priority_reason`。正文优先问题最多 3 条，ID 不重复且确实存在；其余为补充观察。排序依据是任务影响、证据强度和项目相关性，严重程度单独呈现。
- `decision` 为 `adopt`、`adapt`、`keep`、`defer` 或 `reject`；后 3 种是有效结论。`change` 和 `minimum_change` 可说明保留什么、暂停什么，不强制增加功能。
- `business_alignment.basis` 为 `known`、`assumed` 或 `unknown`，`source_or_gap` 必须解释资料出处或信息缺口。产品匹配、复杂度、备选方案不能省略。
- Schema 检查字段类型；渲染器还检查本次证据文件、ID 关联、基线复核覆盖和建议完整性。结构通过不能证明推理正确，仍需按分析框架人工复核。

最终报告必须满足：

- 每条问题和优势至少引用一个本次运行目录中真实存在的证据文件。
- 每条问题都包含观察、原则、可能的用户影响、候选原因或原因未明、条件性改变、理由、代价和验证方法。`root_cause` 不要求确认根因，不能为填字段编造因果关系。
- `top_finding_ids` 必须指向真实 finding，最多 3 条且不重复。
- 至少完成一个任务步骤的四问认知走查。
- 至少分析一个关键页面，且不是只写“好看/不好看”。
- 信息架构只覆盖本次实际经过的局部结构。
- 未实测的字号、颜色、成功率和业务效果不能写成测量事实。
- 报告明确区分 `measured`、`observed`、`inferred` 和 `needs_validation`。
- 不得把状态变更授权扩大为分析或执行权限。

## 生成最终报告

先让设备层生成基础报告，再创建 `ux-analysis.json`。运行：

```bash
python3 .codex/skills/xiangsu100-iphone-competitor-collector/scripts/render_ux_report.py \
  --run RUN_DIR \
  --analysis RUN_DIR/ux-analysis.json
```

渲染器会：

1. 校验分析结构与所有证据路径。
2. 在覆盖前把基础报告保存为 `capture-report.md` 和 `capture-report.html`。
3. 生成最终 `report.md` 和 `report.html`。
4. 生成先读的 `decision-brief.md` 和 `decision-brief.html`。
5. 校验失败时保持原报告不变并返回非零状态。

只检查、不写文件：

```bash
python3 .codex/skills/xiangsu100-iphone-competitor-collector/scripts/render_ux_report.py \
  --run RUN_DIR \
  --analysis RUN_DIR/ux-analysis.json \
  --check-only
```

只更新决策摘要、不覆盖已增强的完整报告：

```bash
python3 .codex/skills/xiangsu100-iphone-competitor-collector/scripts/render_ux_report.py \
  --run RUN_DIR \
  --analysis RUN_DIR/ux-analysis.json \
  --brief-only
```

## 推荐报告顺序

对外阅读先给一页[设计决策摘要](analysis-result-design.md)：证据范围、最多三个方向及其适用条件、最小改动、代价和验证。渲染器正常生成 `report.*` 时同时生成 `decision-brief.md` 和 `decision-brief.html`；对已经人工增强过的历史报告，可用 `--brief-only` 只生成摘要，不覆盖完整报告。下列完整报告保留详细证据和 schema v2 字段；不要为缩短主文删去来源、反例或未验证项。

1. 研究范围和证据边界
2. 核心结论
3. 研究复核与新增认识：基线、反例、变化与待验证内容
4. 关键任务阻力与设计取舍：按指定优先顺序，最多 3 条
5. 完整任务链路与逐步认知走查
6. 信息架构与关键页面视觉检查
7. 补充观察（HTML 默认折叠）
8. 有证据的体验优势
9. 限制、人工介入和回滚状态
10. 基础操作轨迹链接

## 旧报告迁移

V1 数据不能只改版本号：需根据已有证据和用户材料补充研究语境、基线复核、任务阻力和设计取舍。材料缺失时明确未知或待验证；不要自动补写业务动机。移除旧 `ios_hig` 字段，不再生成已取消的分析维度。先使用 `--check-only` 验证，失败不会覆盖原报告。历史报告不会自动迁移，也不代表已通过新版质量规则。
