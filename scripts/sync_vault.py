# -*- coding: utf-8 -*-
r"""Vault 增长后的一键同步：重建索引+向量 → 复验 gold → 重定审计基线 → 回写文档锚点 → 回归。

背景：Vault 每新增笔记，都要走一遍这条链路（2026-09-17 手工走过两次）：
    重建索引 → 全量重建向量 → 复验 60 条 gold → 重定审计基线 → 回写文档锚点 → PDF 重生 → pytest
本脚本把它固化。锚点一律**从 reports/ 现场读**再回写，而不是手抄（见知识卡片
《文档锚点漂移：别手抄数字，让文档去读报告》）。

用法：
    D:\python\python.exe scripts\sync_vault.py                 # 全流程
    D:\python\python.exe scripts\sync_vault.py --dry-run       # 只看会改什么，不落盘
    D:\python\python.exe scripts\sync_vault.py --no-change     # Vault 没变也强制执行
    D:\python\python.exe scripts\sync_vault.py --skip-eval     # 跳过 gold 复验（更快）
    D:\python\python.exe scripts\sync_vault.py --yes           # 不交互（自动化）

前置：Ollama 需在运行（向量化与评测要 bge-m3）。退出码 0=全绿，1=有失败项。
产出：reports/sync_report.md（本次同步报告）、data/sync_state.json（上次指纹）。
"""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vaultmind.config import AUDIT_REPORT, BASELINE_JSON, DATA_DIR, DB_PATH, VAULT_ROOT  # noqa: E402
from vaultmind.eval.runner import load_gold, run_eval, write_report  # noqa: E402
from vaultmind.ingest import run_pipeline  # noqa: E402
from vaultmind.retrieval import vector  # noqa: E402

PY = r"D:\python\python.exe"
if not os.path.exists(PY):          # 换机兜底：用当前解释器
    PY = sys.executable

REPORTS = ROOT / "reports"
BASELINE_MD = REPORTS / "baseline.md"
ABLATION_MD = REPORTS / "ablation.md"
SYNC_REPORT = REPORTS / "sync_report.md"
STATE = DATA_DIR / "sync_state.json"          # 全量同步指纹（含复验/锚点/PDF/pytest）
INDEX_STATE = DATA_DIR / "index_state.json"   # 轻量同步指纹（仅索引+向量）

ANCHOR_FILES = [
    "README.md", "PLAN.md", "CHANGELOG.md",
    "docs/Q&A预案.md", "docs/简历bullet.md",
]

TARGETS = {"recall@5": 0.80, "mrr": 0.65, "ndcg@10": 0.70}


# ---------------------------------------------------------------- 工具

class Run:
    """收集本次同步的过程记录，供报告与终判使用。"""

    def __init__(self):
        self.steps = []      # (步骤, 状态, 说明)
        self.metrics = {}    # 指标名 -> (旧值, 新值)
        self.failed = False

    def ok(self, step, msg=""):
        self.steps.append((step, "OK", msg))

    def warn(self, step, msg=""):
        self.steps.append((step, "WARN", msg))

    def fail(self, step, msg=""):
        self.steps.append((step, "FAIL", msg))
        self.failed = True

    def metric(self, key, old, new):
        self.metrics[key] = (old, new)


def say(msg=""):
    print(msg, flush=True)


def ollama_ok(timeout=5):
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


# ---------------------------------------------------------------- 指纹与变更检测

