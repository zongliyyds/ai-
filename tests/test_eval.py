# -*- coding: utf-8 -*-
"""指标公式探针：构造已知排序，断言 Recall/MRR/nDCG 精确值（防公式写错）。"""
from vaultmind.eval.metrics import aggregate, mrr, ndcg_at_k, recall_at_k

A, B, C, D, Z = "a", "b", "c", "d", "z"


def test_recall_at_k_exact():
    pred = [A, B, C, D]
    true = [B, Z]
    assert recall_at_k(pred, true, 1) == 0.0      # Top-1 无命中
    assert recall_at_k(pred, true, 2) == 0.5      # B 命中，Z 未命中 → 1/2
    assert recall_at_k(pred, true, 5) == 0.5      # 多给 k 不增加召回
    assert recall_at_k([], true, 5) == 0.0        # 空结果
    assert recall_at_k(pred, [], 5) == 0.0        # 无正确答案（分母为 0 不崩）


def test_mrr_exact():
    runs = [
        ([A, B], [B]),     # 首中排名 2 → 0.5
        ([A, C], [Z]),     # 未命中 → 0
        ([B], [B]),        # 首中排名 1 → 1.0
    ]
    assert abs(mrr(runs) - 0.5) < 1e-9
    assert mrr([]) == 0.0


def test_ndcg_at_k_exact():
    # 全命中且排前 → 1.0
    assert abs(ndcg_at_k([A, B], [A, B], 10) - 1.0) < 1e-9
    # 相关文档排第二：DCG = 1/log2(3) ≈ 0.6309，IDCG = 1 → 0.6309
    got = ndcg_at_k([C, B], [B], 10)
    assert abs(got - 0.6309297535714574) < 1e-9
    # 空预测 → 0
    assert ndcg_at_k([], [A], 10) == 0.0


def test_aggregate_shape():
    runs = [([A, B, C], [B, Z], 0.1), ([B], [B], 0.2)]
    m = aggregate(runs)
    assert set(m) == {"recall@1", "recall@5", "recall@10", "mrr",
                      "ndcg@10", "avg_latency_s", "num_queries"}
    assert m["num_queries"] == 2
    assert abs(m["avg_latency_s"] - 0.15) < 1e-9
    assert abs(m["mrr"] - 0.75) < 1e-9  # (0.5 + 1.0) / 2
