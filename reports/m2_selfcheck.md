# VaultMind M2 检索自查表（10 问 × 3 模式，Top-5 命中判定）

> 生成时间：2026-09-16 13:48 ｜ 口径：Top-5 内出现任一「预期笔记」即算命中 ｜ 验收标准：hybrid ≥ 8/10

| # | 问题 | bm25 | vector | hybrid | hybrid Top-3 |
|---|---|---|---|---|---|
| 1 | CET-4 知识库用了什么去重方案？ | ✓ | ✓ | ✗ | 2026-06-04 CET-4 知识库开发记录 / CET-4 知识库原始项目 / CET-4 知识库原始项目 |
| 2 | SQLite FTS5 中文分词怎么配置？ | ✗ | ✓ | ✓ | TF-IDF 中文文本去重实践 / Knowledge Index / SQLite FTS5 全文搜索配置 |
| 3 | python-docx 怎么自动化操作 Word 文档？ | ✓ | ✓ | ✓ | python-docx 文档自动化操作 / 论文格式模板匹配方法论 / python-pptx 演示文稿自动化 |
| 4 | Godot 4.7 GDScript 有哪些坑？ | ✓ | ✓ | ✓ | Godot 4.7 GDScript 踩坑清单 / LLM 响应提速：先判 prefill 还是 decode 瓶颈 / DashScope 语音接口接入实录 |
| 5 | AIGC 检测的论文怎么降重？ | ✓ | ✓ | ✓ | AIGC检测论文降重分析 / 影评写作框架与格式规范 / PaperPass降AIGC五版对照方法论 |
| 6 | 论文格式模板怎么匹配？ | ✓ | ✓ | ✓ | 论文格式模板匹配方法论 / 影评写作框架与格式规范 / 重庆移通学院课程论文项目 |
| 7 | Word 复杂模板 textbox 拼接布局怎么改？ | ✓ | ✓ | ✓ | Word 复杂模板 textbox 拼接布局的精准改造方法论 / 2026-09-09 简历多页OK不强求一页 / 简历诚实改写与可迁移能力提炼法 |
| 8 | python-pptx 怎么做演示文稿？ | ✓ | ✓ | ✓ | python-pptx 演示文稿自动化 / Ardot Canvas 设计稿制作工作流 / 王克力求职自我介绍PPT项目 |
| 9 | Python 数据结构有哪些要点？ | ✓ | ✓ | ✓ | Python 数据结构 / Python 数据结构 / Python 数据结构 |
| 10 | FastAPI 轻量后端项目怎么搭？ | ✓ | ✓ | ✓ | FastAPI 轻量后端项目模板 / Knowledge Index / Windows Python 项目启动器模式 |

## 汇总

| 模式 | 命中 | 达标（≥8/10） |
|---|---|---|
| bm25 | 9/10 | ✓ |
| vector | 10/10 | ✓ |
| hybrid | 9/10 | ✓ |

## 结论

hybrid 达标（9/10），M2 验收通过；未命中的问题列入 M2→M6 优化清单。

## 漏问归因（供 M6 消融与优化）

- bm25 漏问「SQLite FTS5 中文分词怎么配置？」：Top-3 = TF-IDF 中文文本去重实践 / Knowledge Index / 2026-06-04 CET-4 知识库开发记录
- vector：无漏问。
- hybrid 漏问「CET-4 知识库用了什么去重方案？」：Top-3 = 2026-06-04 CET-4 知识库开发记录 / CET-4 知识库原始项目 / CET-4 知识库原始项目

> 已知现象：Q1（CET-4 去重方案）在 bm25/vector 单路均命中，但 RRF 融合后被高频日志类笔记挤出 Top-5 —— 「融合稀释单路强信号」是 M6 消融实验（A/B/C 三配置对比）的直接素材，如实记录。

