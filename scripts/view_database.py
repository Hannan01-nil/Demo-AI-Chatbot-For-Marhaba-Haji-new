import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from utils.db_viewer import (
    show_recent_carts, show_abandoned_carts,
    show_recovery_attempts, show_statistics, print_border, print_header
)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "database", "marhaba.db")


def export_to_json():
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM carts")
        columns = [desc[0] for desc in cursor.description]
        carts = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM recovery_attempts")
        columns = [desc[0] for desc in cursor.description]
        attempts = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM conversations")
        columns = [desc[0] for desc in cursor.description]
        conversations = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM messages")
        columns = [desc[0] for desc in cursor.description]
        messages = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()

        data = {
            "exported_at": datetime.now().isoformat(),
            "carts": carts,
            "recovery_attempts": attempts,
            "conversations": conversations,
            "messages": messages
        }

        export_path = os.path.join(os.path.dirname(__file__), "..", "database_export.json")
        with open(export_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        print(f"  ✅ Exported to {export_path}")
        print(f"     Carts: {len(carts)}, Recovery: {len(attempts)}")
        print(f"     Conversations: {len(conversations)}, Messages: {len(messages)}")
    except Exception as e:
        print(f"  ❌ Export failed: {e}")


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
