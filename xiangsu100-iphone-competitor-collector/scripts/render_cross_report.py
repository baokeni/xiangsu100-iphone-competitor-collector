#!/usr/bin/env python3
"""Validate and render a source-linked cross-competitor decision report."""

from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
from urllib.parse import quote
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence_checks import check_refs
from research_delivery import validate_baseline
from redesign_summary import validate_summary, render_html as summary_html, render_markdown as summary_md


STATUSES = {
    "observed": "已观察",
    "partial": "局部观察",
    "not_verified": "未验证",
    "user_excluded": "用户排除",
    "not_applicable": "不适用",
}
ACTIONS = {
    "adopt": "采用",
    "adapt": "调整后采用",
    "keep": "保持现状",
    "defer": "暂缓判断",
    "reject": "不建议采用",
}
CELL_FIELDS = ("mechanism", "decision_support", "friction", "unknown")
DECISION_FIELDS = (
    "judgment", "conditions", "minimum_change", "cost", "alternative", "validation", "falsifier"
)


def local_path(base: Path, value: str) -> Path:
    return (base / value).resolve()


def text_field(obj: dict, key: str, location: str, errors: list[str]) -> None:
    if not isinstance(obj.get(key), str) or not obj[key].strip():
        errors.append(f"{location}.{key}: 需要非空文字")