def vault_fingerprint():
    """Vault 全量指纹：文件数 + 按相对路径排序后的 (路径, 大小, mtime) 摘要。"""
    metas = []
    for p in sorted(VAULT_ROOT.rglob("*.md")):
        try:
            st = p.stat()
        except OSError:
            continue
        metas.append("%s|%d|%d" % (p.relative_to(VAULT_ROOT).as_posix(), st.st_size, int(st.st_mtime)))
    blob = "\n".join(metas).encode("utf-8")
    return {
        "md_count": len(metas),
        "hash": hashlib.sha256(blob).hexdigest()[:16],
        "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def change_vs_last(fp, state_path=STATE):
    if not state_path.exists():
        return None, "无历史指纹（首次运行）"
    try:
        old = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception as e:
        return None, "历史指纹读取失败：%s" % e
    if old.get("hash") == fp["hash"]:
        return False, "与上次同步一致（%s 篇，%s）" % (fp["md_count"], old.get("at", "?"))
    diff = fp["md_count"] - int(old.get("md_count", 0))
    return True, "相对上次变化：md %+d 篇（%s → %s）" % (diff, old.get("md_count", "?"), fp["md_count"])


def save_state(fp, state_path=STATE):
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(fp, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- 读数（现场解析）

def parse_baseline(path=BASELINE_MD):
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(Recall@\d+|MRR|nDCG@10)\s*\|\s*([0-9.]+)\s*\|", line)
        if m:
            out[m.group(1).lower()] = float(m.group(2))
        m = re.match(r"\|\s*平均延迟\s*\|\s*([0-9.]+)\s*s\s*\|", line)
        if m:
            out["latency"] = float(m.group(1))
    return out


def parse_ablation(path=ABLATION_MD):
    """从 ablation.md 取：hybrid 分层 R@5、E1 增益、改写增益、1-hop 增益、E6 向量延迟。"""
    out = {}
    if not path.exists():
        return out
    section = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:5]
            continue
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if section == "E6" and len(cells) == 4 and cells[0] in ("25%", "100%"):
            try:
                out["e6_" + cells[0].rstrip("%")] = float(cells[2])
            except ValueError:
                pass
            continue
        if len(cells) < 6 or cells[0] in ("变体", "---"):
            continue
        if section == "E1" and cells[0] == "hybrid":
            try:
                out["recall@5"] = float(cells[1])
            except ValueError:
                pass
            mh = re.match(r"([0-9.]+)\((\d+)\)", cells[-2])
            me = re.match(r"([0-9.]+)\((\d+)\)", cells[-1])
            if mh:
                out["hard"] = float(mh.group(1))
            if me:
                out["easy"] = float(me.group(1))
        elif section == "E1" and cells[0] == "bm25":
            try:
                out["bm25_r5"] = float(cells[1])
            except ValueError:
                pass
        elif section == "E1" and cells[0] == "vector":
            try:
                out["vector_r5"] = float(cells[1])
            except ValueError:
                pass
    text = path.read_text(encoding="utf-8")
    m = re.search(r"比 bm25（[0-9.]+）高 \*\*([+-][0-9.]+)\*\*", text)
    if m:
        out["gain"] = float(m.group(1))
    m = re.search(r"规则改写 R@5 [0-9.]+（\*\*([+-][0-9.]+)\*\*）、LLM 改写 [0-9.]+（\*\*([+-][0-9.]+)\*\*）", text)
    if m:
        out["rew_rule"] = float(m.group(1))
        out["rew_llm"] = float(m.group(2))
    m = re.search(r"R@5 [0-9.]+（\*\*([+-][0-9.]+)\*\*）、MRR", text)
    if m:
        out["hop"] = float(m.group(1))
    return out


def db_counts():
    con = sqlite3.connect(str(DB_PATH))
    try:
        return tuple(con.execute(
            "SELECT (SELECT COUNT(*) FROM docs),(SELECT COUNT(*) FROM chunks),"
            "(SELECT COUNT(*) FROM links)").fetchone())
    finally:
        con.close()


def audit_counts():
    if not BASELINE_JSON.exists():
        return {}
    d = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    return {"doc_count": d["doc_count"], "chars": d["total_chars"], "h2": d["total_h2"],
            "links": d["outlink_total"], "dead": d["unresolved_links"],
            "orphans": len(d.get("orphans", []))}


def last_ingest_secs():
    """取上次管道耗时（干跑时不能真跑）：优先 data/audit.json 的 elapsed_sec。"""
    try:
        j = json.loads((DATA_DIR / "audit.json").read_text(encoding="utf-8"))
        sec = j.get("elapsed_sec")
        if sec:
            return "%.1f" % float(sec)
    except Exception:
        pass
    try:
        head = AUDIT_REPORT.read_text(encoding="utf-8")[:800]
        m = re.search(r"耗时\s*([\d.]+)", head)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------- 回写锚点

def anchor_edits(base, abl, aud, dbc, metrics_fresh=True):
    """返回 [(文件, 旧串, 新串)]；旧串用正则匹配，保证幂等。

    metrics_fresh=False（--skip-eval / dry-run）时不回写指标类锚点，
    只回写语料规模类（那些来自 audit/db，本来就是新的）。
    """
    docs, chunks, links = dbc
    wan = aud["chars"] / 10000.0
    lat = base.get("latency")
    edits = []

    def add(path, pattern, new):
        edits.append((path, pattern, new))

    # 语料规模（来自 audit/db，永远是新值）
    add("README.md", r"（\d+ 篇笔记 / [\d.]+ 万字 / \d+ 个 H2 / \d+ 条双链）",
        "（%d 篇笔记 / %.1f 万字 / %d 个 H2 / %d 条双链）" % (docs, wan, aud["h2"], aud["links"]))
    add("README.md", r"docs\(\d+\)/chunks\(\d+\)/links\(\d+\)",
        "docs(%d)/chunks(%d)/links(%d)" % (docs, chunks, links))
    # pytest 条数（现场 count_tests()，永远是新值；2026-09 曾漂移 79→84 未被覆盖）
    add("README.md", r"pytest \d+ 条", "pytest %d 条" % n_tests)
    add("README.md", r"# \d+ passed", "# %d passed" % n_tests)

    # 指标类（仅当基线刚重跑过）
    if metrics_fresh:
        add("README.md", r"\| 平均延迟 \| [\d.]+ s/查询 \|", "| 平均延迟 | %s s/查询 |" % lat)
        add("README.md", r"\| Recall@1 \| [\d.]+ \|", "| Recall@1 | %s |" % fmt4(base["recall@1"]))
        add("README.md", r"\| Recall@5 \| \*\*[\d.]+\*\* \|", "| Recall@5 | **%s** |" % fmt4(base["recall@5"]))
        add("README.md", r"\| Recall@10 \| [\d.]+ \|", "| Recall@10 | %s |" % fmt4(base["recall@10"]))
        add("README.md", r"\| MRR \| \*\*[\d.]+\*\* \|", "| MRR | **%s** |" % fmt4(base["mrr"]))
        add("README.md", r"\| nDCG@10 \| \*\*[\d.]+\*\* \|", "| nDCG@10 | **%s** |" % fmt4(base["ndcg@10"]))

    # Q&A 预案
    add("docs/Q&A预案.md", r"（\d+ 篇笔记、[\d.]+ 万字、\d+ 条双链）",
        "（%d 篇笔记、%.1f 万字、%d 条双链）" % (docs, wan, aud["links"]))
    add("docs/Q&A预案.md", r"：[\d,]+ 个 chunk", "：%s 个 chunk" % format(chunks, ","))
    add("docs/Q&A预案.md", r"\| \d+ / [\d.]+ 万字 / \d+ H2 / \d+ 双链 / \d+ 死链 / \d+ 孤儿 \|",
        "| %d / %.1f 万字 / %d H2 / %d 双链 / %d 死链 / %d 孤儿 |"
        % (docs, wan, aud["h2"], aud["links"], aud["dead"], aud["orphans"]))
    if ingest_secs and ingest_secs[0].isdigit():
        add("docs/Q&A预案.md", r"\| [\d,]+ chunks / 全管道 [\d.]+s（\d+ 篇全量重建） \|",
            "| %s chunks / 全管道 %ss（%d 篇全量重建） |" % (format(chunks, ","), ingest_secs, docs))
    if metrics_fresh:
        add("docs/Q&A预案.md", r"\| \*\*[\d.]+ / [\d.]+ / [\d.]+\*\*（R@5 / MRR / nDCG@10）",
            "| **%s / %s / %s**（R@5 / MRR / nDCG@10）"
            % (fmt4(base["recall@5"]), fmt4(base["mrr"]), fmt4(base["ndcg@10"])))
    add("docs/Q&A预案.md", r"（easy 档 \*\*[\d.]+\*\* / hard 档 \*\*[\d.]+\*\*）",
        "（easy 档 **%s** / hard 档 **%s**）" % (fmt4(abl["easy"]), fmt4(abl["hard"])))
    if abs(abl.get("hop", 0.0)) > 5e-5:
        add("docs/Q&A预案.md", r"1-hop [-+][\d.]+、标题重排",
            "1-hop %+.4f、标题重排" % abl["hop"])
    add("docs/Q&A预案.md", r"语料 [\d.]+→[\d.]+ms",
        "语料 %.0f→%.0fms" % (abl["e6_25"], abl["e6_100"]))
    add("docs/Q&A预案.md", r"pytest \d+ 条含全套探针", "pytest %d 条含全套探针" % n_tests)
    add("docs/Q&A预案.md", r"\| pytest \d+ 条 \+ pre-commit", "| pytest %d 条 + pre-commit" % n_tests)

    # 简历 bullet
    add("docs/简历bullet.md", r"（\*\*\d+ 篇 / [\d.]+ 万字 / \d+ 条双链\*\*",
        "（**%d 篇 / %.1f 万字 / %d 条双链**" % (docs, wan, aud["links"]))
    add("docs/简历bullet.md", r"Recall@5 = \*\*[\d.]+\*\*、MRR = \*\*[\d.]+\*\*、nDCG@10 = \*\*[\d.]+\*\*",
        "Recall@5 = **%s**、MRR = **%s**、nDCG@10 = **%s**"
        % (fmt3(base["recall@5"]), fmt3(base["mrr"]), fmt3(base["ndcg@10"])))
    add("docs/简历bullet.md", r"融合 vs 单路 R@5 [+-][\d.]+",
        "融合 vs 单路 R@5 %+.3f" % abl["gain"])
    add("docs/简历bullet.md", r"规模曲线验证 [\d.]+k chunks", "规模曲线验证 %.1fk chunks" % (chunks / 1000.0))
    add("docs/简历bullet.md", r"数据治理管道：\d+ 篇笔记的\*\*体检基线\*\*（\d+ H2 / \d+ 双链 / \d+ 死链 / \d+ 孤儿）",
        "数据治理管道：%d 篇笔记的**体检基线**（%d H2 / %d 双链 / %d 死链 / %d 孤儿）"
        % (docs, aud["h2"], aud["links"], aud["dead"], aud["orphans"]))
    add("docs/简历bullet.md", r"「为 \d+ 篇知识库建立评测", "「为 %d 篇知识库建立评测" % docs)
    add("docs/简历bullet.md", r"pytest \d+ 条 \+ pre-commit", "pytest %d 条 + pre-commit" % n_tests)

    # PLAN 快照
    add("PLAN.md", r"RRF，[\d,]+ chunks）", "RRF，%s chunks）" % format(chunks, ","))
    add("PLAN.md", r"正式基线（(?:bm25：)?Recall@5=[\d.]+ / MRR=[\d.]+ / nDCG@10=[\d.]+",
        "正式基线（bm25：Recall@5=%s / MRR=%s / nDCG@10=%s"
        % (fmt4(base["recall@5"]), fmt4(base["mrr"]), fmt4(base["ndcg@10"])))
    return edits


def apply_edits(edits, dry_run):
    changed = []
    for rel, pattern, new in edits:
        p = ROOT / rel
        src = p.read_text(encoding="utf-8")
        m = re.search(pattern, src)
        if not m:
            changed.append((rel, "未命中", pattern[:34], ""))
            continue
        if m.group(0) == new:
            continue
        src = src[:m.start()] + new + src[m.end():]
        if not dry_run:
            p.write_text(src, encoding="utf-8", newline="\n")
        changed.append((rel, "已回写" if not dry_run else "待回写", m.group(0)[:34], new[:34]))
    return changed


def fmt4(x):
    return "%.4f" % x


def fmt3(x):
    return "%.3f" % x


# ---------------------------------------------------------------- 主流程

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sync_vault", description="Vault 增长后的一键同步")
    ap.add_argument("--dry-run", action="store_true", help="只报告，不落盘")
    ap.add_argument("--no-change", action="store_true", help="Vault 未变也强制执行")
    ap.add_argument("--skip-eval", action="store_true", help="跳过 60 条 gold 复验")
    ap.add_argument("--yes", action="store_true", help="不交互确认")
    ap.add_argument("--light", action="store_true",
                    help="轻量同步：只重建索引+向量（让新笔记可检索），跳过复验/锚点/PDF/pytest")
    args = ap.parse_args(argv)

    global ingest_secs, n_tests
    ingest_secs = "?"
    n_tests = 0

    t_start = time.time()
    run = Run()
    say("=" * 62)
    say(" VaultMind · Vault 同步（重建 → 复验 → 重锚定 → 回归）")
    say(" 时间：%s%s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "（DRY-RUN，不落盘）" if args.dry_run else ""))
    say("=" * 62)

    # 0. 前置：Vault 可读 + Ollama
    if not VAULT_ROOT.exists():
        run.fail("前置检查", "Vault 不存在：%s" % VAULT_ROOT)
        return finish(run, None, None, args.dry_run, t_start)
    if not ollama_ok():
        run.fail("前置检查", "Ollama 未运行（需 `ollama serve`）：向量化与评测要 bge-m3")
        return finish(run, None, None, args.dry_run, t_start)
    run.ok("前置检查", "Vault 可读 + Ollama 在线")

    fp = vault_fingerprint()

    if args.light:
        return light_sync(run, fp, args, t_start)

    changed, why = change_vs_last(fp)
    say("Vault 指纹：%d 篇 md，hash=%s｜%s" % (fp["md_count"], fp["hash"], why))
    if changed is False and not args.no_change:
        # 变更检测真正短路：未变化时不再全量重建（索引/向量/复验/回归），
        # 使 sync 变成可安全重复触发的幂等命令（一键同步 / 自动同步依赖此行为）。
        run.ok("变更检测", "Vault 未变化，跳过本次同步")
        say("      → 未变化，跳过全流程（如需强制重建请加 --no-change）")
        return finish(run, fp, None, args.dry_run, t_start)
    run.ok("变更检测", why)

    old_baseline = parse_baseline()

    # 1. 重建索引 + 向量
    say("\n[1/6] 重建索引（扫描 → 体检 → 分块 → SQLite/FTS5）...")
    t0 = time.time()
    if args.dry_run:
        # 干跑绝不落盘：只读扫描统计（build_db 会删旧向量产物，不能在 dry-run 里触发）
        from vaultmind.ingest import auditor, chunker, scanner
        dd = scanner.scan_docs()
        mm = auditor.audit(dd)
        ingest_secs = last_ingest_secs()
        run.warn("重建索引", "DRY-RUN 跳过重建；预检会得到 docs=%d chunks≈%d"
                 % (mm["doc_count"], len(chunker.chunk_all(dd))))
        say("      → DRY-RUN：不动索引库（当前 docs=%d，上次管道耗时 %ss）"
            % (mm["doc_count"], ingest_secs))
    else:
        res = run_pipeline()      # 会按守卫删除旧向量产物，强制重建
        ingest_secs = "%.1f" % res["metrics"]["elapsed_sec"]
        docs, chunks, links = db_counts()
        run.ok("重建索引", "docs=%d chunks=%d links=%d（%ss）" % (docs, chunks, links, ingest_secs))
        say("      → docs=%d chunks=%d links=%d（%ss）" % (docs, chunks, links, ingest_secs))

    say("\n[2/6] 全量重建向量（bge-m3，断点续跑）...")
    if args.dry_run:
        run.warn("重建向量", "DRY-RUN 跳过")
    else:
        st = vector.build_embeddings(resume=True)
        run.ok("重建向量", "%d/%d（%d 维）" % (st["embedded"], st["total_chunks"], st["dim"]))
        say("      → %d/%d" % (st["embedded"], st["total_chunks"]))

    # 2. gold 复验
    base = old_baseline
    if args.skip_eval or args.dry_run:
        run.warn("gold 复验", "已跳过（%s）" % ("DRY-RUN" if args.dry_run else "--skip-eval"))
    else:
        say("\n[3/6] 复验 60 条 gold（bm25，top_k=10）...")
        gold = load_gold()
        details, metrics = run_eval(gold, mode="bm25", top_k=10)
        write_report(details, metrics, mode="bm25", top_k=10)
        base = parse_baseline()
        for k in ("recall@1", "recall@5", "recall@10", "mrr", "ndcg@10", "latency"):
            run.metric(k, old_baseline.get(k), base.get(k))
        gate = all(base.get(k, 0) >= v for k, v in TARGETS.items())
        msg = "R@5=%s MRR=%s nDCG@10=%s 延迟=%ss" % (
            fmt4(base["recall@5"]), fmt4(base["mrr"]), fmt4(base["ndcg@10"]), base["latency"])
        (run.ok if gate else run.fail)("gold 复验", msg + ("（三项达标）" if gate else "（未达标！）"))
        say("      → %s" % msg)
        if not gate:
            say("      !! 三项目标未全部达标，停止后续步骤（先查检索质量）")
            return finish(run, fp, None, args.dry_run, t_start)

    # 3. 重定审计基线
    say("\n[4/6] 重定审计基线（BASI json ↔ 当前 Vault）...")
    aud = audit_counts()
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from vaultmind.ingest import auditor, scanner
        m = auditor.audit(scanner.scan_docs())
        keys = ["root", "doc_count", "total_chars", "body_chars", "by_type", "by_top_folder",
                "by_status", "no_frontmatter", "est_chunks_h2", "total_h2", "total_h3",
                "outlink_total", "unresolved_links", "orphans", "top_inbound", "largest",
                "smallest_lt_300"]
        new_base = {k: m[k] for k in keys}
        same = aud.get("doc_count") == m["doc_count"] and aud.get("chars") == m["total_chars"]
        if args.dry_run:
            run.warn("审计基线", "DRY-RUN：当前 Vault %d 篇 / %d 字符（基线 %s 篇）"
                     % (m["doc_count"], m["total_chars"], aud.get("doc_count")))
        elif same:
            run.ok("审计基线", "无需变更（%d 篇 / %d 字符）" % (m["doc_count"], m["total_chars"]))
        else:
            BASELINE_JSON.write_text(json.dumps(new_base, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
            run.ok("审计基线", "已重定 %s→%s 篇、%s→%s 字符"
                   % (aud.get("doc_count"), m["doc_count"], aud.get("chars"), m["total_chars"]))
        aud = {"doc_count": m["doc_count"], "chars": m["total_chars"], "h2": m["total_h2"],
               "links": m["outlink_total"], "dead": m["unresolved_links"],
               "orphans": len(m.get("orphans", []))}
        say("      → %d 篇 / %d 字符 / %d H2 / %d 出链" %
            (aud["doc_count"], aud["chars"], aud["h2"], aud["links"]))
    except Exception as e:
        run.fail("审计基线", "重定失败：%s" % e)

    # 4. 回写锚点
    say("\n[5/6] 回写文档锚点（从 reports 现场取数）...")
    abl = parse_ablation()
    n_tests = count_tests()
    try:
        # --skip-eval 时 baseline.md 未重跑，指标锚点保持原样（否则会用旧值覆盖新值）
        edits = anchor_edits(base, abl, aud, db_counts(),
                             metrics_fresh=not (args.skip_eval or args.dry_run))
        changes = apply_edits(edits, args.dry_run)
        hit = [c for c in changes if c[1] != "未命中"]
        miss = [c for c in changes if c[1] == "未命中"]
        if miss:
            run.warn("回写锚点", "%d 处未命中（模式可能已变，请人工看一眼）：%s"
                     % (len(miss), "; ".join("%s:%s" % (m[0], m[2]) for m in miss[:4])))
        run.ok("回写锚点", "%d 处%s" % (len(hit), "待回写（DRY-RUN）" if args.dry_run else "已回写"))
        for rel, st, old, new in hit:
            say("      [%s] %s：%s → %s" % (st, rel, old, new))
    except Exception as e:
        run.fail("回写锚点", "失败：%s" % e)

    # 5. PDF + 回归
    say("\n[6/6] 交付物与回归...")
    if args.dry_run:
        run.warn("PDF 重生", "DRY-RUN 跳过")
        run.warn("pytest", "DRY-RUN 跳过")
    else:
        r = subprocess.run([PY, str(ROOT / "scripts" / "make_interview_pdf.py")],
                           cwd=str(ROOT), capture_output=True, text=True, timeout=600)
        if r.returncode == 0:
            run.ok("PDF 重生", (r.stdout or "").strip().splitlines()[-1][:80])
        else:
            run.fail("PDF 重生", (r.stderr or r.stdout or "").strip()[-160:])
        r = subprocess.run([PY, "-m", "pytest", "tests", "-q", "--no-header",
                            "-p", "no:cacheprovider"],
                           cwd=str(ROOT), capture_output=True, text=True, timeout=1800)
        tail = (r.stdout or "").strip().splitlines()[-1] if r.stdout else ""
        (run.ok if r.returncode == 0 else run.fail)("pytest", tail[:120])

    return finish(run, fp, abl, args.dry_run, t_start)


def count_tests():
    r = subprocess.run([PY, "-m", "pytest", "tests", "--collect-only", "-q",
                        "--no-header", "-p", "no:cacheprovider"],
                       cwd=str(ROOT), capture_output=True, text=True, timeout=600)
    m = re.search(r"(\d+) tests collected", r.stdout or "")
    return int(m.group(1)) if m else 0


def light_sync(run, fp, args, t_start):
    """轻量同步：只重建索引+向量（让新笔记即刻可检索），用独立指纹 index_state.json。

    刻意不写 sync_report、不更新全量指纹 sync_state.json——「是否要跑全量同步
    （复验/锚点/PDF/pytest）」的判断不受轻量同步污染，全量 sync 仍会在 Vault 变化时触发。
    """
    changed, why = change_vs_last(fp, INDEX_STATE)
    say("Vault 指纹：%d 篇 md，hash=%s｜%s" % (fp["md_count"], fp["hash"], why))
    if changed is False and not args.no_change:
        run.ok("变更检测", "索引已最新，跳过重建")
        say("      → 索引已最新（%s）" % why)
    else:
        if args.dry_run:
            from vaultmind.ingest import auditor, chunker, scanner
            dd = scanner.scan_docs()
            mm = auditor.audit(dd)
            run.warn("重建索引", "DRY-RUN 跳过（docs=%d chunks≈%d）"
                     % (mm["doc_count"], len(chunker.chunk_all(dd))))
            run.warn("重建向量", "DRY-RUN 跳过")
        else:
            res = run_pipeline()
            secs = "%.1f" % res["metrics"]["elapsed_sec"]
            docs, chunks, links = db_counts()
            run.ok("重建索引", "docs=%d chunks=%d links=%d（%ss）" % (docs, chunks, links, secs))
            say("      → docs=%d chunks=%d links=%d（%ss）" % (docs, chunks, links, secs))
            st = vector.build_embeddings(resume=True)
            run.ok("重建向量", "%d/%d（%d 维）" % (st["embedded"], st["total_chunks"], st["dim"]))
            say("      → %d/%d" % (st["embedded"], st["total_chunks"]))
    say("\n[light] 轻量同步完成（仅索引+向量；复验/锚点/PDF/pytest 请跑全量 sync_vault.py）")
    return finish(run, fp, None, args.dry_run, t_start,
                  state_path=INDEX_STATE, write_report=False)


def finish(run, fp, abl, dry_run, t_start, state_path=STATE, write_report=True):
    dur = time.time() - t_start
    say("\n" + "=" * 62)
    say(" 同步结果：%s（%.1fs）" % ("全绿 ✅" if not run.failed else "存在失败项 ❌", dur))
    for step, st, msg in run.steps:
        say("   [%-4s] %-10s %s" % (st, step, msg))
    if run.metrics:
        say(" 指标变化：")
        for k, (old, new) in run.metrics.items():
            flag = "" if old == new else (" ← 变化" if old is not None else "")
            say("   %-10s %s → %s%s" % (k, old, new, flag))
    say("=" * 62)

    if not dry_run:
        if write_report:
            write_sync_report(run, fp, abl, dur)
        if fp and not run.failed:
            # 仅在成功时记住指纹：失败（如 gold 门禁未过）不落盘，
            # 否则下次会被误判「Vault 未变化」而跳过，掩盖失败。
            save_state(fp, state_path)
    return 1 if run.failed else 0


def write_sync_report(run, fp, abl, dur):
    L = ["# Vault 同步报告（scripts/sync_vault.py）", "",
         "> 生成时间：%s ｜ 耗时 %.1fs ｜ 结果：%s"
         % (datetime.now().strftime("%Y-%m-%d %H:%M"), dur,
            "全绿 ✅" if not run.failed else "存在失败项 ❌"), ""]
    if fp:
        L += ["Vault 指纹：**%d 篇 md**，hash `%s`" % (fp["md_count"], fp["hash"]), ""]
    L += ["## 步骤", "", "| 步骤 | 状态 | 说明 |", "|---|---|---|"]
    for step, st, msg in run.steps:
        L.append("| %s | %s | %s |" % (step, st, msg))
    if run.metrics:
        L += ["", "## 指标变化", "", "| 指标 | 上次 | 本次 |", "|---|---|---|"]
        for k, (old, new) in run.metrics.items():
            L.append("| %s | %s | %s |" % (k, old, new))
    L += ["", "> 锚点一律从 `reports/` 现场解析后回写（防漂移）。",
          "> 复现：`%s scripts\\sync_vault.py`" % PY, ""]
    SYNC_REPORT.write_text("\n".join(L), encoding="utf-8")
    say(" 报告：%s" % SYNC_REPORT)


if __name__ == "__main__":
    sys.exit(main())
