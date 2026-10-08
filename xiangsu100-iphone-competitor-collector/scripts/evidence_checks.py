"""File integrity checks; semantic support still requires an actual review."""
import hashlib
import json
from pathlib import Path

SOURCE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp', '.heic', '.pdf', '.mp4',
                   '.mov', '.md', '.txt', '.html', '.csv', '.json', '.jsonl'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_source(path, location):
    path = Path(path)
    if not path.is_file():
        return [f'{location}: 来源不存在 {path.name}']
    if path.suffix.lower() not in SOURCE_SUFFIXES:
        return [f'{location}: 不支持的证据文件类型 {path.suffix}；代码不能冒充观察记录']
    if path.suffix.lower() != '.json':
        return []
    try:
        index = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return [f'{location}: 来源索引无法读取 {path.name}']
    if not isinstance(index, dict) or index.get('kind') != 'source_evidence_index':
        return []  # Snapshots and other JSON records need semantic review.
    source, expected = index.get('source'), index.get('source_sha256')
    if not isinstance(source, str) or not source.strip():
        return [f'{location}: 来源原件不存在 {path.name}']
    original = (path.parent / source).resolve()
    if not original.is_file():
        return [f'{location}: 来源原件不存在 {path.name}']
    if original.suffix.lower() not in SOURCE_SUFFIXES:
        return [f'{location}: 来源原件类型不支持 {original.suffix}']
    if not isinstance(expected, str) or len(expected) != 64 or any(c not in '0123456789abcdefABCDEF' for c in expected):
        return [f'{location}: 来源哈希缺失或格式错误 {path.name}']
    if digest(original) != expected.lower():
        return [f'{location}: 来源哈希不一致 {path.name}']
    return []


def check_refs(refs, base, location, errors):
    if not isinstance(refs, list) or not all(isinstance(x, str) and x.strip() for x in refs):
        errors.append(f'{location}.evidence_refs: 需要路径数组')
        return
    for ref in refs:
        errors.extend(check_source(Path(base) / ref, location))
