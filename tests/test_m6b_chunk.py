# -*- coding: utf-8 -*-
"""M6b 分块粒度消融探针（离线，不依赖 Ollama、不碰正式索引/向量）。

覆盖五件事：
1. 默认行为回归 —— 不传参 = 正式管道分块（逐字一致，防「消融改动污染正式管道」）
2. 粒度单调性 —— doc 块数 ≤ h2 块数 ≤ h3 块数（细粒度确实更细）
3. prefix_mode 语义 —— field / none / inline 三态的字段与文本差异
4. 路径隔离 —— vector._paths 默认 = 正式产物；传参 = 指定临时路径
5. 临时索引隔离 —— 往临时 db 写索引不得触碰正式向量产物
6. 锚点防漂移 —— scripts/m6_ablation.py 的 BASELINE 必须现场取自 reports/baseline.md
"""
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _doc_anchors import parse_report_metrics  # noqa: E402

from vaultmind.config import CHUNK_MAX_CHARS, DB_PATH  # noqa: E402
from vaultmind.ingest.chunker import chunk_doc  # noqa: E402
from vaultmind.ingest.scanner import Doc  # noqa: E402
from vaultmind.retrieval import vector  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent

BODY = """# 样本文档

开头说明段落。

## 第一节

第一节的第一段正文，用于验证 H2 粒度切分。

### 1.1 子节

子节正文内容。

## 第二节

第二节正文内容，比较短。
"""


def sample_doc() -> Doc:
    return Doc(rel="20-Knowledge/样本文档.md", path="",
               body=BODY, tags=["测试", "分块"])


def signature(chunks):
    return [(c.section, c.prefix, c.text) for c in chunks]


# ---- 1. 默认行为回归 ----

def test_default_matches_explicit_baseline_params():
    """默认参数必须与显式基线参数逐字一致（V5 后正式管道默认 = inline 的证据）。"""
    doc = sample_doc()
    assert signature(chunk_doc(doc)) == signature(
        chunk_doc(doc, granularity="h2", max_chars=CHUNK_MAX_CHARS, prefix_mode="inline"))


def test_h2_granularity_keeps_short_section_whole():
    """H2 粒度下，未超上限的小节整节成块（不无谓下钻）。"""
    chunks = chunk_doc(sample_doc())
    assert [c.section for c in chunks] == ["概述", "## 第一节", "## 第二节"]


# ---- 2. 粒度单调性 ----

def test_granularity_monotonic():
    doc = sample_doc()
    n_doc = len(chunk_doc(doc, granularity="doc", max_chars=4000))
    n_h2 = len(chunk_doc(doc, granularity="h2", max_chars=CHUNK_MAX_CHARS))
    n_h3 = len(chunk_doc(doc, granularity="h3", max_chars=300))
    assert n_doc <= n_h2 <= n_h3
    assert n_doc == 1                       # 整篇一块
    assert n_h3 > n_h2                      # 细粒度确实更细


def test_doc_granularity_respects_max_chars():
    """整篇粒度仍受 max_chars 约束（超长按段落硬切，避免超模型上下文）。"""
    big = Doc(rel="x.md", path="", body="# T\n\n" + ("段落内容。" * 200))
    chunks = chunk_doc(big, granularity="doc", max_chars=600)
    assert len(chunks) > 1
    assert all(len(c.body) <= 600 for c in chunks)


def test_h3_granularity_splits_into_subsections():
    chunks = chunk_doc(sample_doc(), granularity="h3", max_chars=300)
    sections = [c.section for c in chunks]
    assert any("1.1 子节" in s for s in sections)


# ---- 3. prefix_mode 语义 ----

def test_prefix_field_mode_keeps_prefix_out_of_text():
    c = chunk_doc(sample_doc(), prefix_mode="field")[0]
    assert c.prefix.startswith("[文档: 样本文档")
    assert "文档: 样本文档" not in c.text    # field 模式：前缀不进正文（故也不进检索信号）


def test_prefix_none_mode_drops_prefix():
    for c in chunk_doc(sample_doc(), prefix_mode="none"):
        assert c.prefix == ""


def test_prefix_inline_mode_moves_prefix_into_text():
    inline = chunk_doc(sample_doc(), prefix_mode="inline")
    field = chunk_doc(sample_doc(), prefix_mode="field")
    # V5：前缀并入 text（进检索），prefix 字段同时保留一份（供展示层 body 剥离）
    assert inline[0].text.startswith("[文档: 样本文档")
    assert all(c.prefix.startswith("[文档: 样本文档") for c in inline)
    # 展示层 body 能精确剥出纯正文 = field 模式的 text
    assert [c.text for c in field] == [c.body for c in inline]


# ---- 4/5. 路径隔离与临时索引隔离 ----

def test_vector_paths_default_and_override(tmp_path):
    assert vector._paths() == (Path(DB_PATH), vector.EMB_NPY, vector.EMB_IDS)
    custom = vector._paths(tmp_path / "a.db", tmp_path / "e.npy", tmp_path / "c.json")
    assert custom == (tmp_path / "a.db", tmp_path / "e.npy", tmp_path / "c.json")


def test_temp_db_write_does_not_touch_official_vectors(tmp_path, monkeypatch):
    """M6b 红线：实验索引只能写临时路径，正式向量产物零变化。

    用哨兵文件冒充「正式向量产物」：即使本机尚未构建正式向量（EMB_NPY/EMB_IDS
    不存在），本测试也必须能证明「临时索引构建不触碰向量产物」——否则空文件
    前后指纹都是 (False,None,None)，红线断言空转通过（假绿）。
    """
    from vaultmind.ingest.indexer import build_db

    sentinel_npy = tmp_path / "emb.npy"
    sentinel_ids = tmp_path / "ids.json"
    sentinel_npy.write_bytes(b"FAKE_NPY_BYTES")
    sentinel_ids.write_text('["sentinel"]', encoding="utf-8")
    monkeypatch.setattr(vector, "EMB_NPY", sentinel_npy)
    monkeypatch.setattr(vector, "EMB_IDS", sentinel_ids)

    doc = sample_doc()
    chunks = chunk_doc(doc)
    before = (sentinel_npy.read_bytes(), sentinel_ids.read_bytes())
    stats = build_db([doc], chunks, db_path=tmp_path / "v.db")
    assert stats["chunks"] == len(chunks) == 3
    assert Path(stats["db_path"]) == tmp_path / "v.db"
    assert (sentinel_npy.read_bytes(), sentinel_ids.read_bytes()) == before, \
        "临时索引构建不得触碰正式向量产物"


# ---- 6. 锚点防漂移 ----

def test_m6_ablation_baseline_is_parsed_live():
    """消融总控的基线常量必须现场取自 reports/baseline.md（2026-09-17 体检修正）。"""
    spec = importlib.util.spec_from_file_location(
        "_m6_ablation_probe", BASE_DIR / "scripts" / "m6_ablation.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    live = parse_report_metrics()
    assert mod.BASELINE["recall@5"] == live["recall@5"]
    assert mod.BASELINE["mrr"] == live["mrr"]
    assert mod.BASELINE["ndcg@10"] == live["ndcg@10"]
