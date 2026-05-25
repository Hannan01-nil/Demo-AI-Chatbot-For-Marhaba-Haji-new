import os
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient

MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'marhaba_haji')

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB_NAME]

print('=' * 50)
print('FULL ABANDONED CART RECOVERY TEST')
print('=' * 50)
print()

pkg = db.packages.find_one({'_id': 'pkg_002'})
if not pkg:
    pkg = db.packages.find_one({})
print(f'[1] Using package: {pkg["name"]} - ${pkg["price"]}')

session_id = f'recovery_test_{uuid.uuid4().hex[:6]}'
cart_id = str(uuid.uuid4())
user_phone = '+919790562321'

two_hours_ago = datetime.now() - timedelta(hours=2)

cart_doc = {
    '_id': cart_id,
    'session_id': session_id,
    'user_phone': user_phone,
    'user_email': None,
    'items': [{
        'package_id': pkg['_id'],
        'name': pkg['name'],
        'price': pkg['price'],
        'quantity': 1,
        'total': pkg['price']
    }],
    'total_amount': pkg['price'],
    'status': 'active',
    'last_activity': two_hours_ago,
    'abandoned_at': None,
    'recovery_attempts': 0,
    'recovered_at': None,
    'created_at': datetime.now()
}

db.carts.insert_one(cart_doc)
print(f'[2] Created cart: {cart_id}')
print(f'    Phone: {user_phone}')
print(f'    Last activity: {two_hours_ago}')

print()
print('[3] Running abandoned cart detection...')
print('-' * 50)

import sys
sys.path.insert(0, 'C:/Users/Mohammed Aakif/Demo-AI-Integration-Marhaba-Haji/Demo-AI-Chatbot-For-Marhaba-Haji-new/backend')

from app import detect_abandoned_carts

count = detect_abandoned_carts()
print()
print('-' * 50)
print(f'[4] Detected {count} abandoned cart(s)')

print()
print('[5] Checking recovery attempts...')
attempts = list(db.recovery_attempts.find({'cart_id': cart_id}))
for a in attempts:
    print(f'    Channel: {a.get("channel")}')
    print(f'    Sent: {a.get("message_sent")}')
    print(f'    Time: {a.get("created_at")}')

cart = db.carts.find_one({'_id': cart_id})
print()
print('[6] Cart status:')
print(f'    Status: {cart.get("status")}')
print(f'    Abandoned at: {cart.get("abandoned_at")}')
print(f'    Recovery attempts: {cart.get("recovery_attempts")}')

client.close()
print()
print('=' * 50)
print('TEST COMPLETE!')
print()
print('You should receive on WhatsApp now!')
print('(and SMS on next recovery attempt)')
print('=' * 50)
