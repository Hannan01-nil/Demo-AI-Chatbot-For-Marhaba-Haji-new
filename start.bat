@echo off
title Marhaba Haji Chatbot
color 0A

echo ========================================
echo    Marhaba Haji Chatbot
echo ========================================
echo.

echo [1/3] Activating virtual environment...
cd C:\Users\Mohammed Aakif\Desktop\marhaba-chatbot
call venv\Scripts\activate

echo [2/3] Installing required packages...
pip install fastapi uvicorn google-generativeai python-dotenv --quiet

echo [3/3] Starting backend server...
cd backend
python app.py

pause