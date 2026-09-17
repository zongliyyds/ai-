# -*- coding: utf-8 -*-
"""M5 API 离线探针：TestClient 全端点（检索/生成打桩，不依赖 Ollama）。

口径锚点：/metrics 与 reports/baseline.md 现场解析值精确一致（锚点不手抄，随报告更新）；
/badcases 条数=11；/stats 与数据库直查一致。
"""
import sqlite3

from fastapi.testclient import TestClient

from _doc_anchors import parse_report_metrics
from vaultmind.api import main as api_main
from vaultmind.api import stats as api_stats
from vaultmind.config import DB_PATH
from vaultmind.retrieval.hit import SearchHit

client = TestClient(api_main.app)


def make_hit(rel="20-Knowledge/Python 数据结构.md", section="## 核心观点",
             text="正文内容测试", score=0.9, chunk_id=1, doc_id=1):
    return SearchHit(chunk_id=chunk_id, doc_id=doc_id, rel=rel, title=rel.split("/")[-1],
                     section=section, prefix="", text=text, score=score, source="rrf")


def fake_generate(question, context, model="qwen2.5:7b-instruct",
                  base_url="http://127.0.0.1:11434", temperature=0.2, timeout=180.0):
    return "见[S1]与[S2]的结论。", {
        "model": "fake", "generation_s": 0.01, "eval_count": 5,
        "prompt_eval_count": 20}


# ---- 基础端点 ----

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["vault_readonly"] is True


def test_index_page():
    r = client.get("/")
    assert r.status_code == 200
    assert "VaultMind" in r.text
    assert "问答" in r.text and "分析看板" in r.text


# ---- /search ----

def test_search_endpoint(monkeypatch):
    monkeypatch.setattr(api_main, "search",
                        lambda q, top_k=10, mode="hybrid": [make_hit()])
    r = client.post("/search", json={"query": "测试", "top_k": 5, "mode": "hybrid"})
    assert r.status_code == 200
    d = r.json()
    assert d["count"] == 1
    h = d["hits"][0]
    assert h["rel"].endswith("Python 数据结构.md")
    assert h["link"].startswith("obsidian://open?vault=AI-Knowledge-Vault")
    assert h["score"] == 0.9


def test_search_reject_bad_mode():
    r = client.post("/search", json={"query": "x", "mode": "bad"})
    assert r.status_code == 422


# ---- /ask（检索与生成打桩） ----

def test_ask_endpoint(monkeypatch):
    monkeypatch.setattr(api_main, "search",
                        lambda q, top_k=10, mode="hybrid": [make_hit(), make_hit(rel="b.md")])
    monkeypatch.setattr("vaultmind.llm.generator.generate", fake_generate)
    monkeypatch.setattr(api_main.api_stats, "insert_qa_log", lambda *a, **k: 42)
    r = client.post("/ask", json={"query": "Python 数据结构讲了什么？"})
    assert r.status_code == 200
    d = r.json()
    assert d["row_id"] == 42
    assert "见[S1]与[S2]" in d["answer"]
    assert [c["num"] for c in d["citations"]] == [1, 2]
    assert d["validation"]["citation_valid"] is True
    assert d["validation"]["cited_ids"] == [1, 2]
    assert d["refusal"] is False
    assert d["mode"] == "hybrid"
    assert d["citations"][0]["link"].startswith("obsidian://")


def test_ask_invalid_citation(monkeypatch):
    monkeypatch.setattr(api_main, "search",
                        lambda q, top_k=10, mode="hybrid": [make_hit()])
    monkeypatch.setattr("vaultmind.llm.generator.generate",
                        lambda *a, **k: ("见[S9]。", {"model": "fake", "generation_s": 0.01,
                                                      "eval_count": 3, "prompt_eval_count": 9}))
    monkeypatch.setattr(api_main.api_stats, "insert_qa_log", lambda *a, **k: 1)
    d = client.post("/ask", json={"query": "q"}).json()
    assert d["validation"]["invalid_ids"] == [9]
    assert d["validation"]["citation_valid"] is False


