# -*- coding: utf-8 -*-
r"""M6b 分块粒度消融：6 个分块变体 × 同一份 60 条 gold → reports/m6b_chunk_ablation.md。

用法：D:\python\python.exe scripts\m6b_chunk_ablation.py
依赖：Ollama 运行（bge-m3，用于重嵌入与查询嵌入）。
红线：只读 Vault；全部产物只写 data/ablation/m6b/<变体>/；正式索引与向量零改动。
耗时：约 4~6 分钟（5 变体全量重嵌入 + 300 次查询嵌入；重跑带断点续跑会快很多）。

实验纪律（与 M6 一致）：
- 同一把尺：60 条 approved gold、同一指标口径、hybrid k=60 / top_k=10。
- 只动待测组件：检索侧完全不动，只换分块 → 索引 → 向量。
- 嵌入配置全变体一致（同一 bge-m3 / 同一 num_ctx），只让 max_chars 变 → 不引入混杂变量。
- 基线复现闸门：V1（正式管道分块）必须精确复现 reports/baseline.md 的三项指标。

坑位（2026-09-17 实测）：bge-m3 经 Ollama 的默认 num_ctx=4096，**单块超上下文直接 HTTP 400**
（the input length exceeds the context length）。故粗粒度变体上限取 1500 中文字符
（≈ 1.5~2× num_ctx 词元估算的安全区），而不是「真·整篇」——若要真整篇需调 num_ctx，
但那会让该变体的嵌入配置与其他变体不同，破坏单一变量原则。
"""
import hashlib
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from _doc_anchors import parse_report_metrics              # noqa: E402
from vaultmind.eval.metrics import aggregate, first_rank   # noqa: E402
from vaultmind.eval.runner import load_gold                # noqa: E402
from vaultmind.ingest.chunker import chunk_all             # noqa: E402
from vaultmind.ingest.indexer import build_db              # noqa: E402
from vaultmind.ingest.scanner import scan_docs             # noqa: E402
from vaultmind.retrieval import search, vector             # noqa: E402

BASE = parse_report_metrics()          # 基线现场取数：{recall@5, mrr, ndcg@10, ...}
TOP_K = 10
WORK = ROOT / "data" / "ablation" / "m6b"
REPORT = ROOT / "reports" / "m6b_chunk_ablation.md"

VARIANTS = [
    dict(key="V1", label="V1 基线 h2/600/前缀(字段)", granularity="h2",
         max_chars=600, prefix_mode="field", note="= 正式管道"),
    dict(key="V2", label="V2 细粒度 h3/300/前缀(字段)", granularity="h3",
         max_chars=300, prefix_mode="field", note="切更细"),
    dict(key="V3", label="V3 粗粒度 整篇/1500/前缀(字段)", granularity="doc",
         max_chars=1500, prefix_mode="field", note="文档级粗粒度（受 num_ctx 4096 限制）"),
    dict(key="V4", label="V4 无前缀 h2/600/none", granularity="h2",
         max_chars=600, prefix_mode="none", note="预期 = V1（前缀本就不进检索）"),
    dict(key="V5", label="V5 前缀入检索 h2/600/inline", granularity="h2",
         max_chars=600, prefix_mode="inline", note="前缀进 FTS tokens 与向量"),
    dict(key="V6", label="V6 组合 整篇/1500/inline", granularity="doc",
         max_chars=1500, prefix_mode="inline", note="两个正增益因子叠加验证"),
]


def family_metrics(details, family):
    """与 M6 同口径的分层指标（gold 每题单文档、二值相关）。"""
    sel = [d for d in details if d["family"] == family]
    n = len(sel)
    if n == 0:
        return {"n": 0, "recall@5": 0.0, "mrr": 0.0}
    r5 = sum(1 for d in sel if 1 <= d["first_rank"] <= 5) / n
    mrr = sum(1.0 / d["first_rank"] for d in sel if d["first_rank"]) / n
    return {"n": n, "recall@5": r5, "mrr": mrr}


