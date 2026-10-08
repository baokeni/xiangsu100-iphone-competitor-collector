#!/usr/bin/env python3
"""Compare reviewed observations, never infer product changes from pixel/file hashes."""
import argparse
import html
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from evidence_checks import check_source, digest

KEYS = ('platform_id', 'profile_id', 'route_id', 'checkpoint_id')
CONDITIONS = ('region', 'account_state', 'content_sample', 'device', 'locale', 'entry_condition')
LABELS = {
    'candidate_change': '候选变化，需复核', 'unchanged_observation': '本次已观察项一致',
    'new_coverage': '新增观察范围，不等于新增功能', 'not_rechecked': '本次未复查',
    'incomparable': '条件不同或未知，暂不能比较', 'unknown': '证据不足，不能判断变化',
}


def key(item):
    return tuple(item[k] for k in KEYS)


def validate_snapshot(data, base):
    errors = []
    if not isinstance(data, dict): return ['快照根节点需要对象']
    if data.get('kind') != 'competitor_snapshot' or data.get('schema_version') != 1:
        errors.append('需要 competitor_snapshot，schema_version=1')
    for field in ('study_id', 'cycle_id', 'recorded_at', 'captured_at', 'research_question', 'scope_note'):
        if not isinstance(data.get(field), str) or not data[field].strip():
            errors.append(f'{field}: 需要非空说明')
    try:
        moment = datetime.fromisoformat(data.get('recorded_at', '').replace('Z', '+00:00'))
        if moment.tzinfo is None: errors.append('recorded_at: 需要带时区时间')
    except (ValueError, TypeError, AttributeError):
        errors.append('recorded_at: 需要本次整理记录的 ISO 时间')
    if data.get('captured_at') != 'unknown':
        try:
            captured = datetime.fromisoformat(data.get('captured_at', '').replace('Z', '+00:00'))
            if captured.tzinfo is None: errors.append('captured_at: 已知采集时间需要时区')
        except (ValueError, TypeError, AttributeError):
            errors.append('captured_at: 需要真实采集时间或 unknown，不能用导入时间替代')
    registries = {}
    for field, required in (('profiles', ('id', 'description', 'basis', 'source_or_assumption')),
                            ('routes', ('id', 'profile_id', 'task', 'entry', 'success_criteria'))):
        rows = data.get(field)
        registry = registries[field] = {}
        if not isinstance(rows, list) or not rows:
            errors.append(f'{field}: 需要非空数组'); continue
        for row in rows:
            if not isinstance(row, dict): errors.append(f'{field}: 每项需要对象'); continue
            for name in required:
                if not isinstance(row.get(name), str) or not row[name].strip():
                    errors.append(f'{field}.{name}: 需要非空说明')
            ident = row.get('id')
            if isinstance(ident, str):
                if ident in registry: errors.append(f'{field}: 编号重复 {ident}')
                registry[ident] = row
            if field == 'profiles' and row.get('basis') not in ('documented', 'hypothesis'):
                errors.append('profiles.basis: documented/hypothesis；模拟用户不能算真实用户测试')
            if field == 'routes' and (not isinstance(row.get('profile_id'), str) or row['profile_id'] not in registries['profiles']):
                errors.append('routes.profile_id: 用户未登记')
    rows = data.get('observations')
    if not isinstance(rows, list) or not rows: return errors + ['observations: 需要观察项，未采项也需标明状态']
    seen = set()
    for row in rows:
        if not isinstance(row, dict): errors.append('observation: 每项需要对象'); continue
        valid_key = all(isinstance(row.get(k), str) and row[k].strip() for k in KEYS)
        if not valid_key: errors.append('observation: 需要平台/用户/路线/检查点稳定编号')
        else:
            ident = key(row)
            if ident in seen: errors.append('observation: 重复检查点')
            seen.add(ident)
        pid, rid = row.get('profile_id'), row.get('route_id')
        if isinstance(pid, str) and isinstance(rid, str):
            route = registries['routes'].get(rid, {})
            if pid not in registries['profiles'] or not route or route.get('profile_id') != pid:
                errors.append('observation: 用户与路线不匹配')
        status = row.get('status')
        if status not in ('observed', 'not_verified', 'blocked', 'excluded'):
            errors.append('observation.status: 未知状态')
        for name in ('app_version', 'limits'):
            if not isinstance(row.get(name), str) or not row[name].strip(): errors.append(f'observation.{name}: 需要说明，未知写 unknown')
        conditions = row.get('conditions')
        if not isinstance(conditions, dict) or any(not isinstance(conditions.get(k), str) or not conditions[k].strip() for k in CONDITIONS):
            errors.append('observation.conditions: 需要地区、账号状态、样本、设备、语言和入口条件')
        facts, evidence = row.get('facts'), row.get('evidence')
        if not isinstance(facts, dict) or any(not isinstance(k, str) or not isinstance(v, str) or not v.strip() for k,v in facts.items()):
            errors.append('observation.facts: 需要已核对事实的键值对象')
        if status == 'observed' and not facts: errors.append('observed: 需要观察事实')
        if not isinstance(evidence, list): errors.append('observation.evidence: 需要数组'); continue
        if status == 'observed' and not evidence: errors.append('observed: 需要证据')
        if status != 'observed' and (facts or evidence):
            errors.append('未验证项不携带旧事实；局部已知事实拆成独立 observed 检查点')
        for ref in evidence:
            if not isinstance(ref, dict) or not isinstance(ref.get('path'), str):
                errors.append('observation.evidence: 需要 path/sha256'); continue
            path = base / ref['path']
            errors.extend(check_source(path, 'observation'))
            if path.is_file() and ref.get('sha256') != digest(path):
                errors.append('observation: 证据哈希不一致')
    return errors


