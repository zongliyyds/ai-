# -*- coding: utf-8 -*-
"""检索层探针：BM25 已知命中、向量维度/行数、RRF 排序、CLI 冒烟。"""
import numpy as np

from vaultmind.retrieval import bm25, fusion, vector
from vaultmind.retrieval.hit import SearchHit


def _hit(cid, score=0.0):
    return SearchHit(chunk_id=cid, doc_id=0, rel="", title="", section="",
                     prefix="", text="", score=score, source="x")


# ---------- BM25 ----------

def test_bm25_known_hit():
    """探针：查「FTS5 中文分词」目标笔记应进 Top-10（纯 BM25 会受短链接 chunk 密度干扰）。"""
    hits = bm25.search_bm25("SQLite FTS5 中文分词怎么配置", top_k=10)
    assert hits, "FTS5 应有命中"
    rels = [h.rel for h in hits]
    assert "20-Knowledge/SQLite FTS5 全文搜索配置.md" in rels, "Top-10 应含目标笔记，实际: %s" % rels


def test_hybrid_known_hit_top5():
    """探针：hybrid（RRF 融合）应把目标笔记拉进 Top-5。"""
    from vaultmind.retrieval import search
    hits = search("SQLite FTS5 中文分词怎么配置", top_k=5, mode="hybrid")
    rels = [h.rel for h in hits]
    assert "20-Knowledge/SQLite FTS5 全文搜索配置.md" in rels, "hybrid Top-5 应含目标笔记，实际: %s" % rels


def test_bm25_empty_query_returns_empty():
    assert bm25.search_bm25("   ") == []


# ---------- 向量 ----------

def test_vector_index_shape():
    m, ids = vector.load_index()
    assert m.dtype == np.float32
    assert m.shape[1] == 1024, "bge-m3 应为 1024 维"
    assert m.shape[0] == len(ids), "矩阵行数必须与 id 映射一致"
    assert m.shape[0] >= 900, "应覆盖全部 chunks"


def test_vector_search_known_hit():
    hits = vector.search_vector("SQLite FTS5 中文全文搜索怎么配置", top_k=5)
    assert hits, "向量检索应有命中"
    rels = [h.rel for h in hits]
    assert "20-Knowledge/SQLite FTS5 全文搜索配置.md" in rels, "Top-5 应含目标笔记，实际: %s" % rels
    assert all(abs(h.score) <= 1.0 + 1e-4 for h in hits), "cosine 得分应在 [-1,1]"


def test_vector_matrix_row_norm():
    m, _ = vector.load_index()
    norms = np.linalg.norm(m, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3), "向量应已 L2 归一化"


# ---------- RRF ----------

def test_rrf_fusion_ordering():
    """探针：两路都命中的 chunk 得分叠加；对称情形（各占一路第 1 与第 2）应并列第一。"""
    a = [_hit(1), _hit(2), _hit(3)]
    b = [_hit(2), _hit(1), _hit(4)]
    merged = fusion.rrf_fuse([a, b], k=60)
    ids = [h.chunk_id for h in merged]
    assert set(ids) == {1, 2, 3, 4}
    # chunk#1: 1/61 + 1/62；chunk#2: 1/62 + 1/61 → 得分对称相等，并列第一
    assert abs(merged[0].score - merged[1].score) < 1e-9
    assert {merged[0].chunk_id, merged[1].chunk_id} == {1, 2}


def test_rrf_scores_are_reciprocal_rank_based():
    a = [_hit(1), _hit(2)]
    b = [_hit(1)]
    merged = fusion.rrf_fuse([a, b], k=60)
    # chunk#1: 1/61 + 1/61；chunk#2: 1/62
    assert merged[0].chunk_id == 1
    assert abs(merged[0].score - 2 / 61) < 1e-6


# ---------- CLI ----------

def test_cli_smoke_bm25(capsys):
    from vaultmind.search import main
    rc = main(["SQLite FTS5 中文分词", "--top", "3", "--mode", "bm25"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "查询：" in out and "文档：" in out


def test_cli_vector_index_missing_message(capsys, monkeypatch):
    from vaultmind.search import main
    monkeypatch.setattr(vector, "load_index",
                        lambda *a, **k: (_raise_missing(), []))
    rc = main(["测试", "--mode", "vector"])
    err = capsys.readouterr().err
    assert rc == 2
    assert "向量索引缺失" in err


def _raise_missing():
    raise vector.VectorIndexMissing("向量索引缺失。请先执行 --build-vectors")
