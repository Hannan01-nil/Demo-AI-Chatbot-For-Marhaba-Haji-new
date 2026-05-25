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

echo [2/3] Starting backend/app.py (full API + webhook)...
start cmd /k "cd /d %~dp0backend && python app.py"

timeout /t 3 /nobreak >nul

echo [3/3] Starting ngrok tunnel...
start ngrok http 8000

echo.
echo System starting at http://localhost:8000
echo Webhook URL: http://localhost:8000/webhook
echo.
echo IMPORTANT: Copy the ngrok HTTPS URL from the ngrok window
echo and set it in Twilio Sandbox:
echo   "When a message comes in" → https://YOUR_NGROK_URL/webhook
echo.
pause
