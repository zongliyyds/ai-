# -*- coding: utf-8 -*-
"""检索层：FTS5 BM25 + bge-m3 向量 + RRF 融合的统一 search() 接口。"""
from vaultmind.retrieval.hit import SearchHit  # noqa: F401（重导出）

from vaultmind.retrieval import bm25, fusion, vector  # noqa: E402


def search(query: str, top_k: int = 10, mode: str = "hybrid") -> list[SearchHit]:
    """统一检索入口。

    mode: bm25（FTS5 关键词）/ vector（bge-m3 余弦）/ hybrid（RRF 融合，默认）
    """
    if mode == "bm25":
        return bm25.search_bm25(query, top_k=top_k)
    if mode == "vector":
        return vector.search_vector(query, top_k=top_k)
    if mode == "hybrid":
        b = bm25.search_bm25(query, top_k=60)
        v = vector.search_vector(query, top_k=60)
        return fusion.rrf_fuse([b, v], k=60)[:top_k]
    raise ValueError("未知检索模式: %s（可选 bm25/vector/hybrid）" % mode)
