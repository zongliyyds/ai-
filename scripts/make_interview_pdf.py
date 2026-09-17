# -*- coding: utf-8 -*-
r"""生成《VaultMind 面试答辩手册》PDF（M7 终期交付物）。

实现说明（本机 PyMuPDF 1.27.2.3 已验证的坑位规避）：
- 文本走 TextWriter + fitz.Font(msyh.ttc)（insert_text 对 .ttc 有 bug）；
- 每页图形（标题条/页脚线/表格底纹）先全部画完，再逐页 write_text
  （write_text 会使其余已存在页面句柄失效，但最终 save 不受影响）；
- 页脚含总页数 → 两遍渲染：第一遍数页数，第二遍带页码正式保存。
用法：D:\python\python.exe scripts\make_interview_pdf.py → docs\面试答辩手册.pdf
"""
import os
import subprocess
import sys

import fitz

OUT = r"D:\RAG\docs\面试答辩手册.pdf"
FONT_CANDIDATES = [r"C:\Windows\Fonts\msyh.ttc",
                   r"C:\Windows\Fonts\simhei.ttf",
                   r"C:\Windows\Fonts\simsun.ttc"]

W, H = 595.28, 841.89
ML, MR, MT, MB = 56, 56, 64, 56
CW = W - ML - MR

ACCENT = (0.09, 0.40, 0.72)
DARK = (0.13, 0.16, 0.22)
GRAY = (0.45, 0.48, 0.53)
LIGHT = (0.93, 0.95, 0.98)
OK = (0.13, 0.62, 0.32)
LINE = (0.80, 0.84, 0.90)

_font = None
for fp in FONT_CANDIDATES:
    if os.path.exists(fp):
        try:
            _font = fitz.Font(fontfile=fp)
            break
        except Exception:
            continue
if _font is None:
    raise RuntimeError("未找到可用中文字体")


