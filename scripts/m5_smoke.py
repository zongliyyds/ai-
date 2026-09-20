# -*- coding: utf-8 -*-
r"""M5 在线冒烟：对运行中的 http://127.0.0.1:8001 做全端点验收（含真模型一问）。

前置：先启动服务（run_api.bat 或 uvicorn vaultmind.api.main:app）。
用法：D:\python\python.exe scripts\m5_smoke.py
"""
import sys
import time

import httpx

BASE = "http://127.0.0.1:8001"


def main() -> int:
    ok = True
    with httpx.Client(base_url=BASE, timeout=240.0) as c:
        r = c.get("/health")
        ok &= r.status_code == 200 and r.json()["status"] == "ok"
        print("[1] /health → %s %s" % (r.status_code, r.json()))

        r = c.get("/")
        page_ok = r.status_code == 200 and "VaultMind" in r.text and "分析看板" in r.text
        ok &= page_ok
        print("[2] /（问答页 HTML）→ %s 含 VaultMind/看板=%s" % (r.status_code, page_ok))

        r = c.get("/stats")
        s = r.json()
        stats_ok = r.status_code == 200 and "error" not in s and s["docs"] > 0
        ok &= stats_ok
        print("[3] /stats → docs=%s chunks=%s links=%s qa_logs=%s" % (
            s.get("docs"), s.get("chunks"), s.get("links"), s.get("qa_logs")))

        r = c.get("/metrics")
        m = r.json()
        m_ok = r.status_code == 200 and m.get("recall@5", {}).get("pass") is True \
            and m.get("mrr", {}).get("pass") is True and m.get("ndcg@10", {}).get("pass") is True
        ok &= m_ok
        print("[4] /metrics → Recall@5=%.4f MRR=%.4f nDCG@10=%.4f 全部达标=%s" % (
            m["values"]["recall@5"], m["values"]["mrr"], m["values"]["ndcg@10"], m_ok))

        r = c.get("/badcases")
        b = r.json()
        ok &= r.status_code == 200 and b["total"] == 11
        print("[5] /badcases → total=%s（期望 11）" % b["total"])

        t0 = time.perf_counter()
        r = c.post("/ask", json={"query": "CET-4 项目用了什么去重方案？",
                                 "mode": "hybrid", "top_k": 8})
        d = r.json()
        v = d.get("validation", {})
        ask_ok = r.status_code == 200 and v.get("has_citation") is True \
            and v.get("citation_valid") is True
        ok &= ask_ok
        print("[6] /ask 真模型一问（%.1fs）→ 引用=%s 非法=%s 拒答=%s → %s" % (
            time.perf_counter() - t0, v.get("cited_ids"), v.get("invalid_ids"),
            d.get("refusal"), "PASS" if ask_ok else "FAIL"))
        print("    答：%s" % d.get("answer", "")[:160].replace("\n", " "))
        print("    引用块数：%d（首条：%s）" % (len(d.get("citations", [])),
              d["citations"][0]["rel"] if d.get("citations") else "-"))

    print("=" * 60)
    print("M5 冒烟结论：%s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
