import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")


def test_connection():
    try:
        if not SENDGRID_API_KEY:
            return {"status": "error", "message": "SendGrid API key not configured in .env"}
        from sendgrid import SendGridAPIClient
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.client._("your-email@example.com").get()
        return {"status": "ok", "message": "SendGrid API key is valid"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def send_email(to_email, subject, body):
    try:
        if not SENDGRID_API_KEY or not EMAIL_FROM:
            return {"status": "error", "message": "SendGrid not configured"}
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=to_email,
            subject=subject,
            html_content=f"<p>{body.replace(chr(10), '<br>')}</p>"
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return {"status": "sent", "status_code": response.status_code, "to": to_email}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_api_status():
    try:
        if not SENDGRID_API_KEY:
            return {"status": "error", "message": "SendGrid not configured"}
        from sendgrid import SendGridAPIClient
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.client._("scopes").get()
        scopes = response.to_dict().get("scopes", []) if hasattr(response, 'to_dict') else []
        return {"status": "ok", "scopes_count": len(scopes), "api_key_valid": True}
    except Exception as e:
        return {"status": "error", "message": str(e)}
