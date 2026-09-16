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


def chunk_doc(doc: Doc) -> list[Chunk]:
    """把一篇笔记切成带上下文前缀的 chunk 列表。"""
    chunks: list[Chunk] = []
    if not doc.body.strip():
        return chunks
    seq = 0

    def emit(section: str, text: str):
        nonlocal seq
        text = text.strip()
        if not text:
            return
        chunks.append(Chunk(doc.rel, section, seq, _prefix(doc, section), text))
        seq += 1

    parts = H2_SPLIT_RE.split(doc.body)
    preamble = parts[0]
    if preamble.strip():
        emit("概述", preamble)

    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        sec_body = parts[i + 1] if i + 1 < len(parts) else ""
        if not sec_body.strip():
            continue
        if len(sec_body) <= CHUNK_MAX_CHARS:
            emit(heading, sec_body)
            continue
        # 超长小节：按 H3 二次切分
        sub = H3_SPLIT_RE.split(sec_body)
        pre = sub[0]
        if pre.strip():
            if len(pre) <= CHUNK_MAX_CHARS:
                emit(f"{heading} / 概述", pre)
            else:
                for k, piece in enumerate(_split_paras(pre), 1):
                    emit(f"{heading} / 概述 ({k})", piece)
        for j in range(1, len(sub), 2):
            h3 = sub[j].strip()
            t = sub[j + 1] if j + 1 < len(sub) else ""
            if not t.strip():
                continue
            if len(t) <= CHUNK_MAX_CHARS:
                emit(f"{heading} / {h3}", t)
            else:
                for k, piece in enumerate(_split_paras(t), 1):
                    emit(f"{heading} / {h3} ({k})", piece)
    return chunks


def chunk_all(docs) -> list[Chunk]:
    out: list[Chunk] = []
    for d in docs:
        out.extend(chunk_doc(d))
    return out
