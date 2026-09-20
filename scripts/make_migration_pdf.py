# -*- coding: utf-8 -*-
"""生成《Ollama 本地模型迁移工作流》PDF（VaultMind 环境准备文档）

实现说明：
- 文本统一走 TextWriter + fitz.Font(msyh.ttc)（本机 PyMuPDF 1.27.2.3 的
  insert_text 对 .ttc 字体文件有 bug，TextWriter 路径已验证可用）。
- 每页的图形（页脚线、色块）都在该页创建时绘制；write_text 后不再触碰
  其他页面的句柄（该版本 write_text 会使其余已存在页面句柄失效）。
- 页脚含总页数，故采用两遍渲染：第一遍统计页数，第二遍带页脚正式保存。
"""
import os
import fitz
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "Ollama本地模型迁移工作流.pdf")
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]

# ---------- 页面常量 ----------
W, H = 595.28, 841.89
ML, MR, MT, MB = 56, 56, 60, 58
CW = W - ML - MR

ACCENT = (0.09, 0.40, 0.72)
DARK = (0.14, 0.16, 0.20)
GRAY = (0.46, 0.48, 0.52)
CODE_BG = (0.955, 0.962, 0.974)
CODE_FG = (0.15, 0.22, 0.32)
CODE_LN = (0.84, 0.87, 0.91)
BOX_FILL = (0.925, 0.955, 1.0)
TBL_HDR = (0.88, 0.93, 1.0)
TBL_LN = (0.80, 0.85, 0.92)
TBL_ALT = (0.972, 0.977, 0.984)

FOOTER_LEFT = "VaultMind 环境准备 · Ollama 本地模型迁移工作流"

# ---------- 字体 ----------
font = None
for fp in FONT_CANDIDATES:
    if os.path.exists(fp):
        try:
            font = fitz.Font(fontfile=fp)
            print("使用字体:", fp)
            break
        except Exception as e:
            print("字体加载失败:", fp, e)
if font is None:
    raise RuntimeError("未找到可用中文字体")

doc = None
sheets = []
N_TOTAL = None  # 总页数（第二遍渲染时已知）


class Sheet:
    def __init__(self):
        self.pg = doc.new_page(width=W, height=H)
        # 页脚线 + 页脚文字：趁本页句柄有效立即绘制
        self.pg.draw_line(fitz.Point(ML, H - 40), fitz.Point(W - MR, H - 40),
                          color=(0.85, 0.88, 0.92), width=0.8)
        self.wrs = {}
        self.y = MT
        if N_TOTAL is not None:
            page_no = doc.page_count  # 新页追加在末尾，1 起编号
            wg = self.wr(GRAY)
            wg.append((ML, H - 26), FOOTER_LEFT, font=font, fontsize=8.2)
            right = "第 %d 页 / 共 %d 页" % (page_no, N_TOTAL)
            rw = font.text_length(right, 8.2)
            wg.append((W - MR - rw, H - 26), right, font=font, fontsize=8.2)

    def wr(self, color):
        key = tuple(color)
        if key not in self.wrs:
            self.wrs[key] = fitz.TextWriter(self.pg.rect, color=key)
        return self.wrs[key]

    def need(self, dy):
        if self.y + dy > H - MB:
            self.flush()
            sheets.append(Sheet())
            return sheets[-1]
        return self

    def flush(self):
        if self.wrs is None:
            return
        for w in self.wrs.values():
            w.write_text(self.pg)
        self.wrs = None


def cur():
    if not sheets:
        sheets.append(Sheet())
    return sheets[-1]


def wrap(text, size, maxw):
    out = []
    for para in text.split("\n"):
        if para == "":
            out.append("")
            continue
        line = ""
        for ch in para:
            if font.text_length(line + ch, size) <= maxw:
                line += ch
            else:
                out.append(line)
                line = ch
        out.append(line)
    return out


def para(text, size=10.5, leading=15.5, indent=0, color=DARK, gap=5):
    s = cur()
    lines = wrap(text, size, CW - indent)
    s = s.need(len(lines) * leading + gap)
    w = s.wr(color)
    for ln in lines:
        w.append((ML + indent, s.y + size * 0.86), ln,
                 font=font, fontsize=size)
        s.y += leading
    s.y += gap


