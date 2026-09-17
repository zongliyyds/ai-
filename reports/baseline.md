# VaultMind 检索基线报告（baseline）

> 生成时间：2026-09-17 09:48 ｜ 检索模式：hybrid ｜ top_k=10 ｜ 口径：仅统计 status=approved 的 gold 条目

## 指标总表

| 指标 | 值 |
|---|---|
| 查询数 | 60 |
| Recall@1 | 0.6333 |
| Recall@5 | 0.8167 |
| Recall@10 | 0.8333 |
| MRR | 0.7096 |
| nDCG@10 | 0.7403 |
| 平均延迟 | 0.253 s |

> 目标值（立项书 §七，先测基线再定稿数字）：Recall@5 ≥ 0.80，MRR ≥ 0.65，nDCG@10 ≥ 0.70。

## 逐题明细

| id | 问题 | 首中排名 | Top-5 命中 | Top-3 文档 | 延迟 |
|---|---|---|---|---|---|
| cand-006 | 论文格式模板匹配方法论 中的「## 核心观点」讲了什么？ | 1 | ✓ | 论文格式模板匹配方法论 / 影评写作框架与格式规范 / 重庆移通学院课程论文项目 | 1.206s |
| cand-007 | ## 关键模式：模板 vs 文字要求的常见矛盾 是什么？怎么做？ | 1 | ✓ | 论文格式模板匹配方法论 / 论文格式模板匹配方法论 / 论文格式模板匹配方法论 | 0.229s |
| cand-016 | python-pptx 演示文稿自动化 中的「## 核心观点」讲了什么？ | 1 | ✓ | python-pptx 演示文稿自动化 / python-docx 文档自动化操作 / HTML演示文稿转可编辑PPTX工作流 | 0.253s |
| cand-017 | ## 品牌视觉系统 是什么？怎么做？ | 4 | ✓ | 四选一答题系统设计 / README / 汽车销售数据分析 | 0.248s |
| cand-021 | python-docx 文档自动化操作 中的「## 核心观点」讲了什么？ | 1 | ✓ | python-docx 文档自动化操作 / 论文格式模板匹配方法论 / python-docx 中文复习资料排版模式 | 0.254s |
| cand-022 | ## 多文档合并模式 是什么？怎么做？ | 1 | ✓ | python-docx 文档自动化操作 / Ardot Canvas 设计稿制作工作流 / 多示例标签页前端交互模式 | 0.248s |
| cand-026 | SQLite FTS5 全文搜索配置 中的「## 核心观点」讲了什么？ | 1 | ✓ | SQLite FTS5 全文搜索配置 / SQLite FTS5 模式迁移与索引重建 / 纯文本内容智能格式化模式 | 0.223s |
| cand-031 | Python 数据结构 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 数据结构 / Python 数据结构 / Python 数据结构 | 0.223s |
| cand-036 | HTML演示文稿转可编辑PPTX工作流 中的「## 核心观点」讲了什么？ | 1 | ✓ | HTML演示文稿转可编辑PPTX工作流 / 2026-09-01 王克力求职自我介绍PPT制作 / Ardot Canvas 设计稿制作工作流 | 0.237s |
| cand-037 | ## 技术方案/关键模式 是什么？怎么做？ | - | ✗ | de-aigc-writing-techniques / 职场关键能力课程论文项目 / README | 0.242s |
| cand-042 | ## 适用场景 是什么？怎么做？ | 5 | ✓ | Python 循环 / 多示例标签页前端交互模式 / Python 面向对象编程 | 0.239s |
| cand-046 | Word 复杂模板 textbox 拼接布局的精准改造方法论 中的「## 核心观点」讲了什么？ | 1 | ✓ | Word 复杂模板 textbox 拼接布局的精准改造方法论 / 简历诚实改写与可迁移能力提炼法 / 2026-09-09 简历多页OK不强求一页 | 0.259s |
| cand-047 | ## 场景识别：什么时候不能用 editor_sdk 是什么？怎么做？ | 1 | ✓ | Word 复杂模板 textbox 拼接布局的精准改造方法论 / README / Word 复杂模板 textbox 拼接布局的精准改造方法论 | 0.243s |
| cand-052 | ## 五版全流程对照（2026-06-17） 是什么？怎么做？ | 3 | ✓ | 2026-06-17 降重实验五版对照 / 2026-06-17 知识库全面整理 / PaperPass降AIGC五版对照方法论 | 0.228s |
| cand-056 | Python 面向对象编程 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 面向对象编程 / Python CLI 项目设计模式 / Python 模块与包 | 0.226s |
| cand-061 | Python 变量与数据类型 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 变量与数据类型 / 01_variables / Knowledge Index | 0.232s |
| cand-066 | 社会实践报告写作方法论 中的「## 核心观点」讲了什么？ | 1 | ✓ | 社会实践报告写作方法论 / README / 社会实践报告写作方法论 | 0.221s |
| cand-071 | TF-IDF 中文文本去重实践 中的「## 核心观点」讲了什么？ | 1 | ✓ | TF-IDF 中文文本去重实践 / SQLite FTS5 全文搜索配置 / jieba 中文分词集成 | 0.208s |
| cand-072 | ## 技术方案 是什么？怎么做？ | - | ✗ | de-aigc-writing-techniques / 2026-09-01 PPTX导出具方案选择 / project_spec | 0.227s |
| cand-076 | Python 文件操作与异常处理 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 文件操作与异常处理 / Pandas 数据清洗与可视化工作流 / Python 文件操作与异常处理 | 0.223s |
| cand-081 | Python 循环 中的「## 核心观点」讲了什么？ | 2 | ✓ | Python 数据结构 / Python 循环 / Python 循环 | 0.235s |
| cand-086 | 多示例标签页前端交互模式 中的「## 核心观点」讲了什么？ | 1 | ✓ | 多示例标签页前端交互模式 / 2026-06-06 CET-4 基础模块详情展示简化 / 2026-06-04 CET-4 示例体系升级 | 0.230s |
| cand-092 | ## 背景 是什么？怎么做？ | - | ✗ | AI 工作流四步法 / 简历诚实改写与可迁移能力提炼法 / AI 工作流四步法 | 0.220s |
| cand-094 | ## 理由 是什么？怎么做？ | - | ✗ | Python 面向对象编程 / 2026-06-06 CET-4 答题系统与必备词汇模块 / 2026-06-06 CET-4 答题系统与必备词汇模块 | 0.243s |
| cand-096 | LLM 响应提速：先判 prefill 还是 decode 瓶颈 中的「## 一句话结论」讲了什么？ | 1 | ✓ | LLM 响应提速：先判 prefill 还是 decode 瓶颈 / Knowledge Index / MEMORY | 0.322s |
| cand-097 | ## 诊断决策树 是什么？怎么做？ | - | ✗ | Godot 角色浮空诊断与修复 / Python 条件判断 / 2026-06-03 Python Learning Lab 技术选型 | 0.295s |
| cand-101 | 游戏成就碎片系统：条件重叠与贪心收集模式 中的「## 核心观点」讲了什么？ | 1 | ✓ | 游戏成就碎片系统 条件重叠与贪心收集模式 / Knowledge Index / 游戏成就碎片系统 条件重叠与贪心收集模式 | 0.285s |
| cand-102 | ## 问题：条件重叠的三个典型形态 是什么？怎么做？ | 1 | ✓ | 游戏成就碎片系统 条件重叠与贪心收集模式 / 游戏成就碎片系统 条件重叠与贪心收集模式 / Knowledge Index | 0.283s |
| cand-106 | Windows Java 环境配置与 VSCode 排查 中的「## 核心观点」讲了什么？ | 1 | ✓ | Windows Java 环境配置与 VSCode 排查 / 2026-06-19 Java JAVA_HOME 修正为 JDK 目录 / 2026-06-19 Java 与 VSCode 配置排查 | 0.282s |
| cand-107 | ## 标准配置（三处一致） 是什么？怎么做？ | 8 | ✗ | 2026-06-19 Java JAVA_HOME 修正为 JDK 目录 / Knowledge Index / Python 面向对象编程 | 0.288s |
| cand-111 | Python 模块与包 中的「## 核心观点」讲了什么？ | 1 | ✓ | Python 模块与包 / 07_modules / Python 函数 | 0.301s |
| cand-116 | SQLite FTS5 模式迁移与索引重建 中的「## 核心观点」讲了什么？ | 1 | ✓ | SQLite FTS5 模式迁移与索引重建 / Knowledge Index / 2026-06-04 CET-4 示例体系升级 | 0.283s |
| cand-121 | jieba 中文分词集成 中的「## 核心观点」讲了什么？ | 1 | ✓ | jieba 中文分词集成 / jieba 中文分词集成 / Knowledge Index | 0.209s |
| cand-122 | ## 集成代码 是什么？怎么做？ | 1 | ✓ | jieba 中文分词集成 / jieba 中文分词集成 / 04_functions | 0.211s |
| cand-126 | Godot 4.7 GDScript 踩坑清单 中的「## 核心观点」讲了什么？ | 1 | ✓ | Godot 4.7 GDScript 踩坑清单 / DashScope 语音接口接入实录 / 2026-08-25 主菜单设置按钮修复WO-013 | 0.253s |
| cand-131 | Knowledge Index 中的「## LLM / AI 应用」讲了什么？ | 3 | ✓ | 2026-06-03 Python Learning Lab 知识沉淀 / AI Knowledge Hub / Knowledge Index | 0.236s |
| cand-136 | 第 8 课：面向对象编程 (OOP) 中的「## 学习目标」讲了什么？ | 2 | ✓ | 07_modules / 08_oop / 05_data_structures | 0.212s |
| cand-137 | ## 8.1 类与对象 是什么？怎么做？ | 1 | ✓ | 08_oop / 08_oop / Python 面向对象编程 | 0.226s |
| cand-142 | ## 标准工作流（8 步） 是什么？怎么做？ | - | ✗ | Knowledge Index / Knowledge Index / AI 工作流四步法 | 0.245s |
| cand-146 | MEMORY 中的「## 长期指令」讲了什么？ | - | ✗ | AI 工作流四步法 / AI-Knowledge-Base-Rules / 2026-09-09 简历模板虚构实习必须替换为真实经历 | 0.230s |
| cand-147 | ## 20-Knowledge 知识条目索引 是什么？怎么做？ | 1 | ✓ | MEMORY / CET-4 知识库参考笔记 / AI Knowledge Hub | 0.251s |
| cand-148 | 第 6 课：文件操作 中的「## 学习目标」讲了什么？ | 2 | ✓ | 05_data_structures / 06_files / 07_modules | 0.231s |
| cand-149 | ## 6.1 打开和关闭文件 是什么？怎么做？ | 1 | ✓ | 06_files / Python 文件操作与异常处理 / 2026-06-04 CET-4 启动器闪退修复 | 0.204s |
| cand-153 | 雾都拾光·洪崖洞天 — Godot 3D 平台跳跃 Demo 中的「## 目标」讲了什么？ | 1 | ✓ | README / 2026-08-19 雾都拾光洪崖洞天Godot游戏Demo开发 / LLM 响应提速：先判 prefill 还是 decode 瓶颈 | 0.236s |
| cand-154 | ## 当前状态 是什么？怎么做？ | - | ✗ | 四选一答题系统设计 / 02_conditions / DashScope 语音接口接入实录 | 0.218s |
| cand-158 | dsh 插件更新与维护工作流 中的「## 核心观点」讲了什么？ | 2 | ✓ | 2026-09-12 dsh 插件检查更新 / 2026-09-12 dsh 插件检查更新 / dsh 插件更新与维护工作流 | 0.213s |
| cand-163 | 第 5 课：数据结构 中的「## 学习目标」讲了什么？ | 1 | ✓ | 05_data_structures / 04_functions / 01_variables | 0.213s |
| cand-164 | ## 5.1 列表 (List) 是什么？怎么做？ | 2 | ✓ | Python 数据结构 / Python 数据结构 / 05_data_structures | 0.197s |
| cand-169 | ## Completed Projects（全部完成） 是什么？怎么做？ | 3 | ✓ | 2026-06-17 知识库全面整理 / project_spec / Project Index | 0.203s |
| cand-171 | 第 7 课：模块与包 中的「## 学习目标」讲了什么？ | 2 | ✓ | 06_files / 07_modules / Python 模块与包 | 0.289s |
| cand-176 | AI Knowledge Hub 中的「## 快速入口」讲了什么？ | 1 | ✓ | AI Knowledge Hub / 2026-05-29 AI Knowledge Base Init / MEMORY | 0.209s |
| cand-184 | 生活中的经济学论文 中的「## 目标」讲了什么？ | 1 | ✓ | README / README / README | 0.225s |
| cand-190 | ## 黄金法则 是什么？怎么做？ | - | ✗ | 2026-09-14 AI 工作流 PPT 设计稿制作 / AI 工作流 PPT 串讲大纲 / Knowledge Index | 0.215s |
| cand-194 | Python 练习题生成提示词 中的「## 用途」讲了什么？ | 1 | ✓ | Python 练习题生成提示词 / 2026-06-03 Python Learning Lab 知识沉淀 / Prompt Index | 0.216s |
| cand-195 | ## 提示词 是什么？怎么做？ | 1 | ✓ | Python 练习题生成提示词 / 2026-06-03 Python Learning Lab 知识沉淀 / Prompt Index | 0.210s |
| cand-199 | 2026-06-03 Python Learning Lab 技术选型决策 中的「## 决策」讲了什么？ | 1 | ✓ | 2026-06-03 Python Learning Lab 技术选型 / 2026-06-03 Python Learning Lab 知识沉淀 / 2026-06-04 CET-4 知识库技术选型 | 0.206s |
| cand-204 | 2026-06-04 CET-4 三层示例与中英对照结构 中的「## 决策」讲了什么？ | 1 | ✓ | 2026-06-04 CET-4 三层示例与中英对照结构 / 2026-06-04 CET-4 示例体系升级 / 2026-06-04 CET-4 示例体系升级 | 0.206s |
| cand-209 | 2026-06-04 CET-4 知识库技术选型 中的「## 决策」讲了什么？ | 1 | ✓ | 2026-06-04 CET-4 知识库技术选型 / 2026-06-03 Python Learning Lab 技术选型 / 2026-06-04 CET-4 知识库开发记录 | 0.229s |
| cand-216 | 2026-06-03 Python Learning Lab 知识沉淀 中的「## 本轮目标」讲了什么？ | 1 | ✓ | 2026-06-03 Python Learning Lab 知识沉淀 / 2026-06-03 Python Learning Lab 技术选型 / Python Learning Lab 原始项目 | 0.217s |
| cand-217 | ## 关键产出 是什么？怎么做？ | - | ✗ | 职场关键能力课程论文项目 / README / README | 0.239s |

## 复现

```powershell
D:\python\python.exe -m vaultmind.eval
```

