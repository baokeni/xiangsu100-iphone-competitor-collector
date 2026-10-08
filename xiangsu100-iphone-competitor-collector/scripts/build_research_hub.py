#!/usr/bin/env python3
"""Build a searchable local HTML reader from an explicit list of source reports."""
from __future__ import annotations

import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlparse


class Scan(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []
        self.words: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag in {"script", "style"}:
            self.skip += 1
        for key in ("href", "src", "poster"):
            if values.get(key):
                self.refs.append(values[key] or "")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data: str) -> None:
        if not self.skip and data.strip():
            self.words.append(data.strip())


def local_target(source: Path, ref: str) -> Path | None:
    parsed = urlparse(html.unescape(ref))
    if parsed.scheme not in {"", "file"} or ref.startswith("#") or ref.startswith("data:"):
        return None
    if not parsed.path:
        return None
    if parsed.scheme == "file":
        return Path(unquote(parsed.path)).resolve()
    return (source.parent / unquote(parsed.path)).resolve()


def build(config_path: Path) -> dict:
    config_path = config_path.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output = (config_path.parent / config["output"]).resolve()
    entries = config["documents"]
    if not entries:
        raise ValueError("documents 不能为空")
    sources = [(config_path.parent / row["path"]).resolve() for row in entries]
    if len(set(sources)) != len(sources) or output in sources:
        raise ValueError("来源重复或把总览自身列为来源")
    for source in sources:
        if not source.is_file() or source.suffix.lower() != ".html":
            raise ValueError(f"来源 HTML 不存在：{source}")
    ids = {source: f"doc-{index:03d}" for index, source in enumerate(sources, 1)}
    urlmap = {source.as_uri(): ids[source] for source in sources}
    missing: list[str] = []
    docs = []
    for row, source in zip(entries, sources):
        original = source.read_text(encoding="utf-8")
        scan = Scan()
        scan.feed(original)
        for ref in scan.refs:
            target = local_target(source, ref)
            if target and not target.is_file():
                missing.append(f"{source}: {ref}")
        content = original

        def inline_script(match: re.Match) -> str:
            target = local_target(source, match.group(2))
            if target and target.is_file():
                script = re.sub(r"</script", r"<\\/script", target.read_text(encoding="utf-8"), flags=re.I)
                opening = re.match(r"<script\b[^>]*>", match.group(0), flags=re.I | re.S).group(0)
                opening = re.sub(r"\s+src=([\'\"])(.*?)\1", "", opening, flags=re.I | re.S)
                return opening + script + "</script>"
            return match.group(0)

        content = re.sub(r'<script\b[^>]*\bsrc=([\'\"])(.*?)\1[^>]*>\s*</script>', inline_script, content, flags=re.I | re.S)

        def inline_css(match: re.Match) -> str:
            tag = match.group(0)
            if not re.search(r'rel=[\'\"]stylesheet[\'\"]', tag, re.I):
                return tag
            found = re.search(r'href=([\'\"])(.*?)\1', tag, re.I)
            target = local_target(source, found.group(2)) if found else None
            return "<style>" + target.read_text(encoding="utf-8") + "</style>" if target and target.is_file() else tag

        content = re.sub(r"<link\b[^>]*>", inline_css, content, flags=re.I)
        content = re.sub(r"<base\b[^>]*>", "", content, flags=re.I)
        base = '<base href="' + html.escape(source.as_uri(), quote=True) + '">'
        if re.search(r"<head\b", content, re.I):
            content = re.sub(r"(<head[^>]*>)", lambda match: match.group(1) + base, content, count=1, flags=re.I)
        elif re.search(r"<html\b", content, re.I):
            content = re.sub(r"(<html[^>]*>)", lambda match: match.group(1) + "<head>" + base + "</head>", content, count=1, flags=re.I)
        else:
            content = "<head>" + base + "</head>" + content
        docs.append({
            "id": ids[source], "group": row["group"], "title": row["title"],
            "kind": row.get("kind", "报告"), "rank": row.get("rank", 1),
            "archive": bool(row.get("archive", False)), "source": str(source),
            "url": source.as_uri(), "text": " ".join(scan.words), "html": content,
            "sha256": hashlib.sha256(original.encode("utf-8")).hexdigest(),
        })
    if missing:
        raise ValueError("本地资源缺失：\n" + "\n".join(missing))
    group_order = {group: index for index, group in enumerate(dict.fromkeys(doc["group"] for doc in docs))}
    docs.sort(key=lambda doc: (group_order[doc["group"]], doc["rank"], doc["title"]))
    payload = json.dumps({"docs": docs, "urlmap": urlmap}, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    script = (Path(__file__).parent / "research_hub.js").read_text(encoding="utf-8")
    title = html.escape(config.get("title", "研究总览"))
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>
*{{box-sizing:border-box}}body{{margin:0;font:15px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;color:#293143;background:#f4f5f7}}button,input{{font:inherit}}button{{cursor:pointer}}header{{height:76px;padding:12px 20px;background:#232b39;color:white;display:flex;justify-content:space-between;align-items:center}}h1{{margin:0;font-size:20px}}header p{{margin:0;color:#c9d0d9;font-size:12px}}.actions{{display:flex;gap:8px}}.actions button{{background:#ffffff20;color:white;border:1px solid #ffffff55;border-radius:8px;padding:7px 12px}}.layout{{display:grid;grid-template-columns:300px 1fr;height:calc(100vh - 76px)}}aside{{background:white;border-right:1px solid #dce2ea;display:flex;flex-direction:column;min-height:0}}.search{{padding:14px}}input[type=search]{{width:100%;padding:9px;border:1px solid #aab5c4;border-radius:7px}}.toggle,small{{display:block;margin-top:8px;font-size:12px;color:#667}}#nav{{overflow:auto;flex:1;padding:0 10px}}.group-title{{font-size:12px;color:#687589;margin:18px 8px 5px}}.item{{display:block;width:100%;text-align:left;background:none;border:0;border-radius:8px;padding:9px;margin:2px 0}}.item:hover,.item.active{{background:#edf1f6}}.title{{display:block;font-weight:600}}.kind,.snippet{{font-size:12px;color:#687589}}.sidefoot{{padding:12px;border-top:1px solid #dde3e9;font-size:12px;color:#687589}}.reader{{min-width:0;display:flex;flex-direction:column}}.reader-head{{background:white;padding:10px 18px;display:flex;align-items:center;justify-content:space-between}}.reader-head h2,.reader-head p{{margin:0}}.reader-head h2{{font-size:15px}}.reader-head p{{font-size:12px;color:#687589}}.quick{{display:flex;gap:7px;padding:8px;overflow:auto}}.quick button{{white-space:nowrap;border:1px solid #ccd4de;border-radius:18px;background:white;padding:4px 10px}}iframe{{border:0;width:100%;flex:1;background:white}}.empty{{padding:15px;color:#687589}}body.focus .layout{{grid-template-columns:1fr}}body.focus aside{{display:none}}.mobile{{display:none}}@media(max-width:760px){{.mobile{{display:inline-block}}.layout{{grid-template-columns:1fr}}aside{{display:none;position:fixed;top:76px;bottom:0;left:0;width:min(340px,90vw);z-index:5}}body.show-nav aside{{display:flex}}}}
</style></head><body><header><div><h1>{title}</h1><p>{len(docs)} 份 HTML 正文内嵌；原图沿用来源目录</p></div><div class="actions"><button class="mobile" id="menu">目录</button><button id="focus">专注阅读</button><button id="print">打印当前内容</button></div></header><div class="layout"><aside><div class="search"><input id="search" type="search" aria-label="搜索全部报告正文" placeholder="搜索全部正文"><label class="toggle"><input id="archive" type="checkbox"> 显示历史记录</label><small id="count" aria-live="polite"></small></div><div id="nav"></div><div class="sidefoot">历史记录请以当前报告核对；迁移时保留原图目录。</div></aside><main class="reader"><div class="reader-head"><div><h2 id="current-title"></h2><p id="current-description"></p></div><a id="original" target="_blank" rel="noopener">打开原文件</a></div><div id="quick" class="quick"></div><iframe id="viewer" title="整合研究内容" sandbox="allow-scripts allow-same-origin allow-modals allow-popups allow-popups-to-escape-sandbox"></iframe></main></div><script id="research-data" type="application/json">{payload}</script><script>{script}</script></body></html>'''
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    manifest = {"output": str(output), "document_count": len(docs), "sources": [{"path": doc["source"], "sha256": doc["sha256"]} for doc in docs], "mode": "embedded_html_with_original_local_assets"}
    output.with_suffix(".manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.config), ensure_ascii=False))
