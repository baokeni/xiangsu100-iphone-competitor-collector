#!/usr/bin/env python3
"""Validate an evidence-bounded UX analysis and render Markdown/HTML reports."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = (
    "schema_version",
    "research_context",
    "research_review",
    "product",
    "executive_summary",
    "journey",
    "information_architecture",
    "screen_reviews",
    "findings",
    "strengths",
    "limitations",
)
PRODUCT_FIELDS = ("app", "platform", "task", "persona", "success_criteria", "scope")
IA_FIELDS = (
    "entry_points",
    "structure",
    "labels",
    "wayfinding",
    "scalability",
    "management_loop",
)
JOURNEY_QUESTIONS = (
    ("goal_formation", "目标形成"),
    ("discoverability", "入口发现"),
    ("meaning_match", "含义匹配"),
    ("progress_feedback", "进展确认"),
)
SCREEN_FIELDS = (
    ("visual_hierarchy", "视觉层级"),
    ("composition", "构图与节奏"),
    ("typography", "排版"),
    ("color", "颜色"),
    ("affordance", "操作暗示"),
    ("information_density", "信息密度"),
    ("feedback", "反馈"),
)
FINDING_FIELDS = (
    "id",
    "title",
    "severity",
    "dimension",
    "journey_step",
    "evidence",
    "observation",
    "principle",
    "user_impact",
    "root_cause",
    "recommendation",
    "confidence",
)
RECOMMENDATION_FIELDS = ("change", "rationale", "tradeoffs", "validation")
FIT_FIELDS = ("applicability", "complexity_cost", "minimum_change", "alternative")
DECISIONS = {"adopt": "采用", "adapt": "调整后采用", "keep": "保持现状", "defer": "暂缓判断", "reject": "不建议采用"}
OUTCOMES = {"supported": "得到支持", "revised": "需要修正", "contradicted": "发现反例", "unresolved": "尚未确认", "new": "新增观察"}
RATINGS = {"clear", "uncertain", "blocked", "not_applicable"}
SEVERITIES = {"critical", "major", "moderate", "minor"}
CONFIDENCE = {"measured", "observed", "inferred", "needs_validation"}
SEVERITY_LABELS = {
    "critical": "严重阻断",
    "major": "重大问题",
    "moderate": "一般问题",
    "minor": "细节优化",
}
RATING_LABELS = {
    "clear": "清晰",
    "uncertain": "存在疑问",
    "blocked": "可能阻断",
    "not_applicable": "不适用",
}
CONFIDENCE_LABELS = {
    "measured": "直接测量",
    "observed": "直接观察",
    "inferred": "专家推断",
    "needs_validation": "待验证",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
UNSUPPORTED_QUANTIFICATION = re.compile(
    r"(?:\b\d+(?:\.\d+)?\s*%|百分之\s*\d+|(?:提升|降低|减少|增加|影响)\s*\d)",
    re.IGNORECASE,
)
GENERIC_CHANGES = {
    "优化页面层级",
    "加强反馈",
    "提升用户体验",
    "建议更醒目",
    "简化流程",
    "优化交互",
    "优化视觉",
    "提升效率",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def require_object(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path} 必须是对象")
        return {}
    return value


def require_list(value: Any, path: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{path} 必须是数组")
        return []
    return value


def require_text_fields(
    obj: dict[str, Any], fields: tuple[str, ...], path: str, errors: list[str]
) -> None:
    for field in fields:
        if not nonempty_string(obj.get(field)):
            errors.append(f"{path}.{field} 必须是非空文本")


def resolve_evidence(run_dir: Path, value: Any) -> tuple[str | None, str | None]:
    run_dir = run_dir.resolve()
    if not nonempty_string(value):
        return None, "证据路径必须是非空文本"
    raw = Path(value)
    target = raw.resolve() if raw.is_absolute() else (run_dir / raw).resolve()
    try:
        relative = target.relative_to(run_dir)
    except ValueError:
        return None, f"证据路径越出运行目录：{value}"
    if not target.is_file():
        return None, f"证据文件不存在：{relative.as_posix()}"
    return relative.as_posix(), None


def validate_evidence_list(
    run_dir: Path, value: Any, path: str, errors: list[str]
) -> list[str]:
    entries = require_list(value, path, errors)
    if not entries:
        errors.append(f"{path} 至少需要一个证据文件")
        return []
    normalized: list[str] = []
    for index, entry in enumerate(entries):
        relative, error = resolve_evidence(run_dir, entry)
        if error:
            errors.append(f"{path}[{index}] {error}")
        elif relative:
            normalized.append(relative)
    return normalized


def validate_analysis(data: Any, run_dir: Path) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    analysis = require_object(data, "analysis", errors)
    if not analysis:
        return errors, {}

    for field in REQUIRED_TOP_LEVEL:
        if field not in analysis:
            errors.append(f"analysis 缺少字段：{field}")
    if type(analysis.get("schema_version")) is not int or analysis.get("schema_version") != 2:
        errors.append("analysis.schema_version 必须为 2；旧报告需人工补充研究复核、任务阻力与建议取舍，不可仅修改版本号")

    product = require_object(analysis.get("product"), "product", errors)
    require_text_fields(product, PRODUCT_FIELDS, "product", errors)

    summary = require_object(
        analysis.get("executive_summary"), "executive_summary", errors
    )
    require_text_fields(
        summary, ("overall", "strongest", "weakest"), "executive_summary", errors
    )
    top_ids = require_list(
        summary.get("top_finding_ids"), "executive_summary.top_finding_ids", errors
    )
    if any(not nonempty_string(item) for item in top_ids):
        errors.append("executive_summary.top_finding_ids 只能包含非空 finding ID")
    valid_top_ids = [item for item in top_ids if nonempty_string(item)]
    if len(top_ids) > 3 or len(set(valid_top_ids)) != len(valid_top_ids):
        errors.append("executive_summary.top_finding_ids 最多 3 条且不能重复；其余作为补充观察")

    journey = require_list(analysis.get("journey"), "journey", errors)
    if not journey:
        errors.append("journey 至少需要一个步骤")
    seen_steps: set[str] = set()
    for index, raw_step in enumerate(journey):
        path = f"journey[{index}]"
        step = require_object(raw_step, path, errors)
        require_text_fields(step, ("step_id", "goal", "state", "action", "friction"), path, errors)
        step_id = step.get("step_id")
        if nonempty_string(step_id):
            if step_id in seen_steps:
                errors.append(f"{path}.step_id 重复：{step_id}")
            seen_steps.add(step_id)
        step["evidence"] = validate_evidence_list(
            run_dir, step.get("evidence"), f"{path}.evidence", errors
        )
        for key, _ in JOURNEY_QUESTIONS:
            question = require_object(step.get(key), f"{path}.{key}", errors)
            if question.get("rating") not in RATINGS:
                errors.append(
                    f"{path}.{key}.rating 必须是 {', '.join(sorted(RATINGS))} 之一"
                )
            if not nonempty_string(question.get("analysis")):
                errors.append(f"{path}.{key}.analysis 必须是非空文本")

    ia = require_object(
        analysis.get("information_architecture"), "information_architecture", errors
    )
    require_text_fields(ia, IA_FIELDS, "information_architecture", errors)

    screen_reviews = require_list(
        analysis.get("screen_reviews"), "screen_reviews", errors
    )
    if not screen_reviews:
        errors.append("screen_reviews 至少需要一个关键页面")
    seen_screens: set[str] = set()
    for index, raw_screen in enumerate(screen_reviews):
        path = f"screen_reviews[{index}]"
        screen = require_object(raw_screen, path, errors)
        if "ios_hig" in screen:
            errors.append(f"{path}.ios_hig 已从分析契约移除，请删除该字段")
        require_text_fields(screen, ("screen_id", "name"), path, errors)
        for key, _ in SCREEN_FIELDS:
            if not nonempty_string(screen.get(key)):
                errors.append(f"{path}.{key} 必须是非空文本")
        screen_id = screen.get("screen_id")
        if nonempty_string(screen_id):
            if screen_id in seen_screens:
                errors.append(f"{path}.screen_id 重复：{screen_id}")
            seen_screens.add(screen_id)
        screen["evidence"] = validate_evidence_list(
            run_dir, screen.get("evidence"), f"{path}.evidence", errors
        )

    findings = require_list(analysis.get("findings"), "findings", errors)
    seen_findings: set[str] = set()
    for index, raw_finding in enumerate(findings):
        path = f"findings[{index}]"
        finding = require_object(raw_finding, path, errors)
        for field in FINDING_FIELDS:
            if field not in finding:
                errors.append(f"{path} 缺少字段：{field}")
        require_text_fields(
            finding,
            (
                "id",
                "title",
                "dimension",
                "journey_step",
                "observation",
                "principle",
                "user_impact",
                "root_cause",
            ),
            path,
            errors,
        )
        finding_id = finding.get("id")
        if nonempty_string(finding_id):
            if finding_id in seen_findings:
                errors.append(f"{path}.id 重复：{finding_id}")
            seen_findings.add(finding_id)
        if finding.get("severity") not in SEVERITIES:
            errors.append(
                f"{path}.severity 必须是 {', '.join(sorted(SEVERITIES))} 之一"
            )
        if finding.get("confidence") not in CONFIDENCE:
            errors.append(
                f"{path}.confidence 必须是 {', '.join(sorted(CONFIDENCE))} 之一"
            )
        journey_step = finding.get("journey_step")
        if nonempty_string(journey_step) and journey_step not in seen_steps:
            errors.append(f"{path}.journey_step 未指向已有 journey.step_id：{journey_step}")
        finding["evidence"] = validate_evidence_list(
            run_dir, finding.get("evidence"), f"{path}.evidence", errors
        )
        recommendation = require_object(
            finding.get("recommendation"), f"{path}.recommendation", errors
        )
        require_text_fields(
            recommendation, RECOMMENDATION_FIELDS, f"{path}.recommendation", errors
        )
        change = str(recommendation.get("change", "")).strip().rstrip("。")
        if change in GENERIC_CHANGES or (change and len(change) < 12):
            errors.append(f"{path}.recommendation.change 过于笼统，必须写明页面与改变")

        quantified_text = " ".join(
            str(value)
            for value in (
                finding.get("user_impact", ""),
                recommendation.get("change", ""),
                recommendation.get("rationale", ""),
            )
        )
        measurements = finding.get("measurements")
        if UNSUPPORTED_QUANTIFICATION.search(quantified_text) and not (
            finding.get("confidence") == "measured"
            and isinstance(measurements, list)
            and measurements
        ):
            errors.append(
                f"{path} 包含未经测量支撑的百分比或量化影响；删除数字或提供 measurements"
            )

    unknown_top_ids = [item for item in valid_top_ids if item not in seen_findings]
    if unknown_top_ids:
        errors.append(
            "executive_summary.top_finding_ids 引用了不存在的 finding："
            + ", ".join(unknown_top_ids)
        )

    strengths = require_list(analysis.get("strengths"), "strengths", errors)
    seen_strengths: set[str] = set()
    for index, raw_strength in enumerate(strengths):
        path = f"strengths[{index}]"
        strength = require_object(raw_strength, path, errors)
        require_text_fields(strength, ("id", "title", "analysis"), path, errors)
        if strength.get("confidence") not in CONFIDENCE:
            errors.append(
                f"{path}.confidence 必须是 {', '.join(sorted(CONFIDENCE))} 之一"
            )
        strength_id = strength.get("id")
        if nonempty_string(strength_id):
            if strength_id in seen_strengths:
                errors.append(f"{path}.id 重复：{strength_id}")
            seen_strengths.add(strength_id)
        strength["evidence"] = validate_evidence_list(
            run_dir, strength.get("evidence"), f"{path}.evidence", errors
        )

    limitations = require_list(analysis.get("limitations"), "limitations", errors)
    if not limitations:
        errors.append("limitations 至少需要说明一项证据或方法限制")
    elif any(not nonempty_string(item) for item in limitations):
        errors.append("limitations 只能包含非空文本")

    validate_research_decisions(analysis, run_dir, errors)
    return errors, analysis


def validate_research_decisions(analysis: dict[str, Any], run_dir: Path, errors: list[str]) -> None:
    context = require_object(analysis.get("research_context"), "research_context", errors)
    require_text_fields(context, ("target_product", "positioning", "business_constraints"), "research_context", errors)
    if context.get("stage") not in ("exploration", "deepening"):
        errors.append("research_context.stage 必须为 exploration 或 deepening")
    if type(context.get("prior_research_provided")) is not bool:
        errors.append("research_context.prior_research_provided 必须是布尔值")
    questions = require_list(context.get("core_questions"), "research_context.core_questions", errors)
    if not questions or any(not nonempty_string(item) for item in questions):
        errors.append("research_context.core_questions 至少包含一个明确研究问题")
    baseline = require_list(context.get("baseline"), "research_context.baseline", errors)
    ids: set[str] = set()
    for index, value in enumerate(baseline):
        path = f"research_context.baseline[{index}]"
        item = require_object(value, path, errors)
        require_text_fields(item, ("id", "claim", "source"), path, errors)
        if item.get("kind") not in ("evidence", "hypothesis", "question"):
            errors.append(f"{path}.kind 必须为 evidence、hypothesis 或 question")
        if nonempty_string(item.get("id")):
            if item["id"] in ids:
                errors.append(f"{path}.id 重复")
            ids.add(item["id"])
    if context.get("prior_research_provided") is True and not baseline:
        errors.append("已提供预研时，baseline 必须提取至少一条与任务相关的证据、假设或问题")

    review = require_object(analysis.get("research_review"), "research_review", errors)
    require_text_fields(review, ("counterexample_search", "incremental_value"), "research_review", errors)
    items = require_list(review.get("items"), "research_review.items", errors)
    reviewed: set[str] = set()
    for index, value in enumerate(items):
        path = f"research_review.items[{index}]"
        item = require_object(value, path, errors)
        require_text_fields(item, ("assessment", "counterevidence"), path, errors)
        if "baseline_id" not in item:
            errors.append(f"{path}.baseline_id 必须显式填写；新增观察用 null")
        outcome = item.get("outcome")
        if not isinstance(outcome, str) or outcome not in OUTCOMES:
            errors.append(f"{path}.outcome 无效")
        baseline_id = item.get("baseline_id")
        if outcome == "new":
            if baseline_id is not None:
                errors.append(f"{path} 新增观察的 baseline_id 必须为 null")
        elif not isinstance(baseline_id, str) or baseline_id not in ids:
            errors.append(f"{path}.baseline_id 必须引用已有基线")
        else:
            if baseline_id in reviewed:
                errors.append(f"{path}.baseline_id 重复复核")
            reviewed.add(baseline_id)
        if outcome == "unresolved" and item.get("evidence") == []:
            require_text_fields(item, ("limitation",), path, errors)
        else:
            item["evidence"] = validate_evidence_list(run_dir, item.get("evidence"), f"{path}.evidence", errors)
    if ids - reviewed:
        errors.append("research_review 尚未复核基线：" + ", ".join(sorted(ids - reviewed)))

    for index, value in enumerate(require_list(analysis.get("findings"), "findings", errors)):
        path = f"findings[{index}]"
        finding = require_object(value, path, errors)
        require_text_fields(finding, ("priority_reason",), path, errors)
        barrier = require_object(finding.get("task_barrier"), f"{path}.task_barrier", errors)
        require_text_fields(barrier, ("user_decision", "missing_support", "consequence"), f"{path}.task_barrier", errors)
        rec = require_object(finding.get("recommendation"), f"{path}.recommendation", errors)
        require_text_fields(rec, FIT_FIELDS, f"{path}.recommendation", errors)
        decision = rec.get("decision")
        if not isinstance(decision, str) or decision not in DECISIONS:
            errors.append(f"{path}.recommendation.decision 无效")
        business = require_object(rec.get("business_alignment"), f"{path}.recommendation.business_alignment", errors)
        require_text_fields(business, ("analysis", "source_or_gap"), f"{path}.recommendation.business_alignment", errors)
        if business.get("basis") not in ("known", "assumed", "unknown"):
            errors.append(f"{path}.recommendation.business_alignment.basis 必须区分 known、assumed、unknown")


def ordered_findings(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {item["id"]: item for item in analysis["findings"]}
    top = analysis["executive_summary"]["top_finding_ids"]
    return [by_id[key] for key in top] + [item for item in analysis["findings"] if item["id"] not in top]


def decision_details(finding: dict[str, Any]) -> list[tuple[str, str]]:
    barrier = finding["task_barrier"]
    rec = finding["recommendation"]
    business = rec["business_alignment"]
    basis = {"known": "有资料支持", "assumed": "假设", "unknown": "未知"}[business["basis"]]
    return [
        ("用户要做的判断", barrier["user_decision"]),
        ("缺少的支持", barrier["missing_support"]),
        ("后续任务影响", barrier["consequence"]),
        ("关注理由", finding["priority_reason"]),
        ("取舍结论", DECISIONS[rec["decision"]]),
        ("适用条件与产品匹配", rec["applicability"]),
        (f"业务判断（{basis}）", business["analysis"]),
        ("业务依据或信息缺口", business["source_or_gap"]),
        ("新增复杂度", rec["complexity_cost"]),
        ("最小改动或维持方式", rec["minimum_change"]),
        ("备选方案与不采用理由", rec["alternative"]),
    ]


def research_details(analysis: dict[str, Any]) -> list[tuple[str, str]]:
    context, review = analysis["research_context"], analysis["research_review"]
    rows = [
        ("研究阶段", "初步探索" if context["stage"] == "exploration" else "深化研究"),
        ("目标产品", context["target_product"]),
        ("产品定位与习惯", context["positioning"]),
        ("业务约束", context["business_constraints"]),
        ("核心问题", "；".join(context["core_questions"])),
        ("是否提供预研", "是" if context["prior_research_provided"] else "否"),
    ]
    for item in context["baseline"]:
        kind = {"evidence": "已有证据", "hypothesis": "研究假设", "question": "待解决问题"}[item["kind"]]
        rows.append((f"基线 {item['id']} · {kind}", f"{item['claim']}（来源：{item['source']}）"))
    rows.extend([("反例与遗漏检查", review["counterexample_search"]), ("本次新增认识", review["incremental_value"])])
    return rows


def md_text(value: Any) -> str:
    return str(value).replace("\r", " ").strip()


def md_evidence(paths: list[str]) -> list[str]:
    lines: list[str] = []
    for path in paths:
        label = Path(path).name
        if Path(path).suffix.lower() in IMAGE_SUFFIXES:
            lines.append(f"![{label}]({path})")
        else:
            lines.append(f"[{label}]({path})")
    return lines


def markdown_findings(findings: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for finding in findings:
        rec = finding["recommendation"]
        lines.extend([f"### {md_text(finding['id'])}｜{md_text(finding['title'])}", ""])
        rows = [
            ("严重程度", SEVERITY_LABELS[finding["severity"]]),
            ("维度 / 步骤", f"{finding['dimension']} / {finding['journey_step']}"),
            ("置信度", CONFIDENCE_LABELS[finding["confidence"]]),
            ("观察", finding["observation"]),
            ("解释原则", finding["principle"]),
            ("用户影响", finding["user_impact"]),
            ("原因判断（可待验证）", finding["root_cause"]),
            *decision_details(finding),
            ("具体建议", rec["change"]),
            ("设计理由", rec["rationale"]),
            ("代价与权衡", rec["tradeoffs"]),
            ("验证方法", rec["validation"]),
        ]
        lines.extend(f"- **{label}**：{md_text(value)}" for label, value in rows)
        lines.extend(["", *md_evidence(finding["evidence"]), ""])
    return lines


def render_markdown(analysis: dict[str, Any], manifest: dict[str, Any]) -> str:
    product = analysis["product"]
    summary = analysis["executive_summary"]
    lines = [
        f"# {md_text(product['app'])}｜{md_text(product['task'])}竞品体验分析",
        "",
        "> 本报告来自真实 iPhone 运行证据，并采用逐步认知走查、启发式评估、信息架构和视觉批评。专家推断不等同于真实用户研究。",
        "",
        "## 研究范围与证据边界",
        "",
        f"- 平台：{md_text(product['platform'])}",
        f"- 目标用户：{md_text(product['persona'])}",
        f"- 用户任务：{md_text(product['task'])}",
        f"- 成功标准：{md_text(product['success_criteria'])}",
        f"- 覆盖范围：{md_text(product['scope'])}",
        f"- 运行状态：{md_text(manifest.get('status', '未知'))}",
        f"- 运行编号：{md_text(manifest.get('run_id', '未知'))}",
        "",
        "## 核心结论",
        "",
        md_text(summary["overall"]),
        "",
        f"- 最强体验：{md_text(summary['strongest'])}",
        f"- 最大问题：{md_text(summary['weakest'])}",
        f"- 优先关注：{', '.join(summary['top_finding_ids']) or '本次未形成问题条目'}",
        "",
        "## 研究复核与新增认识",
        "",
    ]
    lines.extend(f"- **{label}**：{md_text(value)}" for label, value in research_details(analysis))
    for item in analysis["research_review"]["items"]:
        lines.extend([
            "", f"### {OUTCOMES[item['outcome']]}｜{md_text(item.get('baseline_id') or '新增')}", "",
            md_text(item["assessment"]), "", f"- 反向证据与替代解释：{md_text(item['counterevidence'])}",
            *([f"- 未确认原因：{md_text(item['limitation'])}"] if item.get("limitation") else []),
            *md_evidence(item["evidence"]), "",
        ])
    findings = ordered_findings(analysis)
    top_count = len(summary["top_finding_ids"])
    lines.extend(["", "## 关键任务阻力与设计取舍", ""])
    lines.extend(markdown_findings(findings[:top_count]) or ["本次没有列为优先关注的问题，不强行凑数。", ""])
    lines.extend(["## 完整任务链路与认知走查", ""])

    for step in analysis["journey"]:
        lines.extend(
            [
                f"### {md_text(step['step_id'])}｜{md_text(step['action'])}",
                "",
                f"- 用户目标：{md_text(step['goal'])}",
                f"- 当前状态：{md_text(step['state'])}",
                f"- 主要阻力：{md_text(step['friction'])}",
                "",
                "| 判断问题 | 结论 | 分析 |",
                "|---|---|---|",
            ]
        )
        for key, label in JOURNEY_QUESTIONS:
            item = step[key]
            lines.append(
                f"| {label} | {RATING_LABELS[item['rating']]} | {md_text(item['analysis'])} |"
            )
        lines.extend(["", *md_evidence(step["evidence"]), ""])

    ia = analysis["information_architecture"]
    lines.extend(["## 信息架构", ""])
    for key, label in (
        ("entry_points", "入口"),
        ("structure", "结构"),
        ("labels", "标签"),
        ("wayfinding", "寻路"),
        ("scalability", "规模适应"),
        ("management_loop", "管理闭环"),
    ):
        lines.append(f"- **{label}**：{md_text(ia[key])}")

    lines.extend(["", "## 关键页面视觉检查", ""])
    for screen in analysis["screen_reviews"]:
        lines.extend([f"### {md_text(screen['screen_id'])}｜{md_text(screen['name'])}", ""])
        for key, label in SCREEN_FIELDS:
            lines.append(f"- **{label}**：{md_text(screen[key])}")
        lines.extend(["", *md_evidence(screen["evidence"]), ""])

    if findings[top_count:]:
        lines.extend(["## 补充观察", "", *markdown_findings(findings[top_count:])])

    lines.extend(["## 有证据的体验优势", ""])
    if not analysis["strengths"]:
        lines.extend(["本次没有形成可确认的优势条目。", ""])
    for strength in analysis["strengths"]:
        lines.extend(
            [
                f"### {md_text(strength['id'])}｜{md_text(strength['title'])}",
                "",
                f"- 置信度：{CONFIDENCE_LABELS[strength['confidence']]}",
                f"- 分析：{md_text(strength['analysis'])}",
                "",
                *md_evidence(strength["evidence"]),
                "",
            ]
        )

    lines.extend(["## 限制与待验证", ""])
    for limitation in analysis["limitations"]:
        lines.append(f"- {md_text(limitation)}")

    lines.extend(
        [
            "",
            "## 方法与基础证据",
            "",
            "- 分析方法：逐步认知走查、Nielsen 启发式、局部信息架构和关键页面视觉批评。",
            "- 置信度：直接测量、直接观察、专家推断、待验证四级。",
            "- [基础操作轨迹（Markdown）](capture-report.md)",
            "- [基础操作轨迹（HTML）](capture-report.html)",
            "",
        ]
    )
    return "\n".join(lines)


def evidence_html(paths: list[str]) -> str:
    blocks: list[str] = []
    for path in paths:
        escaped = html.escape(path, quote=True)
        label = html.escape(Path(path).name)
        if Path(path).suffix.lower() in IMAGE_SUFFIXES:
            blocks.append(
                f'<a class="shot" href="{escaped}"><img src="{escaped}" alt="{label}"><span>{label}</span></a>'
            )
        else:
            blocks.append(f'<a class="file" href="{escaped}">{label}</a>')
    return '<div class="evidence">' + "".join(blocks) + "</div>"


def p(value: Any) -> str:
    return html.escape(str(value).strip())


def render_html(analysis: dict[str, Any], manifest: dict[str, Any]) -> str:
    product = analysis["product"]
    summary = analysis["executive_summary"]
    research_html = "<article>" + "".join(
        f"<p><strong>{p(label)}：</strong>{p(value)}</p>" for label, value in research_details(analysis)
    ) + "</article>"
    for item in analysis["research_review"]["items"]:
        research_html += (
            f"<article><h3>{p(OUTCOMES[item['outcome']])}｜{p(item.get('baseline_id') or '新增')}</h3>"
            f"<p>{p(item['assessment'])}</p><p><strong>反向证据与替代解释：</strong>{p(item['counterevidence'])}</p>"
            + (f"<p><strong>未确认原因：</strong>{p(item['limitation'])}</p>" if item.get("limitation") else "")
            + evidence_html(item["evidence"]) + "</article>"
        )
    journey_sections: list[str] = []
    for step in analysis["journey"]:
        rows = "".join(
            f"<tr><th>{p(label)}</th><td><span class='rating {p(step[key]['rating'])}'>{p(RATING_LABELS[step[key]['rating']])}</span></td><td>{p(step[key]['analysis'])}</td></tr>"
            for key, label in JOURNEY_QUESTIONS
        )
        journey_sections.append(
            f"<article><div class='eyebrow'>{p(step['step_id'])}</div><h3>{p(step['action'])}</h3>"
            f"<p><strong>用户目标：</strong>{p(step['goal'])}</p>"
            f"<p><strong>当前状态：</strong>{p(step['state'])}</p>"
            f"<p><strong>主要阻力：</strong>{p(step['friction'])}</p>"
            f"<table><thead><tr><th>判断问题</th><th>结论</th><th>分析</th></tr></thead><tbody>{rows}</tbody></table>"
            f"{evidence_html(step['evidence'])}</article>"
        )

    ia = analysis["information_architecture"]
    ia_items = "".join(
        f"<div><dt>{p(label)}</dt><dd>{p(ia[key])}</dd></div>"
        for key, label in (
            ("entry_points", "入口"),
            ("structure", "结构"),
            ("labels", "标签"),
            ("wayfinding", "寻路"),
            ("scalability", "规模适应"),
            ("management_loop", "管理闭环"),
        )
    )

    screen_sections: list[str] = []
    for screen in analysis["screen_reviews"]:
        items = "".join(
            f"<div><dt>{p(label)}</dt><dd>{p(screen[key])}</dd></div>"
            for key, label in SCREEN_FIELDS
        )
        screen_sections.append(
            f"<article><div class='eyebrow'>{p(screen['screen_id'])}</div><h3>{p(screen['name'])}</h3>"
            f"<dl class='grid'>{items}</dl>{evidence_html(screen['evidence'])}</article>"
        )

    finding_sections: list[str] = []
    for finding in ordered_findings(analysis):
        rec = finding["recommendation"]
        decision_rows = decision_details(finding)
        details = "".join(f"<p><strong>{p(label)}：</strong>{p(value)}</p>" for label, value in decision_rows[:5])
        details += "<details><summary>适用条件、业务依据与备选方案</summary>" + "".join(
            f"<p><strong>{p(label)}：</strong>{p(value)}</p>" for label, value in decision_rows[5:]
        ) + "</details>"
        finding_sections.append(
            f"<article class='finding {p(finding['severity'])}'>"
            f"<div class='finding-head'><span class='severity'>{p(SEVERITY_LABELS[finding['severity']])}</span>"
            f"<span>{p(CONFIDENCE_LABELS[finding['confidence']])}</span></div>"
            f"<h3>{p(finding['id'])}｜{p(finding['title'])}</h3>"
            f"<p><strong>维度 / 步骤：</strong>{p(finding['dimension'])} / {p(finding['journey_step'])}</p>"
            f"<p><strong>观察：</strong>{p(finding['observation'])}</p>"
            f"<p><strong>解释原则：</strong>{p(finding['principle'])}</p>"
            f"<p><strong>用户影响：</strong>{p(finding['user_impact'])}</p>"
            f"<p><strong>原因判断（可待验证）：</strong>{p(finding['root_cause'])}</p>"
            f"{details}"
            f"<div class='recommendation'><h4>具体建议</h4>"
            f"<p><strong>改变：</strong>{p(rec['change'])}</p>"
            f"<p><strong>理由：</strong>{p(rec['rationale'])}</p>"
            f"<p><strong>代价：</strong>{p(rec['tradeoffs'])}</p>"
            f"<p><strong>验证：</strong>{p(rec['validation'])}</p></div>"
            f"{evidence_html(finding['evidence'])}</article>"
        )
    top_count = len(summary["top_finding_ids"])
    primary_html = "".join(finding_sections[:top_count]) or "<p class='empty'>本次没有列为优先关注的问题，不强行凑数。</p>"
    supplementary_html = (
        "<section><details><summary>补充观察</summary>" + "".join(finding_sections[top_count:]) + "</details></section>"
        if finding_sections[top_count:] else ""
    )

    strength_sections = "".join(
        f"<article><div class='eyebrow'>{p(item['id'])} · {p(CONFIDENCE_LABELS[item['confidence']])}</div>"
        f"<h3>{p(item['title'])}</h3><p>{p(item['analysis'])}</p>{evidence_html(item['evidence'])}</article>"
        for item in analysis["strengths"]
    ) or "<p class='empty'>本次没有形成可确认的优势条目。</p>"

    limitations = "".join(f"<li>{p(item)}</li>" for item in analysis["limitations"])
    top_ids = "、".join(summary["top_finding_ids"]) or "本次未形成问题条目"
    title = f"{product['app']}｜{product['task']}竞品体验分析"
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{p(title)}</title>
<style>
:root{{--ink:#17202a;--muted:#667085;--line:#e4e7ec;--paper:#fff;--wash:#f6f8fb;--accent:#315efb;--danger:#b42318}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--wash);color:var(--ink);font:16px/1.7 -apple-system,BlinkMacSystemFont,"SF Pro Text","PingFang SC",sans-serif}}
main{{max-width:1080px;margin:0 auto;padding:48px 24px 80px}}header{{background:linear-gradient(135deg,#111827,#263a74);color:white;border-radius:24px;padding:44px;margin-bottom:28px}}
h1{{font-size:clamp(30px,5vw,52px);line-height:1.12;margin:10px 0 20px}}h2{{font-size:28px;margin:52px 0 18px}}h3{{font-size:21px;line-height:1.35;margin:6px 0 16px}}h4{{margin:0 0 8px}}
.lead{{font-size:19px;max-width:800px;color:#e9edff}}.meta{{display:flex;flex-wrap:wrap;gap:8px;margin-top:22px}}.meta span,.eyebrow{{font-size:13px;letter-spacing:.02em}}.meta span{{background:#ffffff1c;border:1px solid #ffffff2b;border-radius:999px;padding:6px 11px}}
.summary{{display:grid;grid-template-columns:2fr 1fr 1fr;gap:14px}}.summary>div,article,.ia{{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:24px;box-shadow:0 8px 24px #1018280a}}
.summary strong{{display:block;margin-bottom:8px}}article{{margin:14px 0}}table{{width:100%;border-collapse:collapse;margin:18px 0}}th,td{{border-bottom:1px solid var(--line);padding:12px;text-align:left;vertical-align:top}}th{{font-size:14px;color:var(--muted)}}
.rating,.severity{{display:inline-block;border-radius:999px;padding:3px 9px;font-size:13px;background:#edf2ff;color:#2949b6}}.rating.blocked,.finding.critical .severity{{background:#fee4e2;color:#b42318}}.rating.uncertain,.finding.major .severity{{background:#fff3d6;color:#8a5700}}
.grid,.ia dl{{display:grid;grid-template-columns:1fr 1fr;gap:0 24px}}dl>div{{border-top:1px solid var(--line);padding:14px 0}}dt{{font-weight:700}}dd{{margin:4px 0 0;color:#344054}}
.finding{{border-left:5px solid #98a2b3}}.finding.critical{{border-left-color:#d92d20}}.finding.major{{border-left-color:#f79009}}.finding.moderate{{border-left-color:#315efb}}.finding-head{{display:flex;justify-content:space-between;color:var(--muted);font-size:13px}}.recommendation{{background:#f7f9ff;border-radius:14px;padding:18px;margin-top:18px}}
.evidence{{display:flex;gap:12px;overflow:auto;padding:12px 0 2px}}.shot{{min-width:180px;text-decoration:none;color:var(--muted);font-size:12px}}.shot img{{display:block;width:180px;max-height:390px;object-fit:contain;background:#111;border-radius:14px;border:1px solid var(--line);margin-bottom:5px}}.file{{color:var(--accent)}}
.limits{{background:#fff7ed;border:1px solid #fed7aa;border-radius:18px;padding:22px}}.footer{{margin-top:52px;color:var(--muted);font-size:14px}}.empty{{color:var(--muted)}}
@media(max-width:760px){{main{{padding:20px 14px 50px}}header{{padding:28px 22px;border-radius:18px}}.summary,.grid,.ia dl{{grid-template-columns:1fr}}table{{display:block;overflow-x:auto}}}}
</style></head><body><main>
<header><div class="eyebrow">真实 iPhone · 证据化 UX 分析</div><h1>{p(title)}</h1><p class="lead">{p(summary['overall'])}</p>
<div class="meta"><span>{p(product['platform'])}</span><span>运行：{p(manifest.get('run_id','未知'))}</span><span>状态：{p(manifest.get('status','未知'))}</span></div></header>
<section><h2>研究范围与证据边界</h2><article><p><strong>目标用户：</strong>{p(product['persona'])}</p><p><strong>成功标准：</strong>{p(product['success_criteria'])}</p><p><strong>覆盖范围：</strong>{p(product['scope'])}</p></article></section>
<section><h2>核心结论</h2><div class="summary"><div><strong>整体判断</strong>{p(summary['overall'])}</div><div><strong>最强体验</strong>{p(summary['strongest'])}</div><div><strong>最大问题</strong>{p(summary['weakest'])}<br><small>优先关注：{p(top_ids)}</small></div></div></section>
<section><h2>研究复核与新增认识</h2>{research_html}</section>
<section><h2>关键任务阻力与设计取舍</h2>{primary_html}</section>
<section><h2>完整任务链路与认知走查</h2>{''.join(journey_sections)}</section>
<section><h2>信息架构</h2><div class="ia"><dl>{ia_items}</dl></div></section>
<section><h2>关键页面视觉检查</h2>{''.join(screen_sections)}</section>
{supplementary_html}
<section><h2>有证据的体验优势</h2>{strength_sections}</section>
<section><h2>限制与待验证</h2><div class="limits"><ul>{limitations}</ul></div></section>
<footer class="footer"><p>方法：逐步认知走查、Nielsen 启发式、局部信息架构和视觉批评。</p><p><a href="capture-report.html">查看基础操作轨迹</a> · <a href="ux-analysis.json">查看结构化分析</a></p></footer>
</main></body></html>"""


