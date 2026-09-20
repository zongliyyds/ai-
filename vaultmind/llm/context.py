# -*- coding: utf-8 -*-
"""M4 上下文组装：检索命中 → 带 [S#] 编号的引用上下文。

设计约束：
- 每文档最多 max_per_doc 个 chunk（按命中顺序取），防止单篇霸屏；
- 总字符预算 max_chars（控制 prefill 成本，7B 模型实测）；
- 编号只在"最终保留块"上顺序分配 → 引用编号永不指向被截断丢弃的块。
"""
from dataclasses import dataclass

MAX_CTX_CHARS = 6000
MAX_PER_DOC = 2


@dataclass
class Citation:
    num: int
    rel: str
    title: str
    section: str
    text: str


def build_context(hits, max_chars: int = MAX_CTX_CHARS,
                  max_per_doc: int = MAX_PER_DOC) -> tuple[str, list[Citation]]:
    """hits：按分数降序的 SearchHit 列表 → (上下文文本, 引用清单)。"""
    # 1) 候选：按文档限流（hits 已有序）
    cands = []
    per_doc: dict[str, int] = {}
    for h in hits:
        if per_doc.get(h.rel, 0) >= max_per_doc:
            continue
        per_doc[h.rel] = per_doc.get(h.rel, 0) + 1
        cands.append(h)

    # 2) 预算内顺序编号（至少保留第一块，即使超预算）
    kept, blocks = [], []
    budget = max_chars
    for h in cands:
        num = len(kept) + 1
        head = "[S%d] 文档：%s（%s）｜ 章节：%s" % (
            num, h.title or h.rel, h.rel, h.section or "-")
        body = h.body[:max_chars]
        block = head + "\n" + body if body else head
        if kept and budget - len(block) <= 0:
            break
        kept.append((num, h))
        blocks.append(block)
        budget -= len(block) + 2

    cites = [Citation(num, h.rel, h.title or "", h.section or "", h.body)
             for num, h in kept]
    return "\n\n".join(blocks), cites
