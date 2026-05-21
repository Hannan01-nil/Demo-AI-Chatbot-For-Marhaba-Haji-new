import os
import sys
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")


def test_connection():
    try:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            return {"status": "error", "message": "Twilio credentials not configured in .env"}
        from twilio.base.exceptions import TwilioRestException
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        return {"status": "ok", "account_name": account.friendly_name, "sid": account.sid}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def send_sms(to_number, message):
    try:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            return {"status": "error", "message": "Twilio not configured"}
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )
        return {"status": "sent", "sid": msg.sid, "to": to_number}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_balance():
    try:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            return {"status": "error", "message": "Twilio not configured"}
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        balance = client.balance.fetch()
        return {
            "status": "ok",
            "currency": balance.currency,
            "balance": balance.balance,
            "subaccount_currency": getattr(balance, 'subaccount_currency', None)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
