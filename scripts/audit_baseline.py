# -*- coding: utf-8 -*-
"""Vault 体检：为 RAG 项目的 M1 数据管道提供真实基线数据（只读）。"""
import os, re, json, collections

ROOT = r"D:\AI-Knowledge-Vault\AI-Knowledge-Vault"
LINK = re.compile(r"\[\[([^\]\|#]+)")
FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)

docs = {}
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if not d.startswith(".")]
    for fn in filenames:
        if not fn.lower().endswith(".md"):
            continue
        p = os.path.join(dirpath, fn)
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        try:
            text = open(p, encoding="utf-8").read()
        except Exception as e:
            docs[rel] = {"error": str(e)}
            continue
        m = FM.match(text)
        fm_raw = m.group(1) if m else ""
        body = text[m.end():] if m else text
        ftype = re.search(r"^type:\s*(.+)$", fm_raw, re.M)
        status = re.search(r"^status:\s*(.+)$", fm_raw, re.M)
        tags = re.findall(r"[\w\u4e00-\u9fff/\-]+", (re.search(r"^tags:\s*(.+)$", fm_raw, re.M) or re.search(r"^tags:\s*$", "", re.M) or type("x", (), {"group": lambda s, i: ""})()).group(1)) if re.search(r"^tags:\s*(.+)$", fm_raw, re.M) else []
        h2 = len(re.findall(r"^##\s+\S", body, re.M))
        h3 = len(re.findall(r"^###\s+\S", body, re.M))
        links = [l.strip() for l in LINK.findall(body)]
        docs[rel] = {
            "chars": len(text), "body_chars": len(body),
            "type": (ftype.group(1).strip() if ftype else None),
            "status": (status.group(1).strip() if status else None),
            "h2": h2, "h3": h3, "links": links,
            "has_fm": bool(m),
        }

# 入链统计（按文件名去重匹配）
stem2rel = {}
for rel in docs:
    stem2rel.setdefault(os.path.splitext(os.path.basename(rel))[0], rel)
inbound = collections.Counter()
for rel, d in docs.items():
    if "links" not in d:
        continue
    for l in d["links"]:
        s = os.path.splitext(os.path.basename(l.replace("\\", "/")))[0]
        if s in stem2rel:
            inbound[stem2rel[s]] += 1

report = {
    "root": ROOT,
    "doc_count": len(docs),
    "total_chars": sum(d.get("chars", 0) for d in docs.values()),
    "body_chars": sum(d.get("body_chars", 0) for d in docs.values()),
    "by_type": dict(collections.Counter(d.get("type") or "NO_FRONTMATTER" for d in docs.values()).most_common()),
    "by_top_folder": dict(collections.Counter(rel.split("/")[0] for rel in docs).most_common()),
    "by_status": dict(collections.Counter(d.get("status") or "(none)" for d in docs.values()).most_common()),
    "no_frontmatter": [r for r, d in docs.items() if not d.get("has_fm")],
    "est_chunks_h2": sum(max(1, d.get("h2", 0) + 1) for d in docs.values()),
    "total_h2": sum(d.get("h2", 0) for d in docs.values()),
    "total_h3": sum(d.get("h3", 0) for d in docs.values()),
    "outlink_total": sum(len(d.get("links", [])) for d in docs.values()),
    "unresolved_links": sum(1 for d in docs.values() for l in d.get("links", [])
                            if os.path.splitext(os.path.basename(l.replace("\\", "/")))[0] not in stem2rel),
    "orphans": sorted([r for r in docs if inbound[r] == 0 and r.split("/")[0] not in ("90-System", ".obsidian")],
                      key=lambda r: -docs[r].get("chars", 0))[:25],
    "top_inbound": [[r, c] for r, c in inbound.most_common(12)],
    "largest": sorted([[r, d.get("chars", 0)] for r, d in docs.items()], key=lambda x: -x[1])[:12],
    "smallest_lt_300": sorted([[r, d.get("chars", 0)] for r, d in docs.items() if d.get("chars", 0) < 300], key=lambda x: x[1])[:20],
}

json.dump(report, open(r"D:\deeseek工作区\_vault_audit.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("done")
