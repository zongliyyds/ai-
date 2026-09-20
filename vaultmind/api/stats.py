# -*- coding: utf-8 -*-
"""看板数据源（纯函数/只读）：库统计（与 DB 一致）、基线指标与坏例（实时读报告）。

口径约定：/stats 数字全部直查 data/vaultmind.db；/metrics 与 /badcases 解析
reports/baseline.md（该报告入 git、随版本走）→ 看板与报告永远一致。
"""
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from vaultmind.config import DB_PATH, WORKSPACE

BASELINE_PATH = WORKSPACE / "reports" / "baseline.md"
BASELINE_JSON_PATH = WORKSPACE / "reports" / "baseline.json"
TARGETS = {"recall@5": 0.80, "mrr": 0.65, "ndcg@10": 0.70}
GOLD_SIZE = 60  # gold 规模（与 gold_finalization 一致）


def init_qa_logs(db_path=None) -> None:
    """qa_logs 表（派生产物，CREATE IF NOT EXISTS）。"""
    db_path = db_path or DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.execute(
        "CREATE TABLE IF NOT EXISTS qa_logs ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "ts TEXT NOT NULL,"
        "question TEXT NOT NULL,"
        "mode TEXT,"
        "top_k INTEGER,"
        "answer_len INTEGER,"
        "cited_ids TEXT,"
        "invalid_ids TEXT,"
        "refusal INTEGER,"
        "latency_s REAL,"
        "rating INTEGER,"
        "category TEXT,"
        "feedback_ts TEXT)")
    con.commit()
    con.close()


def insert_qa_log(question, mode, top_k, answer_len, cited_ids,
                  invalid_ids, refusal, latency_s, db_path=None) -> int:
    db_path = db_path or DB_PATH
    con = sqlite3.connect(str(db_path))
    cur = con.execute(
        "INSERT INTO qa_logs(ts,question,mode,top_k,answer_len,cited_ids,"
        "invalid_ids,refusal,latency_s) VALUES(?,?,?,?,?,?,?,?,?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), question, mode, top_k,
         answer_len, ",".join(map(str, cited_ids)),
         ",".join(map(str, invalid_ids)), int(refusal), round(latency_s, 3)))
    row_id = cur.lastrowid
    con.commit()
    con.close()
    return row_id


def record_feedback(row_id, rating, category, db_path=None) -> bool:
    db_path = db_path or DB_PATH
    con = sqlite3.connect(str(db_path))
    cur = con.execute(
        "UPDATE qa_logs SET rating=?, category=?, feedback_ts=? WHERE id=?",
        (rating, category, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), row_id))
    con.commit()
    changed = cur.rowcount > 0
    con.close()
    return changed


def library_stats(db_path=None) -> dict:
    """库规模与健康度（全部直查索引库 → 与数据库一致）。"""
    db_path = db_path or DB_PATH
    if not db_path.exists():
        return {"error": "索引库缺失：先跑 D:\\python\\python.exe -m vaultmind.ingest"}
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    row = cur.execute(
        "SELECT COUNT(*), COALESCE(SUM(chars),0), COALESCE(SUM(h2),0), "
        "COALESCE(SUM(deadlinks),0) FROM docs").fetchone()
    stats = {
        "docs": row[0],
        "chars": row[1],
        "h2": row[2],
        "dead_links": row[3],
        "chunks": cur.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],
        "links": cur.execute("SELECT COUNT(*) FROM links").fetchone()[0],
        "fts_rows": cur.execute("SELECT COUNT(*) FROM chunks_fts").fetchone()[0],
        "qa_logs": cur.execute("SELECT COUNT(*) FROM qa_logs").fetchone()[0],
        "db_bytes": db_path.stat().st_size,
    }
    con.close()
    return stats


_METRIC_RE = re.compile(r"\|\s*(Recall@\d+|MRR|nDCG@10)\s*\|\s*([0-9.]+)\s*\|")


def _baseline_json() -> dict | None:
    """读取机器可读真相源 reports/baseline.json（由 eval runner 生成）。"""
    if not BASELINE_JSON_PATH.exists():
        return None
    try:
        return json.loads(BASELINE_JSON_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def baseline_metrics(report_path=None) -> dict:
    """指标字典（含目标值与达标判定）。

    优先读 reports/baseline.json（机器可读真相源，防 Markdown 格式耦合）；
    尚未生成时回退到解析 reports/baseline.md（旧环境可用，两者数字同源）。
    """
    data = _baseline_json()
    if data is not None and isinstance(data.get("metrics"), dict):
        m = data["metrics"]
        metrics = {k: m[k] for k in ("recall@1", "recall@5", "recall@10", "mrr", "ndcg@10")
                   if k in m and m[k] is not None}
        out = {"values": metrics, "num_queries": m.get("num_queries", GOLD_SIZE)}
    else:
        report_path = Path(report_path) if report_path else BASELINE_PATH
        if not report_path.exists():
            return {"error": "基线报告缺失：%s" % report_path}
        text = report_path.read_text(encoding="utf-8")
        metrics = {}
        for name, value in _METRIC_RE.findall(text):
            metrics[name.lower()] = float(value)
        out = {"values": metrics, "num_queries": GOLD_SIZE}
    for key, target in TARGETS.items():
        if key in metrics:
            out[key] = {
                "value": metrics[key],
                "target": target,
                "pass": metrics[key] >= target,
            }
    return out


def badcases(report_path=None) -> list[dict]:
    """未进 Top-5 的坏例。

    优先读 reports/baseline.json（真相源）；未生成时回退解析 baseline.md 的 ✗ 行。
    """
    data = _baseline_json()
    if data is not None and isinstance(data.get("details"), list):
        return [
            {"id": d.get("id", ""),
             "question": d.get("question", ""),
             "first_rank": d.get("first_rank") or None,
             "top5_hit": bool(d.get("hit_in_top5")),
             "latency": str(d.get("latency_s", ""))}
            for d in data["details"] if not d.get("hit_in_top5")
        ]
    report_path = Path(report_path) if report_path else BASELINE_PATH
    if not report_path.exists():
        return []
    out = []
    for line in report_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| cand-") or "✗" not in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 6:
            continue
        out.append({
            "id": cells[0],
            "question": cells[1],
            "first_rank": cells[2] if cells[2] != "-" else None,
            "top5_hit": cells[3] == "✓",
            "latency": cells[5].replace("s", ""),
        })
    return out
