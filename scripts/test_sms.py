import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from utils.sms_twilio import send_sms, test_connection, check_balance

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

ADMIN_PHONE = os.getenv("ADMIN_PHONE")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")


def main():
    print("=" * 60)
    print("  MARHABA SMS TEST")
    print("=" * 60)

    print("\n[1/3] Testing Twilio connection...")
    conn_result = test_connection()
    if conn_result["status"] == "ok":
        print(f"  ✅ Connected: {conn_result.get('account_name', 'N/A')}")
    else:
        print(f"  ❌ Connection failed: {conn_result['message']}")
        print("  ℹ️  SMS will be simulated")
        print()

    print("\n[2/3] Sending test SMS...")
    phone = ADMIN_PHONE or TWILIO_PHONE_NUMBER
    if not phone:
        print("  ❌ No ADMIN_PHONE or TWILIO_PHONE_NUMBER in .env")
        print("  ℹ️  Add ADMIN_PHONE=+1234567890 to backend/.env")
        return

    result = send_sms(phone, "🕋 Test message from Marhaba Haji Chatbot - SMS working! Reply OK if received.")
    if result["status"] == "sent":
        print(f"  ✅ SMS sent successfully to {phone}")
        print(f"     SID: {result['sid']}")
    elif result["status"] == "error":
        print(f"  ❌ SMS failed: {result['message']}")
    else:
        print(f"  ℹ️  {result['status']}")

    print("\n[3/3] Checking Twilio balance...")
    balance_result = check_balance()
    if balance_result["status"] == "ok":
        print(f"  ✅ Balance: {balance_result['balance']} {balance_result['currency']}")
    else:
        print(f"  ℹ️  Could not fetch balance: {balance_result['message']}")

    print()
    print("=" * 60)
    print("  Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
