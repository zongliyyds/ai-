# -*- coding: utf-8 -*-
"""冒烟测试：模块可导入、扫描只读、完整管道可重建索引。"""
from vaultmind import __version__
from vaultmind.ingest import scanner
from vaultmind.ingest import run_pipeline


def test_imports():
    assert __version__


def test_scan_readonly():
    """扫描 Vault 得到文档列表；任何文档都必须有相对路径与正文。"""
    docs = scanner.scan_docs()
    assert len(docs) >= 150, "Vault 应有 150+ 篇笔记"
    for d in docs:
        assert d.rel, "每个文档都应有相对路径"


def test_full_pipeline_rebuild(tmp_path):
    """一条命令重建索引（临时库，不动真实 data/vaultmind.db）：
    docs/chunks/links/FTS5 全部写入临时库。
    报告输出重定向到临时路径，避免时间戳污染 tracked 的 reports/audit_report.md。
    """
    res = run_pipeline(report_out=tmp_path / "audit_report.md",
                       db_path=tmp_path / "vaultmind.db")
    s, m = res["stats"], res["metrics"]
    assert m["doc_count"] >= 150
    assert s["docs"] == m["doc_count"]
    assert s["chunks"] >= 900, "结构感知分块应产出 900+ chunk"
    assert s["links"] == m["outlink_total"]
    assert s["fts_rows"] == s["chunks"], "FTS5 行数应与 chunks 一致"
