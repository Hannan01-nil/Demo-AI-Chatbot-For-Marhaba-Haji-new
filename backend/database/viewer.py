from .connection import db


def print_border(char="=", width=80):
    print(char * width)


def print_header(text):
    print_border()
    print(f"  {text}")
    print_border()


def show_tables():
    print_header("DATABASE COLLECTIONS")
    collections = db.list_collection_names()
    if collections:
        for c in sorted(collections):
            count = db[c].count_documents({})
            print(f"  {c} ({count} documents)")
    else:
        print("  (no collections found)")
    print_border()


def show_recent_carts(limit=10):
    print_header(f"RECENT CARTS (last {limit})")
    carts = db.carts.find({}).sort("created_at", -1).limit(limit)

    count = 0
    for c in carts:
        print(f"  ID:       {c['_id']}")
        print(f"     Session:  {c.get('session_id', 'N/A')}")
        print(f"     Phone:    {c.get('user_phone', 'N/A') or 'N/A'}")
        print(f"     Email:    {c.get('user_email', 'N/A') or 'N/A'}")
        print(f"     Total:    ${c.get('total_amount', 0):.2f}")
        print(f"     Status:   {c.get('status', 'N/A')}")
        print(f"     Created:  {c.get('created_at', 'N/A')}")
        print_border("-")
        count += 1

    if count == 0:
        print("  (no carts found)")
        print_border()


def show_abandoned_carts():
    print_header("ABANDONED CARTS")
    carts = db.carts.find({"status": "abandoned"}).sort("abandoned_at", -1)

    count = 0
    for c in carts:
        print(f"  ID:              {c['_id']}")
        print(f"     Session:         {c.get('session_id', 'N/A')}")
        print(f"     Phone:           {c.get('user_phone', 'N/A') or 'N/A'}")
        print(f"     Email:           {c.get('user_email', 'N/A') or 'N/A'}")
        print(f"     Total:           ${c.get('total_amount', 0):.2f}")
        print(f"     Abandoned:       {c.get('abandoned_at', 'N/A')}")
        print(f"     Recovery Att:    {c.get('recovery_attempts', 0)}")
        print_border("-")
        count += 1

    if count == 0:
        print("  (no abandoned carts)")
        print_border()


def show_recovery_attempts():
    print_header("RECOVERY ATTEMPTS")
    attempts = db.recovery_attempts.find({}).sort("created_at", -1)

    count = 0
    for a in attempts:
        print(f"  ID:        {a['_id']}")
        print(f"     Cart:      {a.get('cart_id', 'N/A')}")
        print(f"     Channel:   {a.get('channel', 'N/A')}")
        print(f"     Sent:      {'Yes' if a.get('message_sent') else 'No'}")
        print(f"     Responded: {'Yes' if a.get('user_responded') else 'No'}")
        print(f"     Converted: {'Yes' if a.get('converted') else 'No'}")
        print(f"     Created:   {a.get('created_at', 'N/A')}")
        print_border("-")
        count += 1

    if count == 0:
        print("  (no recovery attempts)")
        print_border()


def show_statistics():
    total_carts = db.carts.count_documents({})
    active_carts = db.carts.count_documents({"status": "active"})
    abandoned_count = db.carts.count_documents({"status": "abandoned"})
    recovered_count = db.carts.count_documents({"status": "recovered"})
    total_attempts = db.recovery_attempts.count_documents({})
    messages_sent = db.recovery_attempts.count_documents({"message_sent": True})
    converted = db.recovery_attempts.count_documents({"converted": True})
    total_conversations = db.conversations.count_documents({})
    total_messages = db.messages.count_documents({})

    recovery_rate = (converted / abandoned_count * 100) if abandoned_count > 0 else 0

    print_header("DATABASE STATISTICS")
    print(f"  Total Carts:          {total_carts}")
    print(f"  Active Carts:         {active_carts}")
    print(f"  Abandoned Carts:      {abandoned_count}")
    print(f"  Recovered Carts:      {recovered_count}")
    print(f"  Recovery Rate:        {recovery_rate:.1f}%")
    print(f"  Recovery Attempts:    {total_attempts}")
    print(f"  Messages Sent:        {messages_sent}")
    print(f"  Conversions:          {converted}")
    print(f"  Conversations:        {total_conversations}")
    print(f"  Messages:             {total_messages}")
    print_border()


def run():
    while True:
        print("\n")
        print_border("=")
        print("  MARHABA DATABASE VIEWER")
        print_border("=")
        print("  1. Show all collections")
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
