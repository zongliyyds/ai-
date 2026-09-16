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
