# VaultMind 可行性评估报告

> 结论先行：**完全可行，无需额外硬件投入**。本机 RTX 4050(6GB) + 32GB 内存 + 133GB 空闲磁盘足以承载「本地 embedding + 本地 7B 生成 + 云端兜底」的完整 RAG 链路。推荐走 Ollama 全家桶（bge-m3 + qwen2.5:7b-instruct），刻意避开 torch/CUDA，把环境风险降到最低。

## 一、硬件实测（2026-09 实测，非估算）

| 项目 | 实测值 | 对项目的影响 |
|---|---|---|
| CPU | AMD Ryzen 5 7535H（6 核 12 线程，带 Radeon 660M 核显） | 7B 模型 CPU 兜底推理可用（慢但能跑） |
| 内存 | 32 GB（当前空闲 18.8 GB） | 7B/8B Q4 模型可整块驻留内存，无需频繁换页 |
| 独立显卡 | **NVIDIA GeForce RTX 4050 Laptop GPU，6 GB 显存，驱动 616.92** | 7B Q4 模型可近乎全量上卡；embedding 秒级 |
| 系统盘 C: | 240 GB，空闲 47.3 GB | 不要放模型（Ollama 默认在 C 盘用户目录，需留意） |
| 数据盘 D: | 236.5 GB，**空闲 133.3 GB** | 项目 + 模型缓存 + 索引库放这里，绰绰有余 |
| 操作系统 | Windows 11 (10.0.22621)，x64 | 常规，无特殊限制 |

## 二、软件环境实测

| 项目 | 状态 |
|---|---|
| Python | 3.13.9（`D:\python\python.exe`，全路径调用） |
| 已装关键包 | fastapi 0.115.6 / uvicorn 0.34.0 / jieba 0.42.1 / scikit-learn 1.6.1 / numpy 2.4.6 / pandas 3.0.3 / PyMuPDF 1.27.2.3 / pydantic 2.10.4 |
| 未装（按设计不装） | torch / chromadb / faiss / sentence-transformers / langchain / openai |
| Ollama | 已装（`...\Programs\Ollama\ollama.exe`），**服务当前未启动**，本机仅有 `qwen2.5-coder:7b`（4.36 GB） |
| git | 已装 `D:\Develop\Git\Git\cmd\git.exe`（未配置 user.name） |
| docker / ffmpeg | 未装（本方案不需要） |

## 三、模型可行性逐项评估

| 用途 | 模型 | 体积 | 运行方式 | 结论 |
|---|---|---|---|---|
| 向量化 Embedding | `bge-m3`（Ollama） | ~1.2 GB | GPU 或 CPU | ✅ 秒级，中文多语言效果好，维度 1024 |
| 生成 LLM | `qwen2.5:7b-instruct`（Q4） | ~4.7 GB | GPU（6GB，近全量）+ CPU 兜底 | ✅ 可用；建议 num_ctx=4096 控制显存，预期 10~30 tok/s |
| 生成 LLM（可选升级） | `qwen2.5:14b-instruct` | ~9 GB | CPU（32GB 内存） | ⚠️ 能跑但慢，仅作"云端兜底"之外的本地高质选项 |
| 重排 Rerank（可选） | `bge-reranker-base` | ~0.3 GB | 需 torch 或 ONNX | ⚠️ 见下方 torch 风险；首选 **LLM 重排**（零新依赖） |
| 云端兜底 | DashScope `text-embedding-v3` / DeepSeek / 通义千问 | — | HTTP API | ✅ 端点均已测通 |

**关键决策：核心链路零 torch。** 用 Ollama 提供 embedding 与生成，用 LLM 做重排，即可完全避开 CUDA/PyTorch 的安装坑（Python 3.13 + 6GB 显存 + torch 下载 ~2.5GB + CUDA 版本匹配，风险高收益低）。bge-reranker 只作为第 4 周的可选对照实验，且优先走 ModelScope 而非 HuggingFace。

## 四、网络与下载可行性

| 目标 | 实测 |
|---|---|
| PyPI（pypi.org） | ✅ 200，可 pip install |
| Ollama 模型仓库 registry.ollama.ai | ✅ 可达，`ollama pull` 可用 |
| GitHub | ✅ HTTPS 200（Python 实测）；git clone 大仓库仍建议走 gh-proxy 镜像 |
| HuggingFace | ❌ 超时（不可用） |
| ModelScope modelscope.cn | ✅ 200（HF 模型的最佳替代源） |
| DashScope / DeepSeek | ✅ 可达 |

## 五、主要风险与对策

| 风险 | 对策 |
|---|---|
| Ollama 服务未启动 | 用户手动 `ollama serve` 或运行 Ollama 桌面端；pull 模型前先启动 |
| Ollama 默认把模型下载到 C 盘（`%USERPROFILE%\.ollama`） | C 盘仅剩 47GB，够用；如需迁移，用 `OLLAMA_MODELS` 环境变量指向 D 盘 |
| 7B 模型在 6GB 显存上需控制上下文 | `num_ctx=4096`；超长上下文自动退回 CPU 或云端 |
| 笔记含隐私（简历手机号/邮箱） | 云端调用前跑 PII 脱敏；默认只走本地模型 |
| 知识库持续更新与索引不同步 | 提供 `/reindex` 与增量重建，索引是派生产物，源永远是 Vault |

## 六、总评

- **算力**：够用（6GB 显存 + 32GB 内存是本地 7B RAG 的"甜点区"）。
- **磁盘**：D 盘 133GB 空闲，模型（~6GB）+ 项目 + venv + 索引库全部放 D 盘无压力。
- **网络**：PyPI / Ollama 仓库 / 云端 API 全通，唯 HuggingFace 不通（用 ModelScope 替代）。
- **环境风险**：已通过"零 torch 设计"主动规避。
- **结论**：直接开工，无需购置/更换任何硬件。
