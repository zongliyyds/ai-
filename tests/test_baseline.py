# -*- coding: utf-8 -*-
"""探针测试：本次审计数字必须与基线 reports/baseline_audit.json 逐项一致。

任何不一致都说明口径漂移或 Vault 内容变化——先查因，再决定改代码还是更新基线。
"""
import json
from pathlib import Path

from vaultmind.ingest import auditor, scanner

ROOT = Path(__file__).resolve().parent.parent
BASELINE = json.loads(
    (ROOT / "reports" / "baseline_audit.json").read_text(encoding="utf-8"))

PARITY_KEYS = ["doc_count", "total_chars", "body_chars", "total_h2", "total_h3",
               "outlink_total", "unresolved_links", "est_chunks_h2"]


def _metrics():
    return auditor.audit(scanner.scan_docs())


def test_headline_numbers_match_baseline():
    m = _metrics()
    for k in PARITY_KEYS:
        assert m[k] == BASELINE[k], f"{k}: 本次 {m[k]} != 基线 {BASELINE[k]}"


def test_distributions_match_baseline():
    m = _metrics()
    assert m["by_type"] == BASELINE["by_type"], "类型分布与基线不一致"
    assert m["by_status"] == BASELINE["by_status"], "状态分布与基线不一致"
    assert m["by_top_folder"] == BASELINE["by_top_folder"], "目录分布与基线不一致"


def test_detail_lists_match_baseline():
    m = _metrics()
    assert m["no_frontmatter"] == BASELINE["no_frontmatter"], "无 frontmatter 清单不一致"
    assert m["orphans"] == BASELINE["orphans"], "孤儿清单不一致"
    assert m["top_inbound"] == BASELINE["top_inbound"], "入链排行不一致"
    assert m["largest"] == BASELINE["largest"], "最大文档清单不一致"
    assert m["smallest_lt_300"] == BASELINE["smallest_lt_300"], "小文档清单不一致"
