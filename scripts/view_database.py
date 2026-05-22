import os
import sys
import json
from datetime import datetime
import dns.resolver
dns.resolver.get_default_resolver().nameservers = ['8.8.8.8', '1.1.1.1']

from pymongo import MongoClient
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from database.viewer import (
    show_recent_carts, show_abandoned_carts,
    show_recovery_attempts, show_statistics, print_border, print_header
)

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "marhaba_haji")

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB_NAME]


def export_to_json():
    try:
        carts = list(db.carts.find({}))
        attempts = list(db.recovery_attempts.find({}))
        conversations = list(db.conversations.find({}))
        messages = list(db.messages.find({}))

        def serialize_docs(docs):
            result = []
            for d in docs:
                serialized = {}
                for k, v in d.items():
                    if isinstance(v, datetime):
                        serialized[k] = v.isoformat()
                    elif k == "_id":
                        serialized[k] = str(v)
                    else:
                        serialized[k] = v
                result.append(serialized)
            return result

        data = {
            "exported_at": datetime.now().isoformat(),
            "carts": serialize_docs(carts),
            "recovery_attempts": serialize_docs(attempts),
            "conversations": serialize_docs(conversations),
            "messages": serialize_docs(messages)
        }

        export_path = os.path.join(os.path.dirname(__file__), "..", "database_export.json")
        with open(export_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        print(f"  Exported to {export_path}")
        print(f"     Carts: {len(carts)}, Recovery: {len(attempts)}")
        print(f"     Conversations: {len(conversations)}, Messages: {len(messages)}")
    except Exception as e:
        print(f"  Export failed: {e}")


def main():
    while True:
        print()
        print_border("=")
        print("  MARHABA DATABASE VIEWER")
        print_border("=")
        print("  1. View Carts")
        print("  2. View Recovery Log")
        print("  3. View Statistics")
        print("  4. Export to JSON")
        print("  5. Exit")
        print_border("-")
        choice = input("  Select option [1-5]: ").strip()

        if choice == "1":
            print("\n  [1] All Carts")
            print("  [2] Abandoned Carts Only")
            sub = input("  Choice [1-2]: ").strip()
            if sub == "2":
                show_abandoned_carts()
            else:
                show_recent_carts(100)
        elif choice == "2":
            show_recovery_attempts()
        elif choice == "3":
            show_statistics()
        elif choice == "4":
            export_to_json()
        elif choice == "5":
            print("  Goodbye!")
            break
        else:
            print("  Invalid option")


if __name__ == "__main__":
    main()
