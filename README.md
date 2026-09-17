# VaultMind · 个人知识库 RAG 问答与评测系统

> 把个人 Obsidian 知识库（168 篇笔记 / 30.0 万字 / 986 个 H2 / 460 条双链）做成**可问答、可评测、可复现**的 RAG 系统。
> 面向「AI 应用开发 + AI 数据分析」双方向求职作品。零 LangChain / 零 torch / 零向量数据库。

## 指标总览（60 条 gold 评测集 · hybrid 检索 · 可复现）

| 指标 | 基线值 | 目标 | 判定 | 出处 |
|---|---|---|---|---|
| Recall@1 | 0.6333 | — | — | `reports/baseline.md` |
| Recall@5 | **0.8167** | ≥0.80 | ✅ | `reports/baseline.md` |
| Recall@10 | 0.8333 | — | — | `reports/baseline.md` |
| MRR | **0.7099** | ≥0.65 | ✅ | `reports/baseline.md` |
| nDCG@10 | **0.7406** | ≥0.70 | ✅ | `reports/baseline.md` |
| 平均延迟 | 0.244 s/查询 | — | — | `reports/baseline.md` |
| 引用可追溯 | 非法引用编号 = 0 | 100% | ✅ | `reports/m4_smoke.md` |
| 超纲拒答 | 2/2 探针拒答 | 拒答 | ✅ | `reports/m4_smoke.md` |
| 消融实验 | 6 组 × 60 gold | 基线复现闸门 | ✅ | `reports/ablation.md` |

> 复现命令：`python -m vaultmind.eval`（60 条 hybrid 基线）；`python scripts\m6_ablation.py`（六组消融，约 10~20 分钟）。
> 数字诚实原则：评测集构建方法、坏例账本（11 题未进 Top-5）、三组负/中性消融结果全部记录在 reports/。

## 架构

```
D:\AI-Knowledge-Vault (Obsidian 源库，只读)
        │  scan → audit → chunk(结构感知, 600字/H2, 元数据前缀)
        ▼
D:\RAG\data\vaultmind.db        ← docs(168)/chunks(1321)/links(460) + FTS5(jieba) + qa_logs
        │  bge-m3 1024维向量化 → embeddings.npy（L2 归一化，cosine=点积）
        ▼
检索层  BM25(FTS5) ─┐
        向量(numpy) ─┴→ RRF 融合(k=60) → [可选: 标题条件化重排]
        ▼
生成层  context 组装[S#]（≤2块/文档, 6000字符预算）
        → qwen2.5:7b-instruct 本地生成 → 引用校验 + 超纲拒答
        ▼
产品层  FastAPI /ask /search /stats /metrics /badcases /feedback
        + 零依赖 Web 问答页与看板（引用 obsidian:// 跳转原笔记）
        ▼
评测层  60 条 gold（分层抽样定稿，seed=42 可复现）→ Recall@k/MRR/nDCG/延迟
        + 六组消融（三路单拆/RRF k/查询改写/标题重排/1-hop/规模曲线）
```

## 核心特性

- **结构感知分块**：H2 为单元、超 600 字按 H3/段落二切、`[文档|章节|标签]` 前缀注入
- **混合检索**：SQLite FTS5 BM25 + numpy 暴力 cosine → RRF 融合（消融验证：融合 R@5 +0.05 正增益）
- **带引用问答**：每个陈述标注 `[S#]`，引用可点击跳回 Obsidian 原笔记；引用校验 100% 可追溯
- **超纲拒答**：提示词约束 + 规则校验双层；"知识库没有"就直说，不编造
- **自建评测集**：220 候选池结构派生（不用 LLM 生成问题防自欺）→ 分层抽样定稿 60 条，seed=42 重跑逐字节一致
- **六组消融**：负结果如实记录（查询改写、1-hop 扩展均不上线），规模曲线验证"零向量库"决策

## 快速开始（Windows 实测环境）

```powershell
# 0. 环境体检（换机后第一件事）
D:\python\python.exe scripts\env_check.py

# 1. 依赖
D:\python\python.exe -m pip install -r requirements.txt

# 2. 模型（ollama serve 需运行；自动存入 OLLAMA_MODELS 目录）
ollama pull bge-m3 & ollama pull qwen2.5:7b-instruct

# 3. 索引（只读扫描知识库 → D:\RAG\data\）
D:\python\python.exe -m vaultmind.ingest
D:\python\python.exe -m vaultmind.search --build-vectors   # bge-m3 全量向量化，断点续跑

# 4. 检索 / 问答 / 评测
D:\python\python.exe -m vaultmind.search "问题" --top 5 --mode hybrid
D:\python\python.exe -m vaultmind.ask "问题"               # 带 [S#] 引用问答
D:\python\python.exe -m vaultmind.eval                     # 60 条基线指标

# 5. Web 演示（双击亦可）
run_api.bat        # http://127.0.0.1:8000（问答页 + 分析看板）

# 6. 知识库有新增/改动时：一条命令同步全套
#    重建索引+向量 → 复验 60 条 gold → 重定审计基线 → 回写文档锚点 → 重生 PDF → pytest
D:\python\python.exe scripts\sync_vault.py          # 只看不改：--dry-run；跳过复验：--skip-eval
```

> 注：默认工作区 `D:\RAG`、知识库 `D:\AI-Knowledge-Vault\AI-Knowledge-Vault`，可用环境变量
> `VAULTMIND_WORKSPACE` / `VAULTMIND_VAULT` 覆盖（换机复用）。

## 红线（本项目的立身之本）

1. **只读知识库**：RAG 绝不修改源 Vault，索引是派生产物（`data/`，gitignore）。
2. **简历诚实**：每个数字都能在 `reports/` 找到出处并重跑复现。
3. **隐私**：默认本地模型；云端兜底前 PII 脱敏。
4. **不开源知识库内容**：仓库只含代码 + 脱敏样例（`scripts/package_repo.py` 打包探针强制校验）。

## 目录

| 路径 | 内容 |
|---|---|
| `vaultmind/ingest|retrieval|llm|eval|api` | 主包（管道/检索/生成/评测/产品层） |
| `eval/gold_set.jsonl` | 60 条 gold 评测集（approved） |
| `reports/` | audit 体检 / baseline 基线 / ablation 消融 / sync_report 同步报告 / m4_smoke / gold_finalization / knowledge_drafts 知识卡片 |
| `docs/` | 立项书、AI 工作手册、各节点工单、简历 bullet、Q&A 预案、求职收尾清单 |
| `tests/` | pytest 63 条（冒烟 + 探针 + 回归；pre-commit 钩子拦截坏提交） |
| `scripts/` | 一键复现（**sync_vault** / finalize_gold / m4_smoke / m5_smoke / m6_ablation / env_check / package_repo / make_interview_pdf） |

## 测试

```powershell
D:\python\python.exe -m pytest tests -q    # 63 passed
```
