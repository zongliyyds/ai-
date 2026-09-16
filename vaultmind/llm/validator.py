# -*- coding: utf-8 -*-
"""M4 引用校验与拒答判定（纯函数，不依赖模型，可离线单测）。

口径：
- 引用可追溯 = 回答中出现的每个 [S#] 编号都落在本次上下文 1..n 范围内；
- 拒答 = 规则启发式话术识别（提示词约束 + 规则校验双层，不用外部模型打分）。
"""
import re

CITE_RE = re.compile(r"[\[【]([Ss][Ss\d\s,，、]*)[\]】]")
_NUM_RE = re.compile(r"\d+")

REFUSAL_PATTERNS = (
    "知识库中没有", "没有相关信息", "无法回答", "未找到相关", "找不到相关",
    "资料中未提及", "参考资料中没", "无法提供", "抱歉，我无法", "不予回答",
    "未提供相关", "无从得知", "没有提供相关",
)


def extract_cites(text: str) -> list[int]:
    """提取回答中出现的全部引用编号（按出现顺序，含重复）。

    支持单编号 `[S1]`、列表式 `[S1, S2, S4]` / `[S1，S3、S5]`、带空格 `[S 3]`
    与中文括号 `【S1】`（模型常见格式变异）。
    """
    ids = []
    for m in CITE_RE.findall(text or ""):
        ids.extend(int(x) for x in _NUM_RE.findall(m))
    return ids


def validate_cites(answer: str, n_citations: int) -> dict:
    """校验引用编号合法性。n_citations = 本次上下文实际块数。"""
    ids = extract_cites(answer)
    valid = sorted({i for i in ids if 1 <= i <= n_citations})
    invalid = sorted({i for i in ids if i < 1 or i > n_citations})
    return {
        "cited_ids": ids,
        "valid_ids": valid,
        "invalid_ids": invalid,
        "citation_valid": not invalid,
        "has_citation": bool(ids),
    }


def is_refusal(answer: str) -> bool:
    """启发式拒答判定：短回答 + 命中拒答话术。"""
    text = (answer or "").strip()
    if not text or len(text) > 800:
        return False
    return any(p in text for p in REFUSAL_PATTERNS)