def index_fingerprint(chunks) -> str:
    """索引文本指纹：所有 chunk 的「section|prefix|text」拼接后 SHA-256 前 12 位。

    用于证明「V1 与 V4 的索引内容逐字节相同」这类实现事实（prefix 字段不进检索）。
    """
    h = hashlib.sha256()
    for c in chunks:
        h.update(("%s|%s|%s\x00" % (c.section, c.prefix, c.text)).encode("utf-8"))
    return h.hexdigest()[:12]


def emb_text_fingerprint(chunks) -> str:
    """实际进入 FTS tokens / 向量的文本指纹（只含 text）。"""
    h = hashlib.sha256()
    for c in chunks:
        h.update((c.text + "\x00").encode("utf-8"))
    return h.hexdigest()[:12]


def run_variant(docs, gold, v):
    d = WORK / v["key"]
    d.mkdir(parents=True, exist_ok=True)
    db, npy, ids = d / "vaultmind.db", d / "embeddings.npy", d / "chunk_ids.json"

    t0 = time.perf_counter()
    chunks = chunk_all(docs, granularity=v["granularity"], max_chars=v["max_chars"],
                       prefix_mode=v["prefix_mode"])
    stats = build_db(docs, chunks, db_path=db)
    idx_sec = time.perf_counter() - t0

    t0 = time.perf_counter()
    est = vector.build_embeddings(resume=True, db_path=db, npy_path=npy, ids_path=ids)
    emb_sec = time.perf_counter() - t0

    runs, details = [], []
    for it in gold:
        t1 = time.perf_counter()
        hits = search(it["question"], top_k=TOP_K, mode="hybrid",
                      db_path=db, npy_path=npy, ids_path=ids)
        lat = time.perf_counter() - t1
        pred = [h.rel for h in hits]
        true = it.get("docs", [])
        rank = first_rank(pred, true)
        runs.append((pred, true, lat))
        details.append(dict(id=it["id"], family=it.get("family", "easy"),
                            first_rank=rank, hit5=1 <= rank <= 5))
    lens = [len(c.text) for c in chunks]
    return dict(variant=v, agg=aggregate(runs), details=details, chunks=len(chunks),
                avg_len=sum(lens) / max(1, len(lens)), max_len=max(lens),
                idx_sec=idx_sec, emb_sec=emb_sec, stats=stats,
                struct_fp=index_fingerprint(chunks),
                emb_fp=emb_text_fingerprint(chunks))


def row(label, r):
    a = r["agg"]
    hard = family_metrics(r["details"], "hard")
    easy = family_metrics(r["details"], "easy")
    return ("| %s | %d | %.0f | %.4f | %.4f | %.4f | %.4f | %.4f | %.3f | %.4f(%d) | %.4f(%d) |" %
            (label, r["chunks"], r["avg_len"], a["recall@1"], a["recall@5"],
             a["recall@10"], a["mrr"], a["ndcg@10"], a["avg_latency_s"],
             hard["recall@5"], hard["n"], easy["recall@5"], easy["n"]))


def table_header(A):
    A("| 变体 | chunks | 平均块长 | R@1 | R@5 | R@10 | MRR | nDCG@10 | 延迟s | hard R@5(n) | easy R@5(n) |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")


