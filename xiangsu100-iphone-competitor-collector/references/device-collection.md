# Real-device collection procedure

Read this entire procedure before authorized capture. Commands using `scripts/iphone_device.py` run from the verified execution project; bundled report tools run from the Skill directory.

For real-device collection, first identify the host and phone separately using [platform adaptation](platform-adaptation.md). The bundled `scripts/plan_device_adapter.py inspect` is a static host/tool check; phone identity is unknown until declared or discovered within the authorized task. Non-Mac/iPhone combinations automatically enter adaptation planning, relevant official-document research and, when environment construction is authorized, isolated adapter implementation. No repeated permission is needed for already authorized work. Real-device smoke evidence is required before research capture; simulation or tool presence never sets readiness.

Only when the selected route is local Mac+iPhone, inspect the existing execution project:

- If `scripts/iphone_device.py`, `agent_device_ios/`, and `config/app_cards/` exist, use the existing safe execution project.
- If they do not exist, do not attempt App operations yet. Create an independent iOS proof-of-concept project, install `agent-device@0.20.8`, implement a safe wrapper and evidence store, run preflight, and only then begin the product task.
- Never claim that the two instruction files alone provide device control. The Mac still needs Xcode, an available Apple development team, a trusted physical iPhone, Developer Mode, and a signed XCTest Runner.

## Recheck current runtime state before continuing capture

At each new turn that resumes device work, and after reconnect, permission/environment/version changes or session failure, recheck the selected device, current permission scope, service reachability and agent session. Reuse unchanged confirmed task scope and setup information. Prior success remains historical evidence; it cannot prove current connectivity. For Windows ADB use [Windows ADB diagnostics](windows-adb-diagnostics.md), including its bounded ordinary-PowerShell comparison.

