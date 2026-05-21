@echo off
title Marhaba Haji Chatbot
color 0A

echo ========================================
echo    MARHABA HAJI CHATBOT
echo ========================================
echo.

cd /d "C:\Users\Mohammed Aakif\marhaba-chatbot"

echo [1/3] Activating virtual environment...
call venv\Scripts\activate

echo [2/3] Installing required packages...
pip install fastapi uvicorn google-generativeai python-dotenv twilio sendgrid apscheduler --quiet

echo [3/3] Starting backend server...
cd backend
start python -X utf8 app.py

timeout /t 3 /nobreak >nul
start ..\frontend\index.html

echo ✅ System Running at http://localhost:8000
pause