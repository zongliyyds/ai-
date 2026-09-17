# -*- coding: utf-8 -*-
"""结构感知分块：以 H2 为基本单元，超 600 字按 H3/段落二次切分；元数据前缀注入。"""
import re
from dataclasses import dataclass

from vaultmind.config import CHUNK_MAX_CHARS
from vaultmind.ingest.scanner import Doc

H2_SPLIT_RE = re.compile(r"^(##\s+.*)$", re.M)
H3_SPLIT_RE = re.compile(r"^(###\s+.*)$", re.M)
PARA_SPLIT_RE = re.compile(r"\n\s*\n")
SENT_SPLIT_RE = re.compile(r"(?<=[。！？.!?])\s*")


@dataclass
class Chunk:
    doc_rel: str
    section: str
    seq: int
    prefix: str
    text: str


def _prefix(doc: Doc, section: str) -> str:
    tags = "、".join(doc.tags) if doc.tags else "-"
    return f"[文档: {doc.title} | 章节: {section} | 标签: {tags}]"


def _hard_split(text: str, max_chars: int) -> list[str]:
    """超长文本按句子边界切分；单句仍超长则按字符硬切。"""
    if len(text) <= max_chars:
        return [text]
    sents = [s for s in SENT_SPLIT_RE.split(text) if s.strip()]
    parts, buf = [], ""
    for s in sents:
        if buf and len(buf) + len(s) > max_chars:
            parts.append(buf)
            buf = s
        else:
            buf += s
    if buf:
        parts.append(buf)
    out = []
    for p in parts:
        while len(p) > max_chars:
            out.append(p[:max_chars])
            p = p[max_chars:]
        if p:
            out.append(p)
    return out


def _split_paras(text: str, max_chars: int = CHUNK_MAX_CHARS) -> list[str]:
    """按空行段落聚合到接近 max_chars。"""
    paras = [p.strip() for p in PARA_SPLIT_RE.split(text) if p.strip()]
    if not paras:
        return []
    parts, buf = [], ""
    for p in paras:
        if buf and len(buf) + len(p) + 2 > max_chars:
            parts.extend(_hard_split(buf, max_chars))
            buf = p
        else:
            buf = (buf + "\n\n" + p) if buf else p
    if buf:
        parts.extend(_hard_split(buf, max_chars))
    return parts


def chunk_doc(doc: Doc, granularity: str = "h2", max_chars: int = CHUNK_MAX_CHARS,
              prefix_mode: str = "field") -> list[Chunk]:
    """把一篇笔记切成带上下文前缀的 chunk 列表。

    默认参数 = 正式管道行为（M6b 分块粒度消融只通过传参改变分块，正式路径零改动）。

    granularity：
    - "h2"（默认，= 正式管道）：以 H2 为单元，超长按 H3/段落二次切分
    - "h3"：H3 优先的细粒度切分（每个 H2 小节都下钻到 H3）
    - "doc"：整篇文档为一块（超长按段落硬切到 max_chars）——最粗粒度
    prefix_mode：
    - "field"（默认，= 正式管道）：前缀只写入 prefix 字段（该字段**不参与** FTS/向量信号）
    - "inline"：前缀并入 text → 进入 FTS tokens 与向量嵌入，即「前缀真正被检索」
    - "none"：不注入前缀
    """
    chunks: list[Chunk] = []
    if not doc.body.strip():
        return chunks
    seq = 0

    def emit(section: str, text: str):
        nonlocal seq
        text = text.strip()
        if not text:
            return
        prefix = _prefix(doc, section) if prefix_mode != "none" else ""
        if prefix_mode == "inline" and prefix:
            chunks.append(Chunk(doc.rel, section, seq, "", prefix + "\n" + text))
        else:
            chunks.append(Chunk(doc.rel, section, seq, prefix, text))
        seq += 1

    def emit_pieces(section: str, text: str):
        """按段落聚合切分后逐块发出（多块才带序号）。"""
        pieces = _split_paras(text, max_chars)
        for k, piece in enumerate(pieces, 1):
            emit(section + (" (%d)" % k if len(pieces) > 1 else ""), piece)

    if granularity == "doc":
        emit_pieces("全文", doc.body)
        return chunks

    if granularity == "h3":
        parts = H2_SPLIT_RE.split(doc.body)
        pre = parts[0]
        if pre.strip():
            emit_pieces("概述", pre)
        for i in range(1, len(parts), 2):
            heading = parts[i].strip()
            sec_body = parts[i + 1] if i + 1 < len(parts) else ""
            if not sec_body.strip():
                continue
            sub = H3_SPLIT_RE.split(sec_body)
            sub_pre = sub[0]
            if sub_pre.strip():
                emit_pieces(f"{heading} / 概述", sub_pre)
            for j in range(1, len(sub), 2):
                h3 = sub[j].strip()
                t = sub[j + 1] if j + 1 < len(sub) else ""
                if not t.strip():
                    continue
                emit_pieces(f"{heading} / {h3}", t)
        return chunks

    # granularity == "h2"：逐字保留正式管道逻辑，仅把长度上限参数化
    parts = H2_SPLIT_RE.split(doc.body)
    preamble = parts[0]
    if preamble.strip():
        emit("概述", preamble)

    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        sec_body = parts[i + 1] if i + 1 < len(parts) else ""
        if not sec_body.strip():
            continue
        if len(sec_body) <= max_chars:
            emit(heading, sec_body)
            continue
        # 超长小节：按 H3 二次切分
        sub = H3_SPLIT_RE.split(sec_body)
        pre = sub[0]
        if pre.strip():
            if len(pre) <= max_chars:
                emit(f"{heading} / 概述", pre)
            else:
                for k, piece in enumerate(_split_paras(pre, max_chars), 1):
                    emit(f"{heading} / 概述 ({k})", piece)
        for j in range(1, len(sub), 2):
            h3 = sub[j].strip()
            t = sub[j + 1] if j + 1 < len(sub) else ""
            if not t.strip():
                continue
            if len(t) <= max_chars:
                emit(f"{heading} / {h3}", t)
            else:
                for k, piece in enumerate(_split_paras(t, max_chars), 1):
                    emit(f"{heading} / {h3} ({k})", piece)
    return chunks


def chunk_all(docs, **kwargs) -> list[Chunk]:
    out: list[Chunk] = []
    for d in docs:
        out.extend(chunk_doc(d, **kwargs))
    return out