On failure, follow [AI-owned troubleshooting](platform-adaptation.md#故障时由ai先处理降低同学操作成本): investigate and perform authorized routine computer steps with available tools first. If a human-only step remains, show one action and its observable completion signal, then inspect the result and continue. Do not turn each failed check into a command list for the student or assume access to their computer when tools are connected elsewhere.

Keep ADB server, phone transport, agent-device daemon/session and Snapshot Helper as separate states. A lost agent session with a healthy ADB device calls for session recovery, not an ADB restart. On session recovery, capture a fresh screenshot/structure and resolve current elements again. Check the selected version's actual help; do not assume newer `doctor`, helper or session commands exist.

Before the first target-App smoke test, verify any required Helper is available. If an OEM install confirmation or phone lock blocks it, ask the user to complete that specific on-device step, then retry the failed step once with fresh evidence. Authentication stays with the user. Do not treat missing Helper, a later lock screen or session expiry as the proven cause of an earlier empty device list.

Record connection success, target-App screenshot success, page-structure success, safe navigation/return and saved evidence separately. Set capture readiness only after the required smoke checks pass on the selected device/App; a screenshot alone is partial capability. Research completion still requires the planned task coverage and analysis. Static `inspect` and `simulate` never perform these runtime checks.

Only for real-device collection, extend that contract with:

- App name and bundle ID (iOS) or package/activity (Android), selected backend and explicit device identity.
- A pre-capture journey plan with branch IDs, entry conditions, expected transitions, return/recovery paths, evidence requirements, and per-App applicability. Planned paths are hypotheses until observed.
- Search terms or test content identifiers.
- Read-only actions that are automatically allowed.
- State-changing actions explicitly authorized by the user.
- Unique temporary data names.
- Required rollback actions.
- Stop conditions and report topics.
- Analysis focus: task learnability, efficiency, information architecture, visual hierarchy, or other user-requested dimensions.

Before starting a run, verify that the execution project has an App Card or equivalent configuration for the requested bundle ID. The current wrapper may have been validated for only one App. If the requested App is not configured, add and validate its bundle ID, launch behavior, safe-page rules, and stop terms before business actions. Never reuse another App's configuration or claim cross-App support from one successful sample.

Read-only actions may include opening or closing the App, browsing, searching, scrolling, returning, taking screenshots, and reading non-sensitive accessibility structure. When the user explicitly permits checkout/payment-page observation, record that scope and allow viewing order summaries, fees, discounts and payment-method information. Viewing a page is distinct from submitting an order or transferring money; never infer payment authorization from page-view authorization.

State-changing actions are denied unless the user explicitly authorizes them for the current task. Examples include favorite, unfavorite, create collection, assign content to the created collection, or delete the created collection. Authorization must be limited to one clearly identified test item and uniquely named temporary data. Do not touch existing user collections or unrelated content.

Always prohibit likes, follows, comments, private messages, publishing, sharing, adding to cart, ordering, purchasing, payment, account changes, password input, verification-code input, and modification of unrelated user data unless a later user request explicitly establishes a safe and narrowly scoped test contract.

## Plan the journey and branches before capture

Before App operations, read [references/journey-planning.md](journey-planning.md). Create a user-readable flow diagram and branch table, plus `journey-plan.json` in the task preparation directory. Link the plan from the task contract. A page list or single happy-path arrow is insufficient.

Derive branches from the research questions and supplied walkthrough, including relevant alternative discovery routes, detail drill-downs, decision changes, back/return, and recovery. For a food-selection task, explicitly plan direct list browsing versus filtering first, item detail to review list/review detail, item detail to shop information/menu, SKU selection/change/cancel, and return-to-list comparison. Verify each App's actual routing; never assume these pages or links exist everywhere. Do not reduce all branches to one optional detour merely to save tokens.

At the stage checkpoint, proactively show the goal, shared scenario, diagram, required and conditional branches, App mapping, success criteria, evidence needs, and remaining gaps. Resolve missing scope or authorization before dependent operations; existing confirmed decisions do not need repeated permission. Purely operational smoke tests may be scoped separately and cannot count as branch coverage.

During capture, maintain per-App branch coverage with evidence and reasons for skips/blocks. Reuse evidence for shared states instead of replaying the whole journey for each branch; preserve the entry, meaningful change, and return state. Cover decision-relevant branches without enumerating every filter/SKU combination. Any reduction in coverage must be stated, never silently dropped.

Before analysis, reconcile the plan against actual evidence. Distinguish planned, observed, blocked, not found in this bounded run, and genuinely inapplicable routes. Report gaps and route differences; do not turn planned diagrams into observed information architecture. Keep this planning sidecar separate from the existing report schema v2.

For new `research_v2` runs, place the current App's `journey-plan.json` in the run directory before `finalize --status completed`. Each observed branch needs a `step_checks` entry for every planned step, actual route, file evidence and fresh return evidence when a return is planned. An explicitly excluded or inapplicable branch needs a reason. Partial, blocked, skipped and unknown branches keep the run partial. Authorized state changes also need `rollback-review.json` with `verified: true` and file evidence after rollback. The controller's `completed` status covers capture and branch evidence; final report, evidence review and user acceptance remain separate gates. Historical runs retain their saved acceptance mode.

## Complete the authorized capture continuously

After scope and device readiness are established, aim to finish one App's agreed capture in one continuous session. Reuse confirmed decisions and the current run. A progress message is not an approval gate: show progress and continue without waiting for “继续”. Check each stage internally before proceeding; ask only when missing information or an actual user-only step prevents safe continuation. Do not end the turn merely because one branch is complete.

Group branches around their shared parent page: finish the relevant detail, review, shop/trust and SKU detours with their returns before moving to another candidate. Resume from the last verified state after bounded recovery instead of replaying from the homepage. Before closing, compare each branch's planned_steps with actual evidence and fill safe, in-scope gaps in the same session. Record user-excluded or genuinely blocked steps explicitly; do not reopen an excluded branch.

Reduce redundant observations and evidence, not required task coverage. Keep the action-to-observation dependency; do not blindly batch clicks through unknown pages. Separate first-time environment setup from routine capture, and do not restart a healthy session just to report progress.

## Show visual collection progress

At meaningful branch checkpoints, show a small selection of newly informative screenshots inline in the conversation using absolute local paths, with a brief action/result/gap caption. A link alone is insufficient. Group related results in one update and continue work immediately. Do not make every tap, snapshot or return a separate image/update cycle. If an update is due but there is no new visual evidence, give concise text progress without taking another screenshot. Reuse saved evidence, do not repeat the same image in successive updates, and apply sensitive-data rules before display.

Maintain a user-readable capture progress document with selected key screenshots and captions, synchronized with branch coverage. Reference an existing image section from other branches instead of embedding the same state repeatedly; keep the complete raw evidence in its run directory. Distinguish an attempted action rejected by the controller, an action that succeeded but whose observation failed, and a branch not yet attempted because the run stopped. State the last verified page and the specific remaining actions. Partial return evidence does not establish full return-to-list comparison, and an automation failure is not a product usability finding.

## Deliver the curated HTML for review before analysis

After collection and internal coverage checks, prepare the evidence-review deliverable described in [references/evidence-review.md](evidence-review.md). Make this a normal workflow output, without requiring the user to ask for screenshot organization. Preserve raw runs. “精选截图” means the complete deduplicated set of distinct pages, objects, visible content and states, not a small selection of representative or important images. Retain every distinct screen, modal, filter result and newly revealed scroll content. Merge only verified repeats, keep return/recovery evidence linked to its representative, and record a per-image duplicate mapping. Never omit a unique state to meet a count or shorten the report.

Deliver a locally openable HTML gallery in the established format: summary counts, task-stage filters, numbered screenshot cards with captions and reasons, click-to-enlarge, and links to the per-image deduplication/source manifest. Display the full deduplicated set and provide a prominent browsable “全部原始截图” entry with every original, exact counts and duplicate-to-representative mappings. Save its path and review status in the journey-planning sidecar. A Markdown list or raw screenshot folder alone does not satisfy this handoff. Verify image links, filters and enlargement before delivery.

When the user requests review before analysis, finish and present this concrete gallery, then await that review once at this stage. Do not interrupt capture for per-image approval. Feedback by screenshot ID updates the selected set/captions and coverage; recapture only a specific unresolved gap within scope. An explicit instruction to proceed to analysis satisfies or waives this review gate; do not ask for the same approval again. Opening the HTML or silence does not mean review passed.

After any user-requested review is complete or explicitly waived, follow the selected report purpose: [exploration](exploration-report.md) or [single-App design analysis](single-app-analysis.md). Cross-competitor conclusions require the relevant competitors' evidence; one completed gallery does not establish that all competitors were collected. Keep collection completion, evidence review and analysis completion as separate statuses.

## Preflight

The environment instructions and `scripts/iphone_device.py` command examples below describe the **local Mac+iPhone route only**. For Android or non-Mac iOS use the selected adapter's commands and prerequisites from [platform-adaptation.md](platform-adaptation.md); do not install Xcode on Windows or request Apple signing for Android. The observation, authorization, payment, rollback and evidence rules remain shared across all routes.

Before the first device attempt, give the user this preparation checklist together: connect the Mac and iPhone to the same Wi-Fi, ensure the phone has Internet access, attach a data cable, unlock the phone and keep it awake, trust this Mac, enable Developer Mode, and complete Developer App trust/verification under Settings → General → VPN & Device Management if prompted. Do not wait for successive failures to reveal these steps one by one.

Distinguish the requirements accurately: the same-network step supports wireless Xcode device communication; Internet access supports developer-certificate verification. A working USB connection need not be rejected solely because Wi-Fi differs. Apple references: [wireless device connection](https://help.apple.com/xcode/mac/current/en.lproj/dev3e2f4ee6d.html), [manual developer trust](https://help.apple.com/xcode/mac/current/en.lproj/dev96a12fb84.html). Certificate expiry, signing and trust failures are separate from connectivity; inspect the Runner diagnostic rather than repeatedly asking the user to reconnect.

Before developer-App trust/verification, also ask the user to check the iPhone VPN/proxy state. In this Skill test, verification failed while Shadowrocket was connected and the user reported success after disabling the VPN and retrying verification. Include temporarily disabling the phone VPN as an upfront preparation/troubleshooting step when it can interfere with Apple verification, especially for “Unable to Verify App / Internet connection required”. Do not treat this single observation as proof that every VPN must always be disabled, or that the Mac VPN must be disabled. A developer may already be trusted while the individual Runner App remains unverified. Get authorization before changing network/security settings, let the user complete trust/verification confirmations when required, and record whether VPN was disabled by the user and whether it was restored. Do not silently reconnect a VPN the user intentionally left off for testing. Recheck real open/snapshot/screenshot after verification; a connected device alone is insufficient.

Confirm all of the following before opening the App:

1. macOS has Xcode and its command-line tools.
2. `agent-device` is pinned to version `0.20.8`.
3. The iPhone is connected by cable, unlocked, trusted, and in Developer Mode.
4. The device is available to Xcode and `agent-device`.
5. XCTest Runner signing, installation, launch, screenshot, snapshot, and one safe tap work.
6. No fallback backend is active.

For the existing execution project, run:

```bash
python3 scripts/iphone_device.py status
```

Do not continue unless `ready_for_open_test` is true.

## Start an evidence run

For a read-only task:

```bash
python3 scripts/iphone_device.py start-run --query "TASK_QUERY"
```

For an explicitly authorized collection-management task, use only the actions needed by the request:

```bash
python3 scripts/iphone_device.py start-run \
  --query "TASK_QUERY" \
  --allow-action favorite \
  --allow-action unfavorite \
  --allow-action create_collection \
  --allow-action assign_to_created_collection \
  --allow-action delete_created_collection \
  --temporary-collection-name "UNIQUE_TEMP_NAME"
```

Keep the returned absolute `run_dir`. Every later device command must specify it.

## Observe, decide, act, verify

Use the smallest sufficient observation for each decision:

1. Start from the latest valid snapshot. The snapshot after the previous action is already the next action's input; do not read it again just to start another loop. If none is valid, capture one.
2. Check current state, action safety and the next target from that evidence. Take a fresh screenshot only when the visual target/state is unclear or the screenshot policy below requires evidence.
   A listed semantic ref is only a candidate: inspect its visible role, label, current state and hittability when the snapshot exposes them. Do not infer a valid tap merely from a ref being present. After the action, name the reached screen from the new observation, not from the intended target label.
3. Execute one authorized action.
4. After every `open`, `press`, `fill`, `scroll` or `back`, run one fresh `snapshot` and verify the outcome before the next action. Previous frame references are invalid. Keep this fresh snapshot for the next iteration.
5. Save a screenshot only when it adds required visual evidence; otherwise continue from the verified snapshot. Log actions and results even when no new image is needed.

Do not automatically run `snapshot + screenshot + view_image + user update` after every action. When using an orchestration helper, make screenshot capture conditional on the criteria below rather than hard-wiring it to all actions. Read/inspect a saved image once when needed and reuse that inspection while the frame remains valid. Avoid printing the full page tree repeatedly when a concise current-state/target summary is sufficient; retain raw evidence locally.

### Screenshot selection and reuse

Capture the first research-relevant view, a meaningful change to price/SKU/selection/filter/content, a required visual comparison or return state, an important confirmation/rollback, and a relevant error/empty state. Preserve loading evidence when it is material to the research or diagnosis; ordinary transient loading does not need a screenshot at every poll. If a fresh snapshot cannot resolve a visual detail, take a current screenshot.

Use page identity, item/shop identity, options, price, filter conditions, scroll position and relevant content to judge whether evidence adds information. A changed clock or animation alone does not justify another report image; the same page title with a changed SKU or price is not a duplicate. One image may support several branches. Do not delete captured originals; select representative images for progress and analysis.

On a return to a previously captured state, verify the actual current state with the new snapshot. If the question is only routing and the snapshot establishes the same item/options, record the return event and reuse the earlier image as context, not as proof of the later state. Capture a new return screenshot when visual position, displayed price or another required before/after comparison is at issue. Historical evidence never authorizes a current coordinate tap: coordinates require a screenshot of the current frame.

If the controller reports an action succeeded but its settle observation failed, do not replay that action. Where the wrapper supports `press --no-settle` and the current App setup has validated explicit post-action snapshots, prefer it to redundant internal tree reads; keep safety checks and frame invalidation. Otherwise inspect the failure before selecting that recovery option. On degraded structure or RUNNER_BUSY, let pending work drain and make one bounded observation retry, using a fresh screenshot if needed. Do not repeatedly poll or replay actions. If recovery fails, record the exact remaining branch and stop dependent operations. A recovery that worked in one run does not establish every timeout's cause.

Use this targeting order:

1. A semantic reference from the latest Accessibility Snapshot.
2. Codex visual judgment from the latest screenshot.
3. A temporary coordinate calculated from that exact screenshot.
4. Pause and request one manual step.

Never reuse a remembered coordinate from a previous page or run. Coordinate fallback requires `--evidence` pointing to the current screenshot.

Command shapes:

```bash
python3 scripts/iphone_device.py open --run RUN_DIR --reason "启动目标 App"
python3 scripts/iphone_device.py snapshot --run RUN_DIR --reason "读取当前页面"
python3 scripts/iphone_device.py screenshot --run RUN_DIR --source accessibility --reason "保存关键页面"
python3 scripts/iphone_device.py press --run RUN_DIR --ref @LATEST_REF --target-label "当前语义元素" --intent browse --source accessibility --reason "推进当前任务"
python3 scripts/iphone_device.py fill --run RUN_DIR --ref @LATEST_REF --text "TASK_QUERY" --target-label "搜索框" --source accessibility --reason "输入登记的任务关键词"
python3 scripts/iphone_device.py scroll --run RUN_DIR --direction down --amount 0.7 --source accessibility --reason "查看下一屏"
python3 scripts/iphone_device.py back --run RUN_DIR --source accessibility --reason "返回上一页"
python3 scripts/iphone_device.py note --run RUN_DIR --stage "STAGE" --source screenshot_visual --text "只记录当前证据直接支持的观察"
```

Coordinate fallback:

```bash
python3 scripts/iphone_device.py press \
  --run RUN_DIR \
  --x X --y Y \
  --evidence RUN_DIR/screenshots/CURRENT.png \
  --target-label "当前截图中的目标" \
  --intent browse \
  --source screenshot_visual \
  --reason "语义树无可用触点，基于当前截图临时定位"
```

Use the matching task-authorized intent for mutations: `favorite`, `unfavorite`, `create_collection`, `assign_to_created_collection`, or `delete_created_collection`. Never disguise a mutation as `browse`.

## Sensitive-page rules

Immediately pause on login, password entry, CAPTCHA, verification-code entry, Face ID confirmation, security verification, private messages, or clearly personal information. Without explicit payment-preview authorization, pause before entering payment flows.

With explicit user authorization, checkout and payment pages may be observed without transferring money. Do not stop merely because ordinary product text or a page contains “支付” or “确认付款”. Preserve the page-view authorization and its user source in the per-run configuration; do not rewrite the policy of a historical run. Keep actual payment, password/verification-code entry, biometric confirmation, wallet/balance deduction, purchase confirmation and automatic renewal prohibited. Determine the next control's actual effect from current evidence: “去支付” may submit an order or initiate payment and is not automatically a safe navigation action. If its effect is unclear, stop at the readable page and record the gap. Existing restrictions on cart/order creation remain unless separately authorized.

The safe wrapper may implement `page_observation_authorization.payment_preview: true` plus a nonempty `source` to prevent the generic “支付” / “确认付款” page markers from blocking authorized observation. This must not grant a payment action or relax credential/security markers. Check the actual next action as well as the page. Payment-page addresses, phone numbers and account/payment identifiers must be excluded or redacted before report use.

- Record only the stop reason.
- Do not upload or include the sensitive screenshot in a report.
- Ask the user to complete the sensitive step manually.
- After the user finishes, capture a new snapshot and discard every pre-pause ref and coordinate.

Screenshots containing account identifiers, profile details, private collections, messages, or other personal data may be stored locally only when required for navigation evidence. Exclude them from the report unless they have been safely redacted.

## Roll back mutations

Before finishing, reverse every task-created change:

- Remove the test item from the temporary state or unfavorite it.
- Delete only the uniquely named collection created by this run.
- Verify the item count or state returns to its original value.
- Verify the temporary name is absent from the latest snapshot.
- Record rollback state in the manifest.

If rollback cannot be verified, stop and report the unresolved mutation prominently. Do not silently close the run.

## Finish and report

Before normal closure, reconcile every planned action and its required evidence in the current session, including selection/change/cancel and return checks. Fill safe, authorized gaps immediately; only then close. If blocked, preserve the verified state and precise gap, then clean up without forcing the missing action. Separate collection coverage from controller acceptance and final analysis; do not add screenshots or actions merely to satisfy a legacy count/time metric.

Always close the session, including after failure:

```bash
python3 scripts/iphone_device.py close --run RUN_DIR --reason "结束真机采集并清理会话"
```

Finalize truthfully. Use `completed` only when the task-specific acceptance criteria and rollback checks pass; otherwise use `partial`, `failed`, or `blocked`:

```bash
python3 scripts/iphone_device.py finalize --run RUN_DIR --status STATUS --summary "如实描述已完成、未验证和已回滚范围"
python3 scripts/iphone_device.py validate --run RUN_DIR
```


After capture, deliver the selected analysis, not just the operation trace. Exploration uses [exploration-report.md](exploration-report.md); single-App design analysis uses [single-app-analysis.md](single-app-analysis.md). Teaching checkpoints follow [teaching-rhythm.md](teaching-rhythm.md); ordinary progress updates never create new approval gates.
