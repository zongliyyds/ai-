# Vault 同步报告（scripts/sync_vault.py）

> 生成时间：2026-09-17 14:55 ｜ 耗时 66.3s ｜ 结果：全绿 ✅

Vault 指纹：**167 篇 md**，hash `bcda3dd25eefc31f`

## 步骤

| 步骤 | 状态 | 说明 |
|---|---|---|
| 前置检查 | OK | Vault 可读 + Ollama 在线 |
| 变更检测 | OK | 无历史指纹（首次运行） |
| 重建索引 | OK | docs=167 chunks=1314 links=455（1.3s） |
| 重建向量 | OK | 1314/1314（1024 维） |
| gold 复验 | OK | R@5=0.8167 MRR=0.7096 nDCG@10=0.7403 延迟=0.374s（三项达标） |
| 审计基线 | OK | 已重定 166→167 篇、294846→297064 字符 |
| 回写锚点 | OK | 11 处已回写 |
| PDF 重生 | OK | [PASS] 生成完成：D:\RAG\docs\面试答辩手册.pdf（6 页，含关键指标数字） |
| pytest | OK | 63 passed in 4.20s |

## 指标变化

| 指标 | 上次 | 本次 |
|---|---|---|
| recall@1 | 0.6333 | 0.6333 |
| recall@5 | 0.8167 | 0.8167 |
| recall@10 | 0.8333 | 0.8333 |
| mrr | 0.7096 | 0.7096 |
| ndcg@10 | 0.7403 | 0.7403 |
| latency | 0.336 | 0.374 |

> 锚点一律从 `reports/` 现场解析后回写（防漂移）。
> 复现：`D:\python\python.exe scripts\sync_vault.py`
