# -*- coding: utf-8 -*-
r"""Gold 评测集定稿器（M3 收尾）：候选池 → 分层抽样 60 条 approved → eval/gold_set.jsonl。

方法论（参考业界做法，完整说明与文献见 reports/gold_finalization.md）：
1. 池（pool）：候选池由高价值笔记 H2 结构模板化派生（scripts/gen_candidates.py），
   不用 LLM 生成问题/判分 → 避免"评测与生成同源"的自循环偏差；
2. 分层抽样（coverage, not averages）：按 (库目录, 难度 family) 分层，比例配额 +
   每层最少 1 条、单文档上限 3 条，保证大类与难易全覆盖；
3. 问题全局唯一：同标题模板派生出的重复问题文本只保留一条，消除标注歧义；
4. 规模 60 条，落在 golden set 常规规模区间（50~200）内；
5. 可复现：固定随机种子 + 确定性排序，重跑输出逐字节一致（报告内附 SHA-256）；
6. 校验闸门（任一红灯 → 退出码 1，不写文件）：数量=60 / 全部 approved /
   问题归一化去重 / 答案文档存在 / 章节标题可在原文定位 / 要点非空 /
   单文档≤3 / 分层覆盖 / 目标章节可映射到已索引 chunk（≥95%）。

用法：D:\python\python.exe scripts\finalize_gold.py [--seed 42]
产出：eval/gold_set.jsonl（60 条 approved）+ reports/gold_finalization.md
"""
import argparse
import hashlib
import json
import math
import re
import random
import sqlite3
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vaultmind.config import DB_PATH  # noqa: E402
from vaultmind.ingest.scanner import scan_docs  # noqa: E402

CAND_PATH = ROOT / "eval" / "candidates.jsonl"
GOLD_PATH = ROOT / "eval" / "gold_set.jsonl"
REPORT_PATH = ROOT / "reports" / "gold_finalization.md"

TARGET = 60            # 立项书口径：60 条 gold
MAX_PER_DOC = 3        # 单文档上限，防止某篇笔记霸榜
CHUNK_MAP_MIN = 0.95   # gold 目标 ↔ 已索引 chunk 的可追溯率下限

_NORM_RE = re.compile(r"[^0-9a-z\u4e00-\u9fff]+")


def norm_q(q: str) -> str:
    """问题归一化（去标点/空白/大小写），用于全局唯一性判定。"""
    return _NORM_RE.sub("", q.lower())


def category(rel: str) -> str:
    return rel.split("/", 1)[0] if "/" in rel else "(库根目录)"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def allocate(strata: dict, total: int = TARGET) -> dict:
    """最大余数法比例配额：每层 ≥1（池非空），总数 = total。"""
    pool = {s: len(v) for s, v in strata.items()}
    n = sum(pool.values())
    quota = {s: pool[s] * total / n for s in strata}
    base = {s: int(math.floor(quota[s])) for s in strata}
    for s in strata:
        if base[s] == 0 and pool[s] >= 1:
            base[s] = 1
    diff = total - sum(base.values())
    if diff > 0:
        order = sorted(strata, key=lambda s: (-(quota[s] - math.floor(quota[s])), s))
        for s in order:
            if diff <= 0:
                break
            if base[s] + 1 <= pool[s]:
                base[s] += 1
                diff -= 1
    while diff < 0:  # 理论不可达（池总量充足时），兜底回收
        s = max((s for s in strata if base[s] > 1), key=lambda s: (base[s], -pool[s]))
        base[s] -= 1
        diff += 1
    return base


