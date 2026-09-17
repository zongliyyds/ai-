@echo off
chcp 65001 >nul
setlocal
title VaultMind - http://127.0.0.1:8000
cd /d D:\RAG

set PY=D:\python\python.exe
set PORT=8000

REM ---- 端口检测：用 TCP 连接探测 ----
REM 勿改回 netstat：本机 netstat 报"内存不足"且返回空，导致误判端口空闲/占用
"%PY%" -c "import socket,sys; s=socket.socket(); s.settimeout(1.5); sys.exit(0 if s.connect_ex(('127.0.0.1',%PORT%))==0 else 1)"
if %errorlevel%==0 (
    echo [VaultMind] 服务已在运行，正在打开浏览器...
    start "" http://127.0.0.1:%PORT%
    echo 若页面仍打不开，请关闭旧的服务窗口后重新双击本文件。
    ping -n 4 127.0.0.1 >nul
    exit /b 0
)

REM 延迟 3 秒开浏览器，等 uvicorn 就绪
start "" cmd /c "ping -n 4 127.0.0.1 >nul & start http://127.0.0.1:%PORT%"

echo [VaultMind] 正在启动服务 http://127.0.0.1:%PORT% ...
echo 日志：D:\RAG\data\api_server.log
echo 本窗口保持不关 = 服务运行中；关闭本窗口 = 停止服务。
echo.
"%PY%" -m uvicorn vaultmind.api.main:app --host 127.0.0.1 --port %PORT% > D:\RAG\data\api_server.log 2>&1

echo.
echo [VaultMind] 服务已退出（返回码 %errorlevel%）。常见原因：
echo   1) Ollama 未运行 - 另开窗口执行 ollama serve
echo   2) 端口 %PORT% 被占用，或索引/向量缺失需重建：
echo      %PY% -m vaultmind.ingest
echo      %PY% -m vaultmind.search --build-vectors
echo.
echo 最近日志：
powershell -NoProfile -Command "if (Test-Path 'D:\RAG\data\api_server.log') { Get-Content 'D:\RAG\data\api_server.log' -Tail 20 }"
ping -n 12 127.0.0.1 >nul
exit /b 0
