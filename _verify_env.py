import os, sys
sys.path.insert(0, 'backend')
from dotenv import load_dotenv
load_dotenv('backend/.env')

sid = os.getenv('TWILIO_ACCOUNT_SID')
token = os.getenv('TWILIO_AUTH_TOKEN')
phone = os.getenv('TWILIO_PHONE_NUMBER')

print("=== .ENV VARIABLES CHECK ===")
sid_display = sid[:20] + "..." if sid else "MISSING"
print("TWILIO_ACCOUNT_SID: " + sid_display)
print("TWILIO_AUTH_TOKEN:  " + ("***present***" if token else "MISSING") + " (len=" + str(len(token) if token else 0) + ")")
print("TWILIO_PHONE_NUMBER: " + str(phone))
print("GOOGLE_API_KEY:     " + ("***present***" if os.getenv('GOOGLE_API_KEY') else "MISSING"))
print("MONGODB_URI:        " + str(os.getenv('MONGODB_URI', 'MISSING'))[:40] + "...")
sg = os.getenv('SENDGRID_API_KEY')
if sg and sg != 'SG.xxxxxxxxxxxxx':
    print("SENDGRID_API_KEY:   ***present*** (valid)")
else:
    print("SENDGRID_API_KEY:   MISSING or placeholder")
print("EMAIL_FROM:         " + str(os.getenv('EMAIL_FROM')))
print("ADMIN_PHONE:        " + str(os.getenv('ADMIN_PHONE')))

print("\n=== TWILIO CONNECTION TEST ===")
from twilio.rest import Client
client = Client(sid, token)
try:
    account = client.api.accounts(sid).fetch()
    print("Twilio connected: " + account.friendly_name)
except Exception as e:
    print("Twilio error: " + str(e))

try:
    balance = client.balance.fetch()
    print("Balance: " + str(balance.balance) + " " + str(balance.currency))
except Exception as e:
    print("Balance error: " + str(e))

print("\n=== HEALTH CHECK ===")
import requests
try:
    r = requests.get('http://localhost:8000/', timeout=5)
    print("Backend: " + str(r.json()))
except Exception as e:
    print("Backend error: " + str(e))

try:
    r = requests.get('http://localhost:8000/packages', timeout=5)
    pkgs = r.json().get('packages', [])
    print("Packages: " + str(len(pkgs)) + " packages found")
    for p in pkgs:
        print("  - " + p['name'] + " ($" + str(p['price']) + ")")
except Exception as e:
    print("Packages error: " + str(e))

try:
    r = requests.get('http://localhost:8000/analytics/abandoned', timeout=5)
    print("Analytics: " + str(r.json()))
except Exception as e:
    print("Analytics error: " + str(e))

print("\n=== WEBHOOK TEST ===")
try:
    r = requests.post('http://localhost:8000/webhook', data={'Body': 'Test message', 'From': 'whatsapp:+14155238886'}, timeout=5)
    print("Webhook response: " + r.text[:200])
    print("Status: " + str(r.status_code))
except Exception as e:
    print("Webhook error: " + str(e))
