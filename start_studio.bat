@echo off
title ReelCraft-AI Studio
echo ===================================================
echo Starting ReelCraft-AI Video Creation Studio...
echo Studio URL: http://localhost:8000
echo API Docs:   http://localhost:8000/docs
echo ===================================================
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