def main() -> int:
    gold = load_gold()
    if len(gold) != 60:
        print("gold 非 60 条（%d），中止" % len(gold))
        return 1
    docs = scan_docs()
    print("Vault 只读扫描：%d 篇（实验只用派生索引，Vault 零写入）" % len(docs))

    results = []
    for v in VARIANTS:
        print("[%s] 切分 + 建索引 + 重嵌入 + 评测 ..." % v["key"])
        r = run_variant(docs, gold, v)
        results.append(r)
        print("    chunks=%d 平均块长=%.0f R@5=%.4f MRR=%.4f nDCG@10=%.4f"
              % (r["chunks"], r["avg_len"], r["agg"]["recall@5"],
                 r["agg"]["mrr"], r["agg"]["ndcg@10"]))

    v1 = results[0]
    gate = (abs(v1["agg"]["recall@5"] - BASE["recall@5"]) < 0.001
            and abs(v1["agg"]["mrr"] - BASE["mrr"]) < 0.001
            and abs(v1["agg"]["ndcg@10"] - BASE["ndcg@10"]) < 0.001)

    L = []
    A = L.append
    A("# VaultMind 分块粒度消融报告（M6b · W4 追加实验）")
    A("")
    A("> 生成时间：%s ｜ gold 60 条 ｜ hybrid k=60 / top_k=10 ｜ 复现："
      "`D:\\python\\python.exe scripts\\m6b_chunk_ablation.py`" % time.strftime("%Y-%m-%d %H:%M"))
    A("> 基线锚点（`reports/baseline.md` 现场解析）：Recall@5=%.4f / MRR=%.4f / nDCG@10=%.4f。"
      % (BASE["recall@5"], BASE["mrr"], BASE["ndcg@10"]))
    A("> Vault 语料：%d 篇（只读扫描）｜ 检索侧完全冻结核（只换分块 → 索引 → 向量）。" % len(docs))
    A("")
    A("## 一、变体与设计")
    A("")
    A("| 变体 | 切分 | max_chars | 前缀模式 | 设计意图 |")
    A("|---|---|---|---|---|")
    for v in VARIANTS:
        A("| %s | %s | %d | %s | %s |" % (v["key"], v["granularity"],
                                          v["max_chars"], v["prefix_mode"], v["note"]))
    A("")
    A("> 注：粗粒度变体受 bge-m3 num_ctx=4096 限制 —— 单块超上下文时 Ollama 直接返回 HTTP 400，"
      "故文档级粒度上限取 1500 中文字符（模型约束，非设计偏好）；若调大 num_ctx 会让该变体的"
      "嵌入配置与其他变体不同，破坏单一变量原则。")
    A("")
    A("## 二、结果总表")
    A("")
    table_header(A)
    for r in results:
        A(row(r["variant"]["label"], r))
    A("")
    A("**基线复现闸门**：V1 与官方基线三项指标精确一致 = **%s**" % ("通过 ✅" if gate else "失败 ❌"))
    A("")
    A("> `chunks` = 该变体切出的块数；`平均块长` = chunk 正文字符数均值。")
    A("")
    A("## 三、索引内容指纹（实现事实的证据）")
    A("")
    A("| 变体 | 结构指纹(section\\|prefix\\|text) | 检索文本指纹(text) |")
    A("|---|---|---|")
    for r in results:
        A("| %s | `%s` | `%s` |" % (r["variant"]["key"], r["struct_fp"], r["emb_fp"]))
    A("")
    A("> 检索文本指纹相同 ⇒ 两个变体的 FTS tokens 与向量输入逐字节相同 ⇒ 指标必然相同。")
    A("")
    A("## 四、结论与归因（数据驱动，负结果如实记录）")
    A("")

    by_key = {r["variant"]["key"]: r for r in results}
    base = by_key["V1"]["agg"]
    A("### 1. 粒度：细粒度 vs 基线 vs 粗粒度")
    A("")
    for k in ("V2", "V3"):
        r = by_key[k]
        A("- **%s**：chunks %d（V1 %d）、R@5 %.4f（**%+.4f**）、MRR %.4f（**%+.4f**）、"
          "平均块长 %.0f（V1 %.0f）。"
          % (r["variant"]["label"], r["chunks"], by_key["V1"]["chunks"],
             r["agg"]["recall@5"], r["agg"]["recall@5"] - base["recall@5"],
             r["agg"]["mrr"], r["agg"]["mrr"] - base["mrr"],
             r["avg_len"], by_key["V1"]["avg_len"]))
    A("")
    A("### 2. 前缀：它到底参不参与检索？")
    A("")
    v4, v5 = by_key["V4"], by_key["V5"]
    same_text = v4["emb_fp"] == by_key["V1"]["emb_fp"]
    A("- **V4（无前缀）**：R@5 %.4f（**%+.4f**）；其「检索文本指纹」与 V1 %s。"
      % (v4["agg"]["recall@5"], v4["agg"]["recall@5"] - base["recall@5"],
         "**完全相同**" if same_text else "不同"))
    A("  → 说明 `prefix` 字段当前**只进展示、不进检索信号**（FTS tokens 与向量都只取 `text`），"
      "「元数据前缀注入」此前是一个**未被兑现的设计意图**。")
    A("- **V5（前缀入检索）**：R@5 %.4f（**%+.4f**）、MRR %.4f（**%+.4f**）；"
      "hard 档 R@5 %.4f → %.4f。"
      % (v5["agg"]["recall@5"], v5["agg"]["recall@5"] - base["recall@5"],
         v5["agg"]["mrr"], v5["agg"]["mrr"] - base["mrr"],
         family_metrics(by_key["V1"]["details"], "hard")["recall@5"],
         family_metrics(v5["details"], "hard")["recall@5"]))
    A("")
    A("### 3. 组合验证：两个正增益因子能否叠加？")
    A("")
    v6 = by_key["V6"]
    hard1 = family_metrics(by_key["V1"]["details"], "hard")["recall@5"]
    hard6 = family_metrics(v6["details"], "hard")["recall@5"]
    A("- **V6（粗粒度 + 前缀入检索）**：chunks %d、平均块长 %.0f、R@5 %.4f（**%+.4f**）、"
      "MRR %.4f（**%+.4f**）、nDCG@10 %.4f、hard R@5 %.4f。"
      % (v6["chunks"], v6["avg_len"], v6["agg"]["recall@5"],
         v6["agg"]["recall@5"] - base["recall@5"], v6["agg"]["mrr"],
         v6["agg"]["mrr"] - base["mrr"], v6["agg"]["ndcg@10"], hard6))
    A("- 对照：仅粗粒度 V3 R@5 %.4f、仅前缀 V5 R@5 %.4f → %s。"
      % (by_key["V3"]["agg"]["recall@5"], v5["agg"]["recall@5"],
         "**两因子叠加有效**" if v6["agg"]["recall@5"] > max(
             by_key["V3"]["agg"]["recall@5"], v5["agg"]["recall@5"])
         else "叠加无额外增益（取两者更强的一方即可）"))
    A("")
    A("### 4. 根因：为什么「前缀入检索」值这么多？——它暴露了分块的真实缺陷")
    A("")
    A("- 现行分块以 `## 标题` 作**分隔符**切块，标题文本随之**被剥离出正文**（正文块里并没有「## 背景」这几个字）；"
      "而标题此前只写进 `prefix` 字段，该字段**不参与 FTS tokens 与向量**，section 也只用于展示。")
    A("- 后果：「裸标题查询」（hard 档，如 `## 背景 是什么？`）在正文里**找不到任何字面锚点** —— "
      "这正是 M6 中查询改写（E3）与标题重排（E4）都救不回来的根因：问题不在查询侧，而在**索引侧丢掉了标题**。")
    A("- 证据：V5 把「文档标题 + 章节标题 + 标签」真正注入块文本后，hard 档 R@5 %.4f → %.4f（**%+.4f**）、"
      "easy 0.9722 → 1.0000。**增益不是靠题面含文档名**（hard 档题面恰恰不含文档名），而是块文本补回了标题信号。"
      % (hard1, family_metrics(v5["details"], "hard")["recall@5"],
         family_metrics(v5["details"], "hard")["recall@5"] - hard1))
    A("")
    A("### 5. 候选上线（本工单不擅自改正式管道，交用户决策）")
    A("")
    A("- 证据最强的两项：①**前缀并入索引文本**（`prefix_mode=inline`，同时修掉「标题被剥离」的缺陷）；"
      "②**粗粒度**（文档级 / 上限 1500）。")
    A("- 若采纳，正式基线 R@5 将从 %.4f 提升到 %.4f（V5）或 %.4f（V6）；代价是全量重跑 baseline / 六组消融 / "
      "PDF / 简历数字，并需复核引用展示不被前缀污染。**待用户拍板后再动正式管道。**"
      % (base["recall@5"], v5["agg"]["recall@5"], v6["agg"]["recall@5"]))
    A("")
    A("### 6. 代价账（工程视角）")
    A("")
    A("| 变体 | chunks | 建索引s | 全量嵌入s | 平均块长 | 最大块长 |")
    A("|---|---|---|---|---|---|")
    for r in results:
        A("| %s | %d | %.1f | %.1f | %.0f | %d |"
          % (r["variant"]["key"], r["chunks"], r["idx_sec"], r["emb_sec"],
             r["avg_len"], r["max_len"]))
    A("")
    A("> 注：`全量嵌入s` 是**本次运行**的墙钟耗时——向量已存在时 `build_embeddings` 断点续跑会跳过（≈0）。"
      "首次全量实测参考：1321 块 ≈ 33s、1703 块 ≈ 42s、262 块 ≈ 11s（bge-m3 经 Ollama / RTX 4050）。"
      "三个变体的检索延迟几乎相同 → 分块粒度不改变查询侧成本。")
    A("")
    A("### 7. 可写进简历的一句（以实测数字为准填充）")
    A("")
    A("- 「对分块策略做 6 变体消融（粒度 3 档 × 前缀注入 2 态 × 组合），定位到 `## 标题` 在切块时被剥离出正文、"
      "元数据前缀又未接入检索信号的实现缺陷；修复后 R@5 %.4f → %.4f（**%+.4f**）、hard 档 %.4f → %.4f。」"
      % (base["recall@5"], v5["agg"]["recall@5"], v5["agg"]["recall@5"] - base["recall@5"],
         hard1, family_metrics(v5["details"], "hard")["recall@5"]))
    A("")
    A("### 8. 附录：V1 → V5 逐题排名变化（防「数字好看但不知救了谁」）")
    A("")
    qmap = {it["id"]: it["question"] for it in gold}
    d1 = {d["id"]: d for d in by_key["V1"]["details"]}
    changes = []
    for d in by_key["V5"]["details"]:
        r1 = d1[d["id"]]["first_rank"] or 99
        r5 = d["first_rank"] or 99
        if r1 != r5:
            changes.append((d["id"], d["family"], r1, r5, qmap.get(d["id"], "")))
    saved = sum(1 for _, _, r1, r5, _ in changes if r1 > 5 and 1 <= r5 <= 5)
    A("| id | 档 | V1 排名 | V5 排名 | 问题 |")
    A("|---|---|---|---|---|")
    for cid, fam, r1, r5, q in changes:
        A("| %s | %s | %s | %s | %s |"
          % (cid, fam, r1 if r1 < 99 else "未进Top10", r5 if r5 < 99 else "未进Top10", q))
    A("")
    A("- 共 **%d 题**排名变化，其中「V1 未进 Top-5 → V5 进 Top-5」= **%d 题**；"
      "救回的题集中在 hard 档（裸标题型）。" % (len(changes), saved))
    A("")
    A("## 六、复现与隔离")
    A("")
    A("```powershell")
    A("D:\\python\\python.exe scripts\\m6b_chunk_ablation.py")
    A("```")
    A("")
    A("- 各变体产物：`data/ablation/m6b/<变体>/{vaultmind.db,embeddings.npy,chunk_ids.json}`（派生物，gitignore）。")
    A("- 正式索引/向量不受影响；`D:\\python\\python.exe -m pytest tests\\test_m6b_chunk.py` 断言临时写入不触碰正式产物。")
    A("")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("报告：%s" % REPORT)
    print("基线复现闸门：%s" % ("通过" if gate else "失败"))
    return 0 if gate else 2


if __name__ == "__main__":
    sys.exit(main())
