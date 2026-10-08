"""Goal-linked redesign ordering and concrete page changes for cross reports."""
import html
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from evidence_checks import check_source, digest

STAGES = {'prototype': '先做原型并测试', 'verify': '先补证再决定', 'implement': '进入实现', 'keep': '保持现状', 'defer': '暂缓', 'reject': '不采用'}


def readiness_subject_digest(data, item):
    """Bind the review to the proposal and its research context, without a cycle."""
    dims = [d for d in data.get('dimensions', []) if d.get('id') in item.get('dimension_ids', [])]
    goal_ids = {d.get('goal_id') for d in dims}
    subject = {
        'target_product': data.get('target_product'), 'task': data.get('task'),
        'target_baseline': data.get('target_baseline'), 'dimensions': dims,
        'research_goals': [g for g in data.get('research_goals', []) if g.get('id') in goal_ids],
        'item': {k: v for k, v in item.items() if k != 'readiness_evidence_refs'},
    }
    return hashlib.sha256(json.dumps(subject, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_readiness(data, item, base, refs):
    errors = []
    for ref in refs:
        path = (base / ref).resolve()
        if path.suffix.lower() != '.json':
            errors.append('readiness: 进入实现需结构化验收记录，普通附件不能替代'); continue
        try:
            review = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            errors.append('readiness: 验收记录无法读取'); continue
        if not isinstance(review, dict) or review.get('kind') != 'implementation_readiness_review':
            errors.append('readiness: 需要 implementation_readiness_review 验收记录'); continue
        if review.get('target_product') != data.get('target_product') or review.get('item_id') != item.get('id'):
            errors.append('readiness: 验收对象与当前产品/方案不符')
        if review.get('subject_sha256') != readiness_subject_digest(data, item):
            errors.append('readiness: 方案或研究依据已改变，必须重新复核')
        if review.get('outcome') != 'pass':
            errors.append('readiness: 验收未通过，不能进入实现')
        for key in ('reviewer', 'reviewed_at', 'effect_validation'):
            if not isinstance(review.get(key), str) or not review[key].strip():
                errors.append(f'readiness.{key}: 需要真实复核记录')
        try:
            datetime.fromisoformat(review.get('reviewed_at', '').replace('Z', '+00:00'))
        except (ValueError, TypeError, AttributeError):
            errors.append('readiness.reviewed_at: 需要 ISO 日期或时间')
        checks = review.get('checks')
        if not isinstance(checks, list) or not checks:
            errors.append('readiness.checks: 需要实际验收项'); continue
        seen, categories = set(), set()
        for check in checks:
            if not isinstance(check, dict):
                errors.append('readiness.checks: 每项需要对象'); continue
            for key in ('id', 'category', 'criterion', 'note'):
                if not isinstance(check.get(key), str) or not check[key].strip():
                    errors.append(f'readiness.checks.{key}: 需要非空说明')
            cid = check.get('id')
            if isinstance(cid, str):
                if cid in seen: errors.append('readiness.checks: 验收编号重复')
                seen.add(cid)
            category = check.get('category')
            if category not in ('target_design', 'implementation_conditions'):
                errors.append('readiness.checks.category: 需核对目标方案或实现条件')
            else: categories.add(category)
            if check.get('outcome') != 'pass':
                errors.append('readiness.checks: 存在未通过/未验证项')
            evidence = check.get('evidence')
            if not isinstance(evidence, list) or not evidence:
                errors.append('readiness.checks.evidence: 需要验收依据及哈希'); continue
            for source in evidence:
                if not isinstance(source, dict) or not isinstance(source.get('path'), str):
                    errors.append('readiness.checks.evidence: 需要 path/sha256'); continue
                source_path = (path.parent / source['path']).resolve()
                if source_path == path:
                    errors.append('readiness: 验收记录不能以自身为证据'); continue
                errors.extend(check_source(source_path, 'readiness'))
                if source_path.is_file() and source.get('sha256') != digest(source_path):
                    errors.append('readiness: 验收依据哈希不一致，必须复核')
        if categories != {'target_design', 'implementation_conditions'}:
            errors.append('readiness: 需同时核对目标方案与实现条件')
    return errors


def validate_summary(data, base):
    errors = []
    summary = data.get('redesign_summary')
    if not isinstance(summary, dict):
        return ['redesign_summary: 新报告必须有最终总结、改版优先级及页面调整清单']
    def text(obj, keys, loc):
        for key in keys:
            if not isinstance(obj.get(key), str) or not obj[key].strip():
                errors.append(f'{loc}.{key}: 需要非空说明')
    text(summary, ('conclusion', 'ranking_basis', 'not_now'), 'redesign_summary')
    dims = {d['id']: d for d in data.get('dimensions', []) if isinstance(d, dict) and isinstance(d.get('id'), str)}
    baseline = data.get('target_baseline')
    evidence = baseline.get('evidence', []) if isinstance(baseline, dict) else []
    evidence_ids = {x['id'] for x in (evidence if isinstance(evidence, list) else []) if isinstance(x, dict) and isinstance(x.get('id'), str)}
    items = summary.get('items')
    if not isinstance(items, list) or not items:
        return errors + ['redesign_summary.items: 至少写一项行动或保持/暂缓结论']
    ids, orders, covered, by_id = set(), set(), set(), {}
    for item in items:
        if not isinstance(item, dict):
            errors.append('redesign_summary.items: 每项需要对象'); continue
        text(item, ('id', 'title', 'reason', 'validation'), 'redesign item')
        iid, order = item.get('id'), item.get('order')
        if isinstance(iid, str):
            if iid in ids: errors.append('redesign item: 编号重复')
            ids.add(iid); by_id[iid] = item
        if type(order) is not int or order < 1:
            errors.append('redesign item.order: 需要正整数')
        elif order in orders:
            errors.append('redesign item.order: 顺序重复')
        else: orders.add(order)
        if item.get('priority') not in ('P1', 'P2', 'P3'):
            errors.append('redesign item.priority: 需要 P1/P2/P3')
        stage = item.get('stage')
        if stage not in STAGES: errors.append('redesign item.stage: 必须区分原型、补证、实现、保留、暂缓或不采用')
        refs = item.get('dimension_ids')
        if not isinstance(refs, list) or not refs or any(not isinstance(x, str) or x not in dims for x in refs):
            errors.append('redesign item.dimension_ids: 必须关联已分析维度及目标')
        else:
            covered.update(refs)
            # A deferred/rejected dimension cannot silently become a delivery commitment.
            if stage in ('prototype', 'implement') and any(dims[x].get('target_decision', {}).get('action') in ('keep', 'defer', 'reject') for x in refs):
                errors.append('redesign item: 最终行动与维度取舍冲突，应先统一当前判断')
        deps = item.get('depends_on')
        if not isinstance(deps, list) or any(not isinstance(x, str) for x in deps):
            errors.append('redesign item.depends_on: 需要方案编号数组，无依赖填空数组')
        readiness = item.get('readiness_evidence_refs', [])
        if not isinstance(readiness, list) or any(not isinstance(x, str) or not (base / x).is_file() for x in readiness):
            errors.append('redesign item.readiness_evidence_refs: 来源缺失或格式错误')
        if stage == 'implement' and not readiness:
            errors.append('redesign item: 进入实现需有目标方案验收/实现条件的记录，竞品截图不能自动证明可上线')
        elif stage == 'implement' and isinstance(readiness, list) and all(isinstance(x, str) for x in readiness):
            errors.extend(validate_readiness(data, item, base, readiness))
        pages = item.get('page_changes')
        if not isinstance(pages, list) or not pages:
            errors.append('redesign item.page_changes: 必须说明落在哪个页面/模块以及怎么调整'); continue
        for page in pages:
            if not isinstance(page, dict): errors.append('page_changes: 每项需要对象'); continue
            text(page, ('page', 'module', 'current', 'change', 'preserve', 'states', 'acceptance'), 'page change')
            refs = page.get('target_evidence_ids')
            if not isinstance(refs, list) or any(not isinstance(x, str) or x not in evidence_ids for x in refs):
                errors.append('page change.target_evidence_ids: 需引用目标现状；无材料填空并说明未知')
    if set(dims) - covered:
        errors.append('redesign_summary: 分析维度未收敛到行动或明确的保持/暂缓结论：' + ', '.join(sorted(set(dims)-covered)))
    valid = [x for x in items if isinstance(x, dict) and type(x.get('order')) is int and x.get('priority') in ('P1','P2','P3')]
    ordered = sorted(valid, key=lambda x: x['order'])
    if [x['priority'] for x in ordered] != sorted(x['priority'] for x in ordered):
        errors.append('redesign_summary: 顺序与P1/P2/P3冲突')
    for item in valid:
        deps = item.get('depends_on', [])
        if not isinstance(deps, list): continue
        for dep in deps:
            if not isinstance(dep, str): continue
            other = by_id.get(dep)
            if not other or type(other.get('order')) is not int or other['order'] >= item['order']:
                errors.append('redesign item.depends_on: 前置方案必须存在且排在本项之前，不能自依赖或循环')
    return errors


def ordered_items(data):
    return sorted(data.get('redesign_summary', {}).get('items', []), key=lambda x: x['order'])


def evidence_links(data, item, base, output_dir):
    dimensions = [x for x in data['dimensions'] if x['id'] in item['dimension_ids']]
    refs = list(dict.fromkeys(ref for d in dimensions for c in d['cells'] for ref in c['evidence_refs']))
    ids = {eid for page in item['page_changes'] for eid in page['target_evidence_ids']}
    target = [(x['id'], x['path']) for x in data.get('target_baseline', {}).get('evidence', []) if x['id'] in ids]
    pairs = [(Path(ref).stem, ref) for ref in refs] + target
    pairs += [('方案验收记录', ref) for ref in item.get('readiness_evidence_refs', [])]
    return [(label, quote(os.path.relpath((base / ref).resolve(), output_dir.resolve()), safe='/')) for label, ref in pairs]


def render_markdown(data, output_dir, base):
    summary = data.get('redesign_summary')
    if not summary: return ''
    clean = lambda x: str(x).replace('|', '\\|').replace('\n', ' ')
    dims = {x['id']: x for x in data['dimensions']}
    lines = ['## 最后总结：改版优先级与页面调整', '', summary['conclusion'], '', '**排序依据**：'+summary['ranking_basis'], '', 'P1先处理，P2随后处理，P3后续考虑；这是本轮行动顺序，是否进入实现以行动阶段为准。', '', '|顺序|建议与目标|阶段|为什么这样排|', '|---|---|---|---|']
    for item in ordered_items(data):
        goals = '/'.join(dict.fromkeys(dims[x].get('goal_id', '历史未登记') for x in item['dimension_ids']))
        lines.append('|'+ '|'.join(clean(x) for x in [f'{item["order"]} · {item["priority"]}', item['title']+' · '+goals, STAGES[item['stage']], item['reason']])+'|')
    for item in ordered_items(data):
        lines.extend(['', f'### {item["id"]} · {item["title"]}', '', '前置事项：'+(', '.join(item['depends_on']) or '无方案依赖；实现条件见分析'), ''])
        for page in item['page_changes']:
            lines.extend([f'**{page["page"]} / {page["module"]}**', '', f'- 当前：{page["current"]}', f'- 调整：{page["change"]}', f'- 保留：{page["preserve"]}', f'- 状态：{page["states"]}', f'- 验收：{page["acceptance"]}', ''])
        lines.extend(['验证任务：'+item['validation'], '来源：'+' · '.join(f'[{label}]({href})' for label, href in evidence_links(data,item,base,output_dir)), ''])
    lines.extend(['**本轮暂不做**：'+summary['not_now'], '', '以上为基于当前证据的设计建议；优先级不代表收益已经验证。', ''])
    return '\n'.join(lines)


def render_html(data, output_dir, base):
    summary = data.get('redesign_summary')
    if not summary: return ''
    e = html.escape
    dims = {x['id']: x for x in data['dimensions']}
    parts = ['<section id="redesign-summary" class="redesign-summary"><style>.redesign-summary{background:#fff8ef;padding:24px;border:1px solid #e5d8cb;border-radius:14px;margin:28px 0}.redesign-summary h2{font-size:26px}.redesign-summary .priority-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}.redesign-summary .priority-card,.redesign-summary .page-change{background:white;border:1px solid #e5ded7;border-radius:10px;padding:16px}.redesign-summary .priority-card h3{font-size:18px}.redesign-summary .rank{font-weight:700;color:#a32c25}.redesign-summary details{margin:14px 0}.redesign-summary summary{cursor:pointer;font-weight:700;padding:12px 0}.redesign-summary .page-change{margin:10px 0}.redesign-summary p{line-height:1.7}.redesign-summary a{overflow-wrap:anywhere}</style><h2>最后总结：改版优先级与页面调整</h2>', f'<p>{e(summary["conclusion"])}</p><p><b>排序依据：</b>{e(summary["ranking_basis"])}</p><p>P1先处理，P2随后处理，P3后续考虑；这是本轮行动顺序，是否进入实现以行动阶段为准。</p><div class="priority-grid">']
    for item in ordered_items(data):
        goals = ' / '.join(dict.fromkeys(dims[x].get('goal_id', '历史未登记') for x in item['dimension_ids']))
        parts.append(f'<article class="priority-card"><span class="rank">{item["order"]} · {e(item["priority"])} · {e(goals)}</span><h3><a href="#plan-{e(item["id"],quote=True)}">{e(item["title"])}</a></h3><p><b>{STAGES[item["stage"]]}</b></p><p>{e(item["reason"])}</p></article>')
    parts.append('</div>')
    for item in ordered_items(data):
        parts.append(f'<details open id="plan-{e(item["id"],quote=True)}"><summary>{e(item["id"])} · 页面怎么改：{e(item["title"])}</summary><p><b>前置事项：</b>{e(", ".join(item["depends_on"]) or "无方案依赖；实现条件见分析")}</p>')
        for page in item['page_changes']:
            parts.append(f'<article class="page-change"><h3>{e(page["page"])} / {e(page["module"])}</h3>')
            for key,label in [('current','当前'),('change','调整'),('preserve','保留'),('states','状态'),('acceptance','验收')]:
                parts.append(f'<p><b>{label}：</b>{e(page[key])}</p>')
            parts.append('</article>')
        links = ' · '.join(f'<a href="{e(href,quote=True)}">{e(label)}</a>' for label,href in evidence_links(data,item,base,output_dir))
        parts.append(f'<p><b>验证任务：</b>{e(item["validation"])}</p><p>分析与现状来源：{links}</p></details>')
    parts.append(f'<p><b>本轮暂不做：</b>{e(summary["not_now"])}</p><p>以上为基于当前证据的设计建议；优先级不代表收益已经验证。</p></section>')
    return '\n'.join(parts)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='读取待复核方案摘要；仅计算绑定哈希，不产生验收通过记录')
    parser.add_argument('--analysis', type=Path, required=True)
    parser.add_argument('--item', required=True)
    args = parser.parse_args()
    analysis = json.loads(args.analysis.read_text(encoding='utf-8'))
    selected = next((x for x in analysis['redesign_summary']['items'] if x['id'] == args.item), None)
    if selected is None: parser.error('方案编号不存在')
    print(readiness_subject_digest(analysis, selected))
