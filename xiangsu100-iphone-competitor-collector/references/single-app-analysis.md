# Single-App design analysis after capture

Use only when the requested deliverable includes UX recommendations or design decisions based on a real run. Pure mechanism exploration uses [exploration-report.md](exploration-report.md), even when evidence came from a device. Keep the existing schema-v2 validator unchanged; `research_context.stage=exploration` describes research maturity, not an exemption from this contract.

After the device session is closed and the basic trace report exists, deliver the curated HTML and honor the evidence-review stage above. Once that review is complete or explicitly waived, read:

- [references/ux-analysis-framework.md](ux-analysis-framework.md) for the analysis method.
- [references/report-contract.md](report-contract.md) for the required `ux-analysis.json` structure and report quality gate.

Then complete all applicable analysis passes:

1. Reconcile `journey-plan.json` and its per-App coverage against `events.jsonl`, screenshots, and snapshots; explain missing branches and actual routing differences, then reconstruct only observed atomic task steps.
2. For every step, answer the four cognitive-walkthrough questions: goal formation, entry discovery, meaning match, and progress confirmation.
3. Apply usability heuristics to the whole task, not as a detached checklist.
4. Map only the local information architecture actually observed in this run.
5. Review the key screens for hierarchy, composition, typography, color, affordance, information density, and feedback.
6. Write findings as `evidence → observation → possible mechanism/impact → candidate cause or unresolved → conditional change/keep → tradeoff → validation`. Expert explanations remain hypotheses unless separate evidence supports them; do not invent a root cause to complete the chain.
7. Add evidence-backed strengths and explicit limitations.

8. Revisit every baseline claim in `research_review`: supported, revised, contradicted, or unresolved. Record counterevidence or an alternative explanation and cite current-run evidence. Add new observations only when evidence supports them; an unresolved claim may have no evidence if the missing capture is explained. State what the study added, even when it only strengthens or narrows an earlier conclusion. No minimum number of new findings is required.
9. For every finding, identify the user's decision, missing information/feedback/control, and downstream task consequence in `task_barrier`. Explain priority using task impact, evidence strength, and project relevance. Do not turn device-targeting failures into user usability problems without separate interface evidence.
10. For every recommendation, decide to adopt, adapt, keep, defer, or reject. Explain target-product fit, business alignment (known/assumed/unknown with a source or gap), added complexity, the minimum change or retained behavior, and an alternative not chosen. A competitor's strength alone does not justify adding its feature to the target product.

Select at most three primary finding IDs; put all other findings in supplementary observations. Do not fill a quota when no major task friction is supported. Exploration reports emphasize a reusable comparison baseline; deepening reports emphasize changed conclusions and design decisions. Simulated personas are explicit assumptions for hypothesis generation, never real user research.

Do not invent user-success percentages, affected-user ratios, business impact, development effort, font sizes, or color values. Use measured values only when the run contains a reproducible measurement source. Otherwise label the statement `observed`, `inferred`, or `needs_validation`.

Create `RUN_DIR/ux-analysis.json`, validate it, and generate the final reports:

Use `schema_version: 2`. Existing version 1 reports must be reviewed and supplemented from their actual evidence before regeneration; never invent missing context or only change the version number. Keep historical reports intact until a revised analysis passes the quality gate. The checker enforces structure, references, and required reasoning fields; Codex must still assess whether the reasoning is relevant and supported.

```bash
python3 .codex/skills/xiangsu100-iphone-competitor-collector/scripts/render_ux_report.py \
  --run RUN_DIR \
  --analysis RUN_DIR/ux-analysis.json
```

If this Skill is installed elsewhere, resolve its actual folder and run the same bundled script from that location. Do not bypass a failed validation by manually publishing the report.

The final Markdown and HTML reports should cover the actual research goal, including as applicable:

- Complete user journey and information architecture.
- Entry visibility and task efficiency.
- Feedback, loading, empty, error, and confirmation states.
- Content organization and management capability.
- Privacy, collaboration, and destructive-action safeguards.
- Evidence-backed strengths, problems, and design opportunities.
- Observed task obstacles, possible explanations and unresolved causes; do not imply user failure or confirmed causality without matching evidence.
- Concrete changes, expected mechanism, tradeoffs, and validation methods.
- Failure points, manual interventions, and rollback status.

Every conclusion must be supported by captured evidence. Mark uncaptured or uncertain information as `待验证`.

Deliver `decision-brief.html` first for the design decision view, with `report.html` and the complete evidence gallery as its supporting layers. Normal rendering writes both formats. When an existing full report has manually added method sections, use `render_ux_report.py --run RUN_DIR --analysis RUN_DIR/ux-analysis.json --brief-only` to refresh only the decision brief; do not overwrite the enhanced report.

The run directory should contain at least:

```text
manifest.json
events.jsonl
screenshots/
snapshots/
diffs/
ux-analysis.json
capture-report.md
capture-report.html
report.md
report.html
decision-brief.md
decision-brief.html
```

`capture-report.*` preserves the basic device-operation trace. `report.*` is the final UX competitor analysis. If analysis validation fails, retain the capture report and mark the run `partial`; do not present it as a completed competitor analysis.

The analysis method is an adapted synthesis of MIT-licensed open-source Skills. Attribution and licenses are in [references/third-party-notices.md](third-party-notices.md).