def brief_evidence(paths: list[str]) -> list[str]:
    if len(paths) <= 4:
        return paths
    return [paths[round(index * (len(paths) - 1) / 3)] for index in range(4)]


def decision_brief_markdown(analysis: dict[str, Any]) -> str:
    context = analysis["research_context"]
    product = analysis["product"]
    summary = analysis["executive_summary"]
    by_id = {finding["id"]: finding for finding in analysis["findings"]}
    lines = [
        f"# {md_text(context['target_product'])}｜设计决策摘要", "",
        f"- **研究任务**：{md_text(product['task'])}",
        f"- **证据范围**：{md_text(product['scope'])}",
        f"- **整体判断**：{md_text(summary['overall'])}",
        f"- **本次新增认识**：{md_text(analysis['research_review']['incremental_value'])}", "",
        "## 建议先验证的决定", "",
    ]
    if not summary["top_finding_ids"]:
        lines.extend(["本次没有足够证据列出优先问题；保持现状或补关键证据均可作为结果。", ""])
    for finding_id in summary["top_finding_ids"]:
        finding = by_id[finding_id]
        recommendation = finding["recommendation"]
        barrier = finding["task_barrier"]
        selected = brief_evidence(finding["evidence"])
        more = len(finding["evidence"]) - len(selected)
        lines.extend([
            f"### {md_text(finding_id)}｜{md_text(finding['title'])}", "",
            f"- **用户决定**：{md_text(barrier['user_decision'])}",
            f"- **观察**：{md_text(finding['observation'])}",
            f"- **解释及证据级别**：{md_text(finding['user_impact'])}（{CONFIDENCE_LABELS[finding['confidence']]}）",
            f"- **取舍与最小动作**：{DECISIONS[recommendation['decision']]}；{md_text(recommendation['minimum_change'])}",
            f"- **适用条件**：{md_text(recommendation['applicability'])}",
            f"- **代价与备选**：{md_text(recommendation['complexity_cost']).rstrip('。；')}；备选：{md_text(recommendation['alternative'])}",
            f"- **验证与反证**：{md_text(recommendation['validation'])}",
            "- **关键来源**：" + "、".join(f"[{Path(path).name}]({path})" for path in selected) + (f"；另 {more} 项见完整报告" if more else ""), "",
        ])
    first_limit = analysis["limitations"][0] if analysis["limitations"] else "本次证据仅覆盖所列任务和状态。"
    lines.extend(["## 结论边界", "", f"- {md_text(first_limit)}", "- 其他未验证、用户排除与敏感操作边界以完整报告为准。", "", "[查看完整分析与限制](report.md) · [查看完整图文](report.html)", ""])
    return "\n".join(lines)


