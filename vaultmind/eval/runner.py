# -*- coding: utf-8 -*-
"""评测 runner：读 gold 集 → 逐条跑检索 → 指标聚合 → reports/baseline.md。"""
import json
import time
from datetime import datetime
from pathlib import Path

from vaultmind.config import WORKSPACE
from vaultmind.eval.metrics import aggregate, first_rank
from vaultmind.retrieval import search

GOLD_PATH = WORKSPACE / "eval" / "gold_set.jsonl"
REPORT_PATH = WORKSPACE / "reports" / "baseline.md"


def load_gold(path=None, include_draft=False) -> list[dict]:
    path = path or GOLD_PATH
    items = []
    if Path(path).exists():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                items.append(json.loads(line))
    if not include_draft:
        items = [it for it in items if it.get("status", "draft") == "approved"]
    return items


def run_eval(gold, mode="bm25", top_k=10) -> tuple[list[dict], dict]:
    runs = []
    details = []
    for it in gold:
        t0 = time.perf_counter()
        hits = search(it["question"], top_k=top_k, mode=mode)
        lat = time.perf_counter() - t0
        pred = [h.rel for h in hits]
        true = it.get("docs", [])
        rank = first_rank(pred, true)
        runs.append((pred, true, lat))
        details.append({
            "id": it.get("id", ""),
            "question": it["question"],
            "docs": true,
            "first_rank": rank,
            "hit_in_top5": 1 <= rank <= 5,
            "top3": [h.rel for h in hits[:3]],
            "latency_s": round(lat, 3),
        })
    return details, aggregate(runs)


def write_report(details, metrics, mode="bm25", top_k=10, out=None) -> str:
    out = Path(out) if out else REPORT_PATH
    approved = len(details)
    L = []
    A = L.append
    A("# VaultMind 检索基线报告（baseline）")
    A("")
    A("> 生成时间：%s ｜ 检索模式：%s ｜ top_k=%d ｜ 口径：仅统计 status=approved 的 gold 条目"
      % (datetime.now().strftime("%Y-%m-%d %H:%M"), mode, top_k))
    A("")
    A("## 指标总表")
    A("")
    A("| 指标 | 值 |")
    A("|---|---|")
    A("| 查询数 | %d |" % metrics["num_queries"])
    A("| Recall@1 | %.4f |" % metrics["recall@1"])
    A("| Recall@5 | %.4f |" % metrics["recall@5"])
    A("| Recall@10 | %.4f |" % metrics["recall@10"])
    A("| MRR | %.4f |" % metrics["mrr"])
    A("| nDCG@10 | %.4f |" % metrics["ndcg@10"])
    A("| 平均延迟 | %.3f s |" % metrics["avg_latency_s"])
    A("")
    A("> 目标值（立项书 §七，先测基线再定稿数字）：Recall@5 ≥ 0.80，MRR ≥ 0.65，nDCG@10 ≥ 0.70。")
    A("")
    A("## 逐题明细")
    A("")
    A("| id | 问题 | 首中排名 | Top-5 命中 | Top-3 文档 | 延迟 |")
    A("|---|---|---|---|---|---|")
    for d in details:
        top3 = " / ".join(r.split("/")[-1].replace(".md", "") for r in d["top3"])
        A("| %s | %s | %s | %s | %s | %.3fs |" % (
            d["id"], d["question"], d["first_rank"] or "-",
            "✓" if d["hit_in_top5"] else "✗", top3, d["latency_s"]))
    A("")
    A("## 复现")
    A("")
    A("```powershell")
    A("D:\\python\\python.exe -m vaultmind.eval")
    A("```")
    A("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    # 机器可读真相源：/metrics 与 /badcases 从此读，不再反解析 Markdown（防格式耦合）
    json_path = Path(str(out)).with_suffix(".json")
    # 与 Markdown 表同精度（recall/mrr/ndcg 4 位、延迟 3 位），保证 JSON 与 md 数字逐位一致
    rounded = {}
    for k, v in metrics.items():
        if k == "avg_latency_s":
            rounded[k] = round(v, 3)
        elif isinstance(v, float):
            rounded[k] = round(v, 4)
        else:
            rounded[k] = v
    json_path.write_text(json.dumps({
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": mode,
        "top_k": top_k,
        "metrics": rounded,
        "details": details,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    return str(out)
