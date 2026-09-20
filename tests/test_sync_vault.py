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
    aud = sv.audit_counts()
    docs, chunks, links = sv.db_counts()
    edits = sv.anchor_edits(base, abl, aud, (docs, chunks, links))
    # 假绿防线：anchor_edits 必须真的产出一批回写项，否则下面 for 循环空转、断言空通过
    assert edits, "anchor_edits 返回空列表——回写逻辑或数据源异常，请排查"

    misses = []
    for rel, pattern, new in edits:
        text = (ROOT / rel).read_text(encoding="utf-8")
        m = re.search(pattern, text)
        if not m:
            misses.append("%s :: %s" % (rel, pattern))
    assert not misses, "以下模式未命中（文档格式已变，请更新 sync_vault.py）：\n" + "\n".join(misses)


def test_anchor_targets_exist():
    """锚点文件必须在仓库里存在。"""
    for rel in sv.ANCHOR_FILES:
        assert (ROOT / rel).exists(), "锚点文件缺失：%s" % rel


def test_change_vs_last_short_circuits(tmp_path):
    """变更检测真正短路：hash 一致 → False；变化 → True（M2 修复的单元级验证）。"""
    state = tmp_path / "s.json"
    fp = {"md_count": 3, "hash": "abc123", "at": "2026-01-01 00:00:00"}
    sv.save_state(fp, state)
    changed, _why = sv.change_vs_last(fp, state)
    assert changed is False, "hash 一致应短路跳过"
    changed2, _why2 = sv.change_vs_last({**fp, "hash": "xyz789"}, state)
    assert changed2 is True, "hash 变化应触发重建"


def test_light_uses_separate_index_state():
    """轻量同步指纹与全量同步指纹必须隔离，避免互相污染变更判断。"""
    assert sv.INDEX_STATE != sv.STATE
    assert sv.INDEX_STATE.name == "index_state.json"
    assert sv.STATE.name == "sync_state.json"


def test_dry_run_apply_is_readonly(tmp_path):
    """apply_edits(dry_run=True) 不得写入任何文件。"""
    edits = [("README.md", r"把个人 Obsidian 知识库（\d+ 篇", "把个人 Obsidian 知识库（999 篇")]
    before = (ROOT / "README.md").read_text(encoding="utf-8")
    sv.apply_edits(edits, dry_run=True)
    after = (ROOT / "README.md").read_text(encoding="utf-8")
    assert before == after, "dry-run 竟然修改了 README.md"
