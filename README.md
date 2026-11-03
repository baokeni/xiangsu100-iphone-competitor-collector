# xiangsu100-iphone-competitor-collector

移动端竞品研究 Skill，帮助学习者从研究问题、竞品选择、用户任务规划，走到证据分析、横向比较和研究结论。

支持使用已有截图、录屏和文档；需要真机采集时，先核对设备环境与授权范围。教学陪跑模式会在需要用户回应时，说明下一步、所需材料，并提供可直接使用的回复示例。

## 快速开始

1. 点击 GitHub 的 **Code → Download ZIP** 并解压，或克隆本仓库：

```bash
git clone https://github.com/baokeni/xiangsu100-iphone-competitor-collector.git
```

2. 将解压后的仓库交给 Codex。完整 Skill 位于同名子目录，保留其中的 `references/`、`scripts/`、`agents/` 和 `assets/`。
3. 发送下面的提示词，将路径替换为你电脑上的真实位置：

```text
请帮我安装当前工作区中的 xiangsu100-iphone-competitor-collector Skill。
完整 Skill 文件夹路径：【本仓库路径】/xiangsu100-iphone-competitor-collector
先检查是否已安装，避免覆盖已有修改；检查入口、引用文件和脚本是否完整。
安装后告诉我是否可以开始使用。
```

安装完成后发送：

```text
请使用 xiangsu100-iphone-competitor-collector Skill，带我完成一次竞品分析。
研究主题：【填写产品、功能或用户任务】
我想解决的问题：【填写】
已有材料：【附件或文件路径；没有就说明暂无】
请一步一步引导，每阶段说明我需要做什么、提供什么、你会产出什么。
需要我回应时，给出下一步回复示例，也允许我修改或补充意见。
先明确研究任务，等我反馈后再进入下一阶段。
```

## 文档入口

- [完整 Skill](xiangsu100-iphone-competitor-collector/SKILL.md)
- [分阶段沟通提示词：从安装到复盘](竞品分析Skill_分阶段沟通提示词.md)
- [第一次使用与两条路线](第一次使用与两条路线_PPT文案.md)
- [执行与设备适配指南](iPhone真机竞品分析Codex执行指南.md)
- [材料说明模板](材料示范/筛选商品_材料说明模板.md)

提示词文档以京东外卖超级补贴为教学案例，使用时可以替换主题。文档中“旧案例原始材料”指授课者自己的案例目录；本仓库不含这些截图、评论报告或历史分析产物，新使用者需要提供自己的材料。

## 研究流程与交付

明确研究问题 → 选择竞品 → 规划用户任务 → 整理材料或授权采集 → 单竞品拆解 → 横向对比 → 回答研究问题。

- **探索研究**：解释竞品做法、差异、适用条件及未知问题。
- **设计决策**：在对照目标产品现状后，提出保留、调整、暂缓或补证方向。
- **教学陪跑**：按用户要求逐阶段讨论；默认连续执行模式无需反复确认。
- **版本跟踪**：仅在用户需要时启用。

交付包括图文 HTML、Markdown 及相应结构化研究数据，具体取决于研究类型。事实、推断和待验证项分开呈现；静态页面不能直接证明操作结果或用户效果。

## 研究澄清与过程留档

- **澄清问答**：第一阶段接入 `grill-with-docs`，联动 `grilling`、`domain-modeling`；复用已确认信息，每轮最多三个关键问题，逐轮记录问题、建议、回答与变更，交付研究任务卡和记录路径。完整规则见[研究澄清与问答留档](xiangsu100-iphone-competitor-collector/references/research-clarification.md)。
- **项目过程档案**：在已有任务笔记或档案中持续记录选样理由、可比条件、证据与实际覆盖、结论修订及用户/AI/教师的真实贡献，交接时链接当前报告和未决项；按需整理作品集框架、面试准备和个人 AI 工作流。详见[项目过程与AI协作](xiangsu100-iphone-competitor-collector/references/project-process-archive.md)及[可选模板](xiangsu100-iphone-competitor-collector/assets/project-process-template.md)。

`grill-with-docs`、`grilling`、`domain-modeling` 是独立 Skill，不随本仓库打包。AI应先检查是否可用；缺失时如实说明，使用本包内置的澄清与留档规则继续准备，不声称已调用缺失依赖。问答记录、过程档案分别链接当前任务卡与报告，不另建互相冲突的结论版本。

## 运行范围

已有材料路线可先从截图和文档开始，配套离线脚本使用 Python 3。手机自动采集还需要独立执行工程、设备驱动、签名及逐 App 验证；这些手机控制依赖不随本仓库一起分发。

Skill 包含设备适配指导和静态检查/规划脚本。历史工程曾使用 Mac+iPhone 路线，其他组合及每位使用者的当前设备都需要单独核对，安装 Skill 不代表真机采集已就绪。

真机检测或适配报错时，AI先查证并处理，优先用可用工具代办常规电脑操作；需要本人操作时，一次只引导一步、说明成功标志并复查。无需同学自行查教程或反复执行整套排错命令。详见[适配排错与引导](xiangsu100-iphone-competitor-collector/references/platform-adaptation.md#故障时由ai先处理降低同学操作成本)；Windows安卓USB连接另见[ADB分支诊断](xiangsu100-iphone-competitor-collector/references/windows-adb-diagnostics.md)。规则与静态检查更新不代表每台设备都已实测。

## 来源说明

方法参考与第三方许可说明见 [third-party-notices.md](xiangsu100-iphone-competitor-collector/references/third-party-notices.md)。设备流程的参考项目也保留在执行指南中。
