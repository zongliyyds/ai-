# -*- coding: utf-8 -*-
r"""SQLite 索引库：docs / chunks / links + FTS5（jieba 分词）全文索引。

红线：索引是派生产物，只写 D:\RAG\data，绝不触碰 Vault。
"""
import logging
import sqlite3

from vaultmind.config import DB_PATH
from vaultmind.ingest.auditor import inbound_counter, link_stem, stem2rel_map
from vaultmind.ingest.scanner import LINK_FULL_RE

SCHEMA = """
CREATE TABLE IF NOT EXISTS docs (
  id INTEGER PRIMARY KEY,
  rel TEXT UNIQUE NOT NULL,
  title TEXT,
  ftype TEXT,
  status TEXT,
  tags TEXT,
  chars INTEGER,
  body_chars INTEGER,
  h2 INTEGER,
  h3 INTEGER,
  outlinks INTEGER,
  deadlinks INTEGER,
  inlinks INTEGER,
  has_fm INTEGER,
  error TEXT
);
CREATE TABLE IF NOT EXISTS chunks (
  id INTEGER PRIMARY KEY,
  doc_id INTEGER NOT NULL,
  section TEXT,
  seq INTEGER,
  prefix TEXT,
  text TEXT,
  tokens TEXT
);
CREATE TABLE IF NOT EXISTS links (
  id INTEGER PRIMARY KEY,
  src TEXT NOT NULL,
  target TEXT NOT NULL,
  alias TEXT,
  valid INTEGER
);
CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_links_src ON links(src);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
  tokens,
  content='chunks',
  content_rowid='id',
  tokenize='unicode61'
);
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
  INSERT INTO chunks_fts(rowid, tokens) VALUES (new.id, new.tokens);
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
  INSERT INTO chunks_fts(chunks_fts, rowid, tokens) VALUES ('delete', old.id, old.tokens);
END;
CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
  INSERT INTO chunks_fts(chunks_fts, rowid, tokens) VALUES ('delete', old.id, old.tokens);
  INSERT INTO chunks_fts(rowid, tokens) VALUES (new.id, new.tokens);
END;
"""


def build_db(docs, chunks, db_path=None) -> dict:
    """重建索引库（清空后全量写入），返回统计信息。"""
    import jieba  # 延迟导入：词典构建较慢，仅索引时需要
    jieba.setLogLevel(logging.WARNING)

    db_path = db_path or DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.executescript(SCHEMA)
    cur = con.cursor()
    cur.execute("DELETE FROM links")
    cur.execute("DELETE FROM chunks")
    cur.execute("DELETE FROM docs")

    s2r = stem2rel_map(docs)
    inbound = inbound_counter(docs, s2r)

    cur.executemany(
        "INSERT INTO docs(rel,title,ftype,status,tags,chars,body_chars,h2,h3,"
        "outlinks,deadlinks,inlinks,has_fm,error) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(d.rel, d.title, d.ftype, d.status, "、".join(d.tags),
          len(d.text), len(d.body), d.h2, d.h3, len(d.links),
          sum(1 for l in d.links if link_stem(l) not in s2r),
          inbound[d.rel], 1 if d.has_fm else 0, d.error) for d in docs],
    )
    doc_ids = {rel: i for rel, i in cur.execute("SELECT rel, id FROM docs")}

    link_rows = []
    for d in docs:
        for m in LINK_FULL_RE.finditer(d.body):
            target = m.group(1).strip()
            alias = (m.group(2) or "").strip()
            link_rows.append((d.rel, target, alias,
                              1 if link_stem(target) in s2r else 0))
    cur.executemany(
        "INSERT INTO links(src,target,alias,valid) VALUES(?,?,?,?)", link_rows)

    chunk_rows = []
    for c in chunks:
        tokens = " ".join(jieba.cut(c.text))
        chunk_rows.append((doc_ids[c.doc_rel], c.section, c.seq,
                           c.prefix, c.text, tokens))
    cur.executemany(
        "INSERT INTO chunks(doc_id,section,seq,prefix,text,tokens) "
        "VALUES(?,?,?,?,?,?)", chunk_rows)

    con.commit()
    stats = {
        "docs": cur.execute("SELECT COUNT(*) FROM docs").fetchone()[0],
        "chunks": len(chunk_rows),
        "links": len(link_rows),
        "fts_rows": cur.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0],
        "db_bytes": db_path.stat().st_size,
        "db_path": str(db_path),
    }
    con.close()
    return stats
