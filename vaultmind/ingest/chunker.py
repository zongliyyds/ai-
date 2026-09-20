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

    @property
    def body(self) -> str:
        """展示用纯正文：inline 模式下 text 以 prefix 开头，据此精确剥掉前缀行。"""
        t = self.text or ""
        p = self.prefix or ""
        if p and t.startswith(p):
            return t[len(p):].lstrip("\n\r").strip()
        return t.strip()


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
              prefix_mode: str = "inline") -> list[Chunk]:
    """把一篇笔记切成带上下文前缀的 chunk 列表。

    默认参数 = 正式管道行为。V5 已采纳：默认 prefix_mode=inline（前缀入检索）。
    M6b 消融脚本对 prefix_mode 显式传参、不依赖默认值 → 实验可复现不受影响。

    granularity：
    - "h2"（默认）：以 H2 为单元，超长按 H3/段落二次切分
    - "h3"：H3 优先的细粒度切分（每个 H2 小节都下钻到 H3）
    - "doc"：整篇文档为一块（超长按段落硬切到 max_chars）——最粗粒度
    prefix_mode：
    - "inline"（默认，= 正式管道，V5 已采纳）：前缀并入 text → 进入 FTS tokens 与向量嵌入；
      prefix 字段同时保留该前缀，供展示层用 body 属性精确剥出纯正文（引用不被前缀污染）
    - "field"：前缀只写入 prefix 字段（该字段**不参与** FTS/向量信号）——M6b 的 V1 基线态
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
            # 前缀并入 text（进检索），prefix 字段同时保留一份（供展示层 body 精确剥离）
            chunks.append(Chunk(doc.rel, section, seq, prefix, prefix + "\n" + text))
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
        # 概述（首个 H2 之前的前言）同样受 max_chars 约束：超长按段落/句子切分，
        # 避免单个 chunk 过大撞上 bge-m3 的 num_ctx=4096 上限（与 h3/doc 路径一致）。
        emit_pieces("概述", preamble)

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
