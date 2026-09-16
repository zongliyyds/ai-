# M4 在线冒烟报告（生成链路 · 2026-09-16）

> 命令：`D:\python\python.exe scripts\m4_smoke.py` ｜ 模型：qwen2.5:7b-instruct（本地，无云端）｜ 检索：hybrid top_k=8
> 判定口径：库内问 → 回答含 [S#] 且非法编号=0；超纲问 → 拒答且无非法编号。

## 结论：4/4 PASS ✅

| # | 探针 | 期望 | 结果 | 引用 | 非法编号 | 拒答 | 端到端 |
|---|---|---|---|---|---|---|---|
| 1 | python-docx 多文档合并为什么要用底层 XML API？ | 引用回答 | ✓ | [1,4] | 0 | 否 | 13.5s |
| 2 | AIGC 检测的原理是什么？ | 引用回答 | ✓ | [6] | 0 | 否 | 17.5s |
| 3 | 今天比特币的价格是多少？ | 拒答 | ✓ | [1,8]（列举无关块） | 0 | 是 | 13.0s |
| 4 | 2027 年上海迪士尼乐园门票多少钱？ | 拒答 | ✓ | [1..8]（列举无关块） | 0 | 是 | 15.4s |

> 生成耗时典型 8~15s（7B 模型 decode 限速）；首问含模型冷加载约 67s（一次性）。
> 拒答样本会"列举 S1..S8 均无关"——诚实可追溯，符合提示词约束。

## 迭代记录（两轮，坏例已修）

1. **v1 FAIL（3/4）**：模型输出 `[S1, S2, S4]` 列表式引用，提取器只认单括号 `[S#]` → 引用提取为空。
2. **v2 PASS（4/4）**：`validator.extract_cites` 支持列表式 `[S1, S2, S4]`、中文分隔 `[S1，S3、S5]`、带空格 `[S 3]`、中文括号 `【S1】`；`tests/test_generation.py` 探针覆盖上述变异。

## 复现

```powershell
D:\python\python.exe -m pytest tests -q              # 32/32（离线探针）
D:\python\python.exe scripts\m4_smoke.py             # 在线冒烟 4/4（需 Ollama 运行）
D:\python\python.exe -m vaultmind.ask "你的问题"      # 带引用问答 CLI
```
