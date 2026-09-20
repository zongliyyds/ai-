# -*- coding: utf-8 -*-
r"""VaultMind 仓库打包（白名单 + 红线探针）：产出可分发 zip，绝不包含 Vault 内容。

用法：D:\python\python.exe scripts\package_repo.py
产出：dist\vaultmind-source-YYYYMMDD.zip
红线探针：打包后对 zip 内文件做三道扫描——①路径含 AI-Knowledge-Vault ②正文含
Vault 绝对路径 ③手机号正则命中 → 任一命中即 FAIL（不产出 zip）。
"""
import json
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
OUT = DIST / ("vaultmind-source-%s.zip" % datetime.now().strftime("%Y%m%d"))

# 白名单（相对路径；目录递归包含）
INCLUDE = [
    "README.md", "PLAN.md", "FEASIBILITY.md", "CHANGELOG.md",
    "requirements.txt", ".gitignore",
    "run_api.bat", "stop_api.bat", "search.bat", "launcher.py",
    "vaultmind/", "tests/", "scripts/",
    "docs/",
]
REPORT_INCLUDE = [  # 报告仅收录不含 Vault 摘录的
    "baseline.md", "ablation.md", "m6b_chunk_ablation.md", "m4_smoke.md", "gold_finalization.md",
    "audit_report.md", "m2_selfcheck.md", "sync_report.md",
]
GOLD_STRIP_FIELDS = ("answer_points",)  # gold 分发版剔除正文摘录

PHONE_RE = re.compile(r"1[3-9]\d{9}")


def sanitized_gold(src: Path, dst: Path):
    items = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    clean = [{k: v for k, v in it.items() if k not in GOLD_STRIP_FIELDS} for it in items]
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in clean),
                   encoding="utf-8")


def main() -> int:
    DIST.mkdir(exist_ok=True)
    tmp = DIST / "_pkg_tmp"
    if tmp.exists():
        import shutil
        shutil.rmtree(tmp)
    tmp.mkdir()

    SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git"}
    SKIP_SUFFIX = (".pyc", ".pyo")

    def copy_rel(rel: str):
        src = ROOT / rel
        if not src.exists():
            print("[WARN] 白名单缺失，跳过：%s" % rel)
            return
        if src.is_dir():
            for p in sorted(src.rglob("*")):
                if not p.is_file():
                    continue
                # 编译缓存/测试缓存不进交付包（2026-09-17 打包体积核查发现）
                if p.suffix in SKIP_SUFFIX or any(
                        part in SKIP_DIRS for part in p.relative_to(src).parts):
                    continue
                dst = tmp / rel / p.relative_to(src)
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(p.read_bytes())
        else:
            dst = tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())

    for rel in INCLUDE:
        copy_rel(rel)
    for name in REPORT_INCLUDE:
        copy_rel("reports/" + name)
    copy_rel("reports/knowledge_drafts/")
    # 立项书属内部规划文档（含知识库统计与摘录风险），不进分发包
    (tmp / "docs" / "立项书-详细版.md").unlink(missing_ok=True)
    # gold 分发版：剔除 answer_points 正文摘录
    sanitized_gold(ROOT / "eval" / "gold_set.jsonl", tmp / "eval" / "gold_set.jsonl")

    # ---- 红线探针（打包后扫描） ----
    bad = []
    for p in sorted(tmp.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(tmp))
        if p.suffix in (".pyc", ".pyo"):
            bad.append((rel, "编译缓存(.pyc)进了包"))
            continue
        if "AI-Knowledge-Vault" in rel:
            bad.append((rel, "文件名含 Vault 名"))
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if PHONE_RE.search(text):
            bad.append((rel, "正文疑似含手机号"))
    # 结构探针：摘录文件不得出现在包内
    for forbidden in ["candidates.jsonl", "candidates_review.md", "rewrites_cache.json"]:
        if (tmp / forbidden).exists() or any(forbidden in str(p.relative_to(tmp))
                                             for p in tmp.rglob("*")):
            bad.append((forbidden, "含 Vault 摘录的文件进了包"))
    # gold 分发版探针：不得携带正文摘录字段
    gold_in_zip = tmp / "eval" / "gold_set.jsonl"
    if gold_in_zip.exists():
        for line in gold_in_zip.read_text(encoding="utf-8").splitlines():
            if line.strip() and "answer_points" in json.loads(line):
                bad.append(("eval/gold_set.jsonl", "仍含 answer_points 正文摘录"))
                break
    if bad:
        print("[FAIL] 红线探针命中，拒绝打包：")
        for rel, why in bad:
            print("  - %s：%s" % (rel, why))
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)   # FAIL 也要清理临时目录，不留 _pkg_tmp
        return 1

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(tmp.rglob("*")):
            if p.is_file():
                # as_posix()：arcname 统一用正斜杠，避免 Windows 反斜杠混入 zip，
                # 否则 Unix/macOS 解压会得到带反斜杠的"单文件"而非目录层级。
                z.write(p, "vaultmind/" + p.relative_to(tmp).as_posix())
    import shutil
    shutil.rmtree(tmp)
    size = OUT.stat().st_size
    print("[PASS] 红线探针通过（无 Vault 路径 / 无手机号）")
    print("[PASS] 打包完成：%s（%.1f KB）" % (OUT, size / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
