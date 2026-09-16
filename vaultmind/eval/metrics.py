# -*- coding: utf-8 -*-
"""评测指标（手写实现，不引 ragas）：Recall@k / MRR / nDCG@k。"""
import math


def _dedup(rels):
    seen, out = set(), []
    for r in rels:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def recall_at_k(pred_rels, true_rels, k):
    """pred[:k]（去重后）中命中的正确文档数 / 正确文档总数。"""
    true = set(true_rels)
    if not true:
        return 0.0
    hit = sum(1 for r in _dedup(pred_rels)[:k] if r in true)
    return hit / len(true)


def first_rank(pred_rels, true_rels):
    """首个正确文档的 1-based 排名；未命中返回 0。"""
    true = set(true_rels)
    for i, r in enumerate(_dedup(pred_rels), 1):
        if r in true:
            return i
    return 0


def mrr(runs):
    """Mean Reciprocal Rank。runs: [(pred_rels, true_rels), ...]"""
    if not runs:
        return 0.0
    total = 0.0
    for pred, true in runs:
        r = first_rank(pred, true)
        if r:
            total += 1.0 / r
    return total / len(runs)


def ndcg_at_k(pred_rels, true_rels, k):
    """二值相关度的 nDCG@k。DCG = Σ rel_i / log2(i+2)，IDCG 为理想排序。"""
    true = set(true_rels)
    pred = _dedup(pred_rels)[:k]
    dcg = 0.0
    for i, r in enumerate(pred):
        if r in true:
            dcg += 1.0 / math.log2(i + 2)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(true), k)))
    if idcg == 0:
        return 0.0
    return dcg / idcg


def aggregate(runs, ks=(1, 5, 10)):
    """runs: [(pred_rels, true_rels, latency_sec), ...] → 指标字典。"""
    out = {}
    for k in ks:
        vals = [recall_at_k(p, t, k) for p, t, _ in runs]
        out["recall@%d" % k] = sum(vals) / len(vals) if vals else 0.0
    out["mrr"] = mrr([(p, t) for p, t, _ in runs])
    out["ndcg@10"] = sum(ndcg_at_k(p, t, 10) for p, t, _ in runs) / len(runs) if runs else 0.0
    lats = [l for _, _, l in runs]
    out["avg_latency_s"] = sum(lats) / len(lats) if lats else 0.0
    out["num_queries"] = len(runs)
    return out