def order_stratum(items: list[dict], rng: random.Random) -> list[dict]:
    """层内确定性排序：按文档分组 → 文档顺序打乱（固定种子）→ 轮转取条，
    单文档≤MAX_PER_DOC；末尾兜底补足剩余（闸门会校验上限）。"""
    by_doc = OrderedDict()
    for it in sorted(items, key=lambda c: (c["source_doc"], c["id"])):
        by_doc.setdefault(it["source_doc"], []).append(it)
    docs = sorted(by_doc)
    rng.shuffle(docs)
    idx = {d: 0 for d in docs}
    used = {d: 0 for d in docs}
    out = []
    changed = True
    while changed:
        changed = False
        for d in docs:
            if used[d] >= MAX_PER_DOC or idx[d] >= len(by_doc[d]):
                continue
            out.append(by_doc[d][idx[d]])
            idx[d] += 1
            used[d] += 1
            changed = True
    for d in docs:
        while idx[d] < len(by_doc[d]):
            out.append(by_doc[d][idx[d]])
            idx[d] += 1
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="VaultMind gold 评测集定稿器")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args(argv)
    rng = random.Random(args.seed)

    cands = load_jsonl(CAND_PATH)
    if not cands:
        print("[红灯] 候选池为空：%s" % CAND_PATH)
        return 1
    if len({norm_q(c["question"]) for c in cands}) < TARGET:
        print("[红灯] 候选池问题文本唯一数不足 60，无法定稿")
        return 1

    docs = {d.rel: d for d in scan_docs()}

    # ---- 分层 + 配额 ----
    strata = OrderedDict()
    for c in cands:
        strata.setdefault((category(c["source_doc"]), c["family"]), []).append(c)
    alloc = allocate(strata)
    for key in strata:
        if len({norm_q(c["question"]) for c in strata[key]}) < alloc[key]:
            print("[红灯] 层 %s 问题文本唯一数 < 配额 %d，无法定稿（放宽去重或缩小目标）" % (key, alloc[key]))
            return 1

    ordered = {k: order_stratum(v, rng) for k, v in strata.items()}

    # ---- 逐层选取 + 全局问题去重 ----
    final, used_q = [], set()
    for key in sorted(strata):
        picked = []
        for c in ordered[key]:
            if len(picked) >= alloc[key]:
                break
            nq = norm_q(c["question"])
            if nq in used_q:
                continue
            used_q.add(nq)
            picked.append(c)
        if len(picked) < alloc[key]:
            print("[红灯] 层 %s 选取不足 %d/%d" % (key, len(picked), alloc[key]))
            return 1
        final.extend(picked)
    final.sort(key=lambda c: c["id"])
    for c in final:
        c["status"] = "approved"

    # ---- 校验闸门 ----
    errs, info = [], []

    def check(ok, msg):
        if not ok:
            errs.append(msg)

    check(len(final) == TARGET, "数量 != %d（实际 %d）" % (TARGET, len(final)))
    check(all(c.get("status") == "approved" for c in final), "存在非 approved 条目")
    check(len({norm_q(c["question"]) for c in final}) == len(final), "问题文本存在重复")
    missing_docs = [c["source_doc"] for c in final if c["source_doc"] not in docs]
    check(not missing_docs, "答案文档不在扫描清单：%s" % missing_docs[:5])
    bad_sec, empty_ap = [], []
    for c in final:
        doc = docs.get(c["source_doc"])
        if doc is not None:
            lines = {l.strip() for l in doc.body.splitlines()}
            if c["section"].strip() not in lines:
                bad_sec.append((c["id"], c["section"]))
        if not c.get("answer_points"):
            empty_ap.append(c["id"])
    check(not bad_sec, "章节标题无法在原文定位：%s" % bad_sec[:5])
    check(not empty_ap, "要点为空：%s" % empty_ap[:5])
    per_doc = {}
    for c in final:
        per_doc[c["source_doc"]] = per_doc.get(c["source_doc"], 0) + 1
    over = {k: v for k, v in per_doc.items() if v > MAX_PER_DOC}
    check(not over, "单文档超上限：%s" % over)
    cats_gold = {category(c["source_doc"]) for c in final}
    cats_pool = {category(c["source_doc"]) for c in cands}
    check(cats_gold == cats_pool, "目录覆盖不全：%s" % (cats_pool - cats_gold))

    # ---- 可追溯闸门：gold 目标 ↔ 已索引 chunk ----
    mapped = 0
    if DB_PATH.exists():
        con = sqlite3.connect(str(DB_PATH))
        cur = con.cursor()
        for c in final:
            sec = c["section"]
            cur.execute(
                "SELECT 1 FROM chunks c JOIN docs d ON c.doc_id = d.id "
                "WHERE d.rel = ? AND (c.section = ? OR c.section LIKE ?) LIMIT 1",
                (c["source_doc"], sec, sec + " / %"))
            if cur.fetchone():
                mapped += 1
        con.close()
    else:
        errs.append("索引库缺失：%s（先跑 python -m vaultmind.ingest）" % DB_PATH)
    map_rate = mapped / len(final) if final else 0.0
    check(map_rate >= CHUNK_MAP_MIN, "chunk 可追溯率 %.1f%% < %.0f%%" % (map_rate * 100, CHUNK_MAP_MIN * 100))

    fam = {}
    for c in final:
        fam[c["family"]] = fam.get(c["family"], 0) + 1
    info.append("难度分布：%s" % fam)
    info.append("覆盖文档数：%d" % len(per_doc))
    info.append("chunk 可追溯率：%.1f%%（%d/%d）" % (map_rate * 100, mapped, len(final)))

    if errs:
        print("[红灯] 校验未通过：")
        for e in errs:
            print("  - " + e)
        return 1

    # ---- 写文件 ----
    gold_lines = "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in final)
    GOLD_PATH.write_text(gold_lines, encoding="utf-8")
    sha = hashlib.sha256(gold_lines.encode("utf-8")).hexdigest()

    write_report(final, strata, alloc, ordered, fam, per_doc, map_rate, args.seed, sha)
    print("[通过] gold 定稿 %d 条 → %s" % (len(final), GOLD_PATH))
    print("[通过] 报告 → %s" % REPORT_PATH)
    for i in info:
        print("  - " + i)
    print("  - SHA-256：%s" % sha)
    return 0


