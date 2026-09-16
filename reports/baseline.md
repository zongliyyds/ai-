# VaultMind 检索基线报告（baseline）

> 生成时间：2026-09-16 13:54 ｜ 检索模式：hybrid ｜ top_k=10 ｜ 口径：仅统计 status=approved 的 gold 条目

## 指标总表

| 指标 | 值 |
|---|---|
| 查询数 | 20 |
| Recall@1 | 0.9500 |
| Recall@5 | 1.0000 |
| Recall@10 | 1.0000 |
| MRR | 0.9750 |
| nDCG@10 | 0.9815 |
| 平均延迟 | 0.569 s |

> 目标值（立项书 §七，先测基线再定稿数字）：Recall@5 ≥ 0.80，MRR ≥ 0.65，nDCG@10 ≥ 0.70。

## 逐题明细

| id | 问题 | 首中排名 | Top-5 命中 | Top-3 文档 | 延迟 |
|---|---|---|---|---|---|
| cand-001 | CET-4 英语四级备考技巧知识库 中的「## 目标」讲了什么？ | 1 | ✓ | README / CET-4 知识库参考笔记 / README | 3.578s |
| cand-006 | 论文格式模板匹配方法论 中的「## 核心观点」讲了什么？ | 1 | ✓ | 论文格式模板匹配方法论 / 影评写作框架与格式规范 / 重庆移通学院课程论文项目 | 0.386s |
| cand-011 | AIGC检测论文降重分析 中的「## 核心观点」讲了什么？ | 1 | ✓ | AIGC检测论文降重分析 / 影评写作框架与格式规范 / PaperPass降AIGC五版对照方法论 | 0.381s |
| cand-016 | python-pptx 演示文稿自动化 中的「## 核心观点」讲了什么？ | 1 | ✓ | python-pptx 演示文稿自动化 / python-docx 文档自动化操作 / HTML演示文稿转可编辑PPTX工作流 | 0.413s |
| cand-021 | python-docx 文档自动化操作 中的「## 核心观点」讲了什么？ | 1 | ✓ | python-docx 文档自动化操作 / 论文格式模板匹配方法论 / python-docx 中文复习资料排版模式 | 0.387s |
| cand-026 | SQLite FTS5 全文搜索配置 中的「## 核心观点」讲了什么？ | 1 | ✓ | SQLite FTS5 全文搜索配置 / SQLite FTS5 模式迁移与索引重建 / 纯文本内容智能格式化模式 | 0.389s |
| cand-031 | Python 数据结构 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 数据结构 / Python 数据结构 / Python 数据结构 | 0.398s |
| cand-036 | HTML演示文稿转可编辑PPTX工作流 中的「## 核心观点」讲了什么？ | 1 | ✓ | HTML演示文稿转可编辑PPTX工作流 / 2026-09-01 王克力求职自我介绍PPT制作 / Ardot Canvas 设计稿制作工作流 | 0.395s |
| cand-041 | Python 函数 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 函数 / Python 函数 / Python 数据结构 | 0.402s |
| cand-046 | Word 复杂模板 textbox 拼接布局的精准改造方法论 中的「## 核心观点」讲了什么？ | 1 | ✓ | Word 复杂模板 textbox 拼接布局的精准改造方法论 / 简历诚实改写与可迁移能力提炼法 / 2026-09-09 简历多页OK不强求一页 | 0.407s |
| cand-051 | PaperPass降AIGC五版对照方法论 中的「## 核心观点」讲了什么？ | 1 | ✓ | PaperPass降AIGC五版对照方法论 / AIGC检测论文降重分析 / 2026-06-17 降重实验五版对照 | 0.382s |
| cand-056 | Python 面向对象编程 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 面向对象编程 / Python CLI 项目设计模式 / Python 模块与包 | 0.380s |
| cand-061 | Python 变量与数据类型 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 变量与数据类型 / 01_variables / Knowledge Index | 0.399s |
| cand-066 | 社会实践报告写作方法论 中的「## 核心观点」讲了什么？ | 1 | ✓ | 社会实践报告写作方法论 / README / 社会实践报告写作方法论 | 0.360s |
| cand-071 | TF-IDF 中文文本去重实践 中的「## 核心观点」讲了什么？ | 1 | ✓ | TF-IDF 中文文本去重实践 / SQLite FTS5 全文搜索配置 / jieba 中文分词集成 | 0.428s |
| cand-076 | Python 文件操作与异常处理 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 文件操作与异常处理 / Pandas 数据清洗与可视化工作流 / Python 文件操作与异常处理 | 0.445s |
| cand-081 | Python 循环 中的「## 核心观点」讲了什么？ | 2 | ✓ | Python 数据结构 / Python 循环 / Python 循环 | 0.432s |
| cand-086 | 多示例标签页前端交互模式 中的「## 核心观点」讲了什么？ | 1 | ✓ | 多示例标签页前端交互模式 / 2026-06-06 CET-4 基础模块详情展示简化 / 2026-06-04 CET-4 示例体系升级 | 0.459s |
| cand-091 | 2026-09-01 PPTX导出方案选择 中的「## 决策」讲了什么？ | 1 | ✓ | 2026-09-01 PPTX导出具方案选择 / 2026-09-01 王克力求职自我介绍PPT制作 / Decision Index | 0.519s |
| cand-096 | LLM 响应提速：先判 prefill 还是 decode 瓶颈 中的「## 一句话结论」讲了什么？ | 1 | ✓ | LLM 响应提速：先判 prefill 还是 decode 瓶颈 / Knowledge Index / MEMORY | 0.433s |

## 复现

```powershell
D:\python\python.exe -m vaultmind.eval
```