def heading(text, level=1, space_before=13):
    s = cur()
    size = 15.5 if level == 1 else 11.8
    s = s.need(space_before + size + 10)
    s.y += space_before
    if level == 1:
        s.pg.draw_rect(fitz.Rect(ML, s.y + 2, ML + 4, s.y + size - 4),
                       color=ACCENT, fill=ACCENT)
    else:
        s.pg.draw_circle(fitz.Point(ML + 2, s.y + size / 2), 1.9,
                         color=ACCENT, fill=ACCENT)
    s.wr(ACCENT).append((ML + 11, s.y + size * 0.86), text,
                        font=font, fontsize=size)
    s.y += size + 5


def bullet(text, size=10.5, leading=15.5, gap=3, color=DARK, marker="•"):
    s = cur()
    lines = wrap(text, size, CW - 16)
    s = s.need(len(lines) * leading + gap)
    w = s.wr(color)
    for i, ln in enumerate(lines):
        if i == 0 and marker:
            s.wr(ACCENT).append((ML, s.y + size * 0.86), marker,
                                font=font, fontsize=size)
        w.append((ML + 13, s.y + size * 0.86), ln, font=font, fontsize=size)
        s.y += leading
    s.y += gap


def code(lines_text, size=9.2, leading=13.5, pad=8, gap=6):
    s = cur()
    lines = wrap(lines_text, size, CW - 2 * pad - 8)
    bh = len(lines) * leading + 2 * pad
    s = s.need(bh + gap)
    rect = fitz.Rect(ML, s.y, ML + CW, s.y + bh)
    s.pg.draw_rect(rect, color=CODE_LN, fill=CODE_BG, width=0.8)
    w = s.wr(CODE_FG)
    ty = s.y + pad
    for ln in lines:
        w.append((ML + pad, ty + size * 0.86), ln, font=font, fontsize=size)
        ty += leading
    s.y += bh + gap


def flow(rows):
    """rows: 每行一个 box 标签列表"""
    s = cur()
    ncol = max(len(r) for r in rows)
    gapx = 30
    bw = (CW - gapx * (ncol - 1)) / ncol
    bh = 36
    row_gap = 24
    total = len(rows) * bh + (len(rows) - 1) * row_gap
    s = s.need(total + 14)
    y0 = s.y
    w = s.wr(DARK)
    for ri, row in enumerate(rows):
        y = y0 + ri * (bh + row_gap)
        for ci, label in enumerate(row):
            x = ML + ci * (bw + gapx)
            rect = fitz.Rect(x, y, x + bw, y + bh)
            s.pg.draw_rect(rect, color=ACCENT, fill=BOX_FILL, width=1.0)
            lns = wrap(label, 9.2, bw - 10)
            th = len(lns) * 11
            ty = y + (bh - th) / 2
            for ln in lns:
                tw_ = font.text_length(ln, 9.2)
                w.append((x + (bw - tw_) / 2, ty + 9), ln,
                         font=font, fontsize=9.2)
                ty += 11
            if ci < len(row) - 1:
                ax0, ax1, ay = x + bw + 3, x + bw + gapx - 3, y + bh / 2
                s.pg.draw_line(fitz.Point(ax0, ay), fitz.Point(ax1, ay),
                               color=ACCENT, width=1.2)
                s.pg.draw_polyline(
                    [fitz.Point(ax1 - 6, ay - 4), fitz.Point(ax1, ay),
                     fitz.Point(ax1 - 6, ay + 4)],
                    color=ACCENT, fill=ACCENT, width=1.0)
        if ri < len(rows) - 1:
            mx = ML + CW / 2
            a1, a2 = y + bh + 7, y + bh + row_gap - 7
            s.pg.draw_line(fitz.Point(mx, a1), fitz.Point(mx, a2),
                           color=ACCENT, width=1.2)
            s.pg.draw_polyline(
                [fitz.Point(mx - 4, a2 - 6), fitz.Point(mx, a2),
                 fitz.Point(mx + 4, a2 - 6)],
                color=ACCENT, fill=ACCENT, width=1.0)
    s.y = y0 + total + 14


