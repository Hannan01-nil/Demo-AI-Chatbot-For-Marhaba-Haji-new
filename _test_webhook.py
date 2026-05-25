import requests
import sys

print("Testing POST /webhook...")
sys.stdout.flush()

try:
    r = requests.post(
        'http://localhost:8000/webhook',
        data={'Body': 'Assalamu Alaikum', 'From': 'whatsapp:+14155551234'},
        timeout=15
    )
    print("Status:", r.status_code)
    print("Headers:", dict(r.headers))
    print("Body:", r.text[:500])
except requests.exceptions.Timeout:
    print("ERROR: Request timed out after 15 seconds")
except Exception as e:
    print("ERROR:", type(e).__name__, str(e))

print("\nDone")
