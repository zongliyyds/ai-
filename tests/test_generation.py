# -*- coding: utf-8 -*-
"""M4 纯函数探针：上下文组装 / 引用校验 / 拒答判定（离线，不依赖 Ollama）。"""
from vaultmind.llm.context import build_context
from vaultmind.llm.validator import extract_cites, is_refusal, validate_cites
from vaultmind.retrieval.hit import SearchHit


def make_hit(rel, text, section="## X", score=1.0, chunk_id=1):
    return SearchHit(chunk_id=chunk_id, doc_id=1, rel=rel, title=rel,
                     section=section, prefix="", text=text, score=score,
                     source="test")


# ---- 上下文组装 ----

def test_context_numbering_and_per_doc_cap():
    hits = [
        make_hit("a.md", "正文A1" * 10, chunk_id=1),
        make_hit("a.md", "正文A2" * 10, chunk_id=2),
        make_hit("a.md", "正文A3" * 10, chunk_id=3),   # 同文档第 3 块 → 应被限流丢弃
        make_hit("b.md", "正文B1" * 10, chunk_id=4),
        make_hit("c.md", "正文C1" * 10, chunk_id=5),
    ]
    context, cites = build_context(hits, max_chars=100000)
    assert len(cites) == 4                      # 3 文档 × ≤2 块
    assert [c.num for c in cites] == [1, 2, 3, 4]
    assert cites[0].rel == "a.md" and cites[1].rel == "a.md"
    assert cites[2].rel == "b.md" and cites[3].rel == "c.md"
    for c in cites:
        assert "[S%d] 文档：%s" % (c.num, c.title) in context


def test_context_truncation_budget():
    hits = [make_hit("d%d.md" % i, "长文本" * 200) for i in range(10)]
    context, cites = build_context(hits, max_chars=500)
    # 至少保留第一块；编号只分配给保留块 → 编号连续且无空洞
    assert len(cites) >= 1
    assert [c.num for c in cites] == list(range(1, len(cites) + 1))
    # 被丢弃块不再出现在上下文中
    for c in cites:
        assert "[S%d]" % c.num in context
    assert "[S%d]" % (len(cites) + 1) not in context


def test_context_empty_hits():
    context, cites = build_context([])
    assert context == "" and cites == []


# ---- 引用提取与校验 ----

def test_extract_cites():
    assert extract_cites("结论见[S1]与[S12]。[W1]不算。") == [1, 12]
    assert extract_cites("[S 3] 带空格") == [3]
    assert extract_cites("[S1, S2, S4] 列表式") == [1, 2, 4]
    assert extract_cites("[S1，S3、S5] 中文分隔") == [1, 3, 5]
    assert extract_cites("【S1】中文括号") == [1]
    assert extract_cites("[S1]至[S8]") == [1, 8]
    assert extract_cites("S1 不带方括号不提取") == []
    assert extract_cites("[W1] 外部编号不提取") == []
    assert extract_cites("") == []


def test_validate_cites():
    chk = validate_cites("见[S1]、[S7]", 5)
    assert chk["cited_ids"] == [1, 7]
    assert chk["valid_ids"] == [1]
    assert chk["invalid_ids"] == [7]
    assert chk["citation_valid"] is False
    assert chk["has_citation"] is True

    ok = validate_cites("见[S2]、[S2]、[S5]", 5)
    assert ok["valid_ids"] == [2, 5] and ok["invalid_ids"] == []
    assert ok["citation_valid"] is True

    empty = validate_cites("没有引用", 5)
    assert empty["has_citation"] is False and empty["citation_valid"] is True


# ---- 拒答判定 ----

def test_is_refusal():
    assert is_refusal("知识库中没有相关信息，无法回答。") is True
    assert is_refusal("抱歉，我无法提供该问题的答案。") is True
    assert is_refusal("AIGC 检测是统计模式识别[S1]。") is False
    # 长回答即使含话术也不算拒答（避免长尾误判）
    long_ans = "知识库中没有相关信息，" + "很长的正文" * 200
    assert is_refusal(long_ans) is False
    assert is_refusal("") is False
