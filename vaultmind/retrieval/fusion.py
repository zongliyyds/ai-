# -*- coding: utf-8 -*-
"""RRF（Reciprocal Rank Fusion）融合：score = Σ 1/(k + rank)，k=60。"""
from vaultmind.retrieval.hit import SearchHit

RRF_K = 60


def rrf_fuse(ranked_lists: list[list[SearchHit]], k: int = RRF_K) -> list[SearchHit]:
    scores: dict[int, float] = {}
    hits: dict[int, SearchHit] = {}
    for lst in ranked_lists:
        for rank, hit in enumerate(lst):
            key = hit.chunk_id
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            hits[key] = hit
    merged = sorted(scores.items(), key=lambda kv: -kv[1])
    out = []
    for cid, s in merged:
        h = hits[cid]
        h.score = round(s, 6)
        h.source = "rrf(bm25+vector)"
        out.append(h)
    return out