def table(headers, rows_data, col_w=None, size=9.6, leading=13.5, pad=6):
    s = cur()
    if col_w is None:
        col_w = [CW / len(headers)] * len(headers)
    n = len(rows_data) + 1
    bh = leading + 2 * pad
    s = s.need(n * bh + 10)
    y0 = s.y
    y = y0
    x = ML
    wd = s.wr(DARK)
    wg = s.wr(GRAY)
    for i, h in enumerate(headers):
        s.pg.draw_rect(fitz.Rect(x, y, x + col_w[i], y + bh),
                       color=ACCENT, fill=TBL_HDR, width=0.8)
        wd.append((x + pad, y + leading - 3.2), h, font=font, fontsize=size)
        x += col_w[i]
    y += bh
    for ri, row in enumerate(rows_data):
        x = ML
        fillc = TBL_ALT if ri % 2 else (1, 1, 1)
        for i, cell in enumerate(row):
            s.pg.draw_rect(fitz.Rect(x, y, x + col_w[i], y + bh),
                           color=TBL_LN, fill=fillc, width=0.8)
            (wd if i == 0 else wg).append(
                (x + pad, y + leading - 3.2), str(cell),
                font=font, fontsize=size)
            x += col_w[i]
        y += bh
    s.y = y + 10


def title(text, sub, meta_lines):
    s = cur()
    s = s.need(110)
    s.wr(ACCENT).append((ML, s.y + 19), text, font=font, fontsize=21)
    s.y += 36
    s.wr(GRAY).append((ML, s.y + 8), sub, font=font, fontsize=11.5)
    s.y += 22
    wg = s.wr(GRAY)
    for m in meta_lines:
        wg.append((ML, s.y + 7), m, font=font, fontsize=9.3)
        s.y += 13
    s.y += 5
    s.pg.draw_line(fitz.Point(ML, s.y), fitz.Point(ML + CW, s.y),
                   color=ACCENT, width=1.6)
    s.y += 14


TODAY = datetime.now().strftime("%Y-%m-%d %H:%M")


