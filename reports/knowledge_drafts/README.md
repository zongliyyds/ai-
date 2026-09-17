# 知识卡片草稿区（沉淀 → 你审阅 → 入 Vault）

> 用途：每个任务完成后，AI 把可复用教训写成 Obsidian 风格知识卡片放在本目录。
> 流程：AI 写草稿 → 你审阅/授权 → 入库 `D:\AI-Knowledge-Vault\AI-Knowledge-Vault` 对应目录（如 `20-Knowledge/`）→ 按 Vault 规则更新 `90-System/Indexes/Knowledge Index` + 写 `50-Logs` 变更记录 → 重跑 `python -m vaultmind.ingest` 与 `--build-vectors` 增量/全量索引。
> 红线：**AI 不擅自写 Vault**，需你明确授权（2026-09-17 首次授权批量入库）；入库时草稿需转成 Vault frontmatter 规范（type/status/created/updated/tags/source/confidence），并把占位链接换成真实双链。

文件清单（✅ = 已入库 `20-Knowledge`）：

- `2026-09 RAG 评测集构建：分层抽样定稿法.md` ✅
- `2026-09 LLM 引用格式不稳定：解析器先冒烟后定正则.md` ✅
- `2026-09 本地服务运维：bat 端口检测与不秒退.md` ✅（本机口径已更新，见 `Windows Python 项目启动器模式`：netstat 不可靠、bat 须纯 ASCII、逻辑进 launcher.py）
- `2026-09 消融实验方法论：负结果也是结论.md` ✅
- `2026-09 开源打包红线：白名单与探针自动化.md` ✅
- `2026-09 索引重建陷阱：自增 rowid 让向量索引张冠李戴.md` ✅（2026-09-17 入库）
- `2026-09 文档锚点漂移：别手抄数字，让文档去读报告.md` ✅（2026-09-17 入库）
- `2026-09 Vault 增长后的同步五步闭环.md` ✅（2026-09-17 入库）
- `2026-09 本地模型掉线：探活 + 结构化 503 + 前端优雅降级.md` ✅（2026-09-17 入库）
- `2026-09 切块别拿标题当分隔符：被剥离的标题与没进索引的前缀.md` 🆕（M6b 产出，待审阅）
- `2026-09 消融的隔离基建：临时索引、基线闸门与内容指纹.md` 🆕（M6b 产出，待审阅）
