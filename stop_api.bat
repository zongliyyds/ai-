@echo off
REM Stop the VaultMind web service started by run_api.bat / launcher.py.
REM ASCII-only on purpose: cmd parses this file in the OEM/GBK codepage.
cd /d "%~dp0"
"D:\python\python.exe" launcher.py --stop
pause
