"""
Marhaba Haji — Twilio WhatsApp Chatbot Webhook
===============================================
Webhook flow:
  1. User sends WhatsApp message to Twilio Sandbox number
  2. Twilio forwards it as POST /webhook with form data (Body, From, etc.)
  3. FastAPI receives it, prints the message, and replies via MessagingResponse
  4. Twilio sends the reply back to the user on WhatsApp

Abandoned cart alerts:
  - Separate endpoint triggers WhatsApp + SMS outbound alerts
  - Not fired on every incoming message
"""

from fastapi import FastAPI, Form, Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

app = FastAPI(title="Marhaba Haji WhatsApp Bot")

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")

if not account_sid or not auth_token:
    raise RuntimeError(
        "Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN in backend/.env"
    )

client = Client(account_sid, auth_token)

WHATSAPP_SANDBOX_NUMBER = "whatsapp:+14155238886"


@app.get("/")
def root():
    return {
        "status": "running",
        "message": "Marhaba Haji WhatsApp Webhook"
    }


@app.post("/webhook")
async def webhook(
    Body: str = Form(...),
    From: str = Form(...)
):
    try:
        print(f"\n[WhatsApp] message from {From}: {Body}")
    except UnicodeEncodeError:
        print(f"\n[WhatsApp] message from {From!r}")

    twilio_response = MessagingResponse()
    twilio_response.message(
        "Assalamu Alaikum! Welcome to Marhaba Haji AI"
    )

    return Response(
        content=str(twilio_response),
        media_type="application/xml"
    )


@app.post("/send-abandoned-cart-alert")
async def send_abandoned_cart_alert(
    user_whatsapp: str = Form(...),
    user_phone: str = Form(...)
):
    results = {}

    whatsapp_msg = client.messages.create(
        from_=WHATSAPP_SANDBOX_NUMBER,
        body="🌙 Assalamu Alaikum! You left your Umrah package in cart. "
             "Complete your booking now: http://localhost:8000/cart/resume",
        to=f"whatsapp:{user_whatsapp}"
    )
    results["whatsapp"] = whatsapp_msg.sid
    print(f"WhatsApp alert sent — SID: {whatsapp_msg.sid}")

    sms_msg = client.messages.create(
        from_=twilio_phone,
        body="Assalamu Alaikum! You left your Umrah package in cart. "
             "Complete your booking: http://localhost:8000/cart/resume",
        to=user_phone
    )
    results["sms"] = sms_msg.sid
    print(f"SMS alert sent — SID: {sms_msg.sid}")

    return {
        "status": "sent",
        "whatsapp_sid": results["whatsapp"],
        "sms_sid": results["sms"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
