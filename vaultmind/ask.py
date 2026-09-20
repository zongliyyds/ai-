# -*- coding: utf-8 -*-
r"""M4 问答 CLI：检索 → 上下文组装 [S#] → 本地生成 → 引用校验 → 拒答判定。

用法：
  D:\python\python.exe -m vaultmind.ask "问题" [--top 8] [--mode hybrid]
      [--model qwen2.5:7b-instruct] [--context-only] [--json]
"""
import argparse
import json
import sys

from vaultmind.llm.context import build_context
from vaultmind.llm.validator import is_refusal, validate_cites
from vaultmind.retrieval import search


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="VaultMind 带引用问答（M4 生成链路）")
    ap.add_argument("question", help="问题文本")
    ap.add_argument("--top", type=int, default=8, help="检索返回块数")
    ap.add_argument("--mode", default="bm25", choices=["bm25", "vector", "hybrid"])
    ap.add_argument("--model", default="qwen2.5:7b-instruct")
    ap.add_argument("--context-only", action="store_true", help="只预览组装后的上下文")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    hits = search(args.question, top_k=args.top, mode=args.mode)
    context, cites = build_context(hits)

    if args.context_only:
        print(context)
        print("\n# 引用清单")
        for c in cites:
            print("[S%d] %s ｜ %s" % (c.num, c.rel, c.section))
        return 0

    from vaultmind.llm.generator import generate
    answer, meta = generate(args.question, context, model=args.model)
    chk = validate_cites(answer, len(cites))
    refusal = is_refusal(answer)

    if args.json:
        out = {
            "question": args.question,
            "mode": args.mode,
            "top_k": args.top,
            "answer": answer,
            "citations": [
                {"num": c.num, "rel": c.rel, "title": c.title, "section": c.section}
                for c in cites],
            "validation": chk,
            "refusal": refusal,
            **meta,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    print("=" * 68)
    print(answer)
    print("=" * 68)
    print("# 引用清单（共 %d 块）" % len(cites))
    for c in cites:
        print("  [S%d] %s（%s）｜ %s" % (c.num, c.rel, c.title or c.rel, c.section or "-"))
    print("# 校验：引用 %s ｜ 非法编号 %s ｜ 拒答 %s ｜ 生成 %.1fs ｜ eval_count=%s" % (
        chk["cited_ids"], chk["invalid_ids"], refusal,
        meta["generation_s"], meta.get("eval_count")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
