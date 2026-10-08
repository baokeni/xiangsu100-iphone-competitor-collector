#!/usr/bin/env python3
"""Offline evidence, design review and derived-report freshness checks. No device APIs."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def strings(obj, fields, label, errors):
    for key in fields:
        if not isinstance(obj.get(key), str) or not obj[key].strip():
            errors.append(f"{label}.{key}: 需要非空文字（未知填写 unknown）")


def verify_file(item, base, label, errors):
    path, expected = item.get("path"), item.get("sha256")
    if not isinstance(path, str) or not path.strip() or not (base / path).is_file():
        errors.append(f"{label}: 来源文件不存在")
    elif not isinstance(expected, str) or len(expected) != 64 or digest(base / path) != expected:
        errors.append(f"{label}: 来源哈希缺失或不一致")


def validate_baseline(data, base):
    errors = []
    baseline = data.get("target_baseline")
    if not isinstance(baseline, dict):
        return ["target_baseline: 新报告需登记目标现状；无材料时 status=unknown、evidence=[]，说明边界"]
    strings(baseline, ("summary", "limits"), "target_baseline", errors)
    if baseline.get("status") not in ("unknown", "partial", "observed"):
        errors.append("target_baseline.status: 只能是 unknown/partial/observed")
    evidence = baseline.get("evidence")
    if not isinstance(evidence, list):
        return errors + ["target_baseline.evidence: 需要数组"]
    ids = set()
    for item in evidence:
        if not isinstance(item, dict):
            errors.append("target_baseline.evidence: 每项需要对象")
            continue
        strings(item, ("id", "page", "object", "state", "captured_at", "observed", "limits"), "target evidence", errors)
        eid = item.get("id")
        if isinstance(eid, str):
            if eid in ids:
                errors.append(f"target evidence: 重复编号 {eid}")
            ids.add(eid)
        if item.get("source_type") not in ("user_screenshot", "device_capture", "document"):
            errors.append("target evidence.source_type: 未知来源类型")
        if item.get("continuity") not in ("not_established", "documented"):
            errors.append("target evidence.continuity: 必须明确连续性")
        if item.get("continuity") == "documented":
            refs = item.get("continuity_refs")
            if not isinstance(refs, list) or not refs or not all(isinstance(x, str) and (base / x).is_file() for x in refs):
                errors.append("target evidence: 连续流程需要事件或前后状态证据，单张图片不够")
        verify_file(item, base, "target evidence", errors)
    if baseline.get("status") != "unknown" and not evidence:
        errors.append("target_baseline: 已观察/局部观察需要来源")
    if baseline.get("status") == "unknown" and evidence:
        errors.append("target_baseline: 已有可见材料时用 partial，未知部分写入 limits")
    for dimension in data.get("dimensions", []):
        if not isinstance(dimension, dict):
            continue
        refs = dimension.get("target_evidence_ids")
        if not isinstance(refs, list) or any(not isinstance(x, str) or x not in ids for x in refs):
            errors.append(f"{dimension.get('id')}.target_evidence_ids: 必须引用已登记目标证据；未知可用空数组")
    return errors


def check_design(data, base):
    """Validate a review record; never infer usability success from a valid record."""
    errors = []
    analysis = data.get("analysis", {})
    verify_file(analysis, base, "design.analysis", errors)
    if errors:
        return errors, "stale_or_invalid"
    source = read(base / analysis["path"])
    from render_cross_report import validate
    errors.extend(validate(source, (base / analysis["path"]).resolve().parent))
    goals = {g["id"] for g in source.get("research_goals", [])}
    dimensions = {d["id"]: d for d in source.get("dimensions", [])}
    scope = data.get("scope_goal_ids")
    if not isinstance(scope, list) or not scope or any(not isinstance(x, str) or x not in goals for x in scope):
        return errors + ["scope_goal_ids: 需要本次设计涵盖的已登记目标"], "invalid"
    strings(data, ("scope_note",), "design", errors)
    regions = data.get("regions")
    if not isinstance(regions, list) or not regions:
        return errors + ["regions: 至少一个改动区域"], "invalid"
    check_ids, covered = set(), set()
    for region in regions:
        if not isinstance(region, dict):
            errors.append("region: 需要对象")
            continue
        strings(region, ("name", "preserve", "change", "information_priority", "data_policy", "states"), "region", errors)
        refs = region.get("dimension_ids")
        if not isinstance(refs, list) or not refs or any(not isinstance(x, str) or x not in dimensions for x in refs):
            errors.append("region.dimension_ids: 改动必须回到分析维度及其目标/证据")
        else:
            for ref in refs:
                gid = dimensions[ref]["goal_id"]
                if gid not in scope:
                    errors.append("region: 改动超出本次设计目标")
                covered.add(gid)
        checks = region.get("acceptance")
        if not isinstance(checks, list) or not checks:
            errors.append("region.acceptance: 需要可检查的成图判据")
            continue
        for check in checks:
            if not isinstance(check, dict):
                errors.append("acceptance: 需要对象")
                continue
            strings(check, ("id", "criterion"), "acceptance", errors)
            cid = check.get("id")
            if isinstance(cid, str):
                if cid in check_ids:
                    errors.append("acceptance: 重复检查编号")
                check_ids.add(cid)
    if set(scope) - covered:
        errors.append("design: 所选目标没有对应设计改动")
    review = data.get("artifact_review")
    if review is None:
        return errors, "not_generated_or_not_reviewed"
    if not isinstance(review, dict):
        return errors + ["artifact_review: 需要对象"], "invalid"
    verify_file(review, base, "artifact_review", errors)
    strings(review, ("reviewer", "reviewed_at", "effect_validation"), "artifact_review", errors)
    checks = review.get("checks")
    if not isinstance(checks, list):
        return errors + ["artifact_review.checks: 需要逐项检查结果"], "invalid"
    seen, outcomes = set(), []
    for check in checks:
        if not isinstance(check, dict):
            errors.append("artifact review check: 需要对象")
            continue
        cid = check.get("check_id")
        if not isinstance(cid, str) or cid not in check_ids or cid in seen:
            errors.append("artifact_review: 检查编号未登记或重复")
        if isinstance(cid, str):
            seen.add(cid)
        strings(check, ("note",), "artifact_review.check", errors)
        outcome = check.get("outcome")
        if outcome not in ("pass", "needs_revision", "not_verified"):
            errors.append("artifact_review: 未知检查结果")
        outcomes.append(outcome)
    if seen != check_ids:
        errors.append("artifact_review: 必须覆盖全部成图检查项")
    status = "needs_revision" if "needs_revision" in outcomes else "not_verified" if "not_verified" in outcomes else "design_checks_passed"
    return errors, status


def artifact_status(item, base):
    receipt = item.get("receipt", {})
    if not (base / item["path"]).is_file():
        return "missing"
    if item["role"] == "historical":
        return "historical"
    deps = item.get("dependencies", [])
    if not receipt or not deps:
        return "pending"
    if any(not (base / x).is_file() for x in deps):
        return "stale"
    actual = {x: digest(base / x) for x in deps}
    if actual != receipt.get("dependencies") or digest(base / item["path"]) != receipt.get("sha256"):
        return "stale"
    return "concept" if item["role"] == "concept" else "current"


def validate_manifest(data, base=Path(".")):
    items = data.get("artifacts")
    if not isinstance(items, list) or not items:
        raise ValueError("artifacts 需要非空数组")
    ids, paths = set(), set()
    for item in items:
        if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k].strip() for k in ("id", "path", "role")):
            raise ValueError("artifact 需要 id/path/role")
        if item["id"] in ids or item["path"] in paths:
            raise ValueError("artifact id/path 重复")
        ids.add(item["id"]); paths.add(item["path"])
        if item["role"] not in ("current", "historical", "concept"):
            raise ValueError("artifact.role 只能为 current/historical/concept")
        deps = item.get("dependencies", [])
        if not isinstance(deps, list) or any(not isinstance(x, str) or not x for x in deps):
            raise ValueError("dependencies 需要路径数组")
        if item["role"] != "historical" and not deps:
            raise ValueError("当前报告与概念稿需要登记 dependencies")
    by_path = {(base / x["path"]).resolve(): x for x in items}
    active, done = set(), set()
    def visit(item):
        key = item["id"]
        if key in active:
            raise ValueError("产物依赖有环，无法按上游到下游重建")
        if key in done:
            return
        active.add(key)
        for dep in item.get("dependencies", []):
            upstream = by_path.get((base / dep).resolve())
            if upstream:
                visit(upstream)
        active.remove(key); done.add(key)
    for item in items:
        visit(item)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    design = sub.add_parser("check-design")
    design.add_argument("path", type=Path)
    design.add_argument("--require-design-pass", action="store_true")
    release = sub.add_parser("check-release")
    release.add_argument("path", type=Path)
    record = sub.add_parser("record", help="仅在实际重建或人工核对产物后登记；不是自动验收")
    record.add_argument("path", type=Path)
    record.add_argument("--artifact", required=True)
    args = parser.parse_args()
    path = args.path.resolve(); data = read(path); base = path.parent
    if args.command == "check-design":
        errors, status = check_design(data, base)
        print(json.dumps({"record_valid": not errors, "design_status": status, "errors": errors, "notice": "记录有效不等于设计通过，更不等于用户效果验证"}, ensure_ascii=False, indent=2))
        return int(bool(errors) or (args.require_design_pass and status != "design_checks_passed"))
    validate_manifest(data, base)
    if args.command == "record":
        matches = [x for x in data["artifacts"] if x["id"] == args.artifact]
        if not matches:
            raise ValueError("未登记的 artifact id")
        item = matches[0]
        item["receipt"] = {"updated_at": datetime.now(timezone.utc).isoformat(), "sha256": digest(base / item["path"]), "dependencies": {x: digest(base / x) for x in item["dependencies"]}}
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("RECORDED:", item["id"], "（仅记录版本与哈希）")
        return 0
    states = {x["id"]: artifact_status(x, base) for x in data["artifacts"]}
    # A derived report cannot remain current when its registered input is stale.
    by_path = {(base / x["path"]).resolve(): x["id"] for x in data["artifacts"]}
    for _ in states:
        for item in data["artifacts"]:
            if states[item["id"]] in ("current", "concept") and any(states.get(by_path.get((base / dep).resolve())) in ("stale", "pending", "missing") for dep in item.get("dependencies", [])):
                states[item["id"]] = "stale"
    print(json.dumps(states, ensure_ascii=False, indent=2))
    return int(any(x in ("stale", "pending", "missing") for x in states.values()))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError) as error:
        print("ERROR:", error)
        raise SystemExit(1)
