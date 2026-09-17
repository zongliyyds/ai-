# -*- coding: utf-8 -*-
r"""校验：当前 chunker 的默认分块与正式索引库是否**逐字节一致**。

为什么需要它：M6b 给 `chunk_doc/chunk_all` 加了 `granularity`/`max_chars`/`prefix_mode`
三个可选参数，并承诺「默认值 = 正式管道行为」。本脚本给出可执行的证据：
用默认参数重新分块整个 Vault，和 `data/vaultmind.db` 里的 (rel, seq, section, prefix, text)
序列逐条比对；不一致就打印第一处差异。

用法：D:\python\python.exe scripts\verify_chunker_parity.py
退出码：0 = 一致；1 = 不一致（或索引库为空/过期，先跑 `python -m vaultmind.ingest`）。
只读 Vault，只读索引库，不写任何文件。
"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vaultmind.config import DB_PATH                    # noqa: E402
from vaultmind.ingest.chunker import chunk_all          # noqa: E402
from vaultmind.ingest.scanner import scan_docs          # noqa: E402


def main() -> int:
    docs = scan_docs()
    mine = sorted((c.doc_rel, c.seq, c.section, c.prefix, c.text)
                  for c in chunk_all(docs))

    con = sqlite3.connect(str(DB_PATH))
    rows = con.execute(
        "SELECT d.rel, c.seq, c.section, c.prefix, c.text FROM chunks c "
        "JOIN docs d ON d.id = c.doc_id").fetchall()
    con.close()
    rows = sorted(tuple(r) for r in rows)

    print("Vault 只读扫描：%d 篇 ｜ 正式索引库：%d 块 ｜ 现分块：%d 块"
          % (len(docs), len(rows), len(mine)))
    if rows == mine:
        print("IDENTICAL：默认分块与正式索引逐字节一致（chunker 默认路径零改动）")
        return 0
    for i in range(min(len(rows), len(mine))):
        if rows[i] != mine[i]:
            print("FIRST_DIFF at #%d\n  db  = %r\n  new = %r" % (i, rows[i], mine[i]))
            break
    else:
        print("长度不一致：db=%d vs new=%d" % (len(rows), len(mine)))
    print("不一致提示：若 Vault 有新笔记，先跑 D:\\python\\python.exe -m vaultmind.ingest 重建索引。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
