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
    b.text("154 篇笔记 / 27.7 万字 / 409 条双链 → 可问答 · 可评测 · 可复现", size=12, color=GRAY)
    b.text("零 LangChain · 零 torch · 零向量数据库", size=12, color=GRAY)
    b.space(40)
    b.text("指标：Recall@5 = 0.8167 · MRR = 0.7010 · nDCG@10 = 0.7339（三项达标）",
           size=12, color=DARK, bold=True)
    b.text("git %s · 2026-09 · 面向 AI 应用开发 + AI 数据分析双方向求职" % GIT,
           size=10.5, color=GRAY)

    # ---- 1 指标 ----
    b.new_page()
    b.heading("1 · 指标总览（60 条 gold 评测集 · hybrid 检索 · 全部可复现）")
    b.table(
        ["指标", "基线值", "目标", "判定", "出处"],
        [["Recall@1", "0.6167", "—", "—", "reports/baseline.md"],
         ["Recall@5", "0.8167", "≥ 0.80", "✅ 达标", "reports/baseline.md"],
         ["Recall@10", "0.8333", "—", "—", "reports/baseline.md"],
         ["MRR", "0.7010", "≥ 0.65", "✅ 达标", "reports/baseline.md"],
         ["nDCG@10", "0.7339", "≥ 0.70", "✅ 达标", "reports/baseline.md"],
         ["平均延迟", "0.866 s", "—", "—", "reports/baseline.md"],
         ["引用可追溯", "非法引用 = 0", "100%", "✅", "reports/m4_smoke.md"],
         ["超纲拒答", "2/2 探针", "拒答", "✅", "reports/m4_smoke.md"],
         ["消融实验", "6 组 × 60 gold", "基线闸门", "✅", "reports/ablation.md"]],
        widths)
    b.space(4)
    b.text("复现：python -m vaultmind.eval（基线）｜ python scripts\\m6_ablation.py（消融）",
           size=9.5, color=GRAY)

    # ---- 2 架构 ----
    b.new_page()
    b.heading("2 · 系统架构（四层管线）")
    arch = [
        "① 数据管道：Obsidian 源库(只读) → 扫描/体检 → 结构感知分块（H2 单元、超 600 字二切、",
        "            [文档|章节|标签] 前缀注入）→ SQLite(docs/chunks/links) + FTS5(jieba)",
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
        "混合检索：消融验证融合 R@5 +0.05 正增益；RRF k 参数不敏感",
        "评测集防自欺：候选不用 LLM 生成，分层抽样定稿，seed=42 重跑逐字节一致",
        "引用 100% 可追溯：提示词约束 + 规则校验双层（4 种格式变异探针全覆盖）",
    ])

    # ---- 3 消融 ----
    b.new_page()
    b.heading("3 · 六组消融（每个组件增益量化，负结果如实记录）")
    b.table(
        ["实验", "关键结果", "结论"],
        [["三路单拆", "0.7667 / 0.7500 / 0.8167；R@1 融合 0.6167 < 向量 0.6667",
          "融合正增益 +0.05；量化「顶部稀释」"],
         ["RRF k=20/60/100", "R@5 恒 0.8167，MRR 极差 0.0012", "参数不敏感，无需调参"],
         ["查询改写", "规则 -0.017 / LLM -0.067；hard 档一路降", "负结果：不上线"],
         ["标题加权重排", "easy 1.0000 / hard 0.3750", "分层撕裂：需条件化"],
         ["双链 1-hop 扩展", "R@5 +0.0000", "中性：转「相关笔记推荐」"],
         ["规模-延迟曲线", "25%→100% 语料 290→286ms；点积 <1ms", "零向量库决策被验证"]],
        [110, 250, 123.28], size=9)
    b.space(4)
    b.text("坏例账本：11 题未进 Top-5（10 题裸标题型）；easy 档 97% / hard 档 58% → 分层归因。",
           size=10, color=DARK, bold=True)

    # ---- 4 高频 Q&A ----
    b.new_page()
    b.heading("4 · 高频面试问题与答法（节选，全文见 docs/Q&A预案.md）")
    qa = [
        ("Q 为什么不用 LangChain / 向量库 / torch？",
         "A 数据规模决定架构：1,237 chunks × 1024 维点积实测 <1ms，向量库是过度设计；"
         "自写管道每个环节可解释、可改动；面试能讲清原理。"),
        ("Q 评测集可信吗？",
         "A 三道防线：候选只用笔记结构模板化派生（不用 LLM 生成问题）；分层抽样定稿 "
         "seed=42 可复现 + SHA-256；每条 gold 目标必须映射回已索引 chunk（实测 100%）。"),
        ("Q 引用可追溯怎么保证？LLM 编造怎么办？",
         "A 提示词约束 + 规则校验双层：引用编号必须落在上下文 1..n；实测模型有 4 种格式"
         "变异（列表式等），解析器宽容 + 探针全覆盖；超纲 2/2 拒答。"),
        ("Q 坏例怎么处理？",
         "A 先分层归因（easy 97% / hard 58%，主因=裸标题查询），再消融验证方案：改写与 "
         "1-hop 被数据否决，标题重排需条件化——不是所有坏例都要修，先算账。"),
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
        [["154 / 27.7万字 / 922 H2 / 409 双链", "知识库体检基线", "audit_report.md"],
         ["1,237 chunks / 管道 1.2s", "索引规模与速度", "M1"],
         ["0.8167 / 0.7010 / 0.7339", "60 条 gold 官方基线（三项达标）", "baseline.md"],
         ["11 题未进 Top-5（97% / 58%）", "坏例分层", "baseline.md"],
         ["非法引用 0 · 拒答 2/2 · 生成 8~15s", "生成链路", "m4_smoke.md"],
         ["+0.05 / -0.017 / -0.067 / +0.000", "消融增益与负结果", "ablation.md"],
         ["点积 <1ms · embedding ~280ms", "规模曲线 → 零向量库", "ablation.md E6"],
         ["pytest 50+ 条 · pre-commit 钩子", "三层防线", "tests/"]],
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
    second.save(OUT)
    second.close()
    # 校验：可打开、可提取中文、含关键数字
    check = fitz.open(OUT)
    text = "".join(p.get_text() for p in check)
    assert "0.8167" in text and "0.7010" in text and "0.7339" in text
    print("[PASS] 生成完成：%s（%d 页，含关键指标数字）" % (OUT, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