def compare(before, after):
    if before['study_id'] != after['study_id']: raise ValueError('不能跨研究项目比较')
    if before['cycle_id'] == after['cycle_id']: raise ValueError('两期 cycle_id 必须不同')
    parse = lambda d: datetime.fromisoformat(d['recorded_at'].replace('Z', '+00:00'))
    if parse(after) <= parse(before): raise ValueError('本期时间必须晚于基线')
    old = {key(x): x for x in before['observations']}
    new = {key(x): x for x in after['observations']}
    profiles = [{x['id']: x for x in d['profiles']} for d in (before, after)]
    routes = [{x['id']: x for x in d['routes']} for d in (before, after)]
    results = []
    for ident in sorted(old.keys() | new.keys()):
        a, b = old.get(ident), new.get(ident)
        reasons = []
        if a is None: status = 'new_coverage'
        elif b is None: status = 'not_rechecked'
        elif a['status'] != 'observed' or b['status'] != 'observed': status = 'unknown'
        else:
            if before['research_question'] != after['research_question']: reasons.append('研究问题改变')
            if before['captured_at'] != 'unknown' and after['captured_at'] != 'unknown':
                capture_time = lambda d: datetime.fromisoformat(d['captured_at'].replace('Z', '+00:00'))
                if capture_time(after) <= capture_time(before): reasons.append('本期证据采集时间未晚于基线')
            for field in CONDITIONS:
                av, bv = a['conditions'][field], b['conditions'][field]
                if av != bv or av.lower() in ('unknown', '未知', '待验证'):
                    reasons.append(f'条件 {field} 不一致或未知')
            if profiles[0][ident[1]] != profiles[1][ident[1]]: reasons.append('用户定义改变')
            if routes[0][ident[2]] != routes[1][ident[2]]: reasons.append('任务路线定义改变')
            if set(a['facts']) != set(b['facts']): reasons.append('记录字段改变，需对齐后复核')
            status = 'incomparable' if reasons else ('unchanged_observation' if a['facts'] == b['facts'] else 'candidate_change')
        results.append({**dict(zip(KEYS, ident)), 'status': status, 'reasons': reasons,
                        'before': a, 'after': b})
    contexts = {phase: {k: d[k] for k in ('recorded_at','captured_at','research_question','scope_note','profiles','routes')} for phase,d in (('baseline',before),('current',after))}
    return {'study_id': after['study_id'], 'baseline_cycle': before['cycle_id'], 'current_cycle': after['cycle_id'], 'contexts': contexts,
            'limits': '仅比较已登记事实；候选变化需打开两期原件复核，不能证明全量发布、根因或用户效果。',
            'items': results}


def source_links(result, value, phase, output_dir):
    if not value: return []
    source_dir = Path(result['inputs'][phase]['path']).parent
    return [(ref['path'], quote(os.path.relpath((source_dir / ref['path']).resolve(), output_dir.resolve()), safe='/')) for ref in value['evidence']]


def render_report(result, output_dir):
    lines = ['# 竞品周期观察对比', '', f"基线：{result['baseline_cycle']} → 本期：{result['current_cycle']}", '', result['limits'], '']
    for phase,label in (('baseline','上期研究范围'),('current','本期研究范围')):
        context=result['contexts'][phase]
        lines += ['## '+label, '', context['research_question'], '', context['scope_note'], '', f"记录时间：{context['recorded_at']}；采集时间：{context['captured_at']}（unknown 不代表本周采集）", '']
        lines += [f"- 用户 {p['id']}：{p['description']}；{p['basis']}；{p['source_or_assumption']}" for p in context['profiles']]
        lines += [f"- 路线 {r['id']} / {r['profile_id']}：{r['task']}；入口：{r['entry']}；成功判据：{r['success_criteria']}" for r in context['routes']]
        lines += ['']
    for row in result['items']:
        lines += [f"## {' / '.join(row[k] for k in KEYS)}", '', '**'+LABELS[row['status']]+'**', '']
        if row['reasons']: lines += ['；'.join(row['reasons']), '']
        for field, label in (('before', '上期'), ('after', '本期')):
            value = row[field]
            lines += [label+'：'+(json.dumps(value['facts'], ensure_ascii=False) if value else '无该期观察记录'), '']
            if value:
                lines += [f"状态：{value['status']}；版本：{value['app_version']}；限制：{value['limits']}", '']
                phase = 'baseline' if field == 'before' else 'current'
                lines += ['证据：'+' · '.join(f'[{name}]({url})' for name,url in source_links(result,value,phase,output_dir)), '']
    return '\n'.join(lines)


