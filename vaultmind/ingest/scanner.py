# -*- coding: utf-8 -*-
"""只读扫描 Vault：frontmatter 解析、标题计数、双链抽取（口径与基线一致）。

红线：本模块对 Vault 只读，绝不写入/修改源文件。
"""
import os
import re
from dataclasses import dataclass, field

from vaultmind.config import VAULT_ROOT

LINK_RE = re.compile(r"\[\[([^\]\|#]+)")                       # 出链目标（与基线口径一致）
LINK_FULL_RE = re.compile(r"\[\[([^\]\|#]+)(?:\|([^\]]+))?\]\]")  # 目标 + 别名
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
TYPE_RE = re.compile(r"^type:\s*(.+)$", re.M)
STATUS_RE = re.compile(r"^status:\s*(.+)$", re.M)
TAGS_RE = re.compile(r"^tags:\s*(.+)$", re.M)
H1_RE = re.compile(r"^#\s+(.+)$", re.M)
H2_RE = re.compile(r"^##\s+\S", re.M)
H3_RE = re.compile(r"^###\s+\S", re.M)


@dataclass
class Doc:
    rel: str
    path: str
    text: str = ""
    body: str = ""
    fm_raw: str = ""
    ftype: str | None = None
    status: str | None = None
    tags: list[str] = field(default_factory=list)
    has_fm: bool = False
    error: str | None = None
    links: list[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        m = H1_RE.search(self.body)
        if m:
            return m.group(1).strip()
        return os.path.splitext(os.path.basename(self.rel))[0]

    @property
    def h2(self) -> int:
        return len(H2_RE.findall(self.body))

    @property
    def h3(self) -> int:
        return len(H3_RE.findall(self.body))


def _parse_tags(fm_raw: str) -> list[str]:
    m = TAGS_RE.search(fm_raw)
    if not m:
        return []
    value = m.group(1).strip()
    tags = [t.strip(" []\"'`") for t in re.split(r"[,\n]+", value)]
    return [t for t in tags if t]


def scan_docs(root=None) -> list[Doc]:
    """遍历 Vault，解析所有 .md（跳过隐藏目录如 .obsidian）。只读。"""
    root = root or VAULT_ROOT
    docs: list[Doc] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for fn in filenames:
            if not fn.lower().endswith(".md"):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root).replace("\\", "/")
            doc = Doc(rel=rel, path=p)
            try:
                with open(p, encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:  # 记录读取失败，不中断整体扫描
                doc.error = str(e)
                docs.append(doc)
                continue
            doc.text = text
            m = FM_RE.match(text)
            if m:
                doc.fm_raw = m.group(1)
                doc.body = text[m.end():]
                doc.has_fm = True
            else:
                doc.body = text
            fm = doc.fm_raw
            t = TYPE_RE.search(fm)
            s = STATUS_RE.search(fm)
            doc.ftype = t.group(1).strip() if t else None
            doc.status = s.group(1).strip() if s else None
            doc.tags = _parse_tags(fm)
            doc.links = [l.strip() for l in LINK_RE.findall(doc.body)]
            docs.append(doc)
    return docs
