# -*- coding: utf-8 -*-
"""pytest 全局配置：确保 vaultmind 可导入。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# 测试之间共享的小工具（如 _doc_anchors）按顶层模块导入
_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))
