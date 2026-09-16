# VaultMind × AI 协作工作手册

> **核心隐喻：别把 AI 当临时工，让它正式入职。** 效率 = 流程清晰度 × AI 能力（AI 是放大器）。
> 适用对象：本项目（`D:\RAG`）的所有 AI 协作会话。任何新会话开工前，把本手册随工单一起交给 AI。

## 0. 手册怎么用

1. **新会话开工**：把本手册 + `README.md` + `PLAN.md` + `CHANGELOG.md` 作为上下文交给 AI，再下工单。
2. **每个节点收尾**：验收通过 → 更新 `CHANGELOG.md` → 新坑写入长期记忆（见 §9 知识沉淀）。
3. **本手册是活文档**：流程有变、踩了新坑，就回来改它（与 §9 收尾三连问联动）。

## 1. 总纲：AI 工作流四步法

```
① 拆解定目标（派工单） → ② 上下文打底（办入职） → ③ 人机分工（定职责） → ④ 闭环校验（交作业）
```

- 别把整项任务甩给 AI：大任务 → 里程碑 → 工单，**一次只做一个模块**。
- 金句：**先局部稳，再整体通**。流程清晰 → 效率翻倍；流程混乱 → 混乱放大。

## 2. 第一步 · 拆解定目标（派工单）

每张工单必须写清四件事，写之前就知道「什么叫做完」：

| 要素 | 说明 |
|---|---|
| 节点 | 属于哪个里程碑（M0–M7 / W1–W4） |
| 交付物 | 具体产出什么文件 / 接口 / 报告 |
| 验收标准 | 可执行的通过条件（数字、命令、断言） |
| 红线 | 不许碰什么（至少包含 §6 四条红线） |

工单模板（复制改写）：

```
【工单】M2-01 检索 v1
节点：M2 检索 v1（W1）
交付物：vaultmind/retrieval 模块 + search CLI
验收标准：一条命令重建索引；audit 数字与 baseline_audit.json 一致；Top-5 命中指定笔记
红线：只读 Vault；索引只写 D:\RAG\data；不引入 torch/langchain/chroma
```

VaultMind 里程碑（详见 `PLAN.md`）：
W1 M0–M2 数据管道 + 检索 v1 ｜ W2 M3–M4 gold 集 + 生成链路 ｜ W3 M5–M6 产品层 + 六组消融 ｜ W4 追加实验 + 工程化/求职转化。

## 3. 第二步 · 上下文打底（办入职）

入职三件套（判断标准：**AI 只看你给的上下文就能干活，不需要反复追问**）：

1. **任务说明文档**：身份 + 规则 = 本手册。
2. **进度档案**：`PLAN.md` + `CHANGELOG.md`，是进度的**唯一事实来源**（AI 每次开工先读，做完节点必须写）。
3. **长期记忆**：本机 MEMORY.md（热记忆）+ Mnemon 文档空间（项目档案）。

AI 开工必读清单：

```
D:\RAG\docs\AI工作手册.md        ← 流程与红线（本文件）
D:\RAG\README.md · PLAN.md · CHANGELOG.md
D:\RAG\FEASIBILITY.md            ← 环境/可行性（按需）
D:\RAG\docs\立项书-详细版.md      ← 完整设计（按需）
相关模块代码 + tests/
```

新会话开场模板（复制即用）：

```
【身份】你是 VaultMind（个人知识库 RAG 问答+评测系统，求职作品）的协作 AI 工程师。
【本次工单】<编号：一句话目标>
【必读】D:\RAG\docs\AI工作手册.md、README.md、PLAN.md、CHANGELOG.md，相关代码
【红线】①只读 D:\AI-Knowledge-Vault\AI-Knowledge-Vault（绝不增删改移）②索引只写 D:\RAG\data
        ③简历数字必须可复现 ④云端调用前 PII 脱敏、默认本地模型 ⑤不开源 Vault 内容
【交付物与验收标准】<写清楚“什么叫做完”>
【环境】Python=D:\python\python.exe；Ollama 模型在 D:\本地模型；HTTPS 探测用 python/curl
```

## 4. 第三步 · 人机分工（定职责）

| 谁 | 干什么 |
|---|---|
| AI | 批量、重复、费时间：写代码、跑测试、写文档、提取汇总、生成报告/图表 |
| 人 | 判断、定方向、把质量：拆工单、定红线、**验收**、试玩 |

- **验收权永远在人手里**，AI 不能自评通过。
- **写一节审一节**，防止错误滚雪球；发现问题立即打回，不要攒到结尾。

## 5. 第四步 · 闭环校验（交作业）

