@echo off
title Marhaba Haji Chatbot
color 0A

echo ========================================
echo    MARHABA HAJI CHATBOT
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Installing required packages...
pip install -r requirements.txt --quiet

echo [2/3] Starting backend server...
cd backend
start python -X utf8 app.py

timeout /t 3 /nobreak >nul
start ..\frontend\index.html

echo System Running at http://localhost:8000
pause