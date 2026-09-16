@echo off
REM VaultMind web demo: FastAPI + Web UI  http://127.0.0.1:8000
cd /d D:\RAG
D:\python\python.exe -m uvicorn vaultmind.api.main:app --host 127.0.0.1 --port 8000