三层防线：

1. **冒烟**：跑起来不报错（导入、启动、一条 happy path）。
2. **探针**：精确断言（数字、计数、命中集），不是「看起来对」。
3. **回归 + 快照 + 人工验收**：改完跑全量测试，交付物入 git 快照，人对照验收标准逐条确认。

校验三问：**前后逻辑通不通 / 风格一不一致 / 数据有没有对不上**（例：audit 数字必须与 `baseline_audit.json` 一致）。

问题清单 → 反馈 AI 定向修改 → 再次对照最初验收标准，通过才进下一个节点。

## 6. 项目红线（任何工单都适用，违反即返工）

1. **只读 Vault**：`D:\AI-Knowledge-Vault\AI-Knowledge-Vault` 是唯一写入入口（Obsidian 照常用），RAG 只扫描；绝不修改/移动/重命名/删除 Vault 内任何文件；索引是派生产物，只写 `D:\RAG\data`。
2. **简历诚实**：只写实际做出、可复现的内容，数字不编造。
3. **隐私**：笔记含手机号/邮箱，云端调用前 PII 脱敏；默认走本地模型。
4. **不开源 Vault 内容**：只开源代码 + 脱敏样例。

## 7. 本机环境事实速查（AI 必读坑位表）

| 事项 | 事实 |
|---|---|
| Python | 必须全路径 `D:\python\python.exe`（`python`/`py` 会无输出且无退出码） |
| 终端 | pwsh 实为 PowerShell 5.1：读写 UTF-8 要显式指定编码避免 BOM；here-string 不保留末尾换行 |
| HTTPS | PowerShell `Invoke-WebRequest` 走 HTTPS 一律失败 → 连通性探测用 python/curl |
| Ollama | 模型库已迁 **`D:\本地模型`**（用户级 `OLLAMA_MODELS` 已设，新 pull 自动入此目录，旧 C 盘目录已删）；服务默认未运行，手动 `ollama serve` |
| 沙箱 | workspace-write 下：node/dsh 命令 stdout 被吞、Ollama 管道 Access is denied、Word COM 报错；跑 dsh/pnpm 需 danger-full-access |
| PDF 库 | PyMuPDF 1.27.2.3 两坑：①`insert_text` 传 .ttc 字体崩溃（用 TextWriter + fitz.Font）②`write_text` 后其他已存在页面句柄失效（图形先画完再写文本；跨页页脚用两遍渲染：第一遍数页数，第二遍带页码输出） |
| 网络 | HuggingFace ❌ → 用 ModelScope；GitHub 直连超时 → gh-proxy.com 镜像；PyPI ✅ |
| 硬件 | RTX 4050 Laptop 6GB + 32GB 内存；C 盘剩 47GB（勿放模型）、D 盘剩 ~133GB |
| 模型 | 现有 qwen2.5-coder:7b；待 pull：bge-m3（~1.2GB）、qwen2.5:7b-instruct（~4.7GB） |

## 8. 常用命令速查

```powershell
# Ollama（模型已指向 D:\本地模型）
ollama serve
ollama pull bge-m3 ; ollama pull qwen2.5:7b-instruct
ollama list

# 项目
D:\python\python.exe -m vaultmind.ingest          # 只读扫描 + 重建索引
D:\python\python.exe -m vaultmind.eval            # 跑评测
D:\python\python.exe -m uvicorn vaultmind.api.main:app --reload
D:\python\python.exe -m pytest                    # 测试

# git（工作区 D:\RAG）
git add -A; git commit -m "M2: 检索 v1"
```

## 9. 知识沉淀约定（每个节点收尾动作）

1. **CHANGELOG**：追加节点条目（做了什么 / 验证结果 / 遗留问题）。
2. **热记忆**：本机环境的新坑、用户的明确要求 → 写入 MEMORY.md。
3. **项目档案**：立项、决策、大段可复用知识 → Mnemon 文档空间（先搜再写，不重复）。
4. **收尾三连问**：手册要改吗？文档要沉淀吗？记忆要更新吗？——坑踩一次不踩第二次。

## 10. 快照与回滚

- 每个节点验收通过后 `git commit`（可回退的进度快照）。
- 提交前 pre-commit 钩子自动跑快速探针（基线数字一致性 + 分块单测，见 `scripts/hooks/pre-commit`），坏提交会被当场拦住。
- 模型/索引等大文件不入库：索引在 `data/`（gitignore），模型在 `D:\本地模型`。
- 换机复现：按 `README.md` 重装依赖 + 重建索引；模型按 `PLAN.md` §5 拉取（自动存入 `D:\本地模型`）。
