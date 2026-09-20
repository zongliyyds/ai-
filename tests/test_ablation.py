# -*- coding: utf-8 -*-
"""M6 消融纯函数探针（离线，不依赖 Ollama）：标题重排 / 规则改写 / 双链扩展 / RRF k。"""
import sqlite3

from vaultmind.retrieval.expand import expand_by_links
from vaultmind.retrieval.fusion import rrf_fuse
from vaultmind.retrieval.hit import SearchHit
from vaultmind.retrieval.rerank import query_tokens, title_boost
from vaultmind.llm.rewrite import rule_rewrite


def make_hit(rel, title, score, source="rrf", chunk_id=None, text="正文"):
    return SearchHit(chunk_id=chunk_id or hash(rel) % 10000, doc_id=1, rel=rel,
                     title=title, section="## X", prefix="", text=text,
                     score=score, source=source)


# ---- 标题加权重排 ----

def test_title_boost_reorders():
    low = make_hit("a.md", "SQLite FTS5 全文搜索配置", 0.95)
    high = make_hit("b.md", "Python 数据结构", 0.90)
    hits = title_boost([low, high], "Python 数据结构是什么")
    # 查询词集中在 b.md 标题 → 加权重排后升到第一
    assert hits[0].rel == "b.md"
    assert hits[1].rel == "a.md"


def test_title_boost_stable_no_tokens():
    a = make_hit("a.md", "A", 0.8)
    b = make_hit("b.md", "B", 0.9)
    hits = title_boost([a, b], "？？？")
    assert [h.rel for h in hits] == ["a.md", "b.md"]  # 无有效词 → 原序不变


def test_query_tokens_filters_stopwords():
    tokens = query_tokens("## 背景 是什么？怎么做？")
    assert "是什么" not in tokens and "##" not in tokens
    assert "背景" in tokens


# ---- 规则改写 ----

def test_rule_rewrite():
    assert rule_rewrite("## 背景 是什么？怎么做？") == "背景 指的是什么？"
    assert rule_rewrite("## 适用场景 是什么？怎么做？") == "适用场景 指的是什么？"
    # 含文档名的 easy 型不改写
    q = "Python 数据结构 中的「## 核心观点」讲了什么？"
    assert rule_rewrite(q) == q


# ---- 双链 1-hop 扩展 ----

def test_expand_by_links(tmp_path):
    db = tmp_path / "x.db"
    con = sqlite3.connect(str(db))
    con.executescript(
        "CREATE TABLE docs(id INTEGER PRIMARY KEY, rel TEXT, title TEXT);"
        "CREATE TABLE chunks(id INTEGER PRIMARY KEY, doc_id INTEGER, section TEXT,"
        " seq INTEGER, prefix TEXT, text TEXT);"
        "CREATE TABLE links(id INTEGER PRIMARY KEY, src TEXT, target TEXT,"
        " alias TEXT, valid INTEGER);"
        "INSERT INTO docs VALUES(1,'a.md','A'),(2,'b.md','B'),(3,'c.md','C');"
        "INSERT INTO chunks(id,doc_id,section,seq,prefix,text) VALUES"
        "(10,2,'## 概述',0,'','B 正文'),(11,2,'## 详情',1,'','B 详情'),"
        "(12,3,'## 概述',0,'','C 正文');"
        "INSERT INTO links(src,target,alias,valid) VALUES('a.md','b.md','',1),"
        "('a.md','c.md','',1),('a.md','a.md','',1);")
    con.commit()
    con.close()

    hit_a = make_hit("a.md", "A", 0.9, chunk_id=1)
    # n=2：预算被首个目标 b.md 的 2 块耗尽 → 验证「每目标最多 2 块」+ 尾部排序
    out2 = expand_by_links([hit_a], n=2, db_path=db)
    assert [h.rel for h in out2] == ["a.md", "b.md", "b.md"]
    assert out2[1].source == "link1hop"
    assert out2[1].score < out2[0].score        # 扩展块排在尾部

    # n=5：预算充足 → 必须继续扩到第二个目标 c.md；且自链 a→a 不得被扩展
    out5 = expand_by_links([hit_a], n=5, db_path=db)
    rels = [h.rel for h in out5]
    assert "c.md" in rels, "多目标应被依次扩展，实际: %s" % rels
    assert rels.count("a.md") == 1, "自链 a→a 不得被扩展（只保留原始命中）"

    # 上限 n=1 → 只补 1 块
    assert len(expand_by_links([hit_a], n=1, db_path=db)) == 2


# ---- RRF k 参数 ----

def test_rrf_k_param():
    a = make_hit("a.md", "A", 1.0, chunk_id=1)
    b = make_hit("b.md", "B", 1.0, chunk_id=2)
    merged = rrf_fuse([[a], [b]], k=20)
    assert len(merged) == 2
    # k=20：rank0 → 1/(20+1)=1/21（fusion 内 round 到 6 位小数）
    assert abs(merged[0].score - 1.0 / 21.0) < 1e-6
    merged60 = rrf_fuse([[a], [b]], k=60)
    assert abs(merged60[0].score - 1.0 / 61.0) < 1e-6
