# -*- coding: utf-8 -*-
"""M7 文档一致性探针：README/简历数字必须与 reports 精确一致（防漂移）。"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BASELINE = {"recall@5": 0.8167, "mrr": 0.7010, "ndcg@10": 0.7339}


def test_readme_metrics_match_baseline():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for key, value in BASELINE.items():
        assert ("%.4f" % value) in text, "README 缺少指标 %s" % key
    # 断言出处标注齐全
    for anchor in ["reports/baseline.md", "reports/ablation.md", "reports/m4_smoke.md"]:
        assert anchor in text


def test_readme_status_and_repro():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "python -m vaultmind.eval" in text
    assert "scripts\\env_check.py" in text
    assert "只读" in text  # 红线表述


def test_resume_bullets_cite_sources():
    text = (ROOT / "docs" / "简历bullet.md").read_text(encoding="utf-8")
    assert "0.817" in text          # 简历口径（四舍五入自 0.8167）
    assert "reports/baseline.md" in text
    assert "reports/ablation.md" in text
    assert "gold_finalization" in text


def test_qa_playbook_covers_hard_questions():
    text = (ROOT / "docs" / "Q&A预案.md").read_text(encoding="utf-8")
    for kw in ["LangChain", "评测集", "顶部稀释", "负结果", "分块", "拒答"]:
        assert kw in text
    assert "0.8167" in text and "0.7010" in text and "0.7339" in text


def test_gold_sixty_approved():
    lines = [l for l in (ROOT / "eval" / "gold_set.jsonl")
             .read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 60
    import json
    assert all(json.loads(l).get("status") == "approved" for l in lines)


def test_ablation_conclusions_have_numbers():
    text = (ROOT / "reports" / "ablation.md").read_text(encoding="utf-8")
    assert "+0.0500" in text and "-0.0667" in text and "+0.0000" in text