def test_ask_refusal(monkeypatch):
    monkeypatch.setattr(api_main, "search",
                        lambda q, top_k=10, mode="hybrid": [make_hit()])
    monkeypatch.setattr("vaultmind.llm.generator.generate",
                        lambda *a, **k: ("知识库中没有相关信息，无法回答。",
                                         {"model": "fake", "generation_s": 0.01,
                                          "eval_count": 4, "prompt_eval_count": 10}))
    monkeypatch.setattr(api_main.api_stats, "insert_qa_log", lambda *a, **k: 1)
    d = client.post("/ask", json={"query": "比特币价格"}).json()
    assert d["refusal"] is True
    assert d["validation"]["has_citation"] is False


# ---- /stats /metrics /badcases（口径锚点） ----

def test_stats_matches_db():
    d = client.get("/stats").json()
    assert "error" not in d
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()
    assert d["docs"] == cur.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
    assert d["chunks"] == cur.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    assert d["links"] == cur.execute("SELECT COUNT(*) FROM links").fetchone()[0]
    assert d["fts_rows"] == cur.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0]
    con.close()


def test_metrics_match_baseline():
    """/metrics 必须与 reports/baseline.md 现场解析值一致（锚点动态取，防漂移）。"""
    d = client.get("/metrics").json()
    v = d["values"]
    expect = parse_report_metrics()
    assert {"recall@5", "mrr", "ndcg@10"} <= set(expect), "baseline.md 指标总表解析失败"
    for key in ["recall@5", "mrr", "ndcg@10"]:
        assert abs(v[key] - expect[key]) < 1e-9, \
            "%s 与 baseline.md 不一致：API=%s 报告=%s" % (key, v[key], expect[key])
    assert d["num_queries"] == 60
    assert d["recall@5"]["pass"] and d["mrr"]["pass"] and d["ndcg@10"]["pass"]


def test_badcases_count():
    d = client.get("/badcases").json()
    assert d["total"] == 11
    assert all("question" in it and "id" in it for it in d["items"])


# ---- /feedback ----

def test_feedback_endpoint(monkeypatch):
    monkeypatch.setattr(api_main.api_stats, "record_feedback",
                        lambda row, rating, cat, **k: True)
    r = client.post("/feedback", json={"row_id": 1, "rating": -1, "category": "检索漏召"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


# ---- stats 纯函数（临时库，不污染真实索引） ----

def test_qa_logs_and_stats_with_tmp_db(tmp_path):
    db = tmp_path / "qa.db"
    api_stats.init_qa_logs(db)
    rid = api_stats.insert_qa_log("问题", "hybrid", 8, 10, [1, 2], [], False, 0.5, db)
    assert api_stats.record_feedback(rid, -1, "生成幻觉", db) is True
    assert api_stats.record_feedback(999, 1, "", db) is False

    con = sqlite3.connect(str(db))
    con.executescript(
        "CREATE TABLE docs(id INTEGER PRIMARY KEY, chars INTEGER, h2 INTEGER, deadlinks INTEGER);"
        "CREATE TABLE chunks(id INTEGER PRIMARY KEY);"
        "CREATE TABLE links(id INTEGER PRIMARY KEY);"
        "CREATE TABLE chunks_fts(id INTEGER PRIMARY KEY);"
        "INSERT INTO docs(chars,h2,deadlinks) VALUES(100,5,1),(200,3,0);"
        "INSERT INTO chunks VALUES(1),(2),(3);"
        "INSERT INTO links VALUES(1);")
    con.commit()
    con.close()
    s = api_stats.library_stats(db)
    assert s["docs"] == 2 and s["chars"] == 300 and s["h2"] == 8
    assert s["dead_links"] == 1 and s["chunks"] == 3 and s["links"] == 1
    assert s["qa_logs"] == 1
