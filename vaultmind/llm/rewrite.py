# -*- coding: utf-8 -*-
"""M6 查询改写：规则版（确定性）与 LLM 版（本地 qwen，不添加新信息）。

背景：坏例账本 11 条未进 Top-5，其中 10 条是"裸标题"hard 型
（如「## 背景 是什么？怎么做？」）——只有章节名、无文档语境。
"""
import httpx

REWRITE_MODEL = "qwen2.5:7b-instruct"
REWRITE_URL = "http://127.0.0.1:11434"

_SUFFIXES = ("是什么？怎么做？", "是什么？怎么实现？", "讲了什么？", "怎么做？")


def rule_rewrite(question: str) -> str:
    """规则改写：仅改写「## 标题 + 模板后缀」的裸标题型问题；其余原样返回。

    - 去 markdown 标记、去模板后缀 → 更接近自然查询；
    - 含文档名的 easy 型问题（非 ## 开头）不改写，避免破坏其强信号。
    """
    q = question.strip()
    if not q.startswith("## "):
        return q
    q = q[3:].strip()
    for suf in _SUFFIXES:
        if q.endswith(suf):
            q = q[: -len(suf)].strip() + " 指的是什么？"
            break
    return q


LLM_REWRITE_PROMPT = (
    "你是查询改写器。把下面这个从知识库章节标题派生的问题改写成一个自然的完整问句。"
    "要求：①不得添加任何新信息、不得猜测具体内容；②保留原意；③只输出改写后的问句，"
    "不要解释。\n\n问题：%s\n改写："
)


def llm_rewrite(question: str, model: str = REWRITE_MODEL,
                base_url: str = REWRITE_URL, timeout: float = 60.0) -> str:
    """LLM 改写：本地 qwen2.5:7b-instruct，温度 0。"""
    payload = {
        "model": model,
        "stream": False,
        "messages": [{"role": "user", "content": LLM_REWRITE_PROMPT % question}],
        "options": {"temperature": 0},
    }
    r = httpx.post(base_url + "/api/chat", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()
