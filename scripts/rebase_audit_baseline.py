# -*- coding: utf-8 -*-
"""重定审计基线：把 reports/baseline_audit.json 更新为当前 Vault 体检数字。

使用场景：用户正常新增/修改笔记后，pytest 基线探针与 pre-commit 会红——
先查因（Vault 合法增长），再运行本脚本重定基线（与 test_baseline 的
docstring「先查因，再决定改代码还是更新基线」一致）。
只写 reports/baseline_audit.json，不碰 Vault。"""
import io, json, sys, traceback
sys.path.insert(0, r"D:\RAG")

out = io.open(r"D:\RAG\data\_rebase_audit.log", "w", encoding="utf-8")
try:
    from vaultmind.ingest import auditor, scanner

    m = auditor.audit(scanner.scan_docs())
    KEYS = ["root", "doc_count", "total_chars", "body_chars", "by_type",
            "by_top_folder", "by_status", "no_frontmatter", "est_chunks_h2",
            "total_h2", "total_h3", "outlink_total", "unresolved_links",
            "orphans", "top_inbound", "largest", "smallest_lt_300"]
    baseline = {k: m[k] for k in KEYS}
    path = r"D:\RAG\reports\baseline_audit.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(baseline, f, ensure_ascii=False, indent=1)
    out.write("rebase OK: doc_count=%d total_chars=%d h2=%d links=%d\n"
              % (m["doc_count"], m["total_chars"], m["total_h2"],
                 m["outlink_total"]))
except Exception:
    traceback.print_exc(file=out)
out.close()
print("done")
