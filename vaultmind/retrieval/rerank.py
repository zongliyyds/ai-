# -*- coding: utf-8 -*-
"""M6 重排变体：标题加权重排（确定性，无模型，可离线单测）。

思路：查询词与文档标题的重合度是廉价强信号（裸标题查询尤其如此）。
title_boost 在既有分数上叠加加权项，不改检索、只动排序。
"""
import jieba

QUERY_STOPWORDS = {
    "是", "什么", "怎么", "如何", "为什么", "哪些", "哪个", "的", "了", "吗",
    "呢", "中", "在", "有", "和", "与", "做", "？", "?", "##", "讲了",
}


def query_tokens(query: str) -> set[str]:
    return {w.strip() for w in jieba.cut(query)
            if w.strip() and w.strip() not in QUERY_STOPWORDS}


def title_match_ratio(title: str, tokens: set[str]) -> float:
    """标题中命中查询词的比例（0~1）。"""
    if not title or not tokens:
        return 0.0
    low = title.lower()
    hit = sum(1 for t in tokens if t.lower() in low)
    return hit / len(tokens)


def title_boost(hits, query: str, weight: float = 1.0) -> list:
    """score' = score + weight * 标题命中率；稳定排序（同分保持原序）。"""
    tokens = query_tokens(query)
    if not tokens:
        return list(hits)
    scored = [(h, h.score + weight * title_match_ratio(h.title, tokens))
              for h in hits]
    scored.sort(key=lambda x: (-x[1], x[0].score))
    return [h for h, _ in scored]
