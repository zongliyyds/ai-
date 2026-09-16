# -*- coding: utf-8 -*-
"""BM25 检索：查询 jieba 分词 → FTS5 MATCH → bm25 得分 → top-k（只读索引库）。"""
import logging
import sqlite3

import jieba

from vaultmind.config import DB_PATH
from vaultmind.retrieval.hit import SearchHit

_SELECT = (
    "SELECT c.id, c.doc_id, d.rel, d.title, c.section, c.prefix, c.text, "
    "bm25(chunks_fts) AS score "
    "FROM chunks_fts f "
    "JOIN chunks c ON c.id = f.rowid "
    "JOIN docs d ON d.id = c.doc_id "
    "WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts) LIMIT ?"
)


# 查询侧停用词：疑问词/虚词不参与 FTS 匹配（只做召回，bm25 负责排序）
QUERY_STOPWORDS = {
    "怎么", "如何", "什么", "哪些", "哪个", "为什么", "的", "了", "是", "在",
    "有", "吗", "呢", "啊", "一下", "请", "请问", "？", "?", "。", "，", ",",
}


def tokenize_query(query: str) -> list[str]:
    tokens = [t.strip().replace('"', "") for t in jieba.cut(query) if t.strip()]
    return [t for t in tokens if t not in QUERY_STOPWORDS]


def search_bm25(query: str, top_k: int = 10, db_path=None) -> list[SearchHit]:
    tokens = tokenize_query(query)
    if not tokens:
        return []
    # OR 语义求召回（bm25 负责排序），引号短语防止分词词元被 FTS 语法打断
    expr = " OR ".join('"%s"' % t for t in tokens)
    con = sqlite3.connect(str(db_path or DB_PATH))
    try:
        rows = con.execute(_SELECT, (expr, top_k)).fetchall()
    except sqlite3.OperationalError as e:
        logging.warning("FTS5 查询失败: %s（表达式: %s）", e, expr)
        rows = []
    finally:
        con.close()
    return [
        SearchHit(chunk_id=r[0], doc_id=r[1], rel=r[2], title=r[3], section=r[4],
                  prefix=r[5], text=r[6], score=float(r[7]), source="bm25")
        for r in rows
    ]