def validate(data: object, base: Path, *, allow_legacy: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["输入根节点需要对象"]
    for key in ("title", "target_product", "task", "scope_note", "limits"):
        text_field(data, key, "root", errors)
    platforms = data.get("platforms")
    channels = data.get("channels")
    dimensions = data.get("dimensions")
    if not isinstance(platforms, list) or not platforms:
        errors.append("platforms: 至少一个独立平台")
        platforms = []
    if not isinstance(channels, list) or not channels:
        errors.append("channels: 至少一个频道")
        channels = []
    if not isinstance(dimensions, list) or not dimensions:
        errors.append("dimensions: 至少一个用户决定")
        dimensions = []
    goals = data.get("research_goals")
    if goals is None and not allow_legacy:
        errors.append("research_goals: 新报告必须登记目标；历史读取须显式使用 --allow-legacy")
    goal_ids: set[str] = set()
    primary_goal_ids: set[str] = set()
    if goals is not None:
        if not isinstance(goals, list) or not goals:
            errors.append("research_goals: 需要非空研究目标数组")
            goals = []
        for i, goal in enumerate(goals):
            loc = f"research_goals[{i}]"
            if not isinstance(goal, dict):
                errors.append(f"{loc}: 需要对象")
                continue
            for key in (("id", "statement") if allow_legacy else ("id", "statement", "original_text", "revision_source", "priority_reason")):
                text_field(goal, key, loc, errors)
            if (not allow_legacy or "experience_status" in goal) and goal.get("experience_status") not in ("unknown", "problem_observed", "satisfactory", "mixed"):
                errors.append(f"{loc}.experience_status: 独立记录现状判断，不能从优先级推断")
            gid = goal.get("id")
            if isinstance(gid, str):
                if gid in goal_ids:
                    errors.append(f"{loc}: 研究目标 id 重复")
                goal_ids.add(gid)
                if goal.get("priority") == "primary":
                    primary_goal_ids.add(gid)
            if goal.get("priority") not in ("primary", "supporting"):
                errors.append(f"{loc}.priority: 只能是 primary/supporting")
    if not allow_legacy or data.get("target_baseline") is not None:
        errors.extend(validate_baseline(data, base))
    platform_ids: set[str] = set()
    for i, item in enumerate(platforms):
        if not isinstance(item, dict):
            errors.append(f"platforms[{i}]: 需要对象")
            continue
        for key in ("id", "name"):
            text_field(item, key, f"platforms[{i}]", errors)
        pid = item.get("id")
        if isinstance(pid, str):
            if pid in platform_ids:
                errors.append(f"platforms[{i}]: 平台 id 重复")
            platform_ids.add(pid)
    channel_ids: set[str] = set()
    for i, item in enumerate(channels):
        if not isinstance(item, dict):
            errors.append(f"channels[{i}]: 需要对象")
            continue
        for key in ("id", "name", "platform_id"):
            text_field(item, key, f"channels[{i}]", errors)
        cid = item.get("id")
        if isinstance(cid, str):
            if cid in channel_ids:
                errors.append(f"channels[{i}]: 频道 id 重复")
            channel_ids.add(cid)
        if item.get("platform_id") not in platform_ids:
            errors.append(f"channels[{i}]: platform_id 未登记")
    primary_count = 0
    dimension_ids: set[str] = set()
    for i, item in enumerate(dimensions):
        loc = f"dimensions[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{loc}: 需要对象")
            continue
        for key in ("id", "user_decision", "necessary_support", "comparability"):
            text_field(item, key, loc, errors)
        did = item.get("id")
        if isinstance(did, str):
            if did in dimension_ids:
                errors.append(f"{loc}: 维度 id 重复")
            dimension_ids.add(did)
        if goals is not None and item.get("goal_id") not in goal_ids:
            errors.append(f"{loc}.goal_id: 必须对应已登记研究目标")
        priority = item.get("priority")
        if priority not in ("primary", "supporting"):
            errors.append(f"{loc}.priority: 只能是 primary/supporting")
        primary_count += priority == "primary"
        if goals is not None and priority == "primary" and item.get("goal_id") not in primary_goal_ids:
            errors.append(f"{loc}: 主要设计方向不能挂在支持性研究目标下")
        cells = item.get("cells")
        if not isinstance(cells, list):
            errors.append(f"{loc}.cells: 需要数组")
            cells = []
        seen: set[str] = set()
        for j, cell in enumerate(cells):
            cloc = f"{loc}.cells[{j}]"
            if not isinstance(cell, dict):
                errors.append(f"{cloc}: 需要对象")
                continue
            cid = cell.get("channel_id")
            if cid not in channel_ids or cid in seen:
                errors.append(f"{cloc}: channel_id 未登记或重复")
            if isinstance(cid, str):
                seen.add(cid)
            status = cell.get("status")
            if status not in STATUSES:
                errors.append(f"{cloc}.status: 未知状态")
            for key in CELL_FIELDS:
                text_field(cell, key, cloc, errors)
            refs = cell.get("evidence_refs")
            check_refs(refs, base, cloc, errors)
            if status in ("observed", "partial") and not refs:
                errors.append(f"{cloc}: 已观察单元需要来源")
        if seen != channel_ids:
            errors.append(f"{loc}: 每个频道需要且只需一个单元")
        decision = item.get("target_decision")
        if not isinstance(decision, dict):
            errors.append(f"{loc}.target_decision: 需要对象")
        else:
            if decision.get("action") not in ACTIONS:
                errors.append(f"{loc}.target_decision.action: 未知动作")
            for key in DECISION_FIELDS:
                text_field(decision, key, f"{loc}.target_decision", errors)
        proposal = item.get("design_proposal")
        if proposal is not None:
            if not isinstance(proposal, dict):
                errors.append(f"{loc}.design_proposal: 需要对象")
            else:
                for key in ("title", "placement", "interaction", "key_states"):
                    text_field(proposal, key, f"{loc}.design_proposal", errors)
                components = proposal.get("components")
                if not isinstance(components, list) or not components or not all(isinstance(x, str) and x.strip() for x in components):
                    errors.append(f"{loc}.design_proposal.components: 需要非空文字数组")
                screens = proposal.get("screens")
                if not isinstance(screens, list) or not screens:
                    errors.append(f"{loc}.design_proposal.screens: 至少一幅界面示意")
                else:
                    for j, screen in enumerate(screens):
                        sloc = f"{loc}.design_proposal.screens[{j}]"
                        if not isinstance(screen, dict):
                            errors.append(f"{sloc}: 需要对象")
                            continue
                        for key in ("name", "title", "action"):
                            text_field(screen, key, sloc, errors)
                        blocks = screen.get("blocks")
                        if not isinstance(blocks, list) or not blocks:
                            errors.append(f"{sloc}.blocks: 至少一个信息块")
                        else:
                            for k, block in enumerate(blocks):
                                if not isinstance(block, dict):
                                    errors.append(f"{sloc}.blocks[{k}]: 需要对象")
                                else:
                                    for key in ("label", "value"):
                                        text_field(block, key, f"{sloc}.blocks[{k}]", errors)
                images = proposal.get("evidence_images")
                if not isinstance(images, list) or not images:
                    errors.append(f"{loc}.design_proposal.evidence_images: 至少一张已审查图片")
                else:
                    for j, item_image in enumerate(images):
                        iloc = f"{loc}.design_proposal.evidence_images[{j}]"
                        if not isinstance(item_image, dict):
                            errors.append(f"{iloc}: 需要对象")
                            continue
                        for key in ("path", "caption"):
                            text_field(item_image, key, iloc, errors)
                        image_path = item_image.get("path")
                        if isinstance(image_path, str):
                            resolved = local_path(base, image_path)
                            if not resolved.is_file() or resolved.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
                                errors.append(f"{iloc}.path: 图片不存在或格式不支持")
    if not allow_legacy or data.get("redesign_summary") is not None:
        errors.extend(validate_summary(data, base))
    if goals is not None:
        covered = {item.get("goal_id") for item in dimensions if isinstance(item, dict) and item.get("priority") == "primary"}
        for gid in primary_goal_ids - covered:
            errors.append(f"research_goals[{gid}]: 主要研究目标缺少对应设计方向")
        if not allow_legacy:
            all_covered = {item.get("goal_id") for item in dimensions if isinstance(item, dict) and isinstance(item.get("goal_id"), str)}
            for gid in goal_ids - primary_goal_ids - all_covered:
                errors.append(f"research_goals[{gid}]: 支持性研究目标缺少对应分析或明确的保持/暂缓结论")
    detail = data.get("detail_report")
    if detail is not None:
        if not isinstance(detail, str) or not local_path(base, detail).is_file():
            errors.append("detail_report: 文件不存在")
    related = data.get("related_links")
    if related is not None:
        if not isinstance(related, list):
            errors.append("related_links: 需要数组")
        else:
            for i, link in enumerate(related):
                if not isinstance(link, dict):
                    errors.append(f"related_links[{i}]: 需要对象")
                    continue
                text_field(link, "label", f"related_links[{i}]", errors)
                path = link.get("path")
                if not isinstance(path, str) or not local_path(base, path).is_file():
                    errors.append(f"related_links[{i}].path: 文件不存在")
    positioning = data.get("positioning")
    if positioning is not None:
        if not isinstance(positioning, dict):
            errors.append("positioning: 需要对象")
        else:
            axes = positioning.get("axes")
            if not isinstance(axes, list) or len(axes) != 2:
                errors.append("positioning.axes: 需要两个轴")
            else:
                for i, axis in enumerate(axes):
                    if not isinstance(axis, dict):
                        errors.append(f"positioning.axes[{i}]: 需要对象")
                    else:
                        for key in ("name", "criteria"):
                            text_field(axis, key, f"positioning.axes[{i}]", errors)
            entries = positioning.get("entries")
            if not isinstance(entries, list):
                errors.append("positioning.entries: 需要数组")
            else:
                seen: set[str] = set()
                for i, entry in enumerate(entries):
                    loc = f"positioning.entries[{i}]"
                    if not isinstance(entry, dict):
                        errors.append(f"{loc}: 需要对象")
                        continue
                    cid = entry.get("channel_id")
                    if cid not in channel_ids or cid in seen:
                        errors.append(f"{loc}: channel_id 未登记或重复")
                    if isinstance(cid, str):
                        seen.add(cid)
                    if entry.get("status") not in ("placed", "partial", "unpositioned"):
                        errors.append(f"{loc}.status: 未知状态")
                    for key in ("x", "y", "reason"):
                        text_field(entry, key, loc, errors)
                    check_refs(entry.get("evidence_refs"), base, loc, errors)
                    if entry.get("status") == "placed" and not entry.get("evidence_refs"):
                        errors.append(f"{loc}: 已定位需要来源")
                if seen != channel_ids:
                    errors.append("positioning.entries: 每个频道需要且只需一项")
    flows = data.get("flows")
    if flows is not None:
        if not isinstance(flows, list):
            errors.append("flows: 需要数组")
        else:
            for i, flow in enumerate(flows):
                loc = f"flows[{i}]"
                if not isinstance(flow, dict):
                    errors.append(f"{loc}: 需要对象")
                    continue
                text_field(flow, "branch", loc, errors)
                routes = flow.get("routes")
                if not isinstance(routes, list):
                    errors.append(f"{loc}.routes: 需要数组")
                    continue
                seen: set[str] = set()
                for j, route in enumerate(routes):
                    rloc = f"{loc}.routes[{j}]"
                    if not isinstance(route, dict):
                        errors.append(f"{rloc}: 需要对象")
                        continue
                    cid = route.get("channel_id")
                    if cid not in channel_ids or cid in seen:
                        errors.append(f"{rloc}: channel_id 未登记或重复")
                    if isinstance(cid, str):
                        seen.add(cid)
                    if route.get("status") not in STATUSES:
                        errors.append(f"{rloc}.status: 未知状态")
                    text_field(route, "route", rloc, errors)
                    check_refs(route.get("evidence_refs"), base, rloc, errors)
                    if route.get("status") in ("observed", "partial") and not route.get("evidence_refs"):
                        errors.append(f"{rloc}: 已观察路由需要来源")
                if seen != channel_ids:
                    errors.append(f"{loc}: 每个频道需要且只需一条路由")
    return errors


