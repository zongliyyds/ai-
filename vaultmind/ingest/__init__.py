# -*- coding: utf-8 -*-
"""M1 数据管道：扫描 → 体检 → 分块 → 索引 → 报告（一条命令重建）。"""
import json
import time

from vaultmind.config import AUDIT_JSON
from vaultmind.ingest import auditor, chunker, indexer, report, scanner


def run_audit_only(root=None) -> dict:
    """只跑体检（快速探针用），不建索引。"""
    docs = scanner.scan_docs(root)
    return auditor.audit(docs, root)


def run_pipeline(root=None, build_index=True, report_out=None) -> dict:
    """完整管道。返回 docs/metrics/chunks/stats。

    report_out：报告输出路径（默认 reports/audit_report.md；测试请传临时路径，
    避免时间戳污染 tracked 报告）。
    """
    t0 = time.time()
    docs = scanner.scan_docs(root)
    metrics = auditor.audit(docs, root)
    chunks = chunker.chunk_all(docs)
    stats = indexer.build_db(docs, chunks) if build_index else None
    metrics["elapsed_sec"] = round(time.time() - t0, 2)

    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=1)
    report.write_audit_report(metrics, stats, out=report_out)
    return {"docs": docs, "metrics": metrics, "chunks": chunks, "stats": stats}