def build():
    """构建整篇文档，返回 doc（不保存）。分页逻辑确定，两遍渲染结果一致。"""
    global doc, sheets
    doc = fitz.open()
    sheets = []

    title(
        "Ollama 本地模型迁移工作流",
        "模型存储路径：C 盘 → D 盘（D:\\本地模型）· 操作步骤、执行结果与使用说明",
        [
            "执行日期：" + TODAY + "    |    机器：Windows 11 x64（Administrator）",
            "Ollama 版本：0.32.0    |    安装位置：C:\\Users\\Administrator\\AppData\\Local\\Programs\\Ollama\\ollama.exe",
            "涉及模型：qwen2.5-coder:7b（4.7 GB）    |    关联项目：VaultMind（D:\\RAG）",
        ],
    )

    heading("一、背景与目标", 1)
    para("工作区 D:\\RAG 为 VaultMind 个人知识库 RAG 问答与评测系统（详见 README.md）。"
         "项目技术栈依赖本地 Ollama 运行模型：向量检索计划使用 bge-m3，生成环节计划使用 qwen2.5:7b-instruct，"
         "随项目推进本地模型体积还将继续增长。")
    para("迁移前，Ollama 模型默认存放在系统盘 C:\\Users\\Administrator\\.ollama\\models，"
         "已占用约 4.7 GB；而 C 盘剩余空间仅约 47 GB，继续扩充模型会挤占系统盘，"
         "影响系统与开发环境稳定。因此需要把模型仓库整体迁到 D 盘，并让 Ollama 永久使用新路径。")
    bullet("在 D 盘新建模型仓库目录：D:\\本地模型")
    bullet("写入用户级环境变量 OLLAMA_MODELS，使 Ollama 永久指向新路径")
    bullet("将现有全部本地模型无损迁移至新目录，并启动 Ollama 验证可用")

    heading("二、执行工作流（六步）", 1)
    para("以下步骤已在真实环境执行并验证通过，可直接复用于今后再次迁移或扩容场景：")
    flow([
        ["① 现状检查", "② 创建新目录", "③ 设置环境变量"],
        ["④ 迁移模型文件", "⑤ 清理旧目录", "⑥ 启动验证"],
    ])

    heading("第 1 步 · 现状检查", 2)
    bullet("ollama --version → 0.32.0；服务默认未运行，需手动 ollama serve")
    bullet("旧模型目录：C:\\Users\\Administrator\\.ollama\\models，含 manifests + blobs 共 6 个文件，4,683,088,419 字节")
    bullet("现有模型：qwen2.5-coder:7b（ID dae161e27b0e，4.7 GB）")
    bullet("D 盘剩余空间约 143 GB，满足迁移条件")

    heading("第 2 步 · 创建新目录", 2)
    code("New-Item -ItemType Directory -Path 'D:\\本地模型'")

    heading("第 3 步 · 设置环境变量（用户级，持久生效）", 2)
    para("将 OLLAMA_MODELS 写入用户级环境变量，之后新启动的进程都会自动读取：")
    code("[Environment]::SetEnvironmentVariable('OLLAMA_MODELS', 'D:\\本地模型', 'User')")

    heading("第 4 步 · 迁移模型文件（跨盘移动 = 复制后删除源文件）", 2)
    code("Move-Item \"$env:USERPROFILE\\.ollama\\models\\blobs\" 'D:\\本地模型\\blobs'\n"
         "Move-Item \"$env:USERPROFILE\\.ollama\\models\\manifests\" 'D:\\本地模型\\manifests'")

    heading("第 5 步 · 清理旧目录", 2)
    code("Remove-Item \"$env:USERPROFILE\\.ollama\\models\"")

    heading("第 6 步 · 启动验证", 2)
    code("$env:OLLAMA_MODELS = 'D:\\本地模型'   # 当前终端临时指定\n"
         "ollama serve                           # 后台启动服务\n"
         "ollama list                            # 应正确列出已有模型")
    para("验证输出：qwen2.5-coder:7b（ID dae161e27b0e，4.7 GB）被正常识别，确认迁移无损；随后关闭临时验证服务。")

    heading("三、执行结果", 1)
    table(
        ["检查项", "预期", "实际结果"],
        [
            ["新目录 D:\\本地模型", "已创建", "√ 通过"],
            ["用户级环境变量 OLLAMA_MODELS", "D:\\本地模型", "√ 通过"],
            ["迁移文件数量", "6 个", "6 个 √ 一致"],
            ["迁移总体积", "4,683,088,419 字节", "4,683,088,419 字节 √ 无损"],
            ["ollama list 模型识别", "能列出 qwen2.5-coder:7b", "√ 通过（dae161e27b0e）"],
            ["旧 C 盘模型目录", "已删除", "√ 已清理，C 盘释放约 4.7 GB"],
        ],
        col_w=[150, 150, CW - 300],
    )

    heading("四、后续使用说明", 1)
    bullet("今后下载任何新模型（如 ollama pull bge-m3、ollama pull qwen2.5:7b）都会自动存入 D:\\本地模型，不再占用 C 盘。")
    bullet("环境变量对“之后新启动的进程”生效：Ollama 桌面应用需完全退出后重新打开；已打开的终端需重开。")
    bullet("本机 Ollama 默认不随系统自启，开发时手动执行 ollama serve 即可，它会自动读取该环境变量。")
    bullet("临时切换路径（仅当前终端）：$env:OLLAMA_MODELS='D:\\本地模型'; ollama serve")
    bullet("VaultMind 项目后续联调 Ollama 时无需任何额外配置，模型路径已全局生效。")

    heading("五、回滚方案（如需迁回 C 盘）", 1)
    code("[Environment]::SetEnvironmentVariable('OLLAMA_MODELS', $null, 'User')   # 删除环境变量\n"
         "New-Item -ItemType Directory -Path \"$env:USERPROFILE\\.ollama\\models\"\n"
         "Move-Item 'D:\\本地模型\\blobs' \"$env:USERPROFILE\\.ollama\\models\\blobs\"\n"
         "Move-Item 'D:\\本地模型\\manifests' \"$env:USERPROFILE\\.ollama\\models\\manifests\"\n"
         "# 随后重启 Ollama 即可")
    para("注意：回滚前请确认没有运行中的 Ollama 进程，避免文件被占用。", gap=8)

    heading("六、检查清单", 1)
    bullet("√  D:\\本地模型 已创建", marker="")
    bullet("√  用户级环境变量 OLLAMA_MODELS=D:\\本地模型 已写入", marker="")
    bullet("√  模型文件全部迁入新目录（6 个文件 / 4,683,088,419 字节）", marker="")
    bullet("√  ollama list 能正确识别 qwen2.5-coder:7b", marker="")
    bullet("√  旧 C 盘模型目录已删除，C 盘释放约 4.7 GB", marker="")
    bullet("√  迁移前后文件体积逐字节一致，无损坏", marker="")

    for s in sheets:
        s.flush()
    return doc


# ---------- 两遍渲染 ----------
doc = build()
n = doc.page_count
doc.close()

N_TOTAL = n
doc = build()
try:
    doc.subset_fonts()   # 只嵌入用到的字形：否则单份文档会带上 ~12MB 的完整中文字体
except Exception as e:   # pragma: no cover - 依 PyMuPDF 版本行为而定
    print("[WARN] subset_fonts 失败（%s），输出完整字体" % e)
doc.save(OUT, garbage=4, deflate=True)
print("PDF 已生成:", OUT)
print("页数:", n)
