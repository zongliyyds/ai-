# VaultMind 实施计划（定稿版 · 工作区已迁移至 D:\RAG）

## 0. 一句话目标

把 `D:\AI-Knowledge-Vault` 做成**可评测的个人知识库 RAG 问答系统**，产出 GitHub 仓库 + 评测报告 + Web 演示，支撑「AI 应用开发 + AI 数据分析」双方向求职。

## 1. 与现有知识库共存（硬约束，不可破坏）

**核心原则：RAG 项目对知识库"只读"，知识库永远是唯一写入入口。**

- 你的知识继续照旧写进 `D:\AI-Knowledge-Vault\AI-Knowledge-Vault`（Obsidian 照常用）。
- RAG 只**扫描读取**，绝不修改、移动、重命名 Vault 里任何文件（遵守《AI-Knowledge-Base-Rules》）。
- 索引库（SQLite + 向量）是**派生产物**，存在 `D:\RAG\data\`，与源 Vault 物理隔离。
- 新增/修改笔记后，运行 `python -m vaultmind.ingest`（或调 `/reindex` 接口）**增量重建**索引即可同步，不影响 Vault 本体。
- 可选增强：加一个文件监听器，检测到 `.md` 变更自动重建对应 chunk。

```
[源 · 唯一写入入口]          [派生 · 只读消费]
D:\AI-Knowledge-Vault ──只读扫描──▶ D:\RAG\data\ 索引库
      ▲                                  │
      └── Obsidian 照常写笔记 ◀── 问答引用可跳回原笔记
```

## 2. 工作区约定（本次已确定）

- **唯一工作区：`D:\RAG`**，所有代码、数据、报告、文档都放这里，不再散落。
- 目录结构：

```
D:\RAG\
├── FEASIBILITY.md        # 可行性报告（本机实测）
├── PLAN.md               # 本计划
├── README.md             # 项目入口
├── requirements.txt
├── .gitignore
├── vaultmind\            # Python 包（ingest/retrieval/llm/api/web 子模块）
├── eval\                 # 评测集 + 指标脚本
├── scripts\              # 一键复现 / 启动脚本
├── tests\                # pytest
├── data\                 # 派生的 SQLite + 向量（gitignore）
├── reports\              # 体检报告 / baseline / 消融表（交付物，纳入 git）
├── docs\                 # 架构图等文档
├── sample_data\          # 脱敏样例数据（让仓库可复现）
└── models\               # 本地模型缓存说明（模型本体不入库）
```

## 3. 技术路线（定稿）

- **Embedding**：Ollama `bge-m3`（本地）→ DashScope `text-embedding-v3`（兜底）
- **生成**：Ollama `qwen2.5:7b-instruct`（本地）→ DeepSeek/通义千问（兜底）
- **检索**：SQLite FTS5(BM25) + numpy 暴力 cosine → RRF 融合 → LLM 重排 → 双链图谱 1-hop/2-hop 扩展
- **分块**：结构感知（frontmatter + H2 层级 + 元数据前缀注入）
- **评测**：60 条 gold 集（候选池结构派生 + 分层抽样定稿，可复现，见 `reports/gold_finalization.md`）+ Recall@k/MRR/nDCG@10/引用命中率/拒答率 + 6 组消融
- **前端**：原生 HTML+CSS+JS + Chart.js（零构建）
- **刻意不用**：LangChain / Chroma / FAISS / torch（理由见 FEASIBILITY.md）

## 4. 里程碑与四周排期

| 周 | 里程碑 | 交付物 | 验收标准 |
|---|---|---|---|
| W1 | M0 立项 + M1 数据管道/体检 + M2 检索 v1 | `ingest.py`、`audit_report.md`、`search` CLI | 一条命令重建索引；报告数字与基线一致；Top-5 命中正确笔记 |
| W2 | M3 gold 集 + baseline + M4 生成链路 | `eval` 一键指标表；带引用问答跑通 | 指标可复现；引用 100% 可追溯；超纲问题拒答 |
| W3 | M5 产品层 + M6 六组消融 | Web 问答 + 分析看板；`ablation.md` | 浏览器问答引用可跳转；消融表各组件增益量化 |
| W4 | 追加实验 + M7 工程化/求职转化 | GitHub 仓库 + 录屏 + 两套简历 bullet + Q&A 预案 + **《面试答辩手册 PDF》（终期交付物）** | 换机按 README 可跑；简历每个数字可复现；手册覆盖高频面试问题 |

**W4 追加实验**：2-hop 图谱深度消融、重排三方案对比、暴力 vs HNSW 规模曲线、本地 vs 云端成本/延迟、**联网采集与保鲜模块（B 主动采集为主 + C 保鲜巡检为辅，设计见 `docs/工单-W4-联网采集与保鲜模块.md`，排期 W4 不阻塞主线）**。
- ✅ **M6b 分块粒度消融已完成**（2026-09-17，`reports/m6b_chunk_ablation.md`，工单见 `docs/工单-W4-M6b-分块粒度消融.md`）：6 变体 × 60 条 gold，含基线复现闸门。结论：细粒度 -0.0333、粗粒度 +0.0333、**前缀入检索 +0.1000（hard 档 +0.2083）**、组合不叠加；真因 = H2 标题在切块时被剥离出正文且前缀未接入检索信号（解释了 M6 的 E3/E4 负结果）。**V5 已采纳（2026-09-20）：`prefix_mode=inline` 并入正式管道，基线 R@5 0.8167→0.9167。**

## 5. 开工前的首次手动准备（沙箱外执行一次，约 6 GB）

```powershell
# 1. 启动 Ollama 服务（当前未运行）
ollama serve        # 或直接打开 Ollama 桌面端

