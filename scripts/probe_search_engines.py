# -*- coding: utf-8 -*-
"""搜索引擎连通性实测：Python httpx 直连探测（只发查询，不落地任何内容）。

用途：为 VaultMind W4 可选模块「联网增强检索」做选型依据。
探测项：可达性 / 状态码 / 延迟 / 返回体积 / 是否疑似含结果。
"""
import sys
import time

import httpx

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

TARGETS = [
    ("DuckDuckGo HTML", "https://html.duckduckgo.com/html/", {"q": "SQLite FTS5 中文分词"}),
    ("DuckDuckGo Lite", "https://lite.duckduckgo.com/lite/", {"q": "SQLite FTS5 中文分词"}),
    ("Bing", "https://www.bing.com/search", {"q": "SQLite FTS5 中文分词"}),
    ("Baidu", "https://www.baidu.com/s", {"wd": "SQLite FTS5 中文分词"}),
    ("Google", "https://www.google.com/search", {"q": "SQLite FTS5 中文分词"}),
    ("SearXNG searx.be", "https://searx.be/search", {"q": "SQLite FTS5 中文分词", "format": "json"}),
    ("SearXNG paulgo", "https://paulgo.io/search", {"q": "SQLite FTS5 中文分词", "format": "json"}),
    ("SearXNG baresearch", "https://baresearch.org/search", {"q": "SQLite FTS5 中文分词", "format": "json"}),
    ("控制组 PyPI", "https://pypi.org/simple/", {}),
]

RESULT_HINTS = ["SQLite", "FTS5", "分词", "result", "Results", "百度"]


def probe(name, url, params):
    t0 = time.time()
    try:
        r = httpx.get(url, params=params, headers={"User-Agent": UA},
                      timeout=12, follow_redirects=True)
        ms = (time.time() - t0) * 1000
        body = r.text
        has_hint = any(h in body for h in RESULT_HINTS)
        print("[%s] %s: HTTP %d, %.0fms, %d bytes, 疑似含结果=%s" % (
            "OK " if r.status_code == 200 else "WARN", name, r.status_code,
            ms, len(body), has_hint), flush=True)
        return {"name": name, "reachable": True, "status": r.status_code,
                "ms": round(ms), "bytes": len(body), "hint": has_hint}
    except Exception as e:
        ms = (time.time() - t0) * 1000
        print("[FAIL] %s: %.0fms %s: %s" % (name, ms, type(e).__name__, str(e)[:80]),
              flush=True)
        return {"name": name, "reachable": False, "error": "%s: %s" % (type(e).__name__, str(e)[:120]),
                "ms": round(ms)}


def main() -> int:
    print("=== 搜索引擎连通性实测（Python httpx 直连，每项超时 12s）===", flush=True)
    results = []
    for name, url, params in TARGETS:
        results.append(probe(name, url, params))
    print("=== 实测结束 ===", flush=True)
    reachable = [r for r in results if r.get("reachable")]
    print("可达 %d/%d" % (len(reachable), len(results)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