def link_target(output_dir: Path, base: Path, ref: str) -> str:
    target = local_path(base, ref)
    return quote(os.path.relpath(target, output_dir.resolve()), safe="/._-~")


def md_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def original_for_ref(base: Path, ref: str) -> str | None:
    path = local_path(base, ref)
    if path.suffix != ".json":
        return None
    try:
        index = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(index, dict) and index.get("kind") == "source_evidence_index":
        source = index.get("source")
        if isinstance(source, str) and (path.parent / source).is_file():
            return str((path.parent / source).resolve())
    return None


def refs_md(refs: list[str], output_dir: Path, base: Path) -> str:
    values = []
    for ref in refs:
        value = f"[{Path(ref).stem}]({link_target(output_dir, base, ref)})"
        original = original_for_ref(base, ref)
        if original:
            value += f"（[原图]({link_target(output_dir, base, original)})）"
        values.append(value)
    return "、".join(values) or "无新增来源"


def refs_html(refs: list[str], output_dir: Path, base: Path) -> str:
    values = []
    for ref in refs:
        value = f'<a href="{html.escape(link_target(output_dir, base, ref), quote=True)}">{html.escape(Path(ref).stem)}</a>'
        original = original_for_ref(base, ref)
        if original:
            href = html.escape(link_target(output_dir, base, original), quote=True)
            value += f'（<a href="{href}">原图</a>）'
        values.append(value)
    return "、".join(values) or "无新增来源"