# 2. 拉取模型（registry.ollama.ai 已测通）
ollama pull bge-m3               # ~1.2 GB  embedding
ollama pull qwen2.5:7b-instruct  # ~4.7 GB  生成
```

> M0/M1（数据管道）不需要模型，可与模型下载并行推进。

## 6. 红线（全程）

1. 只读 Vault，不破坏现有知识库存储。
2. 简历诚实：只写实际做出、可复现的内容，数字不编造。
3. 隐私：笔记含手机号/邮箱，云端调用前 PII 脱敏；默认走本地模型。
4. 不开源 Vault 内容，只开源代码 + 脱敏样例。

## 7. 进度快照（2026-09-20 更新，随 CHANGELOG 走）

- **W1 ✅** M1 数据管道+体检（数字与基线逐项一致）｜ M2 检索 v1（BM25+bge-m3 向量+RRF，1,437 chunks）
- **W2 ✅** M3 gold 60 条定稿 + 正式基线（bm25：Recall@5=0.9333 / MRR=0.8672 / nDCG@10=0.8840，三项达标）｜ M4 生成链路（[S#] 引用问答 + 超纲拒答，冒烟 4/4）
- **W3 ✅** M5 产品层（FastAPI + Web 问答页/看板，人工验收通过；run_api.bat 一键启动，端口 8001）｜ M6 六组消融（`reports/ablation.md`：三路单拆 / RRF k / 查询改写 / 标题重排 / 1-hop / 规模曲线，据数据定检索模式）
- **W4 ▶ 进行中**：M7 工程化/求职转化 AI 侧全部交付（README 指标表、简历 bullet 两套、Q&A 预案、**《面试答辩手册 PDF》终期交付物**、env_check、打包红线探针）；**GitHub 已接入**私有仓库 `zongliyyds/ai-`（2026-09-17）。**V5 已采纳**（前缀入检索 `prefix_mode=inline`，2026-09-20）+ **正式检索模式切 bm25 单路**（消融证明反超 hybrid，基线 R@5 0.9333）+ **端口迁 8001**（避开英语四级知识库 8000）。语料 175 篇 / 1,397 chunks，数字全部现场取数防漂移。**剩余 = 用户侧**：3 分钟录屏（7 幕）、简历贴 bullet。AI 侧追加实验：2-hop、本地 vs 云端、联网 B/C 的 S1 Bing 探测。
