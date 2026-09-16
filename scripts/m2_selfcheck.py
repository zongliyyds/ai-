# -*- coding: utf-8 -*-
r"""M2 自查表生成器：10 个已知答案问题 × 3 种模式 → reports/m2_selfcheck.md。

验收标准（工单 M2-01 §3）：hybrid 模式 Top-5 命中正确笔记 ≥ 8/10。
用法：D:\python\python.exe scripts\m2_selfcheck.py
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vaultmind.retrieval import search  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports" / "m2_selfcheck.md"

QUESTIONS = [
    ("CET-4 知识库用了什么去重方案？",
     "10-Projects/cet4-knowledge-base/README.md",
     ["20-Knowledge/TF-IDF 中文文本去重实践.md"]),
    ("SQLite FTS5 中文分词怎么配置？",
     "20-Knowledge/SQLite FTS5 全文搜索配置.md",
     ["20-Knowledge/SQLite FTS5 全文搜索配置.md"]),
    ("python-docx 怎么自动化操作 Word 文档？",
     "20-Knowledge/python-docx 文档自动化操作.md",
     ["20-Knowledge/python-docx 文档自动化操作.md"]),
    ("Godot 4.7 GDScript 有哪些坑？",
     "20-Knowledge/Godot 4.7 GDScript 踩坑清单.md",
     ["20-Knowledge/Godot 4.7 GDScript 踩坑清单.md"]),
    ("AIGC 检测的论文怎么降重？",
     "20-Knowledge/PaperPass降AIGC五版对照方法论.md",
     ["20-Knowledge/AIGC检测论文降重分析.md",
      "20-Knowledge/PaperPass降AIGC五版对照方法论.md"]),
    ("论文格式模板怎么匹配？",
     "20-Knowledge/论文格式模板匹配方法论.md",
     ["20-Knowledge/论文格式模板匹配方法论.md"]),
    ("Word 复杂模板 textbox 拼接布局怎么改？",
     "20-Knowledge/Word 复杂模板 textbox 拼接布局的精准改造方法论.md",
     ["20-Knowledge/Word 复杂模板 textbox 拼接布局的精准改造方法论.md"]),
    ("python-pptx 怎么做演示文稿？",
     "20-Knowledge/python-pptx 演示文稿自动化.md",
     ["20-Knowledge/python-pptx 演示文稿自动化.md"]),
    ("Python 数据结构有哪些要点？",
     "20-Knowledge/Python 数据结构.md",
     ["20-Knowledge/Python 数据结构.md"]),
    ("FastAPI 轻量后端项目怎么搭？",
     "20-Knowledge/FastAPI 轻量后端项目模板.md",
     ["20-Knowledge/FastAPI 轻量后端项目模板.md"]),
]

MODES = ["bm25", "vector", "hybrid"]


def hit_ok(hits, accepted) -> bool:
    return any(h.rel in accepted for h in hits)


def main() -> int:
    rows = []
    mode_hits = {m: 0 for m in MODES}
    for q, primary, accepted in QUESTIONS:
        row = {"question": q, "primary": primary}
        for mode in MODES:
            hits = search(q, top_k=5, mode=mode)
            ok = hit_ok(hits, accepted)
            row[mode] = "✓" if ok else "✗"
            row[mode + "_top"] = " / ".join(h.rel.split("/")[-1].replace(".md", "") for h in hits[:3])
            mode_hits[mode] += int(ok)
        rows.append(row)

    L = []
    A = L.append
    A("# VaultMind M2 检索自查表（10 问 × 3 模式，Top-5 命中判定）")
    A("")
    A("> 生成时间：%s ｜ 口径：Top-5 内出现任一「预期笔记」即算命中 ｜ "
      "验收标准：hybrid ≥ 8/10" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    A("")
    A("| # | 问题 | bm25 | vector | hybrid | hybrid Top-3 |")
    A("|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        A("| %d | %s | %s | %s | %s | %s |" % (
            i, r["question"], r["bm25"], r["vector"], r["hybrid"], r["hybrid_top"]))
    A("")
    A("## 汇总")
    A("")
    A("| 模式 | 命中 | 达标（≥8/10） |")
    A("|---|---|---|")
    for m in MODES:
        A("| %s | %d/10 | %s |" % (m, mode_hits[m], "✓" if mode_hits[m] >= 8 else "✗"))
    A("")
    A("## 结论")
    A("")
    if mode_hits["hybrid"] >= 8:
        A("hybrid 达标（%d/10），M2 验收通过；未命中的问题列入 M2→M6 优化清单。" % mode_hits["hybrid"])
    else:
        A("hybrid 未达标（%d/10）：逐问归因（分词/密度/语义）后优化再复测，不伪造数字。" % mode_hits["hybrid"])
    A("")
    A("## 漏问归因（供 M6 消融与优化）")
    A("")
    for m in MODES:
        misses = [r for r in rows if r[m] == "✗"]
        if not misses:
            A("- %s：无漏问。" % m)
            continue
        for r in misses:
            A("- %s 漏问「%s」：Top-3 = %s" % (m, r["question"], r[m + "_top"]))
    A("")
    A("> 已知现象：Q1（CET-4 去重方案）在 bm25/vector 单路均命中，但 RRF 融合后被高频日志类笔记挤出 Top-5 —— "
      "「融合稀释单路强信号」是 M6 消融实验（A/B/C 三配置对比）的直接素材，如实记录。")
    A("")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("自查表已生成:", OUT)
    print("模式命中:", mode_hits)
    return 0


if __name__ == "__main__":
    sys.exit(main())