def render_html(result, output_dir):
    e = html.escape
    parts = ['<!doctype html><meta charset="utf-8"><title>竞品周期观察对比</title><style>body{max-width:1000px;margin:40px auto;padding:20px;font:16px/1.8 system-ui}section{border-top:1px solid #ddd;margin-top:24px}pre{white-space:pre-wrap;overflow-wrap:anywhere}a{overflow-wrap:anywhere}</style>', '<h1>竞品周期观察对比</h1>', '<p>'+e(result['baseline_cycle']+' → '+result['current_cycle'])+'</p>', '<p>'+e(result['limits'])+'</p>']
    for phase,label in (('baseline','上期研究范围'),('current','本期研究范围')):
        context=result['contexts'][phase]
        parts += ['<section><h2>'+label+'</h2><p>'+e(context['research_question'])+'</p><p>'+e(context['scope_note'])+'</p>', '<p>'+e(f"记录时间：{context['recorded_at']}；采集时间：{context['captured_at']}（unknown 不代表本周采集）")+'</p><ul>']
        parts += ['<li>'+e(f"用户 {p['id']}：{p['description']}；{p['basis']}；{p['source_or_assumption']}")+'</li>' for p in context['profiles']]
        parts += ['<li>'+e(f"路线 {r['id']} / {r['profile_id']}：{r['task']}；入口：{r['entry']}；成功判据：{r['success_criteria']}")+'</li>' for r in context['routes']]
        parts += ['</ul></section>']
    for row in result['items']:
        parts += ['<section><h2>'+e(' / '.join(row[k] for k in KEYS))+'</h2>', '<p><b>'+e(LABELS[row['status']])+'</b></p>', '<p>'+e('；'.join(row['reasons']))+'</p>']
        for field,label,phase in (('before','上期','baseline'),('after','本期','current')):
            value = row[field]
            parts += ['<h3>'+label+'</h3>']
            if value:
                parts += ['<pre>'+e(json.dumps(value['facts'],ensure_ascii=False,indent=2))+'</pre>', '<p>'+e(f"状态：{value['status']}；版本：{value['app_version']}；限制：{value['limits']}")+'</p>']
                parts += ['<p>证据：'+' · '.join(f'<a href="{e(url,quote=True)}">{e(name)}</a>' for name,url in source_links(result,value,phase,output_dir))+'</p>']
            else: parts += ['<p>无该期观察记录</p>']
        parts += ['</section>']
    return '\n'.join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current', type=Path, required=True)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    try:
        current = json.loads(args.current.read_text(encoding='utf-8'))
        errors = validate_snapshot(current, args.current.parent)
        previous = None
        if args.baseline:
            previous = json.loads(args.baseline.read_text(encoding='utf-8'))
            errors += validate_snapshot(previous, args.baseline.parent)
        if errors: raise ValueError('\n'.join(errors))
        if previous is None:
            print('基线结构与来源检查通过；语义复核及真实用户效果仍需单独验收。'); return
        result = compare(previous, current)
        result['inputs'] = {name: {'path': str(path.resolve()), 'sha256': digest(path)} for name,path in (('baseline', args.baseline), ('current', args.current))}
        if not args.output_dir:
            print(json.dumps(result, ensure_ascii=False, indent=2)); return
        args.output_dir.mkdir(parents=True, exist_ok=True)
        paths = [args.output_dir / ('cycle-diff.'+ext) for ext in ('json','md','html')]
        # Preserve earlier deliveries; use a new cycle directory for each comparison.
        if any(path.exists() for path in paths): raise ValueError('输出已存在，请使用新目录，保留历史对比')
        report = render_report(result, args.output_dir)
        paths[0].write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        paths[1].write_text(report, encoding='utf-8')
        paths[2].write_text(render_html(result, args.output_dir), encoding='utf-8')
        print('已输出候选变化与缺口；尚未确认产品改版或效果。')
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(1, str(error)+'\n')


if __name__ == '__main__': main()
