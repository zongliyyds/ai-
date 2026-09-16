# -*- coding: utf-8 -*-
r"""向量检索：Ollama bge-m3 全量向量化（断点续跑）+ numpy 暴力 cosine。

产物（只写 D:\RAG\data）：
- embeddings.npy：float32 N×1024（已 L2 归一化，cosine = 点积）
- chunk_ids.json：行号 → chunk id 映射
"""
import json
import sqlite3
import time

import httpx
import numpy as np

from vaultmind.config import DATA_DIR, DB_PATH
from vaultmind.retrieval.hit import SearchHit

EMB_MODEL = "bge-m3"
EMB_URL = "http://127.0.0.1:11434/api/embed"
EMB_NPY = DATA_DIR / "embeddings.npy"
EMB_IDS = DATA_DIR / "chunk_ids.json"
BATCH_SIZE = 32


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


def build_embeddings(resume: bool = True, batch: int = BATCH_SIZE, limit: int | None = None) -> dict:
    """全量向量化 chunks；resume=True 时跳过已完成行（断点续跑）。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ids, texts = load_chunk_texts()
    if limit:
        ids, texts = ids[:limit], texts[:limit]

    done_ids = set()
    matrix = []
    if resume and EMB_NPY.exists() and EMB_IDS.exists():
        done_ids = set(json.loads(EMB_IDS.read_text(encoding="utf-8")))
        matrix = list(np.load(EMB_NPY))
        print("断点续跑：已完成 %d 行，续跑剩余部分" % len(done_ids))

    todo = [(i, t) for i, t in zip(ids, texts) if i not in done_ids]
    t0 = time.time()
    for start in range(0, len(todo), batch):
        chunk = todo[start:start + batch]
        texts_b = [t for _, t in chunk]
        emb = _normalize(embed_texts(texts_b))
        matrix.extend(emb)
        done_ids.update(i for i, _ in chunk)
        np.save(EMB_NPY, np.asarray(matrix, dtype=np.float32))
        EMB_IDS.write_text(json.dumps(sorted(done_ids)), encoding="utf-8")
        print("  已向量化 %d/%d（%.1fs）" % (len(done_ids), len(ids), time.time() - t0))

    stats = {
        "total_chunks": len(ids),
        "embedded": len(done_ids),
        "dim": 1024,
        "npy": str(EMB_NPY),
        "ids_json": str(EMB_IDS),
    }
    return stats


def load_index() -> tuple[np.ndarray, list[int]]:
    if not (EMB_NPY.exists() and EMB_IDS.exists()):
        raise VectorIndexMissing(
            "向量索引缺失。请先执行 D:\\python\\python.exe -m vaultmind.search --build-vectors")
    m = np.load(EMB_NPY)
    ids = json.loads(EMB_IDS.read_text(encoding="utf-8"))
    if len(m) != len(ids):
        raise VectorIndexMissing("向量矩阵与 id 映射行数不一致，请重建向量索引")
    return m, ids


def search_vector(query: str, top_k: int = 10) -> list[SearchHit]:
    m, ids = load_index()
    qvec = _normalize(embed_texts([query]))[0]
    scores = m @ qvec  # 已归一化 → 点积 = cosine
    if top_k >= len(scores):
        order = np.argsort(-scores)
    else:
        order = np.argpartition(-scores, top_k - 1)[:top_k]
        order = order[np.argsort(-scores[order])]

    con = sqlite3.connect(str(DB_PATH))
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
