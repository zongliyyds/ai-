@echo off
chcp 65001 >nul
rem VaultMind 检索快捷入口：任何目录双击/命令行运行均可（不需要启动服务）
rem 用法：D:\RAG\search.bat "你的问题" [--top 5] [--mode hybrid]
cd /d D:\RAG
set PY=D:\python\python.exe

if "%~1"=="" (
    echo VaultMind 检索入口（混合检索 BM25 + bge-m3 向量 + RRF）
    echo.
    echo 用法：把问题用引号括起来传给它，例如：
    echo    search.bat "CET-4 项目用了什么去重方案？"
    echo    search.bat "TF-IDF 去重" --top 3 --mode bm25
    echo.
    set /p Q=请输入问题后回车：
    if not defined Q exit /b 1
    "%PY%" -m vaultmind.search "%Q%"
) else (
    "%PY%" -m vaultmind.search %*
)
echo.
echo ---- 检索完成，按任意键关闭窗口 ----
pause >nul
