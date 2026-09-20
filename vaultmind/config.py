# -*- coding: utf-8 -*-
"""全局路径与常量（可用环境变量覆盖，便于换机复现）。"""
import os
from pathlib import Path

# 工作区默认 = 仓库根目录（config.py 位于 <仓库>/vaultmind/ 下，向上两级即仓库根），
# 换机 clone 到任意路径可自定位；仍可用 VAULTMIND_WORKSPACE 覆盖（不再硬编码 D:\RAG）。
_WORKSPACE_DEFAULT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(os.environ.get("VAULTMIND_WORKSPACE", str(_WORKSPACE_DEFAULT)))
# 知识库源默认仍指向本机 Obsidian Vault；换机用 VAULTMIND_VAULT 覆盖（README 已注明）。
VAULT_ROOT = Path(os.environ.get("VAULTMIND_VAULT", r"D:\AI-Knowledge-Vault\AI-Knowledge-Vault"))

DATA_DIR = WORKSPACE / "data"
DB_PATH = DATA_DIR / "vaultmind.db"
AUDIT_JSON = DATA_DIR / "audit.json"
AUDIT_REPORT = WORKSPACE / "reports" / "audit_report.md"
BASELINE_JSON = WORKSPACE / "reports" / "baseline_audit.json"

# 结构感知分块参数
CHUNK_MAX_CHARS = 600   # H2 小节超过该长度则按 H3/段落二次切分

# 孤儿统计排除的顶层目录（系统目录不参与"孤儿"判定）
ORPHAN_SKIP_TOP = ("90-System", ".obsidian")
