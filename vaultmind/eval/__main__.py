# -*- coding: utf-8 -*-
r"""评测 CLI：D:\python\python.exe -m vaultmind.eval [选项]

默认只评测 status=approved 的 gold 条目；--include-draft 预览草稿。
"""
import argparse
import sys

from vaultmind.eval.runner import load_gold, run_eval, write_report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="vaultmind.eval", description="VaultMind 检索评测")
    ap.add_argument("--include-draft", action="store_true",
                    help="把 status=draft 的条目也纳入（仅预览用）")
    ap.add_argument("--mode", default="bm25", choices=["bm25", "vector", "hybrid"])
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    gold = load_gold(include_draft=args.include_draft)
    if not gold:
        print("gold 集为空：请先在 eval/gold_set.jsonl 中定稿条目（status=approved）。", file=sys.stderr)
        return 2

    details, metrics = run_eval(gold, mode=args.mode, top_k=args.top)
    out = write_report(details, metrics, mode=args.mode, top_k=args.top, out=args.out)
    print("评测完成：%d 条 | Recall@5=%.4f | MRR=%.4f | nDCG@10=%.4f | 平均延迟 %.3fs" % (
        metrics["num_queries"], metrics["recall@5"], metrics["mrr"],
        metrics["ndcg@10"], metrics["avg_latency_s"]))
    print("报告：%s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
