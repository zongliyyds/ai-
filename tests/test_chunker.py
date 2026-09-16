# -*- coding: utf-8 -*-
"""分块器单元探针：前缀注入、H2/H3 切分、超长硬切、空文档。"""
from vaultmind.ingest.chunker import chunk_doc
from vaultmind.ingest.scanner import Doc


def _doc(body, tags=("编程", "Python"), rel="测试/示例.md"):
    return Doc(rel=rel, path="x", body=body, tags=list(tags))


def test_doc_level_chunk_and_h2_split():
    d = _doc("# 标题\n\n开头概述。\n\n## 第一节\n内容一。\n\n## 第二节\n内容二。")
    cs = chunk_doc(d)
    assert len(cs) == 3
    assert cs[0].section == "概述" and "开头概述" in cs[0].text
    assert cs[0].prefix == "[文档: 标题 | 章节: 概述 | 标签: 编程、Python]"
    assert cs[1].section == "## 第一节" and cs[2].section == "## 第二节"


def test_long_section_split_keeps_size_bound():
    para = "很长的段落内容。" * 40  # 320 字
    body = "## 长节\n\n" + "\n\n".join([para] * 4)  # ~1288 字
    cs = chunk_doc(_doc(body))
    secs = [c for c in cs if c.section.startswith("## 长节")]
    assert len(secs) >= 2, "超长小节应被二次切分"
    assert all(len(c.text) <= 600 for c in cs), "每个 chunk 都不应超过 600 字"


def test_h3_secondary_split():
    body = "## 节\n\n### 子一\n" + "x" * 700 + "\n\n### 子二\ny"
    cs = chunk_doc(_doc(body))
    assert len(cs) >= 3
    assert any(c.section.startswith("## 节 / ### 子一") for c in cs)
    assert all(len(c.text) <= 600 for c in cs)


def test_single_giant_paragraph_hard_split():
    body = "## 节\n\n" + "字" * 1500
    cs = chunk_doc(_doc(body))
    assert len(cs) >= 3
    assert all(len(c.text) <= 600 for c in cs)


def test_empty_and_whitespace_doc_no_chunks():
    assert chunk_doc(_doc("")) == []
    assert chunk_doc(_doc("\n\n  \n")) == []


def test_prefix_injected_in_every_chunk():
    d = _doc("# 甲\n\n## 乙\n丙", tags=("A",))
    cs = chunk_doc(d)
    for c in cs:
        assert c.prefix.startswith("[文档: 甲 | 章节:")
        assert "| 标签: A]" in c.prefix
