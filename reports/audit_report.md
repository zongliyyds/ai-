# VaultMind 知识库体检报告

> 生成时间：2026-09-20 14:35 ｜ 数据源（只读）：`D:\AI-Knowledge-Vault\AI-Knowledge-Vault` ｜ 复现命令：`D:\python\python.exe -m vaultmind.ingest`

## 1. 规模概览与基线对比

| 指标 | 本次 | 基线 | 一致性 |
|---|---|---|---|
| 笔记数 | 181 | 181 | ✓ 一致 |
| 总字符 | 330515 | 330515 | ✓ 一致 |
| 正文字符 | 294855 | 294855 | ✓ 一致 |
| H2 节数 | 1067 | 1067 | ✓ 一致 |
| H3 节数 | 274 | 274 | ✓ 一致 |
| 双链出链 | 516 | 516 | ✓ 一致 |
| 死链 | 27 | 27 | ✓ 一致 |
| 预估 chunk 数（H2+1/篇） | 1248 | 1248 | ✓ 一致 |

> 出现 ✗ 时先确认 Vault 是否有新增/修改；无变化则回查审计口径（scripts/audit_baseline.py）。

## 2. 类型分布

| type | 数量 |
|---|---|
| knowledge | 69 |
| log | 42 |
| NO_FRONTMATTER | 18 |
| decision | 17 |
| project | 14 |
| source | 14 |
| index | 4 |
| prompt | 2 |
| system-rule | 1 |

## 3. 状态分布（治理点：completed 与 complete 混用）

| status | 数量 |
|---|---|
| active | 150 |
| (none) | 18 |
| completed | 10 |
| complete | 2 |
| draft | 1 |

## 4. 顶层目录分布

| 目录 | 数量 |
|---|---|
| 20-Knowledge | 70 |
| 50-Logs | 42 |
| 10-Projects | 22 |
| 40-Decisions | 17 |
| 60-References | 13 |
| 90-System | 11 |
| AI Knowledge Hub.md | 1 |
| MEMORY.md | 1 |
| 未命名 1.md | 1 |
| 未命名.md | 1 |
| 欢迎.md | 1 |
| 30-Prompts | 1 |

## 5. 图谱与链接健康

- 出链总数 **516**，其中死链 **27**（死链率 5.2%）
- 孤儿笔记（无入链，排除 90-System/.obsidian）：**47** 篇，Top-25（按体量）：

1. `20-Knowledge/Godot 4.7 GDScript 踩坑清单.md`
2. `10-Projects/python-learning-lab/lessons/08_oop.md`
3. `10-Projects/python-learning-lab/lessons/06_files.md`
4. `10-Projects/wudu-hongyadong-godot-demo/README.md`
5. `10-Projects/python-learning-lab/lessons/05_data_structures.md`
6. `10-Projects/python-learning-lab/lessons/07_modules.md`
7. `10-Projects/python-learning-lab/README.md`
8. `10-Projects/python-learning-lab/lessons/04_functions.md`
9. `10-Projects/python-learning-lab/lessons/03_loops.md`
10. `10-Projects/wang-li-ai-product-resume/README.md`
11. `50-Logs/2026-09-20 dsh 密钥失效与端口残留排查.md`
12. `10-Projects/shuangti-weekly-report/README.md`
13. `50-Logs/2026-06-22 职场关键能力论文三轮迭代.md`
14. `10-Projects/python-learning-lab/lessons/02_conditions.md`
15. `10-Projects/python-learning-lab/lessons/01_variables.md`
16. `50-Logs/2026-09-17 VaultMind 知识沉淀入库与检索索引更新.md`
17. `60-References/职场关键能力课程论文项目.md`
18. `10-Projects/vaultmind-rag/README.md`
19. `60-References/CET-4 知识库参考笔记.md`
20. `50-Logs/2026-09-01 王克力求职自我介绍PPT制作.md`
21. `10-Projects/python-learning-lab/capstone/project_spec.md`
22. `50-Logs/2026-06-03 Python Learning Lab 知识沉淀.md`
23. `50-Logs/2026-06-06 CET-4 4级基础模块开发.md`
24. `10-Projects/wang-keli-interview-ppt/README.md`
25. `50-Logs/2026-06-04 CET-4 知识库开发记录.md`

