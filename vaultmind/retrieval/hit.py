# -*- coding: utf-8 -*-
"""检索命中结构（独立模块，避免循环导入）。"""
from dataclasses import dataclass


@dataclass
class SearchHit:
    chunk_id: int
    doc_id: int
    rel: str
    title: str
    section: str
    prefix: str
    text: str
    score: float
    source: str

    @property
    def body(self) -> str:
        """展示用纯正文：inline 模式下 text 以 prefix 开头，据此精确剥掉前缀行。"""
        t = self.text or ""
        p = self.prefix or ""
        if p and t.startswith(p):
            return t[len(p):].lstrip("\n\r").strip()
        return t.strip()
