import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "marhaba_haji")

_client = None
_db = None


def get_db():
    global _client, _db
    if _db is None:
        import dns.resolver
        dns.resolver.get_default_resolver().nameservers = ['8.8.8.8', '1.1.1.1']
        _client = MongoClient(MONGODB_URI)
        _db = _client[MONGODB_DB_NAME]
        _init_db()
    return _db


def _init_db():
    db = _db
    db.conversations.create_index("session_id")
    db.messages.create_index("conversation_id")
    db.messages.create_index([("conversation_id", 1), ("created_at", 1)])
    db.carts.create_index("session_id")
    db.carts.create_index([("status", 1), ("last_activity", 1)])
    db.carts.create_index("id")
    db.recovery_attempts.create_index("cart_id")
    db.recovery_attempts.create_index([("cart_id", 1), ("created_at", -1)])

    if db.packages.count_documents({}) == 0:
        packages = [
            {"_id": "pkg_001", "name": "Economy Umrah", "price": 850, "duration": 7, "description": "3-star hotel, shared transport, visa included"},
            {"_id": "pkg_002", "name": "Deluxe Umrah", "price": 1500, "duration": 14, "description": "4-star hotel near Haram, private transport"},
            {"_id": "pkg_003", "name": "Premium Hajj", "price": 4500, "duration": 21, "description": "5-star hotel, VIP service, full board"}
        ]
        db.packages.insert_many(packages)


db = get_db()
