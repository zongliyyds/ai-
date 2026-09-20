# -*- coding: utf-8 -*-
r"""向量检索：Ollama bge-m3 全量向量化（断点续跑）+ numpy 暴力 cosine。

产物（只写 D:\RAG\data）：
- embeddings.npy：float32 N×1024（已 L2 归一化，cosine = 点积）
- chunk_ids.json：行号 → chunk id 映射
"""
import json
import sqlite3
import time
from pathlib import Path

import httpx
import numpy as np

from vaultmind.config import DATA_DIR, DB_PATH
from vaultmind.retrieval.hit import SearchHit

EMB_MODEL = "bge-m3"
EMB_URL = "http://127.0.0.1:11434/api/embed"
EMB_NPY = DATA_DIR / "embeddings.npy"
EMB_IDS = DATA_DIR / "chunk_ids.json"
BATCH_SIZE = 32


def _paths(db_path=None, npy_path=None, ids_path=None) -> tuple[Path, Path, Path]:
    """解析索引库与向量产物路径（None = 正式路径）。

    M6b 分块粒度消融传临时路径（data/ablation/m6b/<变体>/），
    正式管道不传参 → 行为逐字不变。
    """
    return (Path(db_path) if db_path else Path(DB_PATH),
            Path(npy_path) if npy_path else EMB_NPY,
            Path(ids_path) if ids_path else EMB_IDS)


class VectorIndexMissing(RuntimeError):
    pass


def embed_texts(texts: list[str], model: str = EMB_MODEL, timeout: int = 300) -> np.ndarray:
    try:
        r = httpx.post(EMB_URL, json={"model": model, "input": texts}, timeout=timeout)
    except httpx.HTTPError as e:
        raise RuntimeError("无法连接 Ollama（%s）。请先执行 ollama serve。" % e) from e
    if r.status_code != 200:
        raise RuntimeError("embedding 失败（HTTP %d）：%s" % (r.status_code, r.text[:200]))
    data = r.json()
    emb = np.asarray(data["embeddings"], dtype=np.float32)
    return emb


