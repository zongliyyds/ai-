# -*- coding: utf-8 -*-
"""M5 产品层：FastAPI 问答服务。

红线：只读 Vault（本服务不触碰源文件）；问答日志只写 data/vaultmind.db（派生产物）；
默认本地模型，无云端调用。
"""
import time
import urllib.parse
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from vaultmind.api import stats as api_stats
from vaultmind.config import VAULT_ROOT
from vaultmind.llm.context import build_context
from vaultmind.llm.validator import is_refusal, validate_cites
from vaultmind.retrieval import search

app = FastAPI(title="VaultMind", version="0.1.0", description="个人知识库 RAG 问答与评测系统")
api_stats.init_qa_logs()

STATIC_DIR = Path(__file__).resolve().parent / "static"
VAULT_NAME = VAULT_ROOT.name  # Obsidian vault 名 = 源目录末级


def obsidian_link(rel: str) -> str:
    """引用跳转：obsidian:// URI（浏览器禁 file:// 跨源跳转，Obsidian 已装本机）。"""
    return "obsidian://open?vault=%s&file=%s" % (
        urllib.parse.quote(VAULT_NAME), urllib.parse.quote(rel))


def _hit_payload(h):
    return {
        "rel": h.rel, "title": h.title, "section": h.section,
        "score": round(h.score, 4), "source": h.source,
        "snippet": (h.text or "")[:160], "link": obsidian_link(h.rel),
    }


class SearchReq(BaseModel):
    query: str
    top_k: int = Field(default=8, ge=1, le=60)
    mode: str = Field(default="hybrid", pattern="^(bm25|vector|hybrid)$")


class AskReq(SearchReq):
    model: str = "qwen2.5:7b-instruct"


class FeedbackReq(BaseModel):
    row_id: int
    rating: int = Field(ge=-1, le=1)      # 1 好 / -1 差 / 0 中性
    category: str = ""                     # 检索漏召 / 上下文缺失 / 生成幻觉 / 问题超纲


@app.get("/health")
def health():
    return {"status": "ok", "app": "vaultmind", "vault_readonly": True}


@app.post("/search")
def api_search(req: SearchReq):
    hits = search(req.query, top_k=req.top_k, mode=req.mode)
    return {"query": req.query, "mode": req.mode,
            "count": len(hits), "hits": [_hit_payload(h) for h in hits]}


@app.post("/ask")
def api_ask(req: AskReq):
    t0 = time.perf_counter()
    hits = search(req.query, top_k=req.top_k, mode=req.mode)
    context, cites = build_context(hits)
    from vaultmind.llm.generator import generate  # 局部导入：离线测试可打桩
    answer, meta = generate(req.query, context, model=req.model)
    chk = validate_cites(answer, len(cites))
    refusal = is_refusal(answer)
    latency = round(time.perf_counter() - t0, 3)
    row_id = api_stats.insert_qa_log(
        req.query, req.mode, req.top_k, len(answer), chk["cited_ids"],
        chk["invalid_ids"], refusal, latency)
    return {
        "row_id": row_id,
        "question": req.query,
        "mode": req.mode,
        "answer": answer,
        "citations": [
            {"num": c.num, "rel": c.rel, "title": c.title, "section": c.section,
             "snippet": c.text[:160], "link": obsidian_link(c.rel)}
            for c in cites],
        "validation": chk,
        "refusal": refusal,
        "latency_s": latency,
        **meta,
    }


@app.get("/stats")
def api_library_stats():
    return api_stats.library_stats()


@app.get("/metrics")
def api_metrics():
    return api_stats.baseline_metrics()


@app.get("/badcases")
def api_badcases():
    items = api_stats.badcases()
    return {"total": len(items), "items": items}


@app.post("/feedback")
def api_feedback(req: FeedbackReq):
    ok = api_stats.record_feedback(req.row_id, req.rating, req.category or None)
    return {"ok": ok}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
