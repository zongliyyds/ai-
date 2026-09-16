# -*- coding: utf-8 -*-
"""生成人类可读体检报告 reports/audit_report.md（只写工作区，不碰 Vault）。"""
import json
from datetime import datetime

from vaultmind.config import AUDIT_REPORT, BASELINE_JSON, VAULT_ROOT

PARITY_KEYS = ["doc_count", "total_chars", "body_chars", "total_h2", "total_h3",
               "outlink_total", "unresolved_links", "est_chunks_h2"]
LABELS = {
    "doc_count": "笔记数", "total_chars": "总字符", "body_chars": "正文字符",
    "total_h2": "H2 节数", "total_h3": "H3 节数",
    "outlink_total": "双链出链", "unresolved_links": "死链",
    "est_chunks_h2": "预估 chunk 数（H2+1/篇）",
}


def _md_table(headers, rows):
    lines = ["| " + " | ".join(str(h) for h in headers) + " |",
             "|" + "---|" * len(headers)]
    for r in rows:
        lines.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(lines)


def write_audit_report(metrics, stats=None):
    baseline = None
    if BASELINE_JSON.exists():
        try:
            baseline = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
        except Exception:
            baseline = None

    L = []
    A = L.append
    A("# VaultMind 知识库体检报告")
    A("")
    A("> 生成时间：%s ｜ 数据源（只读）：`%s` ｜ "
      "复现命令：`D:\\python\\python.exe -m vaultmind.ingest`"
      % (datetime.now().strftime("%Y-%m-%d %H:%M"), VAULT_ROOT))
    A("")

    A("## 1. 规模概览与基线对比")
    A("")
    if baseline:
        rows = []
        for k in PARITY_KEYS:
            b = baseline.get(k)
            ok = metrics[k] == b
            rows.append([LABELS[k], metrics[k], b, "✓ 一致" if ok else "✗ 不一致"])
        A(_md_table(["指标", "本次", "基线", "一致性"], rows))
        A("")
        A("> 出现 ✗ 时先确认 Vault 是否有新增/修改；无变化则回查审计口径（scripts/audit_baseline.py）。")
    else:
        A("（未找到基线文件 reports/baseline_audit.json，跳过对比）")
    A("")

    A("## 2. 类型分布")
    A("")
    A(_md_table(["type", "数量"], [[k, v] for k, v in metrics["by_type"].items()]))
    A("")

    A("## 3. 状态分布（治理点：completed 与 complete 混用）")
    A("")
    A(_md_table(["status", "数量"], [[k, v] for k, v in metrics["by_status"].items()]))
    A("")

    A("## 4. 顶层目录分布")
    A("")
    A(_md_table(["目录", "数量"], [[k, v] for k, v in metrics["by_top_folder"].items()]))
    A("")

    A("## 5. 图谱与链接健康")
    A("")
    A("- 出链总数 **%d**，其中死链 **%d**（死链率 %.1f%%）"
      % (metrics["outlink_total"], metrics["unresolved_links"],
         metrics["unresolved_links"] / max(1, metrics["outlink_total"]) * 100))
    A("- 孤儿笔记（无入链，排除 90-System/.obsidian）：**%d** 篇，Top-25（按体量）："
      % metrics.get("orphans_total", len(metrics["orphans"])))
    A("")
    for i, r in enumerate(metrics["orphans"], 1):
        A("%d. `%s`" % (i, r))
    A("")
    A("- 入链 Top 12：")
    A("")
    A(_md_table(["笔记", "入链数"], [[r, c] for r, c in metrics["top_inbound"]]))
    A("")

    A("## 6. 元数据治理")
    A("")
    A("- 无 frontmatter：**%d** 篇" % len(metrics["no_frontmatter"]))
    A("- 有 frontmatter 但缺 type：**%d** 篇" % len(metrics.get("frontmatter_no_type", [])))
    A("- 0 字节文件：**%d** 个：%s"
      % (len(metrics.get("zero_byte", [])),
         "、".join("`%s`" % r for r in metrics.get("zero_byte", [])) or "无"))
    A("")
    if metrics["no_frontmatter"]:
        A("无 frontmatter 清单：")
        A("")
        for r in metrics["no_frontmatter"]:
            A("- `%s`" % r)
        A("")

    A("## 7. 分块与索引（本次管道产出）")
    A("")
    if stats:
        A(_md_table(["指标", "值"], [
            ["docs 表行数", stats["docs"]],
            ["chunks 行数", stats["chunks"]],
            ["links 行数", stats["links"]],
            ["FTS5 索引行数", stats["fts_rows"]],
            ["索引库", "`%s`（%.1f KB）" % (stats["db_path"], stats["db_bytes"] / 1024)],
        ]))
        A("")
        A("> 分块口径：每篇 1 个「概述」chunk + 每个 H2 小节 1 个 chunk；"
          "超 %d 字的小节按 H3/段落二次切分；每个 chunk 注入元数据前缀。" % 600)
    else:
        A("（本次未构建索引）")
    A("")

    A("## 8. 体检结论与治理建议（只建议、不代改——Vault 由用户手动维护）")
    A("")
    zb = metrics.get("zero_byte", [])
    if zb:
        A("1. **清理 0 字节文件**：%s 没有任何内容，建议在 Obsidian 中直接删除。"
          % "、".join("`%s`" % r for r in zb))
    if metrics["by_status"].get("completed") and metrics["by_status"].get("complete"):
        A("2. **统一状态取值**：`completed`（%d）与 `complete`（%d）混用，"
          "建议全局统一为 `completed`。"
          % (metrics["by_status"]["completed"], metrics["by_status"]["complete"]))
    if metrics["no_frontmatter"]:
        A("3. **补齐 frontmatter**：%d 篇笔记缺 frontmatter，建议补 type/status/tags 三字段。"
          % len(metrics["no_frontmatter"]))
    if metrics["unresolved_links"]:
        A("4. **修复失效双链**：%d 条出链指向不存在的笔记（死链率 %.1f%%），"
          "建议逐一修复或删除。"
          % (metrics["unresolved_links"],
             metrics["unresolved_links"] / max(1, metrics["outlink_total"]) * 100))
    if metrics.get("orphans_total"):
        A("5. **孤儿笔记**：%d 篇无任何入链，建议在索引页（90-System/Indexes）补入口或并入相关主题。"
          % metrics["orphans_total"])
    A("")
    A("> 治理前后对比（覆盖率、死链率、孤儿数）将作为 AI 数据分析方向的可视化素材。")
    A("")

    AUDIT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")
    return str(AUDIT_REPORT)