def _normalize(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return m / norms


def load_chunk_texts(db_path=None) -> tuple[list[int], list[str]]:
    con = sqlite3.connect(str(db_path or DB_PATH))
    rows = con.execute("SELECT id, text FROM chunks ORDER BY id").fetchall()
    con.close()
    ids = [r[0] for r in rows]
    texts = [r[1] for r in rows]
    return ids, texts


def build_embeddings(resume: bool = True, batch: int = BATCH_SIZE, limit: int | None = None,
                     db_path=None, npy_path=None, ids_path=None) -> dict:
    """全量向量化 chunks；resume=True 时跳过已完成行（断点续跑）。

    db_path/npy_path/ids_path：索引库与向量产物路径（M6b 消融实验用临时路径，
    默认 = 正式路径 → 正式管道行为不变）。
    """
    db, npy, ids_file = _paths(db_path, npy_path, ids_path)
    npy.parent.mkdir(parents=True, exist_ok=True)
    ids, texts = load_chunk_texts(db)
    if limit:
        ids, texts = ids[:limit], texts[:limit]

    done_ids = set()
    matrix = []
    if resume and npy.exists() and ids_file.exists():
        done_ids = set(json.loads(ids_file.read_text(encoding="utf-8")))
        matrix = list(np.load(npy))
        print("断点续跑：已完成 %d 行，续跑剩余部分" % len(done_ids))

    todo = [(i, t) for i, t in zip(ids, texts) if i not in done_ids]
    t0 = time.time()
    for start in range(0, len(todo), batch):
        chunk = todo[start:start + batch]
        texts_b = [t for _, t in chunk]
        emb = _normalize(embed_texts(texts_b))
        matrix.extend(emb)
        done_ids.update(i for i, _ in chunk)
        np.save(npy, np.asarray(matrix, dtype=np.float32))
        ids_file.write_text(json.dumps(sorted(done_ids)), encoding="utf-8")
        print("  已向量化 %d/%d（%.1fs）" % (len(done_ids), len(ids), time.time() - t0))

    stats = {
        "total_chunks": len(ids),
        "embedded": len(done_ids),
        "dim": 1024,
        "npy": str(npy),
        "ids_json": str(ids_file),
    }
    return stats


_index_cache: dict = {}  # key=(db,npy,ids 路径 + 三者 mtime) → (matrix, ids)


def load_index(db_path=None, npy_path=None, ids_path=None) -> tuple[np.ndarray, list[int]]:
    db, npy, ids_file = _paths(db_path, npy_path, ids_path)
    if not (npy.exists() and ids_file.exists()):
        raise VectorIndexMissing(
            "向量索引缺失。请先执行 D:\\python\\python.exe -m vaultmind.search --build-vectors")
    # 进程内缓存：向量矩阵 ~5MB，每次查询都 np.load + 全表扫 id 是纯浪费；
    # 以三文件 mtime 作键，任一方变化（重建）即失效重载，一致性闸门语义不变。
    try:
        key = (str(db), str(npy), str(ids_file),
               db.stat().st_mtime_ns, npy.stat().st_mtime_ns, ids_file.stat().st_mtime_ns)
    except OSError:
        key = None
    if key is not None and key in _index_cache:
        return _index_cache[key]
    m = np.load(npy)
    ids = json.loads(ids_file.read_text(encoding="utf-8"))
    if len(m) != len(ids):
        raise VectorIndexMissing("向量矩阵与 id 映射行数不一致，请重建向量索引")
    # 一致性闸门：id 映射必须与索引库当前 chunk 行号逐位一致。
    # chunk.id 是自增 rowid（位置性 ID），重建索引后行号错位会导致向量
    # 「张冠李戴」、检索静默退化——宁可报错也不返回脏结果（2026-09-17 事故根因）。
    con = sqlite3.connect(str(db))
    db_ids = [r[0] for r in con.execute("SELECT id FROM chunks ORDER BY id")]
    con.close()
    if ids != db_ids:
        raise VectorIndexMissing(
            "向量索引与当前索引库不一致（chunk 行号错位）。请重建向量索引："
            "D:\\python\\python.exe -m vaultmind.search --build-vectors")
    if key is not None:
        _index_cache[key] = (m, ids)
    return m, ids


def search_vector(query: str, top_k: int = 10, frac: float = 1.0,
                  db_path=None, npy_path=None, ids_path=None) -> list[SearchHit]:
    """frac：语料切片比例（M6 规模-延迟曲线用，默认 1.0=全量）。"""
    db, npy, ids_file = _paths(db_path, npy_path, ids_path)
    m, ids = load_index(db, npy, ids_file)
    if 0.0 < frac < 1.0:
        cut = max(1, int(len(m) * frac))
        m, ids = m[:cut], ids[:cut]
    qvec = _normalize(embed_texts([query]))[0]
    scores = m @ qvec  # 已归一化 → 点积 = cosine
    if top_k >= len(scores):
        order = np.argsort(-scores)
    else:
        order = np.argpartition(-scores, top_k - 1)[:top_k]
        order = order[np.argsort(-scores[order])]

    con = sqlite3.connect(str(db))
    hits = []
    for idx in order:
        cid = ids[int(idx)]
        row = con.execute(
            "SELECT c.id, c.doc_id, d.rel, d.title, c.section, c.prefix, c.text "
            "FROM chunks c JOIN docs d ON d.id=c.doc_id WHERE c.id=?", (cid,)).fetchone()
        if row:
            hits.append(SearchHit(chunk_id=row[0], doc_id=row[1], rel=row[2],
                                  title=row[3], section=row[4], prefix=row[5],
                                  text=row[6], score=float(scores[idx]), source="vector"))
    con.close()
    return hits
