# Marhaba Haji Chatbot — Complete Setup Guide

Hajj & Umrah booking assistant with SMS/Email recovery.

## 1. Install Python packages

Open PowerShell or Command Prompt and run:

```powershell
pip install fastapi uvicorn google-generativeai python-dotenv twilio sendgrid
pip install apscheduler pydantic requests
```

Or use the included virtual environment:

```powershell
venv\Scripts\activate
pip install -r requirements.txt
```


## 2. Environment variables

Edit `backend/.env` with your API keys and contact info, for example:

```env
# Google Gemini AI
GOOGLE_API_KEY=your_gemini_api_key_here

# Twilio (SMS)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890

# SendGrid (Email)
SENDGRID_API_KEY=SG.your_sendgrid_key
EMAIL_FROM=noreply@yourdomain.com
EMAIL_TO=admin@example.com

# Admin contact (for testing)
ADMIN_PHONE=+1234567890
ADMIN_EMAIL=admin@example.com
```

How to get API keys:

- Gemini AI: https://aistudio.google.com/app/apikey
- Twilio: https://console.twilio.com
- SendGrid: https://app.sendgrid.com/settings/api_keys


## 3. Run the system

Option A: Double-click `start.bat`.

Option B — command-line:

```powershell
venv\Scripts\activate
cd backend
python app.py
```

Server: http://localhost:8000
API docs: http://localhost:8000/docs

The abandoned-cart detector runs periodically (default: every 15 minutes).


## 4. Test SMS

Run the Twilio test script:

```powershell
python scripts/test_sms.py
```

This tests Twilio connectivity, sends a test SMS to `ADMIN_PHONE`, and shows account info.


## 5. Test Email

Run the SendGrid test script:

```powershell
python scripts/test_email.py
```

This tests SendGrid connectivity and sends a test email to `ADMIN_EMAIL`.


## 6. View Database

Interactive viewer:

```powershell
python scripts/view_database.py
```

Or the simpler viewer:

```powershell
python backend/utils/db_viewer.py
```

The interactive menu lets you view carts, recovery logs, statistics, and export data.


## 7. Test Recovery Flow

```powershell
python scripts/test_recovery.py
```

This script creates a test session/cart, simulates abandonment, triggers recovery detection, and shows recovery attempts.


## 8. API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | / | Server status |
| GET | /docs | Swagger API documentation |
| POST | /chat/send | Send chat message |
| GET | /packages | List all packages |
| POST | /cart/add/{session_id} | Add item to cart |
| GET | /cart/{session_id} | Get current cart |
| DELETE | /cart/remove/{session_id}/{pkg} | Remove from cart |
| GET | /cart/resume/{cart_id} | Resume abandoned cart |
| POST | /cart/recovery/manual/{cart_id} | Manually trigger recovery |
| GET | /analytics/abandoned | Abandoned cart statistics |


## 9. Troubleshooting

- "No module named ..." — run `pip install <module_name>`.
- Database errors — delete `backend/database/marhaba.db` and restart (auto-creates).
- Gemini AI not responding — verify `GOOGLE_API_KEY` in `.env` (no leading spaces).
- SMS not sending — verify Twilio credentials and `TWILIO_PHONE_NUMBER`. Check balance via `sms_twilio.py`.
- Email not sending — verify `SENDGRID_API_KEY` and `EMAIL_FROM`.
- Port 8000 in use — change port in `app.py` (uvicorn.run) or stop the other process.
- `start.bat` closes immediately — run it from terminal to see errors and ensure `venv/` exists.
- Recovery not triggering — wait 30+ minutes or run `scripts/test_recovery.py`. Check `last_activity` timestamps.


## 10. Project structure

```
marhaba-chatbot/
├── start.bat
├── README.md
├── venv/
├── backend/
│   ├── app.py
│   ├── .env
│   ├── database/
│   │   └── marhaba.db
│   └── utils/
│       ├── sms_twilio.py
│       ├── email_sendgrid.py
│       └── db_viewer.py
├── frontend/
│   └── index.html
└── scripts/
  ├── test_sms.py
  ├── test_email.py
  ├── test_recovery.py
  └── view_database.py
```

---

If you want, I can also update `backend/.env.example` with the sample variables or commit this change.
