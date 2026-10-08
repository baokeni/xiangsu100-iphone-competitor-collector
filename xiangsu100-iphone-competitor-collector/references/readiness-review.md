# 从“附件存在”到“方案已复核”

普通观察材料可以支持研究；只有当前目标方案及实现条件经过复核，行动才能标为 `implement`。没有这份记录时，根据实际情况使用 `verify` 或 `prototype`。该门槛仅适用于进入实现，不增加日常观察/周报的工作量。

## 记录实际复核

`redesign_summary.items[].readiness_evidence_refs` 引用如下 JSON。路径相对 cross-analysis.json；记录内部证据路径相对记录文件。每份引用的记录都必须完整通过，附加材料放在 checks.evidence 中。

```json
{
  "kind": "implementation_readiness_review",
  "target_product": "与分析中的目标产品一致",
  "item_id": "R1",
  "subject_sha256": "由下面命令计算",
  "reviewer": "实际复核人或代理身份，不虚构人工签字",
  "reviewed_at": "2026-09-28T14:00:00+08:00",
  "outcome": "pass",
  "effect_validation": "原型任务检查通过；上线收益未验证",
  "checks": [
    {
      "id": "C1", "category": "target_design",
      "criterion": "目标方案保留必要信息并能完成约定任务",
      "outcome": "pass", "note": "写实际观察结果及适用范围",
      "evidence": [{"path": "target-review.md", "sha256": "实际文件SHA256"}]
    },
    {
      "id": "C2", "category": "implementation_conditions",
      "criterion": "所需字段、依赖及实现限制已核对",
      "outcome": "pass", "note": "写实际核对结果，不用未知冒充具备条件",
      "evidence": [{"path": "conditions-review.md", "sha256": "实际文件SHA256"}]
    }
  ]
}
```

先完成拟交付方案与研究依据，再计算复核对象哈希（不会自动生成 pass）：

```sh
python3 SKILL_DIR/scripts/redesign_summary.py --analysis PROJECT/cross-analysis.json --item R1
```

哈希包含当前方案（排除验收文件路径以避免循环）、所关联维度/目标、目标产品与现状。改动方案或依据后旧复核失效。引用的实际验收附件也检查 SHA256，不能只更新哈希而跳过重审。保持失败或待验证记录；程序会拒绝将其作为进入实现依据。

## 能查什么，不能查什么

- 程序检查：记录类型、产品与方案对应、输入版本、复核身份/日期、目标方案和实现条件两类检查、逐项通过、来源存在与哈希。拒绝截图/代码/随意 JSON 直接代替验收记录。
- 实际复核：打开附件，看它是否真的回答验收项；截图只能支持可见状态，交互任务需要相应过程/结果证据。检查替代解释与剩余风险；Agent 自审要如实标注，不能冒充业务方批准。
- 不承诺：程序无法鉴别伪造的文字记录，也不能单凭结构证明推理正确、用户效果或上线批准。不要把“校验通过”展示为这些结论。

历史输入可显式按旧报告读取，不重写旧证据为新验收；新的当前交付使用上述门槛。