def decision_brief_html(analysis: dict[str, Any]) -> str:
    context = analysis["research_context"]
    product = analysis["product"]
    summary = analysis["executive_summary"]
    by_id = {finding["id"]: finding for finding in analysis["findings"]}
    cards = []
    for finding_id in summary["top_finding_ids"]:
        finding = by_id[finding_id]
        rec = finding["recommendation"]
        selected = brief_evidence(finding["evidence"])
        rows = [
            ("用户决定", finding["task_barrier"]["user_decision"]),
            ("观察", finding["observation"]),
            ("解释及证据级别", f"{finding['user_impact']}（{CONFIDENCE_LABELS[finding['confidence']]}）"),
            ("取舍与最小动作", f"{DECISIONS[rec['decision']]}；{rec['minimum_change']}"),
            ("适用条件", rec["applicability"]),
            ("代价与备选", f"{rec['complexity_cost'].rstrip('。；')}；备选：{rec['alternative']}"),
            ("验证与反证", rec["validation"]),
        ]
        body = "".join(f"<p><strong>{p(label)}：</strong>{p(value)}</p>" for label, value in rows)
        extra = len(finding["evidence"]) - len(selected)
        more = f"<p>另 {extra} 项来源见完整报告。</p>" if extra else ""
        cards.append(f"<article><h2>{p(finding_id)}｜{p(finding['title'])}</h2>{body}<h3>关键来源</h3>{evidence_html(selected)}{more}</article>")
    if not cards:
        cards.append("<article>本次没有足够证据列出优先问题；保持现状或补关键证据均可作为结果。</article>")
    first_limit = analysis["limitations"][0] if analysis["limitations"] else "本次证据仅覆盖所列任务和状态。"
    limits = "".join(f"<li>{p(item)}</li>" for item in analysis["limitations"])
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{p(context['target_product'])}｜设计决策摘要</title><style>
body{{font:16px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;color:#263247;background:#f5f7fa;margin:0}}main{{max-width:900px;margin:auto;padding:32px 20px 72px}}header,article,section{{background:white;border:1px solid #dfe5ec;border-radius:16px;padding:22px;margin:14px 0}}h1{{font-size:29px;line-height:1.25}}h2{{font-size:20px}}h3{{font-size:14px}}p{{margin:9px 0}}.meta{{color:#5c6a7c}}.evidence{{display:flex;gap:10px;overflow:auto}}.shot{{min-width:110px}}.shot img{{display:block;width:110px;max-height:180px;object-fit:contain}}a{{color:#2450a4}}@media(max-width:650px){{main{{padding:14px}}header,article,section{{padding:16px}}}}
</style></head><body><main><header><h1>{p(context['target_product'])}｜设计决策摘要</h1><p class="meta"><strong>研究任务：</strong>{p(product['task'])}</p><p class="meta"><strong>证据范围：</strong>{p(product['scope'])}</p><p><strong>整体判断：</strong>{p(summary['overall'])}</p><p><strong>本次新增认识：</strong>{p(analysis['research_review']['incremental_value'])}</p></header><h2>建议先验证的决定</h2>{''.join(cards)}<section><h2>结论边界</h2><p>{p(first_limit)}</p><details><summary>查看全部限制（{len(analysis['limitations'])} 项）</summary><ul>{limits}</ul></details><p><a href="report.html">查看完整图文</a> · <a href="report.md">查看完整分析</a></p></section></main></body></html>'''


def atomic_write(path: Path, content: str) -> None:
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)


def preserve_capture_report(run_dir: Path) -> None:
    for suffix in ("md", "html"):
        source = run_dir / f"report.{suffix}"
        destination = run_dir / f"capture-report.{suffix}"
        if source.is_file() and not destination.exists():
            shutil.copy2(source, destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="校验证据化 UX 分析并生成最终 Markdown/HTML 报告"
    )
    parser.add_argument("--run", required=True, help="本次运行目录")
    parser.add_argument("--analysis", help="ux-analysis.json；默认位于运行目录")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check-only", action="store_true", help="只校验，不写报告文件")
    mode.add_argument("--brief-only", action="store_true", help="只生成决策摘要，不覆盖完整报告")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run).expanduser().resolve()
    if not run_dir.is_dir():
        print(json.dumps({"ok": False, "errors": [f"运行目录不存在：{run_dir}"]}, ensure_ascii=False))
        return 2

    analysis_path = (
        Path(args.analysis).expanduser().resolve()
        if args.analysis
        else run_dir / "ux-analysis.json"
    )
    try:
        analysis_path.relative_to(run_dir)
    except ValueError:
        print(
            json.dumps(
                {"ok": False, "errors": ["analysis 文件必须位于本次运行目录内"]},
                ensure_ascii=False,
            )
        )
        return 2
    if not analysis_path.is_file():
        print(json.dumps({"ok": False, "errors": [f"分析文件不存在：{analysis_path}"]}, ensure_ascii=False))
        return 2

    try:
        raw_analysis = load_json(analysis_path)
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "errors": [f"无法读取分析文件：{error}"]}, ensure_ascii=False))
        return 2

    errors, analysis = validate_analysis(raw_analysis, run_dir)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 2

    manifest_path = run_dir / "manifest.json"
    manifest = load_json(manifest_path) if manifest_path.is_file() else {}
    result = {
        "ok": True,
        "run_dir": str(run_dir),
        "analysis": str(analysis_path),
        "findings": len(analysis["findings"]),
        "journey_steps": len(analysis["journey"]),
        "screen_reviews": len(analysis["screen_reviews"]),
        "check_only": args.check_only,
    }
    if args.check_only:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    brief_md = decision_brief_markdown(analysis)
    brief_html = decision_brief_html(analysis)
    if args.brief_only:
        atomic_write(run_dir / "decision-brief.md", brief_md)
        atomic_write(run_dir / "decision-brief.html", brief_html)
        result["decision_brief_markdown"] = str(run_dir / "decision-brief.md")
        result["decision_brief_html"] = str(run_dir / "decision-brief.html")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    preserve_capture_report(run_dir)
    markdown = render_markdown(analysis, manifest)
    html_report = render_html(analysis, manifest)
    atomic_write(run_dir / "report.md", markdown)
    atomic_write(run_dir / "report.html", html_report)
    atomic_write(run_dir / "decision-brief.md", brief_md)
    atomic_write(run_dir / "decision-brief.html", brief_html)
    result["report_markdown"] = str(run_dir / "report.md")
    result["report_html"] = str(run_dir / "report.html")
    result["decision_brief_html"] = str(run_dir / "decision-brief.html")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
