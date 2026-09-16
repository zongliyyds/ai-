# -*- coding: utf-8 -*-
r"""M4 在线冒烟：库内 2 问（应引用、可追溯）+ 超纲 2 问（应拒答）。

需要 Ollama 运行（bge-m3 + qwen2.5:7b-instruct）。
用法：D:\python\python.exe scripts\m4_smoke.py
判定：库内问 → has_citation 且非法编号=0；超纲问 → is_refusal 且无非法编号。
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vaultmind.llm.context import build_context          # noqa: E402
from vaultmind.llm.generator import generate             # noqa: E402
from vaultmind.llm.validator import is_refusal, validate_cites  # noqa: E402
from vaultmind.retrieval import search                   # noqa: E402

PROBES = [
    ("python-docx 多文档合并时为什么要用底层 XML API 而不是高层接口？", False),
    ("AIGC 检测的原理是什么？", False),
    ("今天比特币的价格是多少？", True),
    ("2027 年上海迪士尼乐园门票多少钱？", True),
]


def main() -> int:
    ok = True
    rows = []
    for i, (q, expect_refusal) in enumerate(PROBES, 1):
        t0 = time.perf_counter()
        hits = search(q, top_k=8, mode="hybrid")
        context, cites = build_context(hits)
        answer, meta = generate(q, context)
        chk = validate_cites(answer, len(cites))
        refusal = is_refusal(answer)
        wall = round(time.perf_counter() - t0, 2)
        if expect_refusal:
            good = refusal and not chk["invalid_ids"]
        else:
            good = chk["has_citation"] and chk["citation_valid"]
        ok = ok and good
        rows.append((q, good))
        print("=" * 70)
        print("[%d] %s" % (i, q))
        print("答：%s" % answer.strip()[:400])
        print("校验：引用=%s 非法=%s 拒答=%s 端到端=%.2fs（生成 %.1fs，%s tokens）" % (
            chk["cited_ids"], chk["invalid_ids"], refusal, wall,
            meta["generation_s"], meta.get("eval_count")))
    print("=" * 70)
    print("冒烟结论：%s" % ("PASS" if ok else "FAIL"))
    for q, good in rows:
        print("  [%s] %s" % ("✓" if good else "✗", q))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
