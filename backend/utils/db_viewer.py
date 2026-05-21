import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "marhaba.db")


def print_border(char="=", width=80):
    print(char * width)


def print_header(text):
    print_border()
    print(f"  {text}")
    print_border()


def show_tables():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()

        print_header("DATABASE TABLES")
        if tables:
            for t in tables:
                print(f"  📋 {t[0]}")
        else:
            print("  (no tables found)")
        print_border()
    except Exception as e:
        print(f"  ❌ Error: {e}")


def show_recent_carts(limit=10):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, session_id, user_phone, user_email, total_amount, status, last_activity, created_at
            FROM carts ORDER BY created_at DESC LIMIT ?
        """, (limit,))
        carts = cursor.fetchall()
        conn.close()

        print_header(f"RECENT CARTS (last {limit})")
        if carts:
            for c in carts:
                print(f"  🛒 ID:       {c[0]}")
                print(f"     Session:  {c[1]}")
                print(f"     Phone:    {c[2] or 'N/A'}")
                print(f"     Email:    {c[3] or 'N/A'}")
                print(f"     Total:    ${c[4]:.2f}")
                print(f"     Status:   {c[5]}")
                print(f"     Created:  {c[7]}")
                print_border("-")
        else:
            print("  (no carts found)")
            print_border()
    except Exception as e:
        print(f"  ❌ Error: {e}")


def show_abandoned_carts():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, session_id, user_phone, user_email, total_amount, abandoned_at, recovery_attempts
            FROM carts WHERE status = 'abandoned' ORDER BY abandoned_at DESC
        """)
        carts = cursor.fetchall()
        conn.close()

        print_header("ABANDONED CARTS")
        if carts:
            for c in carts:
                print(f"  ⏳ ID:              {c[0]}")
                print(f"     Session:         {c[1]}")
                print(f"     Phone:           {c[2] or 'N/A'}")
                print(f"     Email:           {c[3] or 'N/A'}")
                print(f"     Total:           ${c[4]:.2f}")
                print(f"     Abandoned:       {c[5]}")
                print(f"     Recovery Att:    {c[6]}")
                print_border("-")
        else:
            print("  (no abandoned carts)")
            print_border()
    except Exception as e:
        print(f"  ❌ Error: {e}")


def show_recovery_attempts():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, cart_id, channel, message_sent, user_responded, converted, created_at
            FROM recovery_attempts ORDER BY created_at DESC
        """)
        attempts = cursor.fetchall()
        conn.close()

        print_header("RECOVERY ATTEMPTS")
        if attempts:
            for a in attempts:
                print(f"  🔄 ID:        {a[0]}")
                print(f"     Cart:      {a[1]}")
                print(f"     Channel:   {a[2]}")
                print(f"     Sent:      {'✅' if a[3] else '❌'}")
                print(f"     Responded: {'✅' if a[4] else '❌'}")
                print(f"     Converted: {'✅' if a[5] else '❌'}")
                print(f"     Created:   {a[6]}")
                print_border("-")
        else:
            print("  (no recovery attempts)")
            print_border()
    except Exception as e:
        print(f"  ❌ Error: {e}")


def show_statistics():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM carts")
        total_carts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM carts WHERE status = 'active'")
        active_carts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM carts WHERE status = 'abandoned'")
        abandoned_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM carts WHERE status = 'recovered'")
        recovered_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM recovery_attempts")
        total_attempts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM recovery_attempts WHERE message_sent = 1")
        messages_sent = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM recovery_attempts WHERE converted = 1")
        converted = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_conversations = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]

        conn.close()

        recovery_rate = (converted / abandoned_count * 100) if abandoned_count > 0 else 0

        print_header("DATABASE STATISTICS")
        print(f"  🛒 Total Carts:          {total_carts}")
        print(f"  ✅ Active Carts:         {active_carts}")
        print(f"  ⏳ Abandoned Carts:      {abandoned_count}")
        print(f"  🔄 Recovered Carts:      {recovered_count}")
        print(f"  📊 Recovery Rate:        {recovery_rate:.1f}%")
        print(f"  📨 Recovery Attempts:    {total_attempts}")
        print(f"  📤 Messages Sent:        {messages_sent}")
        print(f"  ✅ Conversions:          {converted}")
        print(f"  💬 Conversations:        {total_conversations}")
        print(f"  ✉️ Messages:             {total_messages}")
        print_border()
    except Exception as e:
        print(f"  ❌ Error: {e}")


def run():
    while True:
        print("\n")
        print_border("=")
        print("  MARHABA DATABASE VIEWER")
        print_border("=")
        print("  1. Show all tables")
        print("  2. Show recent carts (last 10)")
        print("  3. Show abandoned carts")
        print("  4. Show recovery attempts")
        print("  5. Show statistics")
        print("  6. Exit")
        print_border("-")
        choice = input("  Select option [1-6]: ").strip()

        if choice == "1":
            show_tables()
        elif choice == "2":
            show_recent_carts()
        elif choice == "3":
            show_abandoned_carts()
        elif choice == "4":
            show_recovery_attempts()
        elif choice == "5":
            show_statistics()
        elif choice == "6":
            print("  Goodbye!")
            break
        else:
            print("  Invalid option")


if __name__ == "__main__":
    run()
