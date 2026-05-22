import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from utils.email_sendgrid import send_email, test_connection, check_api_status

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL") or os.getenv("EMAIL_TO")
EMAIL_FROM = os.getenv("EMAIL_FROM")


def main():
    print("=" * 60)
    print("  MARHABA EMAIL TEST")
    print("=" * 60)

    print("\n[1/3] Testing SendGrid connection...")
    conn_result = test_connection()
    if conn_result["status"] == "ok":
        print(f"  ✅ {conn_result['message']}")
    else:
        print(f"  ❌ {conn_result['message']}")
        print("  ℹ️  Email will be simulated")
        print()

    print("\n[2/3] Sending test email...")
    to_email = ADMIN_EMAIL
    if not to_email:
        print("  ❌ No ADMIN_EMAIL or EMAIL_TO in .env")
        print("  ℹ️  Add ADMIN_EMAIL=your@email.com to backend/.env")
        return

    result = send_email(
        to_email,
        "Test Email - Marhaba Haji Chatbot",
        "🕋 Assalamu Alaikum!<br><br>This is a test email from Marhaba Haji Chatbot.<br>Your email system is working correctly!<br><br>🤲 Marhaba Haji Team"
    )
    if result["status"] == "sent":
        print(f"  ✅ Email sent successfully to {to_email}")
        print(f"     Status code: {result.get('status_code', 'N/A')}")
    elif result["status"] == "error":
        print(f"  ❌ Email failed: {result['message']}")
    else:
        print(f"  ℹ️  {result['status']}")

    print("\n[3/3] Checking API status...")
    api_result = check_api_status()
    if api_result["status"] == "ok":
        print(f"  ✅ API key is valid, {api_result.get('scopes_count', 'N/A')} scopes")
    else:
        print(f"  ℹ️  {api_result['message']}")

    print()
    print("=" * 60)
    print("  Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
