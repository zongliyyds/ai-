# -*- coding: utf-8 -*-
"""重定审计基线：把 reports/baseline_audit.json 更新为当前 Vault 体检数字。

使用场景：用户正常新增/修改笔记后，pytest 基线探针与 pre-commit 会红——
先查因（Vault 合法增长），再运行本脚本重定基线（与 test_baseline 的
docstring「先查因，再决定改代码还是更新基线」一致）。
只写 reports/baseline_audit.json，不碰 Vault。
"""
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vaultmind.config import BASELINE_JSON, DATA_DIR  # noqa: E402

LOG_PATH = DATA_DIR / "_rebase_audit.log"


def main() -> int:
    try:
        from vaultmind.ingest import auditor, scanner

        m = auditor.audit(scanner.scan_docs())
        KEYS = ["root", "doc_count", "total_chars", "body_chars", "by_type",
                "by_top_folder", "by_status", "no_frontmatter", "est_chunks_h2",
                "total_h2", "total_h3", "outlink_total", "unresolved_links",
                "orphans", "top_inbound", "largest", "smallest_lt_300"]
        baseline = {k: m[k] for k in KEYS}
        BASELINE_JSON.parent.mkdir(parents=True, exist_ok=True)
        with open(BASELINE_JSON, "w", encoding="utf-8") as f:
            json.dump(baseline, f, ensure_ascii=False, indent=1)
        print("rebase OK: doc_count=%d total_chars=%d h2=%d links=%d"
              % (m["doc_count"], m["total_chars"], m["total_h2"], m["outlink_total"]))
        return 0
    except Exception:
        # 失败必须显式报错 + 非零退出码，调用方/pre-commit 才能感知（不吞异常假装 done）
        traceback.print_exc()
        try:
            with open(LOG_PATH, "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
        except Exception:
            pass
        print("rebase FAILED（详见 %s）" % LOG_PATH, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