- 入链 Top 12：

| 笔记 | 入链数 |
|---|---|
| 10-Projects/cet4-knowledge-base/README.md | 38 |
| 20-Knowledge/论文格式模板匹配方法论.md | 12 |
| 20-Knowledge/python-docx 文档自动化操作.md | 10 |
| 20-Knowledge/AIGC检测论文降重分析.md | 10 |
| 20-Knowledge/消融实验方法论：负结果也是结论.md | 9 |
| 20-Knowledge/python-pptx 演示文稿自动化.md | 9 |
| 20-Knowledge/SQLite FTS5 全文搜索配置.md | 9 |
| 20-Knowledge/Python 数据结构.md | 9 |
| 20-Knowledge/素材驱动写作 先分层收全再动笔.md | 8 |
| 20-Knowledge/docx 范文逆向与格式复刻工作流.md | 8 |
| 20-Knowledge/HTML演示文稿转可编辑PPTX工作流.md | 8 |
| 20-Knowledge/Python 函数.md | 8 |

## 6. 元数据治理

- 无 frontmatter：**17** 篇
- 有 frontmatter 但缺 type：**1** 篇
- 0 字节文件：**2** 个：`未命名 1.md`、`未命名.md`

无 frontmatter 清单：

- `MEMORY.md`
- `未命名 1.md`
- `未命名.md`
- `欢迎.md`
- `10-Projects/python-learning-lab/capstone/project_spec.md`
- `10-Projects/python-learning-lab/lessons/01_variables.md`
- `10-Projects/python-learning-lab/lessons/02_conditions.md`
- `10-Projects/python-learning-lab/lessons/03_loops.md`
- `10-Projects/python-learning-lab/lessons/04_functions.md`
- `10-Projects/python-learning-lab/lessons/05_data_structures.md`
- `10-Projects/python-learning-lab/lessons/06_files.md`
- `10-Projects/python-learning-lab/lessons/07_modules.md`
- `10-Projects/python-learning-lab/lessons/08_oop.md`
- `20-Knowledge/dsh 插件更新与维护工作流.md`
- `40-Decisions/2026-09-12 dsh 插件更新 pnpm v11 对齐与构建策略.md`
- `50-Logs/2026-09-12 dsh 插件检查更新.md`
- `90-System/Indexes/Decision Index.md`

## 7. 分块与索引（本次管道产出）

| 指标 | 值 |
|---|---|
| docs 表行数 | 181 |
| chunks 行数 | 1437 |
| links 行数 | 516 |
| FTS5 索引行数 | 1437 |
| 索引库 | `D:\RAG\data\vaultmind.db`（3700.0 KB） |

> 分块口径：每篇 1 个「概述」chunk + 每个 H2 小节 1 个 chunk；超 600 字的小节按 H3/段落二次切分；每个 chunk 注入元数据前缀。

## 8. 体检结论与治理建议（只建议、不代改——Vault 由用户手动维护）

1. **清理 0 字节文件**：`未命名 1.md`、`未命名.md` 没有任何内容，建议在 Obsidian 中直接删除。
2. **统一状态取值**：`completed`（10）与 `complete`（2）混用，建议全局统一为 `completed`。
3. **补齐 frontmatter**：17 篇笔记缺 frontmatter，建议补 type/status/tags 三字段。
4. **修复失效双链**：27 条出链指向不存在的笔记（死链率 5.2%），建议逐一修复或删除。
5. **孤儿笔记**：47 篇无任何入链，建议在索引页（90-System/Indexes）补入口或并入相关主题。

> 治理前后对比（覆盖率、死链率、孤儿数）将作为 AI 数据分析方向的可视化素材。

