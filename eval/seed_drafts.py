# -*- coding: utf-8 -*-
"""从候选池取草稿种子写入 gold_set.jsonl（status=draft，仅供预览评测管道）。

红线：gold 定稿（≥60 条 approved）必须由用户人工完成，本脚本只播种预览草稿。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAND = ROOT / "eval" / "candidates.jsonl"
GOLD = ROOT / "eval" / "gold_set.jsonl"


def main() -> int:
    cands = [json.loads(l) for l in CAND.read_text(encoding="utf-8").splitlines() if l.strip()]
    seen, drafts = set(), []
    for c in cands:
        if c["source_doc"] in seen:
            continue
        seen.add(c["source_doc"])
        drafts.append({**c, "status": "draft"})
        if len(drafts) >= 20:
            break
    GOLD.write_text(
        "".join(json.dumps(d, ensure_ascii=False) + "\n" for d in drafts),
        encoding="utf-8")
    print("草稿种子：%d 条 → %s（status=draft，待你人工定稿为 approved）" % (len(drafts), GOLD))
    return 0


if __name__ == "__main__":
    sys.exit(main())