HTML_STYLE = """
*{box-sizing:border-box}body{margin:0;background:#f2f5f9;color:#17233a;font:16px/1.6 system-ui,-apple-system,sans-serif}
main{max-width:1240px;margin:auto;padding:24px}a{color:#075b9d}h1,h2,h3{line-height:1.25}
.hero{background:#172b48;color:#fff;border-radius:20px;padding:32px;margin-bottom:22px}.hero h1{margin:8px 0 12px;font-size:clamp(26px,3vw,40px)}
.hero p{max-width:950px;margin:10px 0}.eyebrow{font-size:13px;font-weight:750;letter-spacing:.08em;color:#ffd57a}.scope{color:#c9d8ea}
.quicklinks{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0 4px}.quicklinks a{display:inline-block;background:#fff;color:#142b47;text-decoration:none;padding:9px 14px;border-radius:999px;font-weight:700}
.intro{margin:18px 0 22px}.intro p{color:#4a5b6f;margin:6px 0}.scheme{background:#fff;border:1px solid #d9e1ea;border-radius:20px;padding:24px;margin:0 0 24px;box-shadow:0 9px 28px #1837530c}
.scheme-head{display:flex;gap:12px;align-items:flex-start;justify-content:space-between}.scheme-num{display:inline-block;background:#e7f2ff;color:#0a5388;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:800}
.scheme h3{font-size:25px;margin:10px 0 8px}.scheme .placement{margin:0 0 18px;color:#475a70}.scheme-grid{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr);gap:22px}
.panel-label{display:block;font-size:13px;font-weight:800;color:#526a84;margin:0 0 8px}.mock-set{display:flex;gap:12px;overflow:auto;padding:4px 2px 14px}
.mock-phone{flex:1;min-width:215px;max-width:340px;border:2px solid #1e3148;border-radius:25px;background:#f8fafc;padding:14px;box-shadow:0 7px 18px #11294719}
.mock-top{text-align:center;font-size:11px;color:#617084;border-bottom:1px solid #d9e1ea;padding:2px 0 10px}.mock-phone h4{font-size:17px;margin:12px 0}.mock-block{background:#fff;border:1px solid #dce5ee;border-radius:11px;padding:9px 11px;margin:8px 0}.mock-block small{display:block;color:#586d81;font-weight:700}.mock-block strong{display:block;color:#182b42;font-size:14px;font-weight:650}.mock-action{margin-top:13px;background:#165d9b;color:#fff;text-align:center;border-radius:10px;padding:9px;font-weight:750;font-size:13px}
.evidence-gallery{display:flex;gap:10px;overflow:auto;padding:4px 2px 14px}.evidence-gallery figure{flex:1;min-width:145px;max-width:205px;margin:0;background:#f7f9fc;border:1px solid #dce5ee;border-radius:12px;overflow:hidden}
.evidence-gallery img{display:block;width:100%;height:270px;object-fit:contain;background:#e8edf3}.evidence-gallery figcaption{padding:8px 9px;font-size:12px;color:#3e5269}
.components{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:0;margin:14px 0}.components li{background:#eef5fb;color:#173f61;padding:6px 10px;border-radius:8px;font-size:13px}
.scheme-notes{display:grid;grid-template-columns:1fr 1fr;gap:10px}.scheme-notes p{margin:0;padding:12px;background:#f7f9fc;border-radius:10px;font-size:14px}.scheme-notes b{display:block;color:#334e69}
.decision-detail{margin-top:16px;border-top:1px solid #e2e8f0;padding-top:12px;color:#455970;font-size:14px}.decision-detail summary{cursor:pointer;font-weight:750;color:#0b5f9c}.decision-detail p{margin:7px 0}
.goal-map{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px;margin:18px 0}.goal-map article{background:#fff;border:1px solid #dce4ed;border-radius:12px;padding:15px}.goal-map b{color:#0b5f9c}.goal-link{font-size:13px;color:#0b5f9c;font-weight:750;margin:2px 0 10px}
.deep{background:#fff;border:1px solid #dce4ed;border-radius:16px;padding:18px 22px;margin:28px 0}.deep>summary{cursor:pointer;font-size:20px;font-weight:800}.deep section{margin:26px 0;border-top:1px solid #e5e9ef;padding-top:18px}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #dce3eb;vertical-align:top;padding:9px;text-align:left}th{background:#f0f4f8}.scroll{overflow-x:auto}.muted{color:#586b80}
@media(max-width:850px){.scheme-grid{grid-template-columns:1fr}.scheme-notes{grid-template-columns:1fr}}@media(max-width:600px){main{padding:10px}.hero,.scheme{padding:18px}.mock-phone{min-width:200px}table{min-width:800px}}
"""


