# -*- coding: utf-8 -*-
"""回归探针：重建索引后向量索引的失效与守卫（2026-09-17 事故根因）。

事故：chunk.id 为自增 rowid（位置性 ID），Vault 新增笔记后重建索引，
行号整体错位，旧 embeddings 映射到错误内容，hybrid 检索静默退化
（Recall@5 0.8167→0.5167）。两条防线：
1. build_db 重建真实索引库时删除旧向量产物（强制全量重建）；
2. load_index 校验 id 映射与当前库 chunk 行号逐位一致（错位即报错）。
"""
import json
import sqlite3
import types

import numpy as np
import pytest

from vaultmind.ingest import indexer
from vaultmind.retrieval import vector
from vaultmind.retrieval.vector import VectorIndexMissing


def _fake_doc(rel):
    return types.SimpleNamespace(
        rel=rel, title="t-" + rel, ftype="knowledge", status="active",
        tags=["x"], text="正文内容。", body="正文内容。", h2=0, h3=0,
        links=[], has_fm=True, error=None)


def _tmp_chunk_table(db_path, ids):
    con = sqlite3.connect(str(db_path))
    con.execute("CREATE TABLE chunks (id INTEGER PRIMARY KEY)")
    con.executemany("INSERT INTO chunks(id) VALUES(?)", [(i,) for i in ids])
    con.commit()
    con.close()


def test_build_db_invalidates_real_vector_files(tmp_path, monkeypatch):
    """重建真实索引库（db_path 默认/等于 DB_PATH）必须删除向量产物。
    通过 monkeypatch 把「真实库路径」重定向到临时路径，避免污染真实索引。"""
    fake_npy = tmp_path / "emb.npy"
    fake_ids = tmp_path / "ids.json"
    fake_npy.write_bytes(b"x")
    fake_ids.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(indexer, "DB_PATH", tmp_path / "real.db")
    monkeypatch.setattr(vector, "EMB_NPY", fake_npy)
    monkeypatch.setattr(vector, "EMB_IDS", fake_ids)
    # db_path 传 None 即「真实索引库」，invalidate 分支应生效
    indexer.build_db([_fake_doc("20-Knowledge/测试.md")], [])
    assert not fake_npy.exists(), "重建真实索引库后旧 embeddings.npy 必须被删除"
    assert not fake_ids.exists(), "重建真实索引库后旧 chunk_ids.json 必须被删除"


def test_build_db_keeps_vectors_for_temp_db(tmp_path, monkeypatch):
    """重建临时索引库（测试场景）不得误删真实向量产物。"""
    fake_npy = tmp_path / "emb.npy"
    fake_ids = tmp_path / "ids.json"
    fake_npy.write_bytes(b"x")
    fake_ids.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(vector, "EMB_NPY", fake_npy)
    monkeypatch.setattr(vector, "EMB_IDS", fake_ids)
    indexer.build_db([_fake_doc("20-Knowledge/测试.md")], [],
                     db_path=tmp_path / "vaultmind.db")
    assert fake_npy.exists() and fake_ids.exists(), "临时库重建不得触碰向量产物"


def test_load_index_rejects_shifted_ids(tmp_path, monkeypatch):
    """id 映射与库内 chunk 行号错位时必须报错，而不是返回脏结果。"""
    fake_npy = tmp_path / "emb.npy"
    fake_ids = tmp_path / "ids.json"
    db = tmp_path / "vaultmind.db"
    _tmp_chunk_table(db, [1, 2, 3, 4])
    monkeypatch.setattr(vector, "DB_PATH", db)
    monkeypatch.setattr(vector, "EMB_NPY", fake_npy)
    monkeypatch.setattr(vector, "EMB_IDS", fake_ids)
    np.save(fake_npy, np.zeros((3, 4), dtype=np.float32))
    fake_ids.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(VectorIndexMissing, match="不一致"):
        vector.load_index()


def test_load_index_accepts_matching_ids(tmp_path, monkeypatch):
    """id 映射与库内 chunk 行号一致时应正常返回。"""
    fake_npy = tmp_path / "emb.npy"
    fake_ids = tmp_path / "ids.json"
    db = tmp_path / "vaultmind.db"
    _tmp_chunk_table(db, [1, 2, 3])
    monkeypatch.setattr(vector, "DB_PATH", db)
    monkeypatch.setattr(vector, "EMB_NPY", fake_npy)
    monkeypatch.setattr(vector, "EMB_IDS", fake_ids)
    np.save(fake_npy, np.zeros((3, 4), dtype=np.float32))
    fake_ids.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    m, ids = vector.load_index()
    assert len(m) == 3 and ids == [1, 2, 3]
