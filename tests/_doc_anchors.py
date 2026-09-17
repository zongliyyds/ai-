# -*- coding: utf-8 -*-
"""测试共享：从 reports 现场解析锚点数字（防「报告重生、断言钉旧值」的漂移）。

用法：`from _doc_anchors import parse_report_metrics, BASE_DIR`
（conftest.py 已把 tests/ 目录加入 sys.path，故按顶层模块导入）。
"""
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def parse_report_metrics(rel_path="reports/baseline.md"):
    """解析 reports/baseline.md 指标总表 → {'recall@1': 0.6333, 'mrr': 0.7096, ...}。"""
    text = (BASE_DIR / rel_path).read_text(encoding="utf-8")
    out = {}
    for line in text.splitlines():
        m = re.match(r"\|\s*(Recall@\d+|MRR|nDCG@10)\s*\|\s*([0-9.]+)\s*\|", line)
        if m:
            out[m.group(1).lower()] = float(m.group(2))
    return out


def parse_ablation_deltas(rel_path="reports/ablation.md"):
    """解析 reports/ablation.md 结论段的三路增益(E1)与 1-hop 增益(E5)。

    返回 {'e1_delta': 0.0500, 'e5_delta': 0.0000}；解析不到时为 None。
    """
    text = (BASE_DIR / rel_path).read_text(encoding="utf-8")
    e1 = re.search(r"比 bm25（[0-9.]+）高 \*\*([+-][0-9.]+)\*\*", text)
    e5 = re.search(r"R@5 [0-9.]+（\*\*([+-][0-9.]+)\*\*）、MRR", text)
    return {
        "e1_delta": float(e1.group(1)) if e1 else None,
        "e5_delta": float(e5.group(1)) if e5 else None,
    }
