import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = "+14155238886"
ADMIN_PHONE = os.getenv("ADMIN_PHONE")

def send_whatsapp_test():
    print("=" * 60)
    print("  MARHABA WHATSAPP TEST")
    print("=" * 60)

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("❌ Twilio credentials not configured in .env")
        return

    from twilio.rest import Client
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    to_number = ADMIN_PHONE
    if not to_number:
        print("❌ No ADMIN_PHONE set in backend/.env")
        print("   Add: ADMIN_PHONE=+yournumber")
        return

    print(f"\nSending WhatsApp to: {to_number}")
    print(f"From sandbox: {TWILIO_WHATSAPP_NUMBER}")
    print()
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    try:
        msg = client.messages.create(
            body="Test from Marhaba Haji Chatbot - WhatsApp working!",
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            to=f"whatsapp:{to_number}"
        )
        print(f"✅ WhatsApp sent! SID: {msg.sid}")
        print(f"   Check your WhatsApp at {to_number}")
    except Exception as e:
        print(f"❌ WhatsApp failed!")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error code: {getattr(e, 'code', 'N/A')}")
        print(f"   Error msg: {e}")
        print()
        if "63016" in str(e):
            print("💡 This is an OPT-IN error.")
            print(f"   1. Open WhatsApp on your phone")
            print(f"   2. Send a message with the word 'join' to {TWILIO_WHATSAPP_NUMBER}")
            print(f"   3. Wait for the confirmation reply")
            print(f"   4. Run this script again")
        elif "63017" in str(e):
            print("💡 Session expired. Re-send 'join' to the sandbox.")
        elif "63018" in str(e):
            print("💡 Unregistered sender. Verify WhatsApp Sandbox is active in Twilio Console.")
        else:
            print(f"💡 Unknown error. Check Twilio Console for details.")
            print(f"   To: {to_number}")
            print(f"   From: whatsapp:{TWILIO_WHATSAPP_NUMBER}")

if __name__ == "__main__":
    send_whatsapp_test()
