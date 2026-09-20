# -*- coding: utf-8 -*-
"""Vault 体检基线（只读）：独立单文件实现，产出 reports/baseline_audit.json。

注：正式管道统一走 vaultmind.ingest.auditor（rebase_audit_baseline.py 调用它），
本脚本保留为独立快速体检入口，口径保持一致。
"""
import collections
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vaultmind.config import BASELINE_JSON, VAULT_ROOT  # noqa: E402

VAULT = str(VAULT_ROOT)
LINK = re.compile(r"\[\[([^\]\|#]+)")
FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def parse_tags(fm_raw):
    m = re.search(r"^tags:\s*(.+)$", fm_raw, re.M)
    if not m:
        return []
    return [t.strip(" []\"'`") for t in re.split(r"[,\n]+", m.group(1).strip())
            if t.strip(" []\"'`")]


docs = {}
for dirpath, dirnames, filenames in os.walk(VAULT):
    dirnames[:] = [d for d in dirnames if not d.startswith(".")]
    for fn in filenames:
        if not fn.lower().endswith(".md"):
            continue
        p = os.path.join(dirpath, fn)
        rel = os.path.relpath(p, VAULT).replace("\\", "/")
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            docs[rel] = {"error": str(e)}
            continue
        m = FM.match(text)
        fm_raw = m.group(1) if m else ""
        body = text[m.end():] if m else text
        ftype = re.search(r"^type:\s*(.+)$", fm_raw, re.M)
        status = re.search(r"^status:\s*(.+)$", fm_raw, re.M)
        docs[rel] = {
            "chars": len(text), "body_chars": len(body),
            "type": (ftype.group(1).strip() if ftype else None),
            "status": (status.group(1).strip() if status else None),
            "h2": len(re.findall(r"^##\s+\S", body, re.M)),
            "h3": len(re.findall(r"^###\s+\S", body, re.M)),
            "links": [l.strip() for l in LINK.findall(body)],
            "tags": parse_tags(fm_raw),
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
    "root": VAULT,
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

BASELINE_JSON.parent.mkdir(parents=True, exist_ok=True)
with open(BASELINE_JSON, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("done：%d 篇 → %s" % (len(docs), BASELINE_JSON))
