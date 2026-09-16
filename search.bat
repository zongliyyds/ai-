@echo off
rem VaultMind 检索快捷入口：任何目录双击/命令行运行均可
rem 用法：D:\RAG\search.bat "你的问题" [--top 5] [--mode hybrid]
cd /d D:\RAG
D:\python\python.exe -m vaultmind.search %*
