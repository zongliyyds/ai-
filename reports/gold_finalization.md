# Gold 评测集定稿报告（M3 · 官方 60 条）

> 生成时间：2026-09-16 15:25 ｜ 种子：42 ｜ 规模：60 条（全部 approved）｜ 问题文本全局唯一

## 1. 一句话结论

候选池 220 条 → 按业界做法**分层抽样定稿 60 条**：候选问题全部来自笔记 H2 结构模板化派生（不用 LLM 生成），抽样按（库目录 × 难度）分层比例配额、每层至少 1 条、单文档上限 3 条，固定种子可复现；全部通过 8 道校验闸门（含"gold 目标 ↔ 已索引 chunk"可追溯率 100.0%）。

## 2. 方法与业界依据

| 步骤 | 做法 | 依据 |
|---|---|---|
| 候选池 | 高价值笔记（入链 Top + 体量 Top + 各类型/目录覆盖）的 H2 标题+首句模板化派生，**不用 LLM 生成问题/判分** | 避免 RAGAS 类合成评测集的"评测与生成同源"自循环批评；TREC pooling 的"池"思想（[Conversational Gold, arXiv:2503.09902](https://ar5iv.labs.arxiv.org/html/2503.09902)） |
| 分层抽样 | 按（库目录 × easy/hard）分层，比例配额 + 每层最少 1 条，保证全库覆盖 | "Coverage, not averages"：[Semantic Stratification for Trustworthy Retrieval Evaluation, arXiv:2604.20763](https://ar5iv.labs.arxiv.org/html/2604.20763) |
| 规模 | 60 条（golden set 常规区间 50~200） | [When "Better" Prompts Hurt, arXiv:2601.22025](https://ar5iv.labs.arxiv.org/html/2601.22025) 推荐小型、版本化、跨意图分层的 golden set |
| 问题全局唯一 | 同标题模板在不同文档产生的重复问题文本只保留一条 | 消除标注歧义（同一问题两个"正确答案"会污染 MRR/nDCG）；TREC 查询消歧惯例 |
| 可复现 | 随机种子 42 + 确定性排序；重跑逐字节一致，SHA-256 记录在案 | golden set 必须版本化、可重建（[Golden test set construction — RAG Fundamentals, The Neural Base](https://theneuralbase.com/rag-fundamentals/learn/intermediate/golden-test-set-construction/)） |

## 3. 分层抽样分配表

| 库目录 × 难度 | 候选数 | 配额 | 实际入选 |
|---|---|---|---|
| (库根目录) × easy | 3 | 2 | 2 |
| (库根目录) × hard | 2 | 1 | 1 |
| 10-Projects × easy | 24 | 6 | 6 |
| 10-Projects × hard | 16 | 4 | 4 |
| 20-Knowledge × easy | 81 | 22 | 22 |
| 20-Knowledge × hard | 54 | 14 | 14 |
| 30-Prompts × easy | 3 | 1 | 1 |
| 30-Prompts × hard | 2 | 1 | 1 |
| 40-Decisions × easy | 12 | 3 | 3 |
| 40-Decisions × hard | 8 | 2 | 2 |
| 50-Logs × easy | 4 | 1 | 1 |
| 50-Logs × hard | 3 | 1 | 1 |
| 90-System × easy | 5 | 1 | 1 |
| 90-System × hard | 3 | 1 | 1 |

难度分布：easy 36 条 / hard 24 条；覆盖文档 42 篇（共 42 篇）。

## 4. 校验闸门（全部通过才写文件）

| # | 闸门 | 结果 |
|---|---|---|
| 1 | 数量 = 60 | ✅ |
| 2 | 全部 approved | ✅ |
| 3 | 问题文本全局唯一 | ✅ |
| 4 | 答案文档存在且章节可定位 | ✅ |
| 5 | 要点非空 | ✅ |
| 6 | 单文档 ≤ 3 条 | ✅ |
| 7 | 目录全覆盖 | ✅ |
| 8 | chunk 可追溯率 ≥ 95%% | ✅ |

## 5. 官方 60 条清单

| id | 难度 | 问题 | 答案文档 |
|---|---|---|---|
| cand-006 | easy | 论文格式模板匹配方法论 中的「## 核心观点」讲了什么？ | `20-Knowledge/论文格式模板匹配方法论.md` |
| cand-007 | hard | ## 关键模式：模板 vs 文字要求的常见矛盾 是什么？怎么做？ | `20-Knowledge/论文格式模板匹配方法论.md` |
| cand-016 | easy | python-pptx 演示文稿自动化 中的「## 核心观点」讲了什么？ | `20-Knowledge/python-pptx 演示文稿自动化.md` |
| cand-017 | hard | ## 品牌视觉系统 是什么？怎么做？ | `20-Knowledge/python-pptx 演示文稿自动化.md` |
| cand-021 | easy | python-docx 文档自动化操作 中的「## 核心观点」讲了什么？ | `20-Knowledge/python-docx 文档自动化操作.md` |
| cand-022 | hard | ## 多文档合并模式 是什么？怎么做？ | `20-Knowledge/python-docx 文档自动化操作.md` |
| cand-026 | easy | SQLite FTS5 全文搜索配置 中的「## 核心观点」讲了什么？ | `20-Knowledge/SQLite FTS5 全文搜索配置.md` |
| cand-031 | easy | Python 数据结构 中的「## 核心观点」讲了什么？ | `20-Knowledge/Python 数据结构.md` |
| cand-036 | easy | HTML演示文稿转可编辑PPTX工作流 中的「## 核心观点」讲了什么？ | `20-Knowledge/HTML演示文稿转可编辑PPTX工作流.md` |
| cand-037 | hard | ## 技术方案/关键模式 是什么？怎么做？ | `20-Knowledge/HTML演示文稿转可编辑PPTX工作流.md` |
| cand-042 | hard | ## 适用场景 是什么？怎么做？ | `20-Knowledge/Python 函数.md` |
| cand-046 | easy | Word 复杂模板 textbox 拼接布局的精准改造方法论 中的「## 核心观点」讲了什么？ | `20-Knowledge/Word 复杂模板 textbox 拼接布局的精准改造方法论.md` |
| cand-047 | hard | ## 场景识别：什么时候不能用 editor_sdk 是什么？怎么做？ | `20-Knowledge/Word 复杂模板 textbox 拼接布局的精准改造方法论.md` |
| cand-052 | hard | ## 五版全流程对照（2026-06-17） 是什么？怎么做？ | `20-Knowledge/PaperPass降AIGC五版对照方法论.md` |
| cand-056 | easy | Python 面向对象编程 中的「## 核心观点」讲了什么？ | `20-Knowledge/Python 面向对象编程.md` |
| cand-061 | easy | Python 变量与数据类型 中的「## 核心观点」讲了什么？ | `20-Knowledge/Python 变量与数据类型.md` |
| cand-066 | easy | 社会实践报告写作方法论 中的「## 核心观点」讲了什么？ | `20-Knowledge/社会实践报告写作方法论.md` |
| cand-071 | easy | TF-IDF 中文文本去重实践 中的「## 核心观点」讲了什么？ | `20-Knowledge/TF-IDF 中文文本去重实践.md` |
| cand-072 | hard | ## 技术方案 是什么？怎么做？ | `20-Knowledge/TF-IDF 中文文本去重实践.md` |
| cand-076 | easy | Python 文件操作与异常处理 中的「## 核心观点」讲了什么？ | `20-Knowledge/Python 文件操作与异常处理.md` |
| cand-081 | easy | Python 循环 中的「## 核心观点」讲了什么？ | `20-Knowledge/Python 循环.md` |
| cand-086 | easy | 多示例标签页前端交互模式 中的「## 核心观点」讲了什么？ | `20-Knowledge/多示例标签页前端交互模式.md` |
| cand-092 | hard | ## 背景 是什么？怎么做？ | `40-Decisions/2026-09-01 PPTX导出具方案选择.md` |
| cand-094 | hard | ## 理由 是什么？怎么做？ | `40-Decisions/2026-09-01 PPTX导出具方案选择.md` |
| cand-096 | easy | LLM 响应提速：先判 prefill 还是 decode 瓶颈 中的「## 一句话结论」讲了什么？ | `20-Knowledge/LLM 响应提速：先判 prefill 还是 decode 瓶颈.md` |
| cand-097 | hard | ## 诊断决策树 是什么？怎么做？ | `20-Knowledge/LLM 响应提速：先判 prefill 还是 decode 瓶颈.md` |
| cand-101 | easy | 游戏成就碎片系统：条件重叠与贪心收集模式 中的「## 核心观点」讲了什么？ | `20-Knowledge/游戏成就碎片系统 条件重叠与贪心收集模式.md` |
| cand-102 | hard | ## 问题：条件重叠的三个典型形态 是什么？怎么做？ | `20-Knowledge/游戏成就碎片系统 条件重叠与贪心收集模式.md` |
| cand-106 | easy | Windows Java 环境配置与 VSCode 排查 中的「## 核心观点」讲了什么？ | `20-Knowledge/Windows Java 环境配置与 VSCode 排查.md` |
| cand-107 | hard | ## 标准配置（三处一致） 是什么？怎么做？ | `20-Knowledge/Windows Java 环境配置与 VSCode 排查.md` |
| cand-111 | easy | Python 模块与包 中的「## 核心观点」讲了什么？ | `20-Knowledge/Python 模块与包.md` |
| cand-116 | easy | SQLite FTS5 模式迁移与索引重建 中的「## 核心观点」讲了什么？ | `20-Knowledge/SQLite FTS5 模式迁移与索引重建.md` |
| cand-121 | easy | jieba 中文分词集成 中的「## 核心观点」讲了什么？ | `20-Knowledge/jieba 中文分词集成.md` |
| cand-122 | hard | ## 集成代码 是什么？怎么做？ | `20-Knowledge/jieba 中文分词集成.md` |
| cand-126 | easy | Godot 4.7 GDScript 踩坑清单 中的「## 核心观点」讲了什么？ | `20-Knowledge/Godot 4.7 GDScript 踩坑清单.md` |
| cand-131 | easy | Knowledge Index 中的「## LLM / AI 应用」讲了什么？ | `90-System/Indexes/Knowledge Index.md` |
| cand-136 | easy | 第 8 课：面向对象编程 (OOP) 中的「## 学习目标」讲了什么？ | `10-Projects/python-learning-lab/lessons/08_oop.md` |
| cand-137 | hard | ## 8.1 类与对象 是什么？怎么做？ | `10-Projects/python-learning-lab/lessons/08_oop.md` |
| cand-142 | hard | ## 标准工作流（8 步） 是什么？怎么做？ | `20-Knowledge/Ardot Canvas 设计稿制作工作流.md` |
| cand-146 | easy | MEMORY 中的「## 长期指令」讲了什么？ | `MEMORY.md` |
| cand-147 | hard | ## 20-Knowledge 知识条目索引 是什么？怎么做？ | `MEMORY.md` |
| cand-148 | easy | 第 6 课：文件操作 中的「## 学习目标」讲了什么？ | `10-Projects/python-learning-lab/lessons/06_files.md` |
| cand-149 | hard | ## 6.1 打开和关闭文件 是什么？怎么做？ | `10-Projects/python-learning-lab/lessons/06_files.md` |
| cand-153 | easy | 雾都拾光·洪崖洞天 — Godot 3D 平台跳跃 Demo 中的「## 目标」讲了什么？ | `10-Projects/wudu-hongyadong-godot-demo/README.md` |
| cand-154 | hard | ## 当前状态 是什么？怎么做？ | `10-Projects/wudu-hongyadong-godot-demo/README.md` |
| cand-158 | easy | dsh 插件更新与维护工作流 中的「## 核心观点」讲了什么？ | `20-Knowledge/dsh 插件更新与维护工作流.md` |
| cand-163 | easy | 第 5 课：数据结构 中的「## 学习目标」讲了什么？ | `10-Projects/python-learning-lab/lessons/05_data_structures.md` |
| cand-164 | hard | ## 5.1 列表 (List) 是什么？怎么做？ | `10-Projects/python-learning-lab/lessons/05_data_structures.md` |
| cand-169 | hard | ## Completed Projects（全部完成） 是什么？怎么做？ | `90-System/Indexes/Project Index.md` |
| cand-171 | easy | 第 7 课：模块与包 中的「## 学习目标」讲了什么？ | `10-Projects/python-learning-lab/lessons/07_modules.md` |
| cand-176 | easy | AI Knowledge Hub 中的「## 快速入口」讲了什么？ | `AI Knowledge Hub.md` |
| cand-184 | easy | 生活中的经济学论文 中的「## 目标」讲了什么？ | `10-Projects/economics-paper/README.md` |
| cand-190 | hard | ## 黄金法则 是什么？怎么做？ | `20-Knowledge/AI 工作流四步法.md` |
| cand-194 | easy | Python 练习题生成提示词 中的「## 用途」讲了什么？ | `30-Prompts/Python 练习题生成提示词.md` |
| cand-195 | hard | ## 提示词 是什么？怎么做？ | `30-Prompts/Python 练习题生成提示词.md` |
| cand-199 | easy | 2026-06-03 Python Learning Lab 技术选型决策 中的「## 决策」讲了什么？ | `40-Decisions/2026-06-03 Python Learning Lab 技术选型.md` |
| cand-204 | easy | 2026-06-04 CET-4 三层示例与中英对照结构 中的「## 决策」讲了什么？ | `40-Decisions/2026-06-04 CET-4 三层示例与中英对照结构.md` |
| cand-209 | easy | 2026-06-04 CET-4 知识库技术选型 中的「## 决策」讲了什么？ | `40-Decisions/2026-06-04 CET-4 知识库技术选型.md` |
| cand-216 | easy | 2026-06-03 Python Learning Lab 知识沉淀 中的「## 本轮目标」讲了什么？ | `50-Logs/2026-06-03 Python Learning Lab 知识沉淀.md` |
| cand-217 | hard | ## 关键产出 是什么？怎么做？ | `50-Logs/2026-06-03 Python Learning Lab 知识沉淀.md` |

## 6. 复现

```powershell
D:\python\python.exe scripts\finalize_gold.py --seed 42   # 重跑输出逐字节一致
D:\python\python.exe -m vaultmind.eval                      # 正式基线
```

SHA-256（gold_set.jsonl）：`7057c373fdee57101cacf4666d639ea7378d371d278040442baafac8ee1f2bab`

