@echo off
REM One-click Vault sync: rebuild index + vectors, re-eval 60 gold, re-anchor docs, PDF + pytest.
REM ASCII-only on purpose: cmd parses this file in the OEM/GBK codepage.
cd /d "%~dp0"
set PY=D:\python\python.exe
if not exist "%PY%" set PY=python
"%PY%" scripts\sync_vault.py
echo.
echo ---- Sync finished. Press any key to close ----
pause >nul