def render_proposal_html(item: dict, number: int, output_dir: Path, base: Path, goal_statement: str = "") -> str:
    e = html.escape
    d = item["target_decision"]
    proposal = item["design_proposal"]
    parts = [f'<section class="scheme" id="{e(item["id"], quote=True)}"><div class="scheme-head"><div><span class="scheme-num">设计方案 {number:02d} · 拟议界面</span><h3>{e(proposal["title"])}</h3></div></div>']
    if goal_statement:
        parts.append(f'<p class="goal-link">对应研究目标 {e(item["goal_id"])}：{e(goal_statement)}</p>')
    parts.append(f'<p class="placement"><b>放在：</b>{e(proposal["placement"])}</p><div class="scheme-grid"><div><span class="panel-label">目标产品拟议界面 · 非当前页面</span><div class="mock-set">')
    for screen in proposal["screens"]:
        parts.append(f'<div class="mock-phone"><div class="mock-top">{e(screen["name"])}</div><h4>{e(screen["title"])}</h4>')
        for block in screen["blocks"]:
            parts.append(f'<div class="mock-block"><small>{e(block["label"])}</small><strong>{e(block["value"])}</strong></div>')
        parts.append(f'<div class="mock-action">{e(screen["action"])}</div></div>')
    parts.append('</div></div><div><span class="panel-label">已有竞品截图 · 点击查看原图</span><div class="evidence-gallery">')
    for item_image in proposal["evidence_images"]:
        href = e(link_target(output_dir, base, item_image["path"]), quote=True)
        caption = e(item_image["caption"])
        parts.append(f'<figure><a href="{href}"><img src="{href}" alt="{caption}" loading="lazy"></a><figcaption>{caption}</figcaption></figure>')
    parts.append('</div></div></div>')
    parts.append('<ul class="components">' + ''.join(f'<li>{e(x)}</li>' for x in proposal["components"]) + '</ul>')
    parts.append(f'<div class="scheme-notes"><p><b>用户怎么操作</b>{e(proposal["interaction"])}</p><p><b>必须呈现的状态</b>{e(proposal["key_states"])}</p></div>')
    refs = list(dict.fromkeys(ref for cell in item["cells"] for ref in cell["evidence_refs"]))
    parts.append(f'<details class="decision-detail"><summary>查看采用条件、代价和验证</summary><p><b>{ACTIONS[d["action"]]}：</b>{e(d["judgment"])}</p><p><b>条件：</b>{e(d["conditions"])}</p><p><b>最小改动：</b>{e(d["minimum_change"])}</p><p><b>代价与备选：</b>{e(d["cost"])} {e(d["alternative"])}</p><p><b>验证与反证：</b>{e(d["validation"])} {e(d["falsifier"])}</p><p><b>来源：</b>{refs_html(refs[:4], output_dir, base)}</p></details></section>')
    return ''.join(parts)


