@echo off
REM VaultMind web demo entry. Logic lives in launcher.py (see docs AI work manual).
REM Keep ASCII-only: cmd reads this file in the OEM/GBK codepage, so UTF-8
REM Chinese comments can produce stray "command not recognized" errors.
cd /d "%~dp0"
"D:\python\python.exe" launcher.py
pause
