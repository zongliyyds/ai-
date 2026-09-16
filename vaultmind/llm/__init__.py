# -*- coding: utf-8 -*-
"""M4 生成链路：上下文组装 / 本地生成 / 引用校验与拒答判定。"""
from vaultmind.llm.context import Citation, build_context  # noqa: F401
from vaultmind.llm.validator import extract_cites, is_refusal, validate_cites  # noqa: F401
