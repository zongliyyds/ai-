# VaultMind · 个人知识库 RAG 问答与评测系统

> 把个人 Obsidian 知识库（154 篇笔记 / 27.7 万字 / 409 条双链）变成可问答、可评测、可复现的 RAG 系统。
> 面向 AI 应用开发 + AI 数据分析双方向求职作品。

## 当前状态

🟡 已立项：可行性评估完成、工作区建立（`D:\RAG`）、基线体检数据就绪。
下一步：M0/M1 数据管道实现。

## 核心特性

- 结构感知分块（frontmatter + 标题层级 + 元数据前缀注入）
- 双链知识图谱增强检索（1-hop / 2-hop）
- 混合检索（SQLite FTS5 BM25 + 向量 cosine → RRF → LLM 重排）
- 引用溯源问答 + 超纲拒答
- 自建 gold 评测集 + 一键指标（Recall@k / MRR / nDCG@10 / 引用命中率 / 拒答率）
- 6 组消融实验 + 知识库健康度看板

## 技术栈

Python 3.13 · FastAPI · SQLite(FTS5) · jieba · numpy/scikit-learn · Ollama(bge-m3 + qwen2.5:7b) · 原生前端

## 目录

- `FEASIBILITY.md` 可行性报告
- `PLAN.md` 实施计划与排期
- `vaultmind/` 主包
- `eval/` 评测集与指标
- `reports/` 体检报告 / 消融表
- `docs/` 架构图

## 快速开始

```bash
# 依赖
pip install -r requirements.txt
# 重建索引（只读扫描知识库）
python -m vaultmind.ingest
# 跑评测
python -m vaultmind.eval
# 启动服务
uvicorn vaultmind.api.main:app --reload
```

## 数据源

源知识库：`D:\AI-Knowledge-Vault\AI-Knowledge-Vault`（只读，不修改）
派生索引：`D:\RAG\data\`
