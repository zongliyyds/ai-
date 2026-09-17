# -*- coding: utf-8 -*-
"""sync_vault 探针：回写锚点的正则模式必须能命中当前文档。

动机：`scripts/sync_vault.py` 靠正则匹配文档里的旧数字再回写。文档格式一旦变化，
模式就会静默失配（脚本报"未命中"但不失败）——本探针让这种失配变成红灯。
"""
import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


def _load():
    spec = importlib.util.spec_from_file_location("sync_vault", ROOT / "scripts" / "sync_vault.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sv = _load()


@pytest.fixture()
def ctx():
    base = sv.parse_baseline()
    abl = sv.parse_ablation()
    assert {"recall@1", "recall@5", "recall@10", "mrr", "ndcg@10", "latency"} <= set(base), \
        "reports/baseline.md 指标总表解析失败"
    assert {"easy", "hard", "gain", "e6_25", "e6_100"} <= set(abl), \
        "reports/ablation.md 解析失败（分层/增益/E6 缺字段）"
    return base, abl


def test_anchor_patterns_all_match(ctx):
    """所有回写模式都必须能在目标文件里命中（否则脚本会静默漏改）。"""
    base, abl = ctx
    sv.ingest_secs = "1.4"
    sv.n_tests = 60
    sv.title_easy, sv.title_hard = 1.0000, 0.3750
    aud = sv.audit_counts()
    docs, chunks, links = sv.db_counts()
    edits = sv.anchor_edits(base, abl, aud, (docs, chunks, links), "1.4")

    misses = []
    for rel, pattern, new in edits:
        text = (ROOT / rel).read_text(encoding="utf-8")
        m = re.search(pattern, text)
        if not m:
            misses.append("%s :: %s" % (rel, pattern))
        elif m.group(0) == new:
            continue
    assert not misses, "以下模式未命中（文档格式已变，请更新 sync_vault.py）：\n" + "\n".join(misses)


def test_anchor_targets_exist():
    """锚点文件必须在仓库里存在。"""
    for rel in sv.ANCHOR_FILES:
        assert (ROOT / rel).exists(), "锚点文件缺失：%s" % rel


def test_dry_run_apply_is_readonly(tmp_path):
    """apply_edits(dry_run=True) 不得写入任何文件。"""
    edits = [("README.md", r"把个人 Obsidian 知识库（\d+ 篇", "把个人 Obsidian 知识库（999 篇")]
    before = (ROOT / "README.md").read_text(encoding="utf-8")
    sv.apply_edits(edits, dry_run=True)
    after = (ROOT / "README.md").read_text(encoding="utf-8")
    assert before == after, "dry-run 竟然修改了 README.md"
