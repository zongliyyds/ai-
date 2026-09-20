# -*- coding: utf-8 -*-
"""M4 生成器：Ollama qwen2.5:7b-instruct 本地生成（默认本地，无云端调用）。"""
import httpx

DEFAULT_MODEL = "qwen2.5:7b-instruct"
DEFAULT_URL = "http://127.0.0.1:11434"

SYSTEM_PROMPT = (
    "你是 VaultMind 个人知识库问答助手。必须遵守："
    "①只能依据【参考资料】回答，每个事实陈述后标注来源编号，格式 [S#]；"
    "②参考资料不足以回答时，明确说明知识库中没有相关信息，严禁编造或使用外部知识补充事实；"
    "③用简体中文回答，先结论后要点，保持简洁。"
)


def generate(question: str, context: str, model: str = DEFAULT_MODEL,
             base_url: str = DEFAULT_URL, temperature: float = 0.2,
             timeout: float = 180.0) -> tuple[str, dict]:
    """调用 Ollama /api/chat 生成回答 → (回答文本, 元信息字典)。"""
    user = ("【问题】%s\n\n【参考资料】\n%s\n\n"
            "请回答（引用编号格式 [S#]；资料不足时明确拒答）。" % (question, context))
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        "options": {"temperature": temperature},
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(base_url + "/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            elapsed = resp.elapsed.total_seconds()
    except httpx.HTTPError as e:
        # 把连接拒绝/超时/HTTP 400（含上下文超限）统一包成 RuntimeError，
        # 与 embed_texts 保持一致 → CLI 与 API 都能按「依赖故障」处理，而非裸 traceback。
        raise RuntimeError(
            "本地生成失败（Ollama）：%s。请确认已执行 `ollama serve` 且模型已加载。" % e) from e
    return data["message"]["content"], {
        "model": data.get("model", model),
        "generation_s": round(elapsed, 2),
        "eval_count": data.get("eval_count"),
        "prompt_eval_count": data.get("prompt_eval_count"),
    }
