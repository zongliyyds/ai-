# CHANGELOG（进度档案 · 唯一事实来源）

> 约定：每个节点验收通过后追加一条；格式：`日期 · 节点 | 做了什么 | 验证结果 | 遗留与下一步`。
> AI 会话开工必读本文件 + `PLAN.md`；节点收尾必须回来追加。

## 2026-09-16 · 环境准备（开工前，M0 前置）

- **做了什么**：Ollama 模型库从 C 盘迁至 `D:\本地模型`；写入用户级环境变量 `OLLAMA_MODELS=D:\本地模型`；删除旧目录 `C:\Users\Administrator\.ollama\models`。
- **验证结果**：`ollama serve` + `ollama list` 正确识别 `qwen2.5-coder:7b`（4.7 GB）；迁移前后 6 个文件 / 4,683,088,419 字节逐字节一致；C 盘释放约 4.7 GB。
- **交付物**：`docs/Ollama本地模型迁移工作流.pdf`、`scripts/make_migration_pdf.py`。

## 2026-09-16 · 协作体系建立（M0 前置）

- **做了什么**：建立 AI 协作工作手册 `docs/AI工作手册.md`（四步法 + 工单模板 + 红线 + 坑位表 + 命令速查 + 知识沉淀约定）；建立本 CHANGELOG 作为进度档案；知识沉淀至 Mnemon 文档空间与记忆空间。
- **验证结果**：手册覆盖全部已踩坑位（Python 全路径、pwsh 5.1 编码、HTTPS、沙箱、PyMuPDF 两坑、Ollama 路径）；与 PLAN/FEASIBILITY 红线一致。
- **遗留与下一步**：开工前首次手动准备——`ollama serve` 后 `ollama pull bge-m3`（~1.2 GB）、`ollama pull qwen2.5:7b-instruct`（~4.7 GB），自动存入 `D:\本地模型`；随后进入 W1：M0 立项收尾 + M1 数据管道/体检 + M2 检索 v1。