def git_short():
    r = subprocess.run(["git", "-C", r"D:\RAG", "rev-parse", "--short", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else "?"


def _load_anchors():
    """锚点全部从 reports/ + 索引库现场取数，不手抄数字（防重锚定后 PDF 与报告脱节）。"""
    import json
    import re as _re
    import sqlite3

    ws = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    m = {}
    base_md = os.path.join(ws, "reports", "baseline.md")
    if os.path.exists(base_md):
        with open(base_md, encoding="utf-8") as f:
            for line in f:
                mm = _re.match(r"\|\s*(Recall@\d+|MRR|nDCG@10)\s*\|\s*([0-9.]+)\s*\|", line)
                if mm:
                    m[mm.group(1).lower()] = mm.group(2)
                mm = _re.match(r"\|\s*平均延迟\s*\|\s*([0-9.]+)\s*s\s*\|", line)
                if mm:
                    m["latency"] = mm.group(1)

    audit = {}
    aj = os.path.join(ws, "reports", "baseline_audit.json")
    if os.path.exists(aj):
        with open(aj, encoding="utf-8") as f:
            audit = json.load(f)

    try:
        con = sqlite3.connect(os.path.join(ws, "data", "vaultmind.db"))
        m["docs"], m["chunks"], m["links"] = con.execute(
            "SELECT (SELECT COUNT(*) FROM docs),(SELECT COUNT(*) FROM chunks),"
            "(SELECT COUNT(*) FROM links)").fetchone()
        con.close()
    except Exception:
        m.setdefault("docs", "?"), m.setdefault("chunks", "?"), m.setdefault("links", "?")
    return m, audit


ANCHOR, AUDIT = _load_anchors()


def _load_ablation():
    """从 reports/ablation.md 现场解析全部消融数字（三路/分层/RRF k/改写/1-hop/规模）。

    目的是让 PDF 与报告同源：报告重跑后 PDF 重新生成即自动跟随，不再手抄。
    """
    import re as _re

    ws = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    abl = os.path.join(ws, "reports", "ablation.md")
    out = {}
    if not os.path.exists(abl):
        return out
    section = None
    with open(abl, encoding="utf-8") as f:
        for line in f:
            if line.startswith("## "):
                section = line[3:5]
                continue
            if not line.startswith("| "):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            # E6 规模-延迟表只有 4 列，需先单独处理（否则会被下面的列数检查跳过）
            if section == "E6" and len(cells) == 4 and cells[0] in ("25%", "50%", "100%"):
                try:
                    out.setdefault("e6", {})[cells[0]] = float(cells[2])
                except ValueError:
                    pass
                continue
            if len(cells) < 6 or cells[0] in ("变体", "---"):
                continue
            try:
                r5, mrr = float(cells[1]), float(cells[2])
            except ValueError:
                continue
            label = cells[0]
            # 只在 E1 段取 hybrid 的分层值：总览表里同名 hybrid 行会覆盖（曾致误读）
            if label == "hybrid" and section == "E1":
                mh = _re.match(r"([0-9.]+)\((\d+)\)", cells[-2])
                me = _re.match(r"([0-9.]+)\((\d+)\)", cells[-1])
                if mh:
                    out.setdefault("fam", {})["hard"] = (float(mh.group(1)), int(mh.group(2)))
                if me:
                    out.setdefault("fam", {})["easy"] = (float(me.group(1)), int(me.group(2)))
            if section == "E1" and label in ("bm25", "vector", "hybrid"):
                out.setdefault("e1", {})[label] = (r5, mrr, float(cells[4]))
            elif section == "E2" and label.startswith("k="):
                out.setdefault("k_mrrs", {})[label] = mrr
            elif section == "E3":
                out.setdefault("rewrite", {})[label] = r5
            elif section == "E5" and label.startswith("hybrid+1hop"):
                out.setdefault("hop", {})["r5"] = r5
            elif section == "E6" and label in ("25%", "50%", "100%"):
                try:
                    out.setdefault("e6", {})[label] = float(cells[2])
                except ValueError:
                    pass

    e1 = out.get("e1", {})
    fam = out.setdefault("fam", {})
    if {"bm25", "vector", "hybrid"} <= set(e1):
        h = e1["hybrid"][0]
        fam["recall@5"] = h
        fam["recall@1"] = e1["hybrid"][2]
        fam["vrecall@1"] = e1["vector"][2]
        fam["gain"] = h - max(e1["bm25"][0], e1["vector"][0])
        fam["top_dilution"] = e1["hybrid"][2] - e1["vector"][2]
    km = list(out.get("k_mrrs", {}).values())
    fam["k_range"] = (max(km) - min(km)) if len(km) >= 2 else 0.0
    rw = out.get("rewrite", {})
    fam["rew_r"] = rw.get("规则改写", fam.get("recall@5", 0.0)) - fam.get("recall@5", 0.0)
    fam["rew_l"] = rw.get("LLM 改写", fam.get("recall@5", 0.0)) - fam.get("recall@5", 0.0)
    fam["hop"] = out.get("hop", {}).get("r5", fam.get("recall@5", 0.0)) - fam.get("recall@5", 0.0)
    e6 = out.get("e6", {})
    fam["v25"] = e6.get("25%", 0.0)
    fam["v100"] = e6.get("100%", 0.0)
    return out


def _load_m6b():
    """从 reports/m6b_chunk_ablation.md 现场解析 6 变体指标（防手抄漂移）。"""
    import re as _re

    ws = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(ws, "reports", "m6b_chunk_ablation.md")
    out = {}
    if not os.path.exists(path):
        return out
    pat = _re.compile(
        r"\|\s*(V\d)[^|]*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([0-9.]+)\s*\|\s*"
        r"([0-9.]+)\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)\s*\|\s*([0-9.]+)\s*\|")
    with open(path, encoding="utf-8") as f:
        for line in f:
            mm = pat.match(line)
            if mm:
                out[mm.group(1)] = {
                    "chunks": int(mm.group(2)), "avglen": int(mm.group(3)),
                    "r5": float(mm.group(5)), "mrr": float(mm.group(7)),
                    "ndcg": float(mm.group(8)),
                }
    return out


ABL = _load_ablation()
FAMILY = ABL.get("fam", {})
M6B = _load_m6b()
M6B_LABEL = {"V1": "V1 基线 h2/600", "V2": "V2 细粒度 h3/300",
             "V3": "V3 粗粒度 整篇/1500", "V4": "V4 无前缀（对照）",
             "V5": "V5 前缀入检索", "V6": "V6 组合 粗+前缀"}
GIT = git_short()


def measure(text, size):
    return _font.text_length(text, fontsize=size)


def wrap(text, size, max_w):
    """按字符贪心折行（中英混排）。"""
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        if measure(cur + ch, size) > max_w and cur:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


class Builder:
    def __init__(self, total=None):
        self.doc = fitz.open()
        self.total = total
        self.y = MT
        self.page = None
        self.writers = {}  # page_index -> TextWriter

    # ---- 基础 ----
    def new_page(self):
        self.page = self.doc.new_page(width=W, height=H)
        idx = len(self.doc) - 1
        # TextWriter.append 不支持 color → 每页按颜色维护多个 writer（本机已验证）
        self.writers[idx] = {}
        # 页脚线（图形先行）
        self.page.draw_line((ML, H - 40), (W - MR, H - 40),
                            color=LINE, width=0.6)
        self.y = MT
        return idx

    def _writer(self, color):
        wdict = self.writers[len(self.doc) - 1]
        if color not in wdict:
            wdict[color] = fitz.TextWriter(self.page.rect)
        return wdict[color]

    def text(self, s, size=10.5, color=DARK, bold=False, x=None, y=None,
             max_w=None):
        x = ML if x is None else x
        y = self.y if y is None else y
        max_w = CW if max_w is None else max_w
        writer = self._writer(color)
        for i, line in enumerate(wrap(s, size, max_w)):
            writer.append((x, y + i * (size + 4)), line,
                          font=_font, fontsize=size)
        self.y = y + len(wrap(s, size, max_w)) * (size + 4)
        return self.y

    def space(self, dy=8):
        self.y += dy

    def need(self, dy):
        if self.y + dy > H - 52:
            self.new_page()

    def heading(self, s, level=1):
        if level == 1:
            self.need(46)
            self.space(6)
            idx = len(self.doc) - 1
            self.page.draw_rect(fitz.Rect(ML, self.y, ML + 3.2, self.y + 15),
                                color=ACCENT, fill=ACCENT)
            self.text(s, size=14.5, color=ACCENT, bold=True, x=ML + 10)
            self.space(6)
        else:
            self.need(30)
            self.space(4)
            self.text(s, size=12, color=DARK, bold=True)
            self.space(2)

    def bullets(self, items, size=10.5):
        for it in items:
            self.need(20)
            self.text("•  " + it, size=size)
            self.space(2)

    def table(self, header, rows, widths, size=9.5):
        self.need(18 + 18 * (len(rows) + 1))
        x = ML
        top = self.y
        hh = 16
        # 表头底纹
        self.page.draw_rect(fitz.Rect(ML, top, W - MR, top + hh),
                            color=LIGHT, fill=LIGHT)
        for i, h in enumerate(header):
            self.text(h, size=size, color=DARK, bold=True,
                      x=x + 3, y=top + 4, max_w=widths[i] - 6)
            x += widths[i]
        self.y = top + hh
        for r in rows:
            self.need(hh + 2)
            y0 = self.y
            self.page.draw_line((ML, y0 + hh), (W - MR, y0 + hh),
                                color=LINE, width=0.5)
            x = ML
            for i, cell in enumerate(r):
                self.text(str(cell), size=size, x=x + 3, y=y0 + 4,
                          max_w=widths[i] - 6)
                x += widths[i]
            self.y = y0 + hh
        self.space(6)

    def finish(self):
        # 图形已全部就位 → 逐页写文本（每页多颜色 writer 依次写入）
        for idx in range(len(self.doc)):
            pg = self.doc[idx]
            if self.total:
                self._writer_on(idx, GRAY).append(
                    (ML, H - 34), "VaultMind 面试答辩手册 · %d / %d" % (idx + 1, self.total),
                    font=_font, fontsize=8.5)
                self._writer_on(idx, GRAY).append(
                    (W - MR - measure("git %s" % GIT, 8.5), H - 34),
                    "git %s" % GIT, font=_font, fontsize=8.5)
            for writer in self.writers[idx].values():
                writer.write_text(pg)
        return self.doc

    def _writer_on(self, idx, color):
        if color not in self.writers[idx]:
            self.writers[idx][color] = fitz.TextWriter(self.doc[idx].rect)
        return self.writers[idx][color]


def build(total=None) -> fitz.Document:
    b = Builder(total)
    widths = [100, 90, 80, 90, 123.28]
    # ---- 封面 ----
    b.new_page()
    b.space(180)
    b.text("VaultMind", size=40, color=ACCENT, bold=True)
    b.text("个人知识库 RAG 问答与评测系统", size=20, color=DARK, bold=True)
    b.space(10)
    b.text("面 试 答 辩 手 册", size=30, color=ACCENT, bold=True)
    b.space(26)
    b.text("%s 篇笔记 / %.1f 万字 / %s 条双链 → 可问答 · 可评测 · 可复现"
           % (AUDIT.get("doc_count", "?"), AUDIT.get("total_chars", 0) / 10000.0,
              AUDIT.get("outlink_total", "?")), size=12, color=GRAY)
    b.text("零 LangChain · 零 torch · 零向量数据库", size=12, color=GRAY)
    b.space(40)
    b.text("指标：Recall@5 = %s · MRR = %s · nDCG@10 = %s（三项达标）"
           % (ANCHOR.get("recall@5"), ANCHOR.get("mrr"), ANCHOR.get("ndcg@10")),
           size=12, color=DARK, bold=True)
    b.text("git %s · 2026-09 · 面向 AI 应用开发 + AI 数据分析双方向求职" % GIT,
           size=10.5, color=GRAY)

    # ---- 1 指标 ----
    b.new_page()
    b.heading("1 · 指标总览（60 条 gold 评测集 · hybrid 检索 · 全部可复现）")
    b.table(
        ["指标", "基线值", "目标", "判定", "出处"],
        [["Recall@1", ANCHOR.get("recall@1"), "—", "—", "reports/baseline.md"],
         ["Recall@5", ANCHOR.get("recall@5"), "≥ 0.80", "✅ 达标", "reports/baseline.md"],
         ["Recall@10", ANCHOR.get("recall@10"), "—", "—", "reports/baseline.md"],
         ["MRR", ANCHOR.get("mrr"), "≥ 0.65", "✅ 达标", "reports/baseline.md"],
         ["nDCG@10", ANCHOR.get("ndcg@10"), "≥ 0.70", "✅ 达标", "reports/baseline.md"],
         ["平均延迟", "%s s" % ANCHOR.get("latency"), "—", "—", "reports/baseline.md"],
         ["引用可追溯", "非法引用 = 0", "100%", "✅", "reports/m4_smoke.md"],
         ["超纲拒答", "2/2 探针", "拒答", "✅", "reports/m4_smoke.md"],
         ["消融实验", "6 组 × 60 gold", "基线闸门", "✅", "reports/ablation.md"]],
        widths)
    b.space(4)
    b.text("复现：python -m vaultmind.eval（基线）｜ python scripts\\m6_ablation.py（消融）"
           "｜ python scripts\\m6b_chunk_ablation.py（分块粒度消融）",
           size=9.5, color=GRAY)

    # ---- 2 架构 ----
    b.new_page()
    b.heading("2 · 系统架构（四层管线）")
    arch = [
        "① 数据管道：Obsidian 源库(只读) → 扫描/体检 → 结构感知分块（H2 单元、超 600 字二切、",
        "            [文档|章节|标签] 前缀注入）→ SQLite(docs=%s/chunks=%s/links=%s) + FTS5(jieba)"
        % (ANCHOR.get("docs"), ANCHOR.get("chunks"), ANCHOR.get("links")),
        "② 检索层：BM25(FTS5) + bge-m3 向量(numpy 暴力 cosine) → RRF 融合(k=60)",
        "③ 生成层：[S#] 编号上下文(≤2块/文档, 6000字符预算) → qwen2.5:7b 本地生成",
        "            → 引用校验(编号∈1..n) + 超纲拒答(话术规则双层)",
        "④ 产品层：FastAPI(/ask /search /stats /metrics /badcases /feedback) + 零依赖 Web",
        "            问答页/看板；引用 obsidian:// 跳回原笔记；qa_logs 四分类归因",
    ]
    for line in arch:
        b.need(18)
        b.text(line, size=9.5)
    b.space(6)
    b.heading("核心设计决策", level=2)
    b.bullets([
        "结构感知分块：一块三用（引用溯源 / 语义上下文 / 评测可追溯）",
        "混合检索：消融验证融合 R@5 %+.2f 正增益；RRF k 参数不敏感" % FAMILY.get("gain", 0.0),
        "评测集防自欺：候选不用 LLM 生成，分层抽样定稿，seed=42 重跑逐字节一致",
        "引用 100% 可追溯：提示词约束 + 规则校验双层（4 种格式变异探针全覆盖）",
    ])

    # ---- 3 消融 ----
    b.new_page()
    b.heading("3 · 六组消融（每个组件增益量化，负结果如实记录）")
    b.table(
        ["实验", "关键结果", "结论"],
        [["三路单拆", "B/V/H = %.4f / %.4f / %.4f；R@1 融合 %.4f < 向量 %.4f"
          % (ABL.get("e1", {}).get("bm25", (0.0,) * 3)[0],
             ABL.get("e1", {}).get("vector", (0.0,) * 3)[0],
             FAMILY.get("recall@5", 0.0),
             FAMILY.get("recall@1", 0.0), FAMILY.get("vrecall@1", 0.0)),
          "融合 R@5 正增益 %+.4f；量化「顶部稀释」" % FAMILY.get("gain", 0.0)],
         ["RRF k=20/60/100", "R@5 恒 %.4f，MRR 极差 %.4f"
          % (FAMILY.get("recall@5", 0.0), FAMILY.get("k_range", 0.0)), "参数不敏感，无需调参"],
         ["查询改写", "规则 %+.3f / LLM %+.3f；hard 档一路降"
          % (FAMILY.get("rew_r", 0.0), FAMILY.get("rew_l", 0.0)), "负结果：不上线"],
         ["标题加权重排", "easy %.4f / hard %.4f"
          % (FAMILY.get("easy", (0.0, 0))[0], FAMILY.get("hard", (0.0, 0))[0]),
          "分层撕裂：需条件化"],
         ["双链 1-hop 扩展", "R@5 %+.4f" % FAMILY.get("hop", 0.0), "中性：转「相关笔记推荐」"],
         ["规模-延迟曲线", "25%%→100%% 语料 %.0f→%.0f ms；点积 <1ms"
          % (FAMILY.get("v25", 0.0), FAMILY.get("v100", 0.0)), "零向量库决策被验证"]],
        [110, 250, 123.28], size=9)
    b.space(4)
    b.text("坏例账本：11 题未进 Top-5（10 题裸标题型）；easy 档 %.0f%% / hard 档 %.0f%% → 分层归因。"
           % (FAMILY["easy"][0] * 100, FAMILY["hard"][0] * 100),
           size=10, color=DARK, bold=True)

    # ---- 3b 分块粒度消融（M6b） ----
    if M6B:
        b.new_page()
        b.heading("3b · 分块粒度消融（M6b：查出「标题被剥离 + 前缀没进检索」）")
        rows = []
        for k in sorted(M6B):
            m = M6B[k]
            rows.append([M6B_LABEL.get(k, k), "%d 块 / %d 字" % (m["chunks"], m["avglen"]),
                         "%.4f" % m["r5"], "%.4f" % m["mrr"], "%.4f" % m["ndcg"]])
        b.table(["变体（分块策略）", "规模", "R@5", "MRR", "nDCG@10"],
                rows, [200, 108, 55, 55, 65.28], size=9)
        b.space(6)
        v1 = M6B.get("V1")
        v5 = M6B.get("V5")
        v6 = M6B.get("V6", v1)
        if v1 and v5 and M6B.get("V2") and M6B.get("V3"):
            b.text("结论：细粒度 %.4f（%+.4f）｜粗粒度 %.4f（%+.4f）｜前缀入检索 %.4f（%+.4f）｜"
                   "组合 %.4f 不叠加 → 最优是 V5「前缀入检索」。"
                   % (M6B["V2"]["r5"], M6B["V2"]["r5"] - v1["r5"],
                      M6B["V3"]["r5"], M6B["V3"]["r5"] - v1["r5"],
                      v5["r5"], v5["r5"] - v1["r5"], v6["r5"]),
                   size=10, color=DARK, bold=True)
            b.space(4)
        b.text("根因（本轮最重要产出）：切块拿「## 标题」当分隔符，标题文本被剥离出正文；"
               "而标题只写进不参与 FTS/向量检索的 prefix 字段 → 裸标题查询在正文里没有任何字面锚点。"
               "这正是上一轮「查询改写」「标题重排」都救不回来的真因：问题不在查询侧，而在索引侧丢了标题。",
               size=10)
        b.space(4)
        b.text("铁证：V1（前缀进字段）与 V4（无前缀）的「检索文本指纹」完全相同 → 前缀此前对检索零贡献。"
               "正式基线未改动（仍为 %s），V5 属候选改进，待拍板。"
               % ANCHOR.get("recall@5", "-"), size=10, color=GRAY)

    # ---- 4 高频 Q&A ----
    b.new_page()
    b.heading("4 · 高频面试问题与答法（节选，全文见 docs/Q&A预案.md）")
    qa = [
        ("Q 为什么不用 LangChain / 向量库 / torch？",
         "A 数据规模决定架构：%s chunks × 1024 维点积实测 <1ms，向量库是过度设计；"
         "自写管道每个环节可解释、可改动；面试能讲清原理。"
         % format(ANCHOR.get("chunks", 0), ",")),
        ("Q 评测集可信吗？",
         "A 三道防线：候选只用笔记结构模板化派生（不用 LLM 生成问题）；分层抽样定稿 "
         "seed=42 可复现 + SHA-256；每条 gold 目标必须映射回已索引 chunk（实测 100%）。"),
        ("Q 引用可追溯怎么保证？LLM 编造怎么办？",
         "A 提示词约束 + 规则校验双层：引用编号必须落在上下文 1..n；实测模型有 4 种格式"
         "变异（列表式等），解析器宽容 + 探针全覆盖；超纲 2/2 拒答。"),
        ("Q 坏例怎么处理？",
         "A 先分层归因（easy %.0f%% / hard %.0f%%，主因=裸标题查询），再消融验证方案：改写与 "
         "1-hop 被数据否决，标题重排需条件化——不是所有坏例都要修，先算账。"
         % (FAMILY.get("easy", (0.0, 0))[0] * 100, FAMILY.get("hard", (0.0, 0))[0] * 100)),
        ("Q 最难的三个坑？",
         "A 评测集防自欺、LLM 输出格式不稳定、Windows 环境工程（全路径/编码/服务掉线/"
         "bat 端口秒退）——全部沉淀成知识卡片。"),
    ]
    for q, a in qa:
        b.need(60)
        b.text(q, size=10.5, color=ACCENT, bold=True)
        b.space(2)
        b.text(a, size=10)
        b.space(6)

    # ---- 5 数字速查 ----
    b.new_page()
    b.heading("5 · 数字速查表（每个数字可指路出处）")
    b.table(
        ["数字", "含义", "出处"],
        [["%s / %.1f万字 / %s H2 / %s 双链" % (AUDIT.get("doc_count"), AUDIT.get("total_chars", 0) / 10000.0,
                                                   AUDIT.get("total_h2"), AUDIT.get("outlink_total")),
          "知识库体检基线", "audit_report.md"],
         ["%s chunks / 管道 1.2s" % format(ANCHOR.get("chunks", 0), ","), "索引规模与速度", "M1"],
         ["%s / %s / %s" % (ANCHOR.get("recall@5"), ANCHOR.get("mrr"), ANCHOR.get("ndcg@10")),
          "60 条 gold 官方基线（三项达标）", "baseline.md"],
         ["11 题未进 Top-5（%.0f%% / %.0f%%）" % (FAMILY.get("easy", (0.0, 0))[0] * 100,
                                               FAMILY.get("hard", (0.0, 0))[0] * 100),
          "坏例分层", "baseline.md"],
         ["非法引用 0 · 拒答 2/2 · 生成 8~15s", "生成链路", "m4_smoke.md"],
         ["%+.4f / %+.3f / %+.3f / %+.4f" % (FAMILY.get("gain", 0.0), FAMILY.get("rew_r", 0.0),
                                                   FAMILY.get("rew_l", 0.0), FAMILY.get("hop", 0.0)),
          "消融增益与负结果", "ablation.md"],
         ["分块粒度消融 %s" % ("｜".join("%+.4f" % (M6B[k]["r5"] - M6B["V1"]["r5"])
                                    for k in ("V2", "V3", "V5"))
                              if (M6B.get("V1") and M6B.get("V2") and M6B.get("V3")
                                  and M6B.get("V5")) else "-"),
          "M6b：细/粗/前缀入检索（候选）", "m6b_chunk_ablation.md"],
         ["点积 <1ms · embedding ~280ms", "规模曲线 → 零向量库", "ablation.md E6"],
         ["pytest 79 条 · pre-commit 钩子", "三层防线", "tests/"]],
        [200, 168, 115.28], size=9)
    b.space(8)
    b.heading("复现与演示", level=2)
    b.bullets([
        "环境体检：D:\\python\\python.exe scripts\\env_check.py（13 项 PASS）",
        "Web 演示：run_api.bat → http://127.0.0.1:8000（问答页 + 分析看板）",
        "问答 CLI：D:\\python\\python.exe -m vaultmind.ask \"问题\"",
        "全量测试：D:\\python\\python.exe -m pytest tests -q",
    ])

    doc = b.finish()
    return doc


def main() -> int:
    first = build(total=None)   # 第一遍：数页数
    n = len(first)
    first.close()
    second = build(total=n)     # 第二遍：带页脚正式输出
    # 字体子集化 + 压缩：TextWriter 默认嵌入完整中文字体，7 页 PDF 会因此膨胀到 ~19MB；
    # subset_fonts 只保留用到的字形（失败则退回完整字体，不影响正确性）。
    try:
        second.subset_fonts()
    except Exception as e:  # pragma: no cover - 依 PyMuPDF 版本行为而定
        print("[WARN] subset_fonts 失败（%s），输出完整字体" % e)
    second.save(OUT, garbage=4, deflate=True)
    second.close()
    # 校验：可打开、可提取中文、含关键数字
    check = fitz.open(OUT)
    text = "".join(p.get_text() for p in check)
    for key in ("recall@5", "mrr", "ndcg@10"):
        assert ANCHOR.get(key) in text, "PDF 文本层缺少锚点 %s=%s" % (key, ANCHOR.get(key))
    if M6B.get("V5"):
        assert ("%.4f" % M6B["V5"]["r5"]) in text, "PDF 文本层缺少 M6b V5 的 R@5"
        assert ("%+.4f" % (M6B["V5"]["r5"] - M6B["V1"]["r5"])) in text, "PDF 缺少 M6b 增益"
    print("[PASS] 生成完成：%s（%d 页，含关键指标数字）" % (OUT, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