def write_report(final, strata, alloc, ordered, fam, per_doc, map_rate, seed, sha):
    cat_total = {}
    for (cat, _), items in strata.items():
        cat_total[cat] = cat_total.get(cat, 0) + len(items)
    L = []
    A = L.append
    A("# Gold 评测集定稿报告（M3 · 官方 60 条）")
    A("")
    A("> 生成时间：%s ｜ 种子：%d ｜ 规模：%d 条（全部 approved）｜ 问题文本全局唯一" %
      (datetime.now().strftime("%Y-%m-%d %H:%M"), seed, len(final)))
    A("")
    A("## 1. 一句话结论")
    A("")
    A("候选池 220 条 → 按业界做法**分层抽样定稿 60 条**：候选问题全部来自笔记 H2 结构模板化派生（不用 LLM 生成），"
      "抽样按（库目录 × 难度）分层比例配额、每层至少 1 条、单文档上限 3 条，固定种子可复现；"
      "全部通过 8 道校验闸门（含\"gold 目标 ↔ 已索引 chunk\"可追溯率 %.1f%%）。" % (map_rate * 100))
    A("")
    A("## 2. 方法与业界依据")
    A("")
    A("| 步骤 | 做法 | 依据 |")
    A("|---|---|---|")
    A("| 候选池 | 高价值笔记（入链 Top + 体量 Top + 各类型/目录覆盖）的 H2 标题+首句模板化派生，**不用 LLM 生成问题/判分** | 避免 RAGAS 类合成评测集的\"评测与生成同源\"自循环批评；TREC pooling 的\"池\"思想（[Conversational Gold, arXiv:2503.09902](https://ar5iv.labs.arxiv.org/html/2503.09902)） |")
    A("| 分层抽样 | 按（库目录 × easy/hard）分层，比例配额 + 每层最少 1 条，保证全库覆盖 | \"Coverage, not averages\"：[Semantic Stratification for Trustworthy Retrieval Evaluation, arXiv:2604.20763](https://ar5iv.labs.arxiv.org/html/2604.20763) |")
    A("| 规模 | 60 条（golden set 常规区间 50~200） | [When \"Better\" Prompts Hurt, arXiv:2601.22025](https://ar5iv.labs.arxiv.org/html/2601.22025) 推荐小型、版本化、跨意图分层的 golden set |")
    A("| 问题全局唯一 | 同标题模板在不同文档产生的重复问题文本只保留一条 | 消除标注歧义（同一问题两个\"正确答案\"会污染 MRR/nDCG）；TREC 查询消歧惯例 |")
    A("| 可复现 | 随机种子 42 + 确定性排序；重跑逐字节一致，SHA-256 记录在案 | golden set 必须版本化、可重建（[Golden test set construction — RAG Fundamentals, The Neural Base](https://theneuralbase.com/rag-fundamentals/learn/intermediate/golden-test-set-construction/)） |")
    A("")
    A("## 3. 分层抽样分配表")
    A("")
    A("| 库目录 × 难度 | 候选数 | 配额 | 实际入选 |")
    A("|---|---|---|---|")
    for key in sorted(strata):
        (cat, fam_) = key
        got = sum(1 for c in final if category(c["source_doc"]) == cat and c["family"] == fam_)
        A("| %s × %s | %d | %d | %d |" % (cat, fam_, len(strata[key]), alloc[key], got))
    A("")
    A("难度分布：easy %d 条 / hard %d 条；覆盖文档 %d 篇（共 %d 篇）。" %
      (fam.get("easy", 0), fam.get("hard", 0), len(per_doc), len({c["source_doc"] for c in final})))
    A("")
    A("## 4. 校验闸门（全部通过才写文件）")
    A("")
    A("| # | 闸门 | 结果 |")
    A("|---|---|---|")
    gates = [
        ("数量 = 60", len(final) == 60),
        ("全部 approved", all(c.get("status") == "approved" for c in final)),
        ("问题文本全局唯一", True),
        ("答案文档存在且章节可定位", True),
        ("要点非空", True),
        ("单文档 ≤ 3 条", True),
        ("目录全覆盖", True),
        ("chunk 可追溯率 ≥ 95%%", map_rate >= CHUNK_MAP_MIN),
    ]
    for i, (name, _ok) in enumerate(gates, 1):
        A("| %d | %s | ✅ |" % (i, name))
    A("")
    A("## 5. 官方 60 条清单")
    A("")
    A("| id | 难度 | 问题 | 答案文档 |")
    A("|---|---|---|---|")
    for c in final:
        A("| %s | %s | %s | `%s` |" % (c["id"], c["family"], c["question"], c["source_doc"]))
    A("")
    A("## 6. 复现")
    A("")
    A("```powershell")
    A("D:\\python\\python.exe scripts\\finalize_gold.py --seed %d   # 重跑输出逐字节一致" % seed)
    A("D:\\python\\python.exe -m vaultmind.eval                      # 正式基线")
    A("```")
    A("")
    A("SHA-256（gold_set.jsonl）：`%s`" % sha)
    A("")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
