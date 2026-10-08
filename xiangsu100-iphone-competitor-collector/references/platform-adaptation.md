# 设备环境识别与适配

## 工作方式

先判断本轮是否需要控制设备。已有材料分析、报告修订、设计交接不需要手机驱动。只有当前任务包含真机采集/环境建设，才进入设备适配。Skill名称保留以兼容已有调用，不再将所有用户限定为Mac+iPhone。

默认流程：**识别环境 → 选择已有路线 → 针对缺口研究 → 隔离建设 → 目标App验证 → 正式采集**。检测不匹配后自动进入研究和方案准备；不要求用户自己找技术。不能把“同学跑通过”“官方支持”“模拟通过”“设备连上”合并为本机已适配。

### 环境识别/模拟脚本

```sh
python3 scripts/plan_device_adapter.py inspect --project PROJECT --output adaptation-plan.json
python3 scripts/plan_device_adapter.py simulate --host windows --phone android --tools node adb --output windows-android-plan.json
python3 scripts/plan_device_adapter.py simulate --host windows --phone ios --ios-major 18 --wda-available --output windows-ios-plan.json
```

Windows可用 `py -3` 代替 `python3`；所有路径相对当前Skill安装目录调整。inspect只读主机类型、架构、PATH中的工具位置、项目文件及包版本，不运行设备命令，不联网、不安装。手机类型必须来自用户说明或已授权的设备发现；默认unknown，不能从Windows推断安卓，也不能从Mac推断iPhone。模拟始终标simulation，不生成采集证据。工具存在不代表版本、驱动、权限或设备已就绪；脚本的 `ready_for_capture` 始终为false，退出码0只表示方案生成成功。

识别的是运行终端所在执行主机。WSL、远程SSH和容器可能返回Linux，继续核对手机在哪台机器、USB由谁持有，不猜测Windows宿主机。多个设备必须明确选择，不能取列表第一个。

## 路线矩阵（文档核对：2026-09-22）

|组合|候选技术|此包状态|
|---|---|---|
|Mac+iPhone|现有agent-device 0.20.8 + XCTest封装|有既有工程及历史样本，当前仍需status与目标App验证|
|Mac+安卓|先检查已安装agent-device的Android能力与ADB；否则评估Appium+UiAutomator2|分流可模拟，新的安全封装和真机验证待完成|
|Windows/Linux+安卓|Appium+UiAutomator2+Android SDK/ADB；同学验证过的其他路线优先复核|官方列出这些主机支持；本项目尚无实机验收|
|Windows/Linux+iPhone|满足条件时Appium XCUITest非Mac路线；也可由授权远端执行|有限支持，按下列条件判断，不能一概判定不可行|

Windows/Linux+iPhone的官方有限路线要求iOS/tvOS 18+真机，预装WDA或外部管理的WDA，RemoteXPC通信，以及显式设备ID/系统版本。Windows不能执行默认xcodebuild构建WDA；准备WDA的签名/构建来源需单独说明。`appium-ios-remotexpc`官方文档提示手动安装时至少5.1.0，运行时须重新核对整套兼容版本。缺这些条件时研究学生成功方案或授权Mac执行端，不自动购买云真机、上传登录态或连接陌生远端。

官方来源：

- [agent-device安装与平台依赖](https://oss.callstack.com/agent-device/docs/installation)：Android需要SDK/ADB；本项目已安装包是0.20.8，当前网站文档可能对应更新版本，不直接照抄新命令。
- [Appium UiAutomator2主机要求](https://github.com/appium/appium-uiautomator2-driver#requirements)：Windows/Linux/macOS、SDK及JDK；必须按手机API和驱动版本核对兼容性。
- [XCUITest非Mac主机](https://appium.github.io/appium-xcuitest-driver/latest/guides/non-macos-hosts/)及[版本关系](https://appium.github.io/appium-xcuitest-driver/latest/getting-started/system-requirements/)：有限支持条件。
- [Android ADB](https://developer.android.com/tools/adb)：USB调试、设备授权和指定设备。

## 自动研究与建设边界

1. **复用成功案例**：记录同学使用的主机OS/架构、手机OS、工具及驱动版本、连接方式、目标App、命令和实际产物。缺详情先记user_reported，继续官方资料研究，不将口头可行等同已验证，也不因此否定案例。
2. **写适配计划**：记录当前组合、推荐后端、版本依据、缺少条件、安装位置、预计会变更什么、人工动作、验证步骤和退出方式。工具版本未知时先检查，不自动安装latest。更换路线前说明具体失败证据及新路线条件，不进行循环猜试。
3. **在当前授权内建设**：用户已要求建设适配环境时，可继续创建独立项目、复用/安装项目内兼容依赖、实现适配器并测试，不反复要求“继续”。仅咨询/模拟时做到计划与离线测试。管理员驱动、设备信任、USB调试授权、签名凭据、系统安全/网络修改等需要的真实用户动作不能代签或跳过；已授权的同一动作无需再次询问。
4. **可恢复执行**：依赖隔离，保留现有工作后端；不自动修改当前 `default_backend`，不禁用支付/授权规则求跑通。发现同一阻塞反复出现且无新证据时停止该尝试，给出最小缺口；不每次失败就换一套框架。
5. **通过后再采集**：记录实际设备/App/工具版本及证据路径，范围只覆盖这组组合。下次版本/设备变化重新检查，不推广成所有安卓或所有Windows均通过。

## 新适配器统一接口与验收

在独立执行工程实现 `status/open/snapshot/screenshot/press/fill/scroll/back/close/finalize`，禁止让模型通过任意shell命令绕开安全封装。Android将package/activity映射到App Card，iOS用bundle ID；保留设备唯一标识、权限、停止词和授权范围。

各后端规范化输出：成功/失败、时间、后端及版本、设备标识、目标App、动作参数、前后状态引用、截图/结构文件路径与哈希、错误和返回证据。未知的可点击性/结构保持unknown，不能默认true；press/fill基于当前观测解析元素，不能跨截图复用坐标或ID。没有页面结构时明确能力降级，只有经复核的当前截图定位才可作为条件路径，禁止盲目固定坐标回放。

最小实机验证：

- 唯一设备可见且用户已授权，目标App可打开；不能只截系统桌面。
- 获取目标App真实截图与结构；证明App/页面身份，而非仅HTTP成功。
- 在明确无副作用的页面完成安全导航、滚动及返回，保存前后证据。
- 支付/下单/验证码等拦截先用离线假事件验证，不在真机点击交易按钮“测试拦截”。观察支付页的授权仍不等于交易授权。
- 正常关闭、连接丢失及重试不丢证据；若本轮允许数据变更，再检查对应回滚，不为验收强行制造数据。
- Windows检查路径空格/中文、UTF-8、命令参数数组及二进制截图写入；不沿用zsh/brew/xcrun命令，不用旧PowerShell文本重定向保存PNG。

适配器的事件/截图只是采集层输出；接回原报告、分支覆盖、来源哈希及当前目标校验，不能因为换了驱动就减少研究验收。

## 当前实现边界

本Skill已提供环境静态识别、路线规划、模拟测试和适配指导。**脚本不是Android/Windows驱动，也不会自动编译一个已验收的后端**。实际适配由Codex按本指导在使用者环境中继续完成；本包尚未交付这些新组合的运行封装或真机通过证明。只能在对应后端实装、逐项实测后把状态升级为已验证。
