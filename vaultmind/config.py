# -*- coding: utf-8 -*-
"""全局路径与常量（可用环境变量覆盖，便于换机复现）。"""
import os
from pathlib import Path

WORKSPACE = Path(os.environ.get("VAULTMIND_WORKSPACE", r"D:\RAG"))
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
