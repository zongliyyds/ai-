@echo off
REM VaultMind Web demo: http://127.0.0.1:8000
REM - already running on port 8000?  -> just tell user to open browser
REM - otherwise start uvicorn and auto-open browser in ~3 seconds
REM - on failure, show the error instead of closing instantly
cd /d D:\RAG

netstat -ano | findstr /r ":8000 .*LISTENING" >nul 2>&1
if %errorlevel%==0 goto :running

start "" cmd /c "ping -n 4 127.0.0.1 >nul & start http://127.0.0.1:8000"
D:\python\python.exe -m uvicorn vaultmind.api.main:app --host 127.0.0.1 --port 8000
if %errorlevel% neq 0 (
    echo.
    echo [VaultMind] start FAILED, exit code %errorlevel%.
    echo Common fixes: 1^) ensure Ollama is running ^(ollama serve^)
    echo              2^) reindex + rebuild vectors:
    echo                 D:\python\python.exe -m vaultmind.ingest
    echo                 D:\python\python.exe -m vaultmind.search --build-vectors
    ping -n 9 127.0.0.1 >nul
)
exit /b 0

:running
echo [VaultMind] server is ALREADY running on port 8000.
echo Open your browser: http://127.0.0.1:8000
ping -n 6 127.0.0.1 >nul
exit /b 0
