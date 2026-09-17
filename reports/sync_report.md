# Vault 同步报告（scripts/sync_vault.py）

> 生成时间：2026-09-17 14:57 ｜ 耗时 43.4s ｜ 结果：全绿 ✅

Vault 指纹：**167 篇 md**，hash `bcda3dd25eefc31f`

## 步骤

| 步骤 | 状态 | 说明 |
|---|---|---|
| 前置检查 | OK | Vault 可读 + Ollama 在线 |
| 变更检测 | OK | 无历史指纹（首次运行） |
| 重建索引 | OK | docs=167 chunks=1314 links=455（1.4s） |
| 重建向量 | OK | 1314/1314（1024 维） |
| gold 复验 | WARN | 已跳过（--skip-eval） |
| 审计基线 | OK | 无需变更（167 篇 / 297064 字符） |
| 回写锚点 | OK | 1 处已回写 |
| PDF 重生 | OK | [PASS] 生成完成：D:\RAG\docs\面试答辩手册.pdf（6 页，含关键指标数字） |
| pytest | OK | 63 passed in 4.53s |

> 锚点一律从 `reports/` 现场解析后回写（防漂移）。
> 复现：`D:\python\python.exe scripts\sync_vault.py`
