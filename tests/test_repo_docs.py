# -*- coding: utf-8 -*-
"""M7 文档一致性探针：README/简历数字必须与 reports 精确一致（防漂移）。

锚点不再手抄常量，而是**从 reports 现场解析**——报告更新时探针自动跟随，
不会出现「报告已重生、断言还钉旧数字」的漂移（2026-09-17 重锚定修复）。
"""
from _doc_anchors import BASE_DIR as ROOT, parse_ablation_deltas, parse_report_metrics

BASE = parse_report_metrics()
DELTAS = parse_ablation_deltas()


def test_readme_metrics_match_baseline():
    assert {"recall@5", "mrr", "ndcg@10"} <= set(BASE), "baseline.md 指标总表解析失败"
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for key in ["recall@5", "mrr", "ndcg@10"]:
        assert ("%.4f" % BASE[key]) in text, "README 缺少指标 %s（应为 %.4f）" % (key, BASE[key])
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
    for key in ["recall@5", "mrr", "ndcg@10"]:
        assert ("%.4f" % BASE[key]) in text, "Q&A 预案数字过期：%s 应为 %.4f" % (key, BASE[key])


def test_gold_sixty_approved():
    lines = [l for l in (ROOT / "eval" / "gold_set.jsonl")
             .read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 60
    import json
    assert all(json.loads(l).get("status") == "approved" for l in lines)


def test_ablation_conclusions_have_numbers():
    """消融结论段必须含实测增益（从报告解析，不钉死某一轮的具体数值）。"""
    assert DELTAS["e1_delta"] is not None, "ablation.md 未解析到 E1 三路增益"
    assert DELTAS["e5_delta"] is not None, "ablation.md 未解析到 E5 1-hop 增益"
    text = (ROOT / "reports" / "ablation.md").read_text(encoding="utf-8")
    for shown in ["%+.4f" % DELTAS["e1_delta"], "%+.4f" % DELTAS["e5_delta"]]:
        assert shown in text, "结论段缺少增益数字 %s" % shown
    assert "负结果" in text
