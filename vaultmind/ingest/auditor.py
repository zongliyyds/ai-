# -*- coding: utf-8 -*-
"""知识库体检：统计指标，口径与 reports/baseline_audit.json 保持一致（只读）。"""
import collections
import os

from vaultmind.config import ORPHAN_SKIP_TOP, VAULT_ROOT
from vaultmind.ingest.scanner import scan_docs


def link_stem(link: str) -> str:
    return os.path.splitext(os.path.basename(link.replace("\\", "/")))[0]


def stem2rel_map(docs):
    m = {}
    for d in docs:
        stem = os.path.splitext(os.path.basename(d.rel))[0]
        m.setdefault(stem, d.rel)  # 重名时先到先得（与基线口径一致）
    return m


def inbound_counter(docs, s2r):
    inbound = collections.Counter()
    for d in docs:
        for l in d.links:
            s = link_stem(l)
            if s in s2r:
                inbound[s2r[s]] += 1
    return inbound


def audit(docs=None, root=None):
    """扫描 + 统计，返回指标字典（超集于 baseline_audit.json 字段）。"""
    if docs is None:
        docs = scan_docs(root)
    s2r = stem2rel_map(docs)
    inbound = inbound_counter(docs, s2r)
    chars = {d.rel: len(d.text) for d in docs}

    orphans_all = sorted(
        [d.rel for d in docs
         if inbound[d.rel] == 0 and d.rel.split("/")[0] not in ORPHAN_SKIP_TOP],
        key=lambda r: -chars[r],
    )

    metrics = {
        "root": str(root or VAULT_ROOT),
        "doc_count": len(docs),
        "total_chars": sum(chars.values()),
        "body_chars": sum(len(d.body) for d in docs),
        "by_type": dict(collections.Counter(
            d.ftype or "NO_FRONTMATTER" for d in docs).most_common()),
        "by_top_folder": dict(collections.Counter(
            d.rel.split("/")[0] for d in docs).most_common()),
        "by_status": dict(collections.Counter(
            d.status or "(none)" for d in docs).most_common()),
        "no_frontmatter": [d.rel for d in docs if not d.has_fm],
        "frontmatter_no_type": [d.rel for d in docs if d.has_fm and not d.ftype],
        "est_chunks_h2": sum(max(1, d.h2 + 1) for d in docs),
        "total_h2": sum(d.h2 for d in docs),
        "total_h3": sum(d.h3 for d in docs),
        "outlink_total": sum(len(d.links) for d in docs),
        "unresolved_links": sum(
            1 for d in docs for l in d.links if link_stem(l) not in s2r),
        "orphans": orphans_all[:25],
        "orphans_total": len(orphans_all),
        "top_inbound": [[r, c] for r, c in inbound.most_common(12)],
        "largest": sorted([[d.rel, len(d.text)] for d in docs],
                          key=lambda x: -x[1])[:12],
        "smallest_lt_300": sorted(
            [[d.rel, len(d.text)] for d in docs if len(d.text) < 300],
            key=lambda x: x[1])[:20],
        "zero_byte": [d.rel for d in docs if len(d.text) == 0],
    }
    return metrics