def render_markdown(data: dict, output_dir: Path, base: Path) -> str:
    channels = {x["id"]: x for x in data["channels"]}
    goals = {x["id"]: x for x in data.get("research_goals", [])}
    lines = [f'# {data["title"]}', "", f'**目标产品**：{data["target_product"]}　**共同任务**：{data["task"]}', "", data["scope_note"], "", f'**覆盖**：{len(data["platforms"])} 个独立平台、{len(data["channels"])} 个频道。{data["limits"]}', ""]
    if not goals or data.get("_legacy_mode"):
        lines.extend(["> 历史兼容报告：未执行完整的新报告验收，不代表当前结论。", ""])
    baseline = data.get("target_baseline")
    if baseline:
        lines.extend(["## 目标产品现状", "", baseline["summary"], "", "边界：" + baseline["limits"], ""])
        for item in baseline["evidence"]:
            lines.append(f'- **{item["id"]} · {item["page"]}**：{item["observed"]}；状态：{item["state"]}；采集时间：{item["captured_at"]}；来源：[{item["id"]}]({link_target(output_dir, base, item["path"])})')
    if data.get("related_links"):
        lines.extend(["**原报告与证据**：" + " · ".join(f'[{link["label"]}]({link_target(output_dir, base, link["path"])})' for link in data["related_links"]), ""])
    if goals:
        lines.extend(["## 研究目标与方案对应", ""])
        for goal in data["research_goals"]:
            direction = "主要改版目标" if goal["priority"] == "primary" else "支持性核对目标"
            lines.extend([f'- **{goal["id"]} · {direction}**：{goal["statement"]}', ""])
    lines.extend(["## 先看设计方案", ""])
    primary = [x for x in data["dimensions"] if x["priority"] == "primary"]
    if not primary:
        lines.extend(["本轮没有足够证据形成首页设计决定。", ""])
    for item in primary[:3]:
        d = item["target_decision"]
        refs = list(dict.fromkeys(ref for cell in item["cells"] for ref in cell["evidence_refs"]))
        proposal = item.get("design_proposal")
        if proposal:
            lines.extend([f'### {proposal["title"]}', ""])
            if goals:
                lines.extend([f'**对应研究目标 {item["goal_id"]}**：{goals[item["goal_id"]]["statement"]}', ""])
            lines.extend([f'**拟议位置**：{proposal["placement"]}', "", "**界面组成**：" + "；".join(proposal["components"]), "", f'**操作**：{proposal["interaction"]}', "", f'**关键状态**：{proposal["key_states"]}', ""])
            for screen in proposal["screens"]:
                lines.extend([f'#### 界面示意：{screen["name"]}', "", f'**{screen["title"]}**', ""])
                lines.extend([f'- {block["label"]}：{block["value"]}' for block in screen["blocks"]])
                lines.extend([f'- 操作：{screen["action"]}', ""])
            for item_image in proposal["evidence_images"]:
                href = link_target(output_dir, base, item_image["path"])
                lines.extend([f'![{item_image["caption"]}]({href})', "", f'*竞品证据：{item_image["caption"]}。这是既有截图，非目标产品现状。*', ""])
        else:
            lines.extend([f'### {item["user_decision"]}', ""])
        lines.extend([
            f'**判断**：{ACTIONS[d["action"]]}。{d["judgment"]}', "",
            f'**依据**：{refs_md(refs[:4], output_dir, base)}。**适用条件**：{d["conditions"]}', "",
            f'**最小改动**：{d["minimum_change"]}　**代价**：{d["cost"]}', "",
            f'**备选**：{d["alternative"]}', "",
            f'**验证与反证**：{d["validation"].rstrip("。；; ")}；{d["falsifier"]}', "",
        ])
    lines.extend(["## 按用户决定对照", ""])
    for item in data["dimensions"]:
        lines.extend([f'### {item["id"]}｜{item["user_decision"]}', "", f'**必要支持**：{item["necessary_support"]}', "", f'**可比口径**：{item["comparability"]}', "", "| 频道 | 证据状态 | 实际机制 | 支持判断 | 阻力 | 未知项 | 来源 |", "|---|---|---|---|---|---|---|"])
        for cell in item["cells"]:
            values = [channels[cell["channel_id"]]["name"], STATUSES[cell["status"]], *(cell[k] for k in CELL_FIELDS), refs_md(cell["evidence_refs"], output_dir, base)]
            lines.append("| " + " | ".join(md_escape(x) for x in values) + " |")
        d = item["target_decision"]
        lines.extend(["", f'**目标产品结论**：{ACTIONS[d["action"]]}。{d["judgment"]} 条件：{d["conditions"]}', ""])
    if data.get("positioning"):
        axes = data["positioning"]["axes"]
        lines.extend(["## 定位轴与证据范围", "", f'**横轴：{axes[0]["name"]}**。判据：{axes[0]["criteria"]}', "", f'**纵轴：{axes[1]["name"]}**。判据：{axes[1]["criteria"]}', "", "| 频道 | 定位状态 | 横轴观察 | 纵轴观察 | 落点理由与边界 | 来源 |", "|---|---|---|---|---|---|"])
        labels = {"placed": "已定性定位", "partial": "局部定位", "unpositioned": "待定位"}
        for entry in data["positioning"]["entries"]:
            values = [channels[entry["channel_id"]]["name"], labels[entry["status"]], entry["x"], entry["y"], entry["reason"], refs_md(entry["evidence_refs"], output_dir, base)]
            lines.append("| " + " | ".join(md_escape(x) for x in values) + " |")
        lines.append("")
    if data.get("flows"):
        lines.extend(["## 共同任务的实际分支", "", "| 分支 | 频道 | 状态 | 实际路由或缺口 | 来源 |", "|---|---|---|---|---|"])
        for flow in data["flows"]:
            for route in flow["routes"]:
                values = [flow["branch"], channels[route["channel_id"]]["name"], STATUSES[route["status"]], route["route"], refs_md(route["evidence_refs"], output_dir, base)]
                lines.append("| " + " | ".join(md_escape(x) for x in values) + " |")
        lines.append("")
    if data.get("detail_report"):
        lines.extend([f'更多流程、证据和图库见[详细横向报告]({link_target(output_dir, base, data["detail_report"])})。', ""])
    lines.append(summary_md(data, output_dir, base))
    lines.append("本报告是现有证据的结构化试稿；链接与结构通过检查不代表真实用户验证或浏览器视觉验收。")
    return "\n".join(lines) + "\n"


