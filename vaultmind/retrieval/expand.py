# -*- coding: utf-8 -*-
"""M6 召回扩展：双链 1-hop 扩展（图谱信号，可离线单测）。

从 top 命中文档出发，取其出链（links 表）目标文档的前几块追加到候选尾部，
分数置底（排在原有命中之后）→ 只扩召回、不干扰原排序。
"""
import sqlite3

from vaultmind.config import DB_PATH
from vaultmind.retrieval.hit import SearchHit


def expand_by_links(hits, n: int = 4, db_path=None) -> list:
    """hits（已排序）→ 追加出链目标文档的 top 块（每目标最多 2 块）。"""
    db_path = db_path or DB_PATH
    if not db_path.exists() or not hits:
        return list(hits)
    src_rels = [h.rel for h in hits]
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    marks = ",".join("?" * len(src_rels))
    targets = [r[0] for r in cur.execute(
        "SELECT DISTINCT target FROM links WHERE src IN (%s) AND valid=1" % marks,
        src_rels).fetchall()]
    out = list(hits)
    seen_src = {h.rel for h in hits}
    added = 0
    base_score = min(h.score for h in hits) - 1.0 if hits else -1.0
    for t in targets:
        if added >= n or t in seen_src:
            continue
        rows = cur.execute(
            "SELECT c.id, c.doc_id, d.rel, d.title, c.section, c.prefix, c.text "
            "FROM chunks c JOIN docs d ON c.doc_id=d.id "
            "WHERE d.rel=? ORDER BY c.seq LIMIT 2", (t,)).fetchall()
        for r in rows:
            if added >= n:
                break
            out.append(SearchHit(
                chunk_id=r[0], doc_id=r[1], rel=r[2], title=r[3] or t,
                section=r[4] or "", prefix=r[5] or "", text=r[6] or "",
                score=base_score - added * 0.01, source="link1hop"))
            added += 1
        if added >= n:
            break
    con.close()
    return out
