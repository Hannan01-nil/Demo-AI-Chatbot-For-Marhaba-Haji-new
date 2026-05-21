================================================================================
  MARHABA HAJI CHATBOT - COMPLETE SETUP GUIDE
  Hajj & Umrah Booking Assistant with SMS/Email Recovery
================================================================================

1. INSTALL PYTHON PACKAGES
================================================================================

Open a terminal (PowerShell or Command Prompt) and run:

    pip install fastapi uvicorn google-generativeai python-dotenv twilio sendgrid
    pip install apscheduler pydantic requests

Or use the included virtual environment:

    venv\Scripts\activate
    pip install -r requirements.txt

(If requirements.txt does not exist, manually install the packages above.)


2. ENVIRONMENT VARIABLES
================================================================================

Edit backend/.env with your actual API keys:

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

How to get API keys:
  - Gemini AI: https://aistudio.google.com/app/apikey
  - Twilio:    https://console.twilio.com
  - SendGrid:  https://app.sendgrid.com/settings/api_keys


3. RUN THE SYSTEM
================================================================================

Option A: Double-click start.bat (recommended)

Option B: Command-line:

    venv\Scripts\activate
    cd backend
    python app.py

The server starts at http://localhost:8000
API docs at http://localhost:8000/docs

The abandoned cart detector runs every 15 minutes automatically.
Carts inactive for 30+ minutes are flagged as abandoned and recovery
messages are sent via SMS and/or Email.


4. TEST SMS
================================================================================

    python scripts/test_sms.py

This will:
  - Test Twilio connection
  - Send a test SMS to ADMIN_PHONE
  - Show remaining account balance


5. TEST EMAIL
================================================================================

    python scripts/test_email.py

This will:
  - Test SendGrid connection
  - Send a test email to ADMIN_EMAIL
  - Show API status


6. VIEW DATABASE
================================================================================

    python scripts/view_database.py

Interactive menu:
  1. View Carts (all or abandoned only)
  2. View Recovery Log
  3. View Statistics
  4. Export to JSON
  5. Exit

Or use the simpler viewer:

    python backend/utils/db_viewer.py


7. TEST RECOVERY FLOW
================================================================================

    python scripts/test_recovery.py

This will:
  - Create a test session and cart
  - Add a package to the cart
  - Simulate abandonment (backdate last_activity)
  - Trigger the recovery detection
  - Show recovery attempts


8. API ENDPOINTS
================================================================================

  Method  Path                         Description
  ------  --------------------------   --------------------------------
  GET     /                            Server status
  GET     /docs                        Swagger API documentation
  POST    /chat/send                   Send chat message
  GET     /packages                    List all packages
  POST    /cart/add/{session_id}       Add item to cart
  GET     /cart/{session_id}           Get current cart
  DELETE  /cart/remove/{session_id}/{pkg}  Remove from cart
  GET     /cart/resume/{cart_id}       Resume abandoned cart
  POST    /cart/recovery/manual/{cart_id}  Manually trigger recovery
  GET     /analytics/abandoned         Abandoned cart statistics


9. TROUBLESHOOTING
================================================================================

Problem: "No module named ..."
  -> Run: pip install <module_name>

Problem: Database errors
  -> Delete backend/database/marhaba.db and restart (auto-creates)

Problem: Gemini AI not responding
  -> Check GOOGLE_API_KEY in .env (no leading spaces)

Problem: SMS not sending
  -> Verify TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
  -> Check Twilio balance (sms_twilio.py check_balance)
  -> SMS will simulate if Twilio is not configured

Problem: Email not sending
  -> Verify SENDGRID_API_KEY and EMAIL_FROM in .env
  -> Email will simulate if SendGrid is not configured

Problem: Port 8000 already in use
  -> Change port in app.py (uvicorn.run line) or kill the other process

Problem: start.bat opens and closes immediately
  -> Run from terminal to see error messages
  -> Ensure virtual environment exists at venv/

Problem: Recovery not triggering
  -> Wait 30+ minutes (or run test_recovery.py)
  -> Check last_activity timestamp in database


10. PROJECT STRUCTURE
================================================================================

marhaba-chatbot/
├── start.bat                     # One-click launcher
├── README.txt                    # This file
├── venv/                         # Python virtual environment
├── backend/
│   ├── app.py                    # Main FastAPI application
│   ├── .env                      # API keys and config
│   ├── database/
│   │   └── marhaba.db            # SQLite database (auto-created)
│   └── utils/
│       ├── sms_twilio.py         # SMS helper functions
│       ├── email_sendgrid.py     # Email helper functions
│       └── db_viewer.py          # Database viewer
├── frontend/
│   └── index.html                # Chat interface
└── scripts/
    ├── test_sms.py               # Test SMS
    ├── test_email.py             # Test email
    ├── test_recovery.py          # Test recovery flow
    └── view_database.py          # Database viewer with export
================================================================================
