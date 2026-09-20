# VaultMind 检索基线报告（baseline）

> 生成时间：2026-09-20 14:34 ｜ 检索模式：bm25 ｜ top_k=10 ｜ 口径：仅统计 status=approved 的 gold 条目

## 指标总表

| 指标 | 值 |
|---|---|
| 查询数 | 60 |
| Recall@1 | 0.8167 |
| Recall@5 | 0.9333 |
| Recall@10 | 0.9333 |
| MRR | 0.8672 |
| nDCG@10 | 0.8840 |
| 平均延迟 | 0.003 s |

> 目标值（立项书 §七，先测基线再定稿数字）：Recall@5 ≥ 0.80，MRR ≥ 0.65，nDCG@10 ≥ 0.70。

## 逐题明细

| id | 问题 | 首中排名 | Top-5 命中 | Top-3 文档 | 延迟 |
|---|---|---|---|---|---|
| cand-006 | 论文格式模板匹配方法论 中的「## 核心观点」讲了什么？ | 1 | ✓ | 论文格式模板匹配方法论 / 论文格式模板匹配方法论 / 论文格式模板匹配方法论 | 0.003s |
| cand-007 | ## 关键模式：模板 vs 文字要求的常见矛盾 是什么？怎么做？ | 1 | ✓ | 论文格式模板匹配方法论 / 2026-06-11 课程论文项目完成 / 论文格式模板匹配方法论 | 0.003s |
| cand-016 | python-pptx 演示文稿自动化 中的「## 核心观点」讲了什么？ | 1 | ✓ | python-pptx 演示文稿自动化 / python-pptx 演示文稿自动化 / 王克力求职自我介绍PPT项目 | 0.003s |
| cand-017 | ## 品牌视觉系统 是什么？怎么做？ | 1 | ✓ | python-pptx 演示文稿自动化 / python-pptx 演示文稿自动化 / README | 0.002s |
| cand-021 | python-docx 文档自动化操作 中的「## 核心观点」讲了什么？ | 1 | ✓ | python-docx 文档自动化操作 / python-docx 文档自动化操作 / python-docx 文档自动化操作 | 0.005s |
| cand-022 | ## 多文档合并模式 是什么？怎么做？ | 1 | ✓ | python-docx 文档自动化操作 / python-docx 文档自动化操作 / Knowledge Index | 0.004s |
| cand-026 | SQLite FTS5 全文搜索配置 中的「## 核心观点」讲了什么？ | 1 | ✓ | SQLite FTS5 全文搜索配置 / SQLite FTS5 全文搜索配置 / SQLite FTS5 全文搜索配置 | 0.003s |
| cand-031 | Python 数据结构 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 数据结构 / Python 初学者学习路线 / jieba 中文分词集成 | 0.003s |
| cand-036 | HTML演示文稿转可编辑PPTX工作流 中的「## 核心观点」讲了什么？ | 1 | ✓ | HTML演示文稿转可编辑PPTX工作流 / 王克力求职自我介绍PPT项目 / Ardot Canvas 设计稿制作工作流 | 0.003s |
| cand-037 | ## 技术方案/关键模式 是什么？怎么做？ | 2 | ✓ | 多示例标签页前端交互模式 / HTML演示文稿转可编辑PPTX工作流 / 前端子标签过滤模式 | 0.003s |
| cand-042 | ## 适用场景 是什么？怎么做？ | - | ✗ | 前端子标签过滤模式 / Godot 4 headless 冒烟自测工作流 / Python 面向对象编程 | 0.002s |
| cand-046 | Word 复杂模板 textbox 拼接布局的精准改造方法论 中的「## 核心观点」讲了什么？ | 1 | ✓ | Word 复杂模板 textbox 拼接布局的精准改造方法论 / Word 复杂模板 textbox 拼接布局的精准改造方法论 / Word 复杂模板 textbox 拼接布局的精准改造方法论 | 0.003s |
| cand-047 | ## 场景识别：什么时候不能用 editor_sdk 是什么？怎么做？ | 1 | ✓ | Word 复杂模板 textbox 拼接布局的精准改造方法论 / Word 复杂模板 textbox 拼接布局的精准改造方法论 / Word 复杂模板 textbox 拼接布局的精准改造方法论 | 0.002s |
| cand-052 | ## 五版全流程对照（2026-06-17） 是什么？怎么做？ | 2 | ✓ | 2026-06-17 降重实验五版对照 / PaperPass降AIGC五版对照方法论 / PaperPass降AIGC五版对照方法论 | 0.002s |
| cand-056 | Python 面向对象编程 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 面向对象编程 / jieba 中文分词集成 / Python 函数 | 0.003s |
| cand-061 | Python 变量与数据类型 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 变量与数据类型 / Python 变量与数据类型 / 01_variables | 0.003s |
| cand-066 | 社会实践报告写作方法论 中的「## 核心观点」讲了什么？ | 1 | ✓ | 社会实践报告写作方法论 / README / 社会实践报告写作方法论 | 0.002s |
| cand-071 | TF-IDF 中文文本去重实践 中的「## 核心观点」讲了什么？ | 1 | ✓ | TF-IDF 中文文本去重实践 / TF-IDF 中文文本去重实践 / jieba 中文分词集成 | 0.002s |
| cand-072 | ## 技术方案 是什么？怎么做？ | - | ✗ | 2026-06-03 Python Learning Lab 技术选型 / de-aigc-writing-techniques / 前端子标签过滤模式 | 0.002s |
| cand-076 | Python 文件操作与异常处理 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 文件操作与异常处理 / Python 文件操作与异常处理 / Python 数据结构 | 0.004s |
| cand-081 | Python 循环 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 循环 / jieba 中文分词集成 / Python 函数 | 0.003s |
| cand-086 | 多示例标签页前端交互模式 中的「## 核心观点」讲了什么？ | 1 | ✓ | 多示例标签页前端交互模式 / 前端子标签过滤模式 / 多示例标签页前端交互模式 | 0.005s |
| cand-092 | ## 背景 是什么？怎么做？ | - | ✗ | 2026-09-06 登顶贺卡与碎片收集系统 / 2026-06-03 Python Learning Lab 技术选型 / SQLite FTS5 全文搜索配置 | 0.001s |
| cand-094 | ## 理由 是什么？怎么做？ | 5 | ✓ | 2026-08-25 语音识别三层降级路由选择 / 2026-06-03 Python Learning Lab 技术选型 / SQLite FTS5 全文搜索配置 | 0.001s |
| cand-096 | LLM 响应提速：先判 prefill 还是 decode 瓶颈 中的「## 一句话结论」讲了什么？ | 1 | ✓ | LLM 响应提速：先判 prefill 还是 decode 瓶颈 / LLM 响应提速：先判 prefill 还是 decode 瓶颈 / LLM 响应提速：先判 prefill 还是 decode 瓶颈 | 0.003s |
| cand-097 | ## 诊断决策树 是什么？怎么做？ | 1 | ✓ | LLM 响应提速：先判 prefill 还是 decode 瓶颈 / Godot 角色浮空诊断与修复 / Godot 角色浮空诊断与修复 | 0.001s |
| cand-101 | 游戏成就碎片系统：条件重叠与贪心收集模式 中的「## 核心观点」讲了什么？ | 1 | ✓ | 游戏成就碎片系统 条件重叠与贪心收集模式 / 游戏成就碎片系统 条件重叠与贪心收集模式 / Knowledge Index | 0.004s |
| cand-102 | ## 问题：条件重叠的三个典型形态 是什么？怎么做？ | 1 | ✓ | 游戏成就碎片系统 条件重叠与贪心收集模式 / 游戏成就碎片系统 条件重叠与贪心收集模式 / 游戏成就碎片系统 条件重叠与贪心收集模式 | 0.002s |
| cand-106 | Windows Java 环境配置与 VSCode 排查 中的「## 核心观点」讲了什么？ | 1 | ✓ | Windows Java 环境配置与 VSCode 排查 / Windows Java 环境配置与 VSCode 排查 / 2026-06-19 Java 与 VSCode 配置排查 | 0.004s |
| cand-107 | ## 标准配置（三处一致） 是什么？怎么做？ | 1 | ✓ | Windows Java 环境配置与 VSCode 排查 / Windows Java 环境配置与 VSCode 排查 / dsh 密钥来源与端口残留排查 | 0.001s |
| cand-111 | Python 模块与包 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 模块与包 / Python 模块与包 / Python 面向对象编程 | 0.004s |
| cand-116 | SQLite FTS5 模式迁移与索引重建 中的「## 核心观点」讲了什么？ | 1 | ✓ | SQLite FTS5 模式迁移与索引重建 / SQLite FTS5 模式迁移与索引重建 / Knowledge Index | 0.004s |
| cand-121 | jieba 中文分词集成 中的「## 核心观点」讲了什么？ | 1 | ✓ | jieba 中文分词集成 / jieba 中文分词集成 / jieba 中文分词集成 | 0.002s |
| cand-122 | ## 集成代码 是什么？怎么做？ | 1 | ✓ | jieba 中文分词集成 / SQLite FTS5 全文搜索配置 / jieba 中文分词集成 | 0.001s |
| cand-126 | Godot 4.7 GDScript 踩坑清单 中的「## 核心观点」讲了什么？ | 1 | ✓ | Godot 4.7 GDScript 踩坑清单 / Godot 4.7 GDScript 踩坑清单 / Godot 4.7 GDScript 踩坑清单 | 0.003s |
| cand-131 | Knowledge Index 中的「## LLM / AI 应用」讲了什么？ | 1 | ✓ | Knowledge Index / Knowledge Index / AI Knowledge Hub | 0.003s |
| cand-136 | 第 8 课：面向对象编程 (OOP) 中的「## 学习目标」讲了什么？ | 2 | ✓ | 07_modules / 08_oop / 08_oop | 0.003s |
| cand-137 | ## 8.1 类与对象 是什么？怎么做？ | 1 | ✓ | 08_oop / 08_oop / Python 面向对象编程 | 0.003s |
| cand-142 | ## 标准工作流（8 步） 是什么？怎么做？ | 1 | ✓ | Ardot Canvas 设计稿制作工作流 / Ardot Canvas 设计稿制作工作流 / Ardot Canvas 设计稿制作工作流 | 0.002s |
| cand-146 | MEMORY 中的「## 长期指令」讲了什么？ | 1 | ✓ | MEMORY / 2026-06-06 CET-4 4级基础模块与刘晓艳词汇书主源 / MEMORY | 0.002s |
| cand-147 | ## 20-Knowledge 知识条目索引 是什么？怎么做？ | 1 | ✓ | MEMORY / MEMORY / MEMORY | 0.002s |
| cand-148 | 第 6 课：文件操作 中的「## 学习目标」讲了什么？ | 1 | ✓ | 06_files / 05_data_structures / 06_files | 0.003s |
| cand-149 | ## 6.1 打开和关闭文件 是什么？怎么做？ | 1 | ✓ | 06_files / Python 文件操作与异常处理 / Python 文件操作与异常处理 | 0.002s |
| cand-153 | 雾都拾光·洪崖洞天 — Godot 3D 平台跳跃 Demo 中的「## 目标」讲了什么？ | 1 | ✓ | README / README / 2026-08-19 雾都拾光洪崖洞天Godot游戏Demo开发 | 0.002s |
| cand-154 | ## 当前状态 是什么？怎么做？ | - | ✗ | README / README / README | 0.001s |
| cand-158 | dsh 插件更新与维护工作流 中的「## 核心观点」讲了什么？ | 1 | ✓ | dsh 插件更新与维护工作流 / dsh 插件更新与维护工作流 / 2026-09-12 dsh 插件检查更新 | 0.003s |
| cand-163 | 第 5 课：数据结构 中的「## 学习目标」讲了什么？ | 1 | ✓ | 05_data_structures / 04_functions / 05_data_structures | 0.003s |
| cand-164 | ## 5.1 列表 (List) 是什么？怎么做？ | 2 | ✓ | Python 数据结构 / 05_data_structures / 05_data_structures | 0.001s |
| cand-169 | ## Completed Projects（全部完成） 是什么？怎么做？ | 1 | ✓ | Project Index / 2026-06-17 知识库全面整理 / Project Index | 0.003s |
| cand-171 | 第 7 课：模块与包 中的「## 学习目标」讲了什么？ | 1 | ✓ | 07_modules / 07_modules / 06_files | 0.005s |
| cand-176 | AI Knowledge Hub 中的「## 快速入口」讲了什么？ | 1 | ✓ | AI Knowledge Hub / AI Knowledge Hub / 2026-05-29 AI Knowledge Base Init | 0.004s |
| cand-184 | 生活中的经济学论文 中的「## 目标」讲了什么？ | 1 | ✓ | README / README / README | 0.003s |
| cand-190 | ## 黄金法则 是什么？怎么做？ | 1 | ✓ | AI 工作流四步法 / MEMORY / Knowledge Index | 0.002s |
| cand-194 | Python 练习题生成提示词 中的「## 用途」讲了什么？ | 1 | ✓ | Python 练习题生成提示词 / Prompt Index / 2026-06-03 Python Learning Lab 知识沉淀 | 0.003s |
| cand-195 | ## 提示词 是什么？怎么做？ | 3 | ✓ | 2026-06-03 Python Learning Lab 知识沉淀 / Prompt Index / Python 练习题生成提示词 | 0.002s |
| cand-199 | 2026-06-03 Python Learning Lab 技术选型决策 中的「## 决策」讲了什么？ | 1 | ✓ | 2026-06-03 Python Learning Lab 技术选型 / 2026-06-03 Python Learning Lab 知识沉淀 / 2026-06-03 Python Learning Lab 技术选型 | 0.004s |
| cand-204 | 2026-06-04 CET-4 三层示例与中英对照结构 中的「## 决策」讲了什么？ | 1 | ✓ | 2026-06-04 CET-4 三层示例与中英对照结构 / Decision Index / CET-4 知识库原始项目 | 0.004s |
| cand-209 | 2026-06-04 CET-4 知识库技术选型 中的「## 决策」讲了什么？ | 1 | ✓ | 2026-06-04 CET-4 知识库技术选型 / 2026-06-04 CET-4 知识库技术选型 / Decision Index | 0.005s |
| cand-216 | 2026-06-03 Python Learning Lab 知识沉淀 中的「## 本轮目标」讲了什么？ | 1 | ✓ | 2026-06-03 Python Learning Lab 知识沉淀 / 2026-06-03 Python Learning Lab 知识沉淀 / 2026-06-03 Python Learning Lab 知识沉淀 | 0.006s |
| cand-217 | ## 关键产出 是什么？怎么做？ | 2 | ✓ | Python 面向对象编程 / 2026-06-03 Python Learning Lab 知识沉淀 / 2026-08-25 认知植入WO-010 | 0.003s |

## 复现

```powershell
D:\python\python.exe -m vaultmind.eval
```

