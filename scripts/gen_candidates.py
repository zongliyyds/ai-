# -*- coding: utf-8 -*-
r"""候选问题生成器：从高价值笔记的 H2 结构模板化派生候选问题池。

红线（M3）：候选只做结构派生、不用 LLM 生成，gold 定稿必须人工完成。
用法：D:\python\python.exe scripts\gen_candidates.py [--limit 220]
产出：eval/candidates.jsonl + reports/candidates_review.md（人读版）
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vaultmind.ingest.chunker import H2_SPLIT_RE  # noqa: E402
from vaultmind.ingest.scanner import scan_docs  # noqa: E402
from vaultmind.ingest.auditor import inbound_counter, stem2rel_map  # noqa: E402

CAND_PATH = ROOT / "eval" / "candidates.jsonl"
REVIEW_PATH = ROOT / "reports" / "candidates_review.md"

MAX_PER_DOC = 5
TOP_INBOUND = 25
TOP_LARGE = 15
PER_TYPE = 3
MIN_SEC_CHARS = 40
MIN_H2 = 2


def first_line(text: str) -> str:
    for line in text.strip().splitlines():
        line = line.strip()
        if line:
            return line[:80]
    return ""


def select_docs(docs):
    s2r = stem2rel_map(docs)
    inbound = inbound_counter(docs, s2r)
    by_rel = {d.rel: d for d in docs}
    selected, seen = [], set()

    def add(rel):
        if rel in seen or rel not in by_rel:
            return
        d = by_rel[rel]
        if d.h2 < MIN_H2 or not d.body.strip():
            return
        seen.add(rel)
        selected.append(d)

    for rel, _ in inbound.most_common(TOP_INBOUND):
        add(rel)
    for rel, _ in sorted([(d.rel, len(d.text)) for d in docs],
                         key=lambda x: -x[1])[:TOP_LARGE]:
        add(rel)
    # 类型覆盖：每种 type 补采若干篇
    by_type = {}
    for d in docs:
        by_type.setdefault(d.ftype or "NO_FRONTMATTER", []).append(d)
    for t, ds in by_type.items():
        for d in ds[:PER_TYPE]:
            add(d.rel)
    return selected


def gen_candidates(docs, limit=220):
    out = []
    n = 0
    for doc in select_docs(docs):
        parts = H2_SPLIT_RE.split(doc.body)
        secs = []
        for i in range(1, len(parts), 2):
            heading = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""
            if len(body) >= MIN_SEC_CHARS:
                secs.append((heading, body))
        for j, (heading, body) in enumerate(secs[:MAX_PER_DOC]):
            if n >= limit:
                return out
            if j % 2 == 0:
                # family A 明确型（较易）：含文档名
                question = "%s 中的「%s」讲了什么？" % (doc.title, heading)
                family = "easy"
            else:
                # family B 转述型（较难）：只给标题短语
                question = "%s 是什么？怎么做？" % heading
                family = "hard"
            n += 1
            out.append({
                "id": "cand-%03d" % n,
                "question": question,
                "docs": [doc.rel],
                "source_doc": doc.rel,
                "section": heading,
                "family": family,
                "answer_points": [first_line(body)],
            })
    return out


def write_review(cands, groups):
    L = []
    A = L.append
    A("# M3 候选问题池（人读版，供定稿筛选）")
    A("")
    A("> 共 %d 条候选。请挑 60 条：口语化改写 question、核对/补充 docs、补 answer_points，"
      "把选中条目 status 改为 approved 放入 eval/gold_set.jsonl。" % len(cands))
    A("")
    for rel, items in groups.items():
        A("## %s" % rel)
        A("")
        for it in items:
            A("- [ ] `%s`（%s）%s" % (it["id"], it["family"], it["question"]))
            A("  - 章节：%s ｜ 要点草稿：%s" % (it["section"], it["answer_points"][0]))
        A("")
    REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_PATH.write_text("\n".join(L) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="VaultMind M3 候选问题生成器")
    ap.add_argument("--limit", type=int, default=220)
    args = ap.parse_args(argv)

    docs = scan_docs()
    cands = gen_candidates(docs, limit=args.limit)
    CAND_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CAND_PATH, "w", encoding="utf-8") as f:
        for c in cands:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    groups = {}
    for c in cands:
        groups.setdefault(c["source_doc"], []).append(c)
    write_review(cands, groups)

    print("候选生成：%d 条 → %s" % (len(cands), CAND_PATH))
    print("人读版：%s" % REVIEW_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