def render_html(data: dict, output_dir: Path, base: Path) -> str:
    e = html.escape
    channels = {x["id"]: x for x in data["channels"]}
    goals = {x["id"]: x for x in data.get("research_goals", [])}
    parts = [f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(data["title"])}</title><style>{HTML_STYLE}</style></head><body><main>']
    parts.append(f'<header class="hero"><span class="eyebrow">横向竞品分析 · 方案试稿</span><h1>{e(data["title"])}</h1><p><b>目标产品：</b>{e(data["target_product"])}　<b>共同任务：</b>{e(data["task"])}</p><p class="scope">{e(data["scope_note"])} 覆盖 {len(data["platforms"])} 个独立平台、{len(data["channels"])} 个频道。</p><nav class="quicklinks" aria-label="研究材料入口">')
    for link in data.get("related_links", []):
        href = e(link_target(output_dir, base, link["path"]), quote=True)
        parts.append(f'<a href="{href}">{e(link["label"])}</a>')
    parts.append('</nav></header>')
    if data.get('redesign_summary'):
        parts.append('<p><a href="#redesign-summary">直接查看：改版优先级与页面调整 ↓</a></p>')
    if not goals or data.get("_legacy_mode"):
        parts.append('<p role="status">历史兼容报告：未执行完整的新报告验收，不代表当前结论。</p>')
    baseline = data.get("target_baseline")
    if baseline:
        parts.append(f'<details class="deep"><summary>目标产品现状与来源</summary><p>{e(baseline["summary"])}</p><p>{e(baseline["limits"])}</p>')
        for item in baseline["evidence"]:
            href = e(link_target(output_dir, base, item['path']), quote=True)
            parts.append(f'<p><a href="{href}">{e(item["id"])} · {e(item["page"])}</a>：{e(item["observed"])}；状态：{e(item["state"])}；采集时间：{e(item["captured_at"])}</p>')
        parts.append('</details>')
    if goals:
        parts.append('<div class="goal-map" aria-label="研究目标与改版范围">')
        for goal in data["research_goals"]:
            label = '主要改版目标' if goal['priority'] == 'primary' else '支持性核对目标'
            parts.append(f'<article><b>{e(goal["id"])} · {label}</b><p>{e(goal["statement"])}</p></article>')
        parts.append('</div>')
    primary = [x for x in data["dimensions"] if x["priority"] == "primary"]
    parts.append(f'<div class="intro"><h2>先看 {min(len(primary), 3)} 项拟议设计方案</h2><p>全部 {len(primary)} 项主要方向及其行动顺序见逐维度证据和最后总结。左侧是目标产品的低保真示意，右侧是既有竞品截图。示意不代表目标产品当前界面；{e(data["limits"])}</p></div>')
    if not primary:
        parts.append('<p>本轮没有足够证据形成首页设计方案。</p>')
    for number, item in enumerate(primary[:3], 1):
        if item.get("design_proposal"):
            parts.append(render_proposal_html(item, number, output_dir, base, goals.get(item.get("goal_id"), {}).get("statement", "")))
            continue
        d = item["target_decision"]
        refs = list(dict.fromkeys(ref for cell in item["cells"] for ref in cell["evidence_refs"]))
        parts.append(f'<section class="scheme" id="{e(item["id"], quote=True)}"><h3>{e(item["user_decision"])}</h3><p><b>{ACTIONS[d["action"]]}：</b>{e(d["judgment"])}</p><p><b>依据：</b>{refs_html(refs[:4], output_dir, base)}</p><p><b>条件：</b>{e(d["conditions"])}</p><p><b>最小改动：</b>{e(d["minimum_change"])}</p></section>')
    parts.append('<details class="deep"><summary>查看逐维度证据与适用条件</summary><h2>按用户决定对照</h2>')
    for item in data["dimensions"]:
        parts.append(f'<section id="detail-{e(item["id"], quote=True)}"><h3>{e(item["id"])}｜{e(item["user_decision"])}</h3><p><b>必要支持：</b>{e(item["necessary_support"])}<br><b>可比口径：</b>{e(item["comparability"])}</p><div class="scroll"><table><thead><tr><th>频道</th><th>证据状态</th><th>实际机制</th><th>支持判断</th><th>阻力</th><th>未知项</th><th>来源</th></tr></thead><tbody>')
        for cell in item["cells"]:
            values = [e(channels[cell["channel_id"]]["name"]), STATUSES[cell["status"]], *(e(cell[k]) for k in CELL_FIELDS), refs_html(cell["evidence_refs"], output_dir, base)]
            parts.append('<tr>' + ''.join(f'<td>{x}</td>' for x in values) + '</tr>')
        d = item["target_decision"]
        parts.append(f'</tbody></table></div><p><b>目标产品结论：</b>{ACTIONS[d["action"]]}。{e(d["judgment"])} 条件：{e(d["conditions"])}</p></section>')
    if data.get("positioning"):
        axes = data["positioning"]["axes"]
        parts.append(f'<section><h2>定位轴与证据范围</h2><p><b>横轴：{e(axes[0]["name"])}</b>。判据：{e(axes[0]["criteria"])}<br><b>纵轴：{e(axes[1]["name"])}</b>。判据：{e(axes[1]["criteria"])}</p><div class="scroll"><table><thead><tr><th>频道</th><th>定位状态</th><th>横轴观察</th><th>纵轴观察</th><th>落点理由与边界</th><th>来源</th></tr></thead><tbody>')
        labels = {"placed": "已定性定位", "partial": "局部定位", "unpositioned": "待定位"}
        for entry in data["positioning"]["entries"]:
            values = [e(channels[entry["channel_id"]]["name"]), labels[entry["status"]], e(entry["x"]), e(entry["y"]), e(entry["reason"]), refs_html(entry["evidence_refs"], output_dir, base)]
            parts.append('<tr>' + ''.join(f'<td>{x}</td>' for x in values) + '</tr>')
        parts.append('</tbody></table></div></section>')
    if data.get("flows"):
        parts.append('<section><h2>共同任务的实际分支</h2><div class="scroll"><table><thead><tr><th>分支</th><th>频道</th><th>状态</th><th>实际路由或缺口</th><th>来源</th></tr></thead><tbody>')
        for flow in data["flows"]:
            for route in flow["routes"]:
                values = [e(flow["branch"]), e(channels[route["channel_id"]]["name"]), STATUSES[route["status"]], e(route["route"]), refs_html(route["evidence_refs"], output_dir, base)]
                parts.append('<tr>' + ''.join(f'<td>{x}</td>' for x in values) + '</tr>')
        parts.append('</tbody></table></div></section>')
    parts.append('</details>')
    parts.append(summary_html(data, output_dir, base))
    if data.get("detail_report"):
        href = e(link_target(output_dir, base, data["detail_report"]), quote=True)
        parts.append(f'<p>更多证据与完整方法见<a href="{href}">原横向竞品分析报告</a>。</p>')
    parts.append('<p class="muted">本页方案仅供原型与任务测试；来源链接与结构通过检查不代表真实用户验证或浏览器视觉验收。</p></main></body></html>')
    return "\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--allow-legacy", action="store_true", help="仅兼容缺少目标的历史报告，不作为新报告验收")
    args = parser.parse_args()
    analysis = args.analysis.resolve()
    data = json.loads(analysis.read_text(encoding="utf-8"))
    errors = validate(data, analysis.parent, allow_legacy=args.allow_legacy)
    if errors:
        for error in errors:
            print("ERROR:", error)
        return 1
    if args.allow_legacy:
        data["_legacy_mode"] = True
        print("LEGACY: 历史兼容读取，未通过当前目标对应验收")
    else:
        print(f'VALID: {len(data["platforms"])} platforms, {len(data["channels"])} channels, {len(data["dimensions"])} dimensions')
    if args.check_only:
        return 0
    output_dir = (args.output_dir or analysis.parent).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "cross-decision-report.md").write_text(render_markdown(data, output_dir, analysis.parent), encoding="utf-8")
    (output_dir / "cross-decision-report.html").write_text(render_html(data, output_dir, analysis.parent), encoding="utf-8")
    print("WROTE:", output_dir / "cross-decision-report.md")
    print("WROTE:", output_dir / "cross-decision-report.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
