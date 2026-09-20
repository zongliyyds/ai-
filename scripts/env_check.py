# -*- coding: utf-8 -*-
r"""VaultMind 环境体检（换机复现第一件事）：只读检查，输出 PASS/WARN/FAIL 清单。

用法：D:\python\python.exe scripts\env_check.py
退出码：0=全部 PASS；1=存在 FAIL；2=仅 WARN。
"""
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vaultmind.config import DATA_DIR, DB_PATH, VAULT_ROOT, WORKSPACE  # noqa: E402

REQUIRED_PACKAGES = ["fastapi", "uvicorn", "jieba", "numpy",
                     "fitz", "pytest", "httpx"]
REQUIRED_MODELS = ["bge-m3", "qwen2.5:7b-instruct"]


def main() -> int:
    rows = []  # (级别, 项目, 结果)

    def add(level, item, msg):
        rows.append((level, item, msg))

    # 1. Python 版本
    v = sys.version_info
    add("PASS" if v >= (3, 10) else "FAIL", "Python 版本",
        "%d.%d.%d（%s）" % (v[0], v[1], v[2], sys.executable))

    # 2. 依赖包
    missing = [p for p in REQUIRED_PACKAGES if importlib.util.find_spec(p) is None]
    add("PASS" if not missing else "FAIL", "依赖包",
        "缺失：%s" % missing if missing else "全部可导入")

    # 3. 工作区与知识库
    add("PASS" if WORKSPACE.exists() else "FAIL", "工作区", str(WORKSPACE))
    if VAULT_ROOT.exists():
        md = len(list(VAULT_ROOT.rglob("*.md")))
        add("PASS", "知识库（只读源）", "%s（%d 篇 md）" % (VAULT_ROOT, md))
    else:
        add("FAIL", "知识库（只读源）", "不存在：%s（可用 VAULTMIND_VAULT 环境变量指定）" % VAULT_ROOT)

    # 4. 索引库
    if DB_PATH.exists():
        con = sqlite3.connect(str(DB_PATH))
        cur = con.cursor()
        docs = cur.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
        chunks = cur.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        links = cur.execute("SELECT COUNT(*) FROM links").fetchone()[0]
        con.close()
        add("PASS", "索引库", "docs=%d chunks=%d links=%d" % (docs, chunks, links))
    else:
        add("FAIL", "索引库", "缺失（运行 python -m vaultmind.ingest）")

    # 5. 向量索引
    npy = DATA_DIR / "embeddings.npy"
    ids = DATA_DIR / "chunk_ids.json"
    if npy.exists() and ids.exists():
        n = len(json.loads(ids.read_text(encoding="utf-8")))
        add("PASS", "向量索引", "embeddings.npy（id 映射 %d 条）" % n)
    else:
        add("FAIL", "向量索引", "缺失（运行 python -m vaultmind.search --build-vectors）")

    # 6. Ollama 与模型
    try:
        import httpx
        r = httpx.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if r.status_code == 200:
            names = {m["name"] for m in r.json().get("models", [])}
            # 精确匹配或带后缀变体（如 qwen2.5:7b-instruct-q4_0）；绝不退化成
            # split(":")[0] 只比对主名——否则只装 qwen2.5:7b（无 -instruct）也会 PASS。
            miss = [m for m in REQUIRED_MODELS
                    if not any(n == m or n.startswith(m + ":") for n in names)]
            add("PASS" if not miss else "FAIL", "Ollama 模型",
                "缺失：%s（ollama pull ...）" % miss if miss else "bge-m3 + qwen2.5:7b-instruct 齐")
        else:
            add("FAIL", "Ollama", "HTTP %d" % r.status_code)
    except Exception as e:
        add("FAIL", "Ollama", "不可达（%s）。先执行 ollama serve" % e)

    # 7. 评测与报告
    gold = ROOT / "eval" / "gold_set.jsonl"
    if gold.exists():
        items = [json.loads(l) for l in gold.read_text(encoding="utf-8").splitlines() if l.strip()]
        ok = all(i.get("status") == "approved" for i in items)
        add("PASS" if len(items) == 60 and ok else "WARN", "gold 评测集",
            "%d 条（approved=%s）" % (len(items), ok))
    else:
        add("FAIL", "gold 评测集", "缺失")
    for name in ["baseline.md", "ablation.md", "m4_smoke.md", "gold_finalization.md"]:
        p = ROOT / "reports" / name
        add("PASS" if p.exists() else "WARN", "报告 " + name, str(p))

    # 8. git
    import subprocess
    git = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                         capture_output=True, text=True)
    add("PASS" if git.returncode == 0 else "WARN", "git 快照",
        git.stdout.strip() if git.returncode == 0 else "非 git 目录")

    # ---- 输出 ----
    for level, item, msg in rows:
        mark = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]"}[level]
        print("%s %-14s %s" % (mark, item, msg))
    fails = sum(1 for r in rows if r[0] == "FAIL")
    warns = sum(1 for r in rows if r[0] == "WARN")
    print("-" * 60)
    print("结论：%d PASS / %d WARN / %d FAIL" % (len(rows) - fails - warns, warns, fails))
    return 1 if fails else (2 if warns else 0)


if __name__ == "__main__":
    sys.exit(main())
