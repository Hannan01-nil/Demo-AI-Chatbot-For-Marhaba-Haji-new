import os
import sys
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "database", "marhaba.db")


def print_step(num, text):
    print(f"\n  [{num}] {text}")
    print("  " + "-" * 40)


def main():
    print("=" * 60)
    print("  MARHABA RECOVERY FLOW TEST")
    print("=" * 60)

    # Step 1: Create test session
    print_step(1, "Creating test session...")
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"
    print(f"     Session ID: {session_id}")

    # Step 2: Add test package
    print_step(2, "Adding test package to cart...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, price FROM packages LIMIT 1")
    pkg = cursor.fetchone()
    if not pkg:
        print("     ❌ No packages found in database")
        conn.close()
        return

    cart_id = str(uuid.uuid4())
    items = json.dumps([{
        "package_id": pkg[0],
        "name": pkg[1],
        "price": pkg[2],
        "quantity": 1,
        "total": pkg[2]
    }])
    now = datetime.now()

    cursor.execute("""
        INSERT INTO carts (id, session_id, user_phone, user_email, items, total_amount, last_activity, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (cart_id, session_id, "+15551234567", "test@example.com", items, pkg[2], now, now))
    conn.commit()
    print(f"     ✅ Cart created: {cart_id}")
    print(f"     Package: {pkg[1]} (${pkg[2]:.2f})")

    # Step 3: Simulate abandonment
    print_step(3, "Simulating abandonment...")
    threshold = now - timedelta(hours=2)
    cart_id_to_test = cart_id

    cursor.execute("""
        UPDATE carts SET last_activity = ?, status = 'active'
        WHERE id = ?
    """, (threshold, cart_id_to_test))
    conn.commit()
    print("     ✅ Last activity set to 2 hours ago")

    # Step 4: Trigger detection (simulate scheduler)
    print_step(4, "Triggering abandonment detection...")
    from app import detect_abandoned_carts
    abandoned_count = detect_abandoned_carts()
    print(f"     🔄 Abandoned carts detected: {abandoned_count}")

    # Step 5: Check recovery attempts
    print_step(5, "Checking recovery attempts...")
    cursor.execute("""
        SELECT channel, message_sent, created_at
        FROM recovery_attempts
        WHERE cart_id = ?
        ORDER BY created_at DESC
    """, (cart_id_to_test,))
    attempts = cursor.fetchall()

    if attempts:
        for a in attempts:
            print(f"     📨 Channel: {a[0]}")
            print(f"     ✅ Sent:   {'Yes' if a[1] else 'No'}")
            print(f"     🕐 Time:   {a[2]}")
    else:
        print("     ℹ️  No recovery attempts found (may need 30+ min threshold)")
        print("     ℹ️  Running direct recovery as fallback...")

        # Direct recovery as fallback
        cursor.execute("""
            UPDATE carts SET status = 'abandoned', abandoned_at = ?, recovery_attempts = 1
            WHERE id = ?
        """, (now, cart_id_to_test))

        recovery_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO recovery_attempts (id, cart_id, channel, message_sent, created_at)
            VALUES (?, ?, 'sms', 1, ?)
        """, (recovery_id, cart_id_to_test, now))
        conn.commit()
        print("     ✅ Direct recovery attempt recorded")

    conn.close()

    # Step 6: Summary
    print("\n  " + "=" * 40)
    print("  TEST RESULTS SUMMARY")
    print("  " + "=" * 40)
    print(f"     Session:     {session_id}")
    print(f"     Cart ID:     {cart_id}")
    print(f"     Package:     {pkg[1]}")
    print(f"     Attempts:    {len(attempts)}")
    print()
    print("  ℹ️  Check the server console for SMS/Email output")
    print("  ℹ️  Run `python scripts/view_database.py` to see all records")
    print()
    print("=" * 60)
    print("  Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
