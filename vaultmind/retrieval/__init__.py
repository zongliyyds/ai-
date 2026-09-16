# -*- coding: utf-8 -*-
"""检索层：FTS5 BM25 + bge-m3 向量 + RRF 融合的统一 search() 接口。

可选参数（M6 消融用；默认值 = 基线行为，M3 官方数字不受影响）：
- rrf_k：RRF 融合参数 k（默认 60）
- rerank："title" → 标题加权重排（确定性，无模型）
- expand_links：双链 1-hop 扩展块数（默认 0=关闭；>0 时扩展块竞争尾部名额）
"""
from vaultmind.retrieval.hit import SearchHit  # noqa: F401（重导出）

from vaultmind.retrieval import bm25, expand, fusion, vector  # noqa: E402
from vaultmind.retrieval import rerank as rerank_mod           # noqa: E402


def search(query: str, top_k: int = 10, mode: str = "hybrid",
           rrf_k: int = 60, rerank: str | None = None,
           expand_links: int = 0) -> list[SearchHit]:
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
        fused = fusion.rrf_fuse([b, v], k=rrf_k)
        if rerank == "title":
            fused = rerank_mod.title_boost(fused, query)
        if expand_links > 0:
            base = fused[: max(1, top_k - expand_links)]
            return expand.expand_by_links(base, n=expand_links)
        return fused[:top_k]
    raise ValueError("未知检索模式: %s（可选 bm25/vector/hybrid）" % mode)
