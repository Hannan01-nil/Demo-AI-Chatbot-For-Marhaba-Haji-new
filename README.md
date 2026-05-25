# Marhaba Haji Chatbot

AI chatbot for Hajj and Umrah package assistance, cart recovery, SMS, WhatsApp, email alerts, and basic abandoned-cart analytics.

The project has a FastAPI backend, a static HTML frontend, MongoDB storage, Gemini AI responses, Twilio messaging, SendGrid email, and Vercel deployment support.

## Features

- Chat assistant for Hajj and Umrah package questions
- Package listing and cart management
- Abandoned-cart recovery flow
- SMS and WhatsApp alerts through Twilio
- Email alerts through SendGrid
- MongoDB-backed conversations, carts, packages, and recovery logs
- Static frontend that works locally and on Vercel
- FastAPI backend deployable as a Vercel Python Function

## Project Structure

```text
Demo-AI-Chatbot-For-Marhaba-Haji-new/
|-- README.md
|-- requirements.txt
|-- start.bat
|-- vercel.json
|-- .vercelignore
|-- api/
|   `-- index.py
|-- backend/
|   |-- app.py
|   |-- .env
|   |-- .env.example
|   |-- database/
|   |   |-- __init__.py
|   |   |-- connection.py
|   |   `-- viewer.py
|   |-- services/
|   |   `-- gemini_service.py
|   `-- utils/
|       |-- email_sendgrid.py
|       `-- sms_twilio.py
|-- frontend/
|   `-- index.html
|-- public/
|   `-- index.html
|-- scripts/
|   |-- test_email.py
|   |-- test_recovery.py
|   |-- test_sms.py
|   `-- view_database.py
|-- main.py
|-- check_status.py
|-- run_recovery_test.py
|-- _test_webhook.py
|-- _verify_abandon_workflow.py
`-- _verify_env.py
```

## Important Files

- `backend/app.py`: Main FastAPI app for chat, packages, cart, recovery, analytics, and Twilio webhook routes.
- `backend/database/connection.py`: MongoDB connection and package seed setup.
- `backend/services/gemini_service.py`: Gemini AI integration.
- `frontend/index.html`: Local development frontend.
- `public/index.html`: Vercel static frontend.
- `api/index.py`: Vercel Python Function entrypoint for the FastAPI backend.
- `vercel.json`: Vercel routing. `/api/*` goes to FastAPI, everything else serves the frontend.
- `start.bat`: Windows helper to install packages, start backend, and start ngrok.

## Requirements

- Python 3.10+ locally
- MongoDB running locally or MongoDB Atlas
- Gemini API key
- Twilio credentials for SMS/WhatsApp features
- SendGrid API key for email features
- Ngrok only if you want to test Twilio webhooks locally

## Install

From the project root:

```powershell
pip install -r requirements.txt
```

Optional virtual environment:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

Create `backend/.env` for local development. You can copy `backend/.env.example` and fill in the real values:

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=marhaba_haji

GOOGLE_API_KEY=your_gemini_api_key

TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

SENDGRID_API_KEY=SG.your_sendgrid_key
EMAIL_FROM=noreply@example.com

ADMIN_PHONE=+1234567890
ADMIN_EMAIL=admin@example.com

APP_URL=http://localhost:8000
```

For Vercel, add the same values in Vercel Project Settings instead of uploading `.env`.

## Run Locally

Option 1, use the helper:

```powershell
.\start.bat
```

Option 2, run the backend manually:

```powershell
cd backend
python app.py
```

Backend:

```text
http://localhost:8000
```

API docs:

```text
http://localhost:8000/docs
```

Frontend:

```text
frontend/index.html
```

Open `frontend/index.html` in your browser. When opened from the file system, it automatically calls `http://localhost:8000`.

## Local Webhook Testing

`start.bat` also starts:

```powershell
ngrok http 8000
```

Copy the HTTPS ngrok URL and set your Twilio Sandbox webhook:

```text
https://YOUR_NGROK_URL/webhook
```

## Vercel Deployment

This repo is prepared for Vercel:

- `public/index.html` is served as the frontend.
- `api/index.py` exposes the FastAPI backend.
- `vercel.json` rewrites `/api/*` to the backend and all other paths to the frontend.
- `.vercelignore` prevents local secrets, scripts, pycache files, and dev-only files from being deployed.

Set these environment variables in Vercel:

```env
MONGODB_URI=your_mongodb_atlas_connection_string
MONGODB_DB_NAME=marhaba_haji
GOOGLE_API_KEY=your_gemini_api_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
SENDGRID_API_KEY=SG.your_sendgrid_key
EMAIL_FROM=noreply@example.com
APP_URL=https://your-vercel-domain.vercel.app
```

Use MongoDB Atlas or another hosted MongoDB for deployment. `mongodb://localhost:27017` only works on your own machine.

## API Endpoints

Local endpoints use `http://localhost:8000`. On Vercel, prefix backend routes with `/api`.

| Method | Local Path | Vercel Path | Description |
|---|---|---|---|
| GET | `/` | `/api/` | Server status |
| GET | `/docs` | `/api/docs` | Swagger API docs |
| POST | `/chat/send` | `/api/chat/send` | Send a chat message |
| GET | `/packages` | `/api/packages` | List packages |
| POST | `/cart/add/{session_id}` | `/api/cart/add/{session_id}` | Add item to cart |
| GET | `/cart/{session_id}` | `/api/cart/{session_id}` | Get active cart |
| DELETE | `/cart/remove/{session_id}/{package_id}` | `/api/cart/remove/{session_id}/{package_id}` | Remove item |
| GET | `/cart/resume/{cart_id}` | `/api/cart/resume/{cart_id}` | Resume recovered cart |
| POST | `/cart/recovery/manual/{cart_id}` | `/api/cart/recovery/manual/{cart_id}` | Trigger recovery manually |
| GET | `/analytics/abandoned` | `/api/analytics/abandoned` | Abandoned-cart stats |
| POST | `/demo-sms` | `/api/demo-sms` | Send demo SMS |
| POST | `/demo-abandon` | `/api/demo-abandon` | Send demo SMS and WhatsApp recovery alert |
| POST | `/webhook` | `/api/webhook` | Twilio WhatsApp webhook |

## Scripts

```powershell
python scripts/test_sms.py
python scripts/test_email.py
python scripts/test_recovery.py
python scripts/view_database.py
```

Additional local helper scripts:

```powershell
python check_status.py
python run_recovery_test.py
python _verify_env.py
python _verify_abandon_workflow.py
python _test_webhook.py
```

## Troubleshooting

- Backend not opening: make sure `python app.py` is running inside `backend/`.
- `No module named ...`: run `pip install -r requirements.txt`.
- MongoDB errors: check `MONGODB_URI` and make sure MongoDB is running or Atlas allows your IP.
- Gemini not responding: check `GOOGLE_API_KEY`.
- SMS or WhatsApp not sending: check Twilio credentials and Sandbox setup.
- Email not sending: check `SENDGRID_API_KEY` and `EMAIL_FROM`.
- Port 8000 in use: stop the other process or change the `uvicorn.run` port in `backend/app.py`.
- Vercel database failure: replace local MongoDB URI with MongoDB Atlas.

## Current Local Check

The backend was verified locally on port `8000` with:

- `GET /`
- `GET /packages`
- `POST /chat/send`

All returned `200 OK`.
