# -*- coding: utf-8 -*-
r"""CLI 入口：D:\python\python.exe -m vaultmind.ingest [--audit-only] [--vault 路径]"""
import argparse
import sys

from vaultmind.ingest import run_audit_only, run_pipeline


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="vaultmind.ingest",
        description="VaultMind M1 数据管道：扫描→体检→分块→索引→报告（对 Vault 只读）")
    ap.add_argument("--audit-only", action="store_true",
                    help="只跑体检，不重建索引")
    ap.add_argument("--vault", default=None,
                    help="覆盖知识库根目录（默认取配置/环境变量）")
    args = ap.parse_args(argv)

    if args.audit_only:
        m = run_audit_only(args.vault)
        print("体检完成：%d 篇笔记 / %d 字符 / %d H2 / %d 出链 / %d 死链" % (
            m["doc_count"], m["total_chars"], m["total_h2"],
            m["outlink_total"], m["unresolved_links"]))
        return 0

    res = run_pipeline(root=args.vault)
    m, s = res["metrics"], res["stats"]
    print("=" * 62)
    print("VaultMind 数据管道完成")
    print("  笔记 %d 篇 | 总字符 %d | H2 %d | 出链 %d（死链 %d）" % (
        m["doc_count"], m["total_chars"], m["total_h2"],
        m["outlink_total"], m["unresolved_links"]))
    print("  chunks %d | links %d | FTS5 %d 行" % (s["chunks"], s["links"], s["fts_rows"]))
    print("  索引库：%s" % s["db_path"])
    print("  体检报告：D:\\RAG\\reports\\audit_report.md")
    print("  耗时 %.1fs" % m["elapsed_sec"])
    print("=" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main())
