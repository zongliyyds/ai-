# -*- coding: utf-8 -*-
r"""检索调试 CLI：D:\python\python.exe -m vaultmind.search "问题" [选项]

选项：
  --top N          返回条数（默认 5）
  --mode MODE      bm25 / vector / hybrid（默认 hybrid）
  --build-vectors  全量构建/续跑向量索引后退出
  --limit N        --build-vectors 时只处理前 N 个 chunk（调试用）
"""
import argparse
import sys

from vaultmind import retrieval
from vaultmind.retrieval import vector


def _print_hits(query, hits):
    print("=" * 78)
    print("查询：%s" % query)
    print("-" * 78)
    for i, h in enumerate(hits, 1):
        print("%2d. [chunk#%d] score=%s source=%s" % (i, h.chunk_id, h.score, h.source))
        print("    文档：%s" % h.rel)
        print("    章节：%s" % h.section)
        print("    摘要：%s" % h.text[:100].replace("\n", " "))
    if not hits:
        print("（无命中）")
    print("=" * 78)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="vaultmind.search", description="VaultMind 检索调试工具")
    ap.add_argument("query", nargs="?", default="", help="查询问题")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--mode", default="hybrid", choices=["bm25", "vector", "hybrid"])
    ap.add_argument("--build-vectors", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)

    if args.build_vectors:
        stats = vector.build_embeddings(resume=True, limit=args.limit)
        print("向量索引就绪：%d/%d chunks，维度 %d" % (
            stats["embedded"], stats["total_chunks"], stats["dim"]))
        print("  %s" % stats["npy"])
        return 0

    if not args.query:
        ap.error("请提供查询内容，或使用 --build-vectors 构建向量索引")

    try:
        hits = retrieval.search(args.query, top_k=args.top, mode=args.mode)
    except vector.VectorIndexMissing as e:
        print("错误：%s" % e, file=sys.stderr)
        return 2
    _print_hits(args.query, hits)
    return 0


if __name__ == "__main__":
    sys.exit(main())
