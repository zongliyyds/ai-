# CHANGELOG（进度档案 · 唯一事实来源）

> 约定：每个节点验收通过后追加一条；格式：`日期 · 节点 | 做了什么 | 验证结果 | 遗留与下一步`。
> AI 会话开工必读本文件 + `PLAN.md`；节点收尾必须回来追加。

## 2026-09-16 · M4 生成链路（W2 全部收官）

- **做了什么**：`vaultmind/llm/`（context 上下文组装 [S#]：每文档≤2 块/6000 字符预算/编号只分配给保留块；generator Ollama qwen2.5:7b-instruct 本地生成；validator 引用校验+拒答话术判定，纯函数）+ `vaultmind/ask.py` CLI（`--context-only`/`--json`）；离线探针 `tests/test_generation.py`（6 条）；在线冒烟 `scripts/m4_smoke.py`（2 库内 + 2 超纲）；pre-commit 钩子纳入 M4 探针；范围界定：查询改写不归 M4、归 M6 消融（防破坏 M3 基线可复现）。
- **验证结果**：pytest **32/32**；冒烟 **4/4 PASS**——库内 2 问引用可追溯（非法编号=0）、超纲 2 问拒答（比特币/迪士尼票价，拒答时诚实列举 S1..S8 均无关）；端到端 13~17s（生成 8~15s，首问冷加载 67s）；踩坑并修复：模型输出 `[S1, S2, S4]` 列表式引用 → validator 正则支持（含 `【S1】`、`[S 3]` 变异）。
- **交付物**：`vaultmind/llm/*`、`vaultmind/ask.py`、`tests/test_generation.py`、`scripts/m4_smoke.py`、`docs/工单-M4-生成链路.md`、`reports/m4_smoke.md`。
- **遗留与下一步**：W2 收官 → **W3 M5 产品层**（FastAPI 问答接口 + Web 页面 + 引用可跳转回原笔记 + 分析看板）→ M6 六组消融。

## 2026-09-16 · M3 gold 定稿 + 正式基线（W2 第一块完成）

- **做了什么**：gold 定稿器 `scripts/finalize_gold.py`（参考业界做法：候选池即"池"、不用 LLM 生成问题；按库目录×难度 14 层分层抽样、比例配额、每层≥1、单文档≤3、问题文本全局唯一、seed=42 可复现）；60 条 approved → `eval/gold_set.jsonl`；8 道校验闸门（含"gold 目标 ↔ 已索引 chunk"可追溯率 100%）；正式基线；工单 M3 更新 + W4 联网模块设计文档。
- **验证结果**：pytest **26/26**；基线 60 条 hybrid：Recall@1=0.6167 / **Recall@5=0.8167** / Recall@10=0.8333 / **MRR=0.7010** / **nDCG@10=0.7339** / 平均延迟 0.866s —— 三项目标值（≥0.80 / ≥0.65 / ≥0.70）**全部达标**。坏例账本：11 题未进 Top-5（10 题为"裸标题"hard 型、1 题 easy），已列 M6 查询改写/重排消融素材。
- **交付物**：`scripts/finalize_gold.py`、`eval/gold_set.jsonl`（60 approved，SHA-256 7057c373…）、`reports/gold_finalization.md`（方法+文献+清单）、`reports/baseline.md`、`docs/工单-W4-联网采集与保鲜模块.md`。
- **遗留与下一步**：~~M4 生成链路~~（已完成，见上方条目；查询改写归 M6 消融）。

## 2026-09-16 · W4 联网采集与保鲜模块设计定稿

- **做了什么**：按用户确认的方向（B 主动采集为主、C 保鲜巡检为辅，不做 A 临时联网问答为主）落成 `docs/工单-W4-联网采集与保鲜模块.md`（定位/数据流/红线/子步骤 S1-S5/验收/风险）。
- **验证结果**：与立项书红线一致（抓取绝不自动写 Vault，落点仅 `data/web_capture` 或 `reports`）；排期 W4 不阻塞主线。
- **遗留与下一步**：开工前先跑 S1 Bing 解析可行性探测（`reports/bing_probe.md`）。



## 2026-09-16 · M3 评测基建（历史条目 · 已被上方「M3 gold 定稿」条目接续）

- **做了什么**：`vaultmind/eval`（metrics 手写：Recall@1/5/10、MRR、nDCG@10、平均延迟 + runner + CLI）；候选问题生成器 `scripts/gen_candidates.py`（220 条，H2 结构模板化派生，不用 LLM 防自欺）→ `eval/candidates.jsonl` + `reports/candidates_review.md` 人读版；`eval/seed_drafts.py` 播种 20 条 draft；指标探针 `tests/test_eval.py`（已知排序断言精确值）。
- **验证结果**：pytest **26/26**；评测管道预览跑通（20 条 draft：Recall@5=1.0、MRR=0.975、nDCG@10=0.9815、平均延迟 0.57s——草稿多为含文档名的易题，最终数字以定稿后为准）。
- **交付物**：`vaultmind/eval/*`、`scripts/gen_candidates.py`、`eval/candidates.jsonl`、`eval/gold_set.jsonl`（20 draft）、`reports/candidates_review.md`、`reports/baseline.md`（预览）。
- **遗留与下一步**：~~用户人工定稿 60 条 gold~~（2026-09 用户改授权为算法定稿，见上方条目）；随后 M4 生成链路（引用/拒答）。

## 2026-09-16 · 环境准备（开工前，M0 前置）

- **做了什么**：Ollama 模型库从 C 盘迁至 `D:\本地模型`；写入用户级环境变量 `OLLAMA_MODELS=D:\本地模型`；删除旧目录 `C:\Users\Administrator\.ollama\models`。
- **验证结果**：`ollama serve` + `ollama list` 正确识别 `qwen2.5-coder:7b`（4.7 GB）；迁移前后 6 个文件 / 4,683,088,419 字节逐字节一致；C 盘释放约 4.7 GB。
- **交付物**：`docs/Ollama本地模型迁移工作流.pdf`、`scripts/make_migration_pdf.py`。

## 2026-09-16 · M2 检索 v1（W1 全部里程碑收官）

- **做了什么**：`vaultmind/retrieval`（bm25 / vector / fusion + `search()` 统一接口）+ search CLI（`--build-vectors` / `--mode bm25|vector|hybrid`）；bge-m3 全量向量化 1,237 chunks（87s，断点续跑，L2 归一化，`data/embeddings.npy` + `chunk_ids.json`）；查询侧停用词过滤；自查表生成器 `scripts/m2_selfcheck.py`。
- **验证结果**：pytest **22/22 通过**；10 问自查：bm25 **9/10**、vector **10/10**、hybrid **9/10**（达标线 8/10，✅）；发现并记录「RRF 融合稀释单路强信号」案例（Q1）作为 M6 消融素材。
- **交付物**：`vaultmind/retrieval/*`、`vaultmind/search.py`、`tests/test_retrieval.py`、`reports/m2_selfcheck.md`、`scripts/m2_selfcheck.py`。
- **遗留与下一步**：待人工抽查 3~5 问签字验收；W2 开工 **M3 评测集（gold 60 条，人工定稿）+ M4 生成链路（引用/拒答）**。

## 2026-09-16 · 环境准备补录：模型拉取完成（M2 前置）

- **做了什么**：后台拉取 `bge-m3`（1.2 GB）与 `qwen2.5:7b-instruct`（4.7 GB），自动存入 `D:\本地模型`；验证 bge-m3 embedding 接口（1024 维，首次加载 23.5s）。
- **验证结果**：`ollama list` 显示 3 个模型齐全；Ollama 启动日志确认 CUDA0=RTX 4050 6GB 接管、`OLLAMA_MODELS` 生效。
- **交付物**：模型本体（`D:\本地模型`，不入库）。

## 2026-09-16 · M1 数据管道 + 知识库体检（W1）

- **做了什么**：`vaultmind` 包落地（config / scanner / auditor / chunker / indexer / report + CLI）；一条命令 `D:\python\python.exe -m vaultmind.ingest` 完成 扫描→体检→分块→索引→报告；SQLite 索引库（docs / chunks / links + FTS5 jieba 分词）；三层防线测试骨架（tests/：冒烟 + 基线探针 + 分块单测）；pre-commit 钩子（提交前跑基线探针）。
- **验证结果**：审计数字与 `baseline_audit.json` 逐项一致（154 篇 / 276,977 字符 / 922 H2 / 409 出链 / 29 死链 / 孤儿 25）；pytest 12/12 通过（1.52s）；FTS5 中文检索探针命中；索引产出 1,237 chunks / 409 links，全管道 1.2s。
- **交付物**：`vaultmind/` 包、`reports/audit_report.md`、`data/audit.json` + `data/vaultmind.db`（gitignore）、`tests/`×4、`scripts/hooks/pre-commit`。
- **遗留与下一步**：M2 检索 v1（FTS5 已可用，待接向量 + RRF 融合）；开工前首次手动准备：`ollama serve` 后 `ollama pull bge-m3`（~1.2 GB）、`ollama pull qwen2.5:7b-instruct`（~4.7 GB）。

## 2026-09-16 · 协作体系建立（M0 前置）

- **做了什么**：建立 AI 协作工作手册 `docs/AI工作手册.md`（四步法 + 工单模板 + 红线 + 坑位表 + 命令速查 + 知识沉淀约定）；建立本 CHANGELOG 作为进度档案；知识沉淀至 Mnemon 文档空间与记忆空间。
- **验证结果**：手册覆盖全部已踩坑位（Python 全路径、pwsh 5.1 编码、HTTPS、沙箱、PyMuPDF 两坑、Ollama 路径）；与 PLAN/FEASIBILITY 红线一致。
- **遗留与下一步**：开工前首次手动准备——`ollama serve` 后 `ollama pull bge-m3`（~1.2 GB）、`ollama pull qwen2.5:7b-instruct`（~4.7 GB），自动存入 `D:\本地模型`；随后进入 W1：M0 立项收尾 + M1 数据管道/体检 + M2 检索 v1。
