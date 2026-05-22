""" Twilio SMS + WhatsApp Sandbox verification script """
import os
from dotenv import load_dotenv

load_dotenv()

TEST_PHONE = "+919790562321"
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_SMS_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TWILIO_WHATSAPP_NUMBER = "+14155238886"


def check_twilio_balance(client):
    try:
        balance = client.api.accounts(TWILIO_ACCOUNT_SID).fetch().balance
        return f"${balance}" if balance else "Available"
    except:
        return "Unknown"


def main():
    print("=" * 70)
    print("   TWILIO SMS & WHATSAPP SANDBOX VERIFICATION")
    print("=" * 70)

    # 1. Credential check
    print(f"\n[1/5] Checking credentials...")
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_SMS_NUMBER]):
        print("   ❌ Missing Twilio credentials in .env")
        return
    print(f"   ✅ Account SID: {TWILIO_ACCOUNT_SID[:8]}...")
    print(f"   ✅ SMS Number:  {TWILIO_SMS_NUMBER}")
    print(f"   ✅ WhatsApp:    {TWILIO_WHATSAPP_NUMBER}")

    from twilio.rest import Client
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    # 2. Account & balance
    print(f"\n[2/5] Checking account status...")
    try:
        account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
        status = account.status
        balance = check_twilio_balance(client)
        print(f"   ✅ Account: {status}")
        print(f"   ✅ Balance: {balance}")
    except Exception as e:
        print(f"   ❌ Account check failed: {e}")
        return

    # 3. Test SMS
    print(f"\n[3/5] Sending test SMS to {TEST_PHONE}...")
    sms_sid = None
    try:
        msg = client.messages.create(
            body="🕋 Marhaba Haji - SMS verification test. Reply OK if received.",
            from_=TWILIO_SMS_NUMBER,
            to=TEST_PHONE
        )
        sms_sid = msg.sid
        print(f"   📤 SMS sent (SID: {msg.sid})")
    except Exception as e:
        print(f"   ❌ SMS FAILED - {e}")

    # 4. Test WhatsApp
    print(f"\n[4/5] Sending test WhatsApp to {TEST_PHONE}...")
    wa_sid = None
    wa_error = None
    try:
        msg = client.messages.create(
            body="🕋 Marhaba Haji - WhatsApp verification. If you see this, it's working!",
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            to=f"whatsapp:{TEST_PHONE}"
        )
        wa_sid = msg.sid
        print(f"   📤 WhatsApp sent (SID: {msg.sid})")
    except Exception as e:
        wa_error = str(e)
        if "63016" in wa_error:
            print(f"   ⚠️  WhatsApp Sandbox NOT ACTIVATED for this number")
            print(f"   📋 To activate: message '{TWILIO_WHATSAPP_NUMBER}' on WhatsApp with 'join code'")
        else:
            print(f"   ❌ WhatsApp FAILED - {wa_error[:120]}")

    # 5. Delivery status (poll once after short wait)
    import time
    print(f"\n[5/5] Checking delivery status (waiting 5 sec)...")
    time.sleep(5)

    results = {"sms": "❓ Pending", "whatsapp": "❓ Pending"}

    if sms_sid:
        try:
            msg = client.messages(sms_sid).fetch()
            results["sms"] = f"{'✅' if msg.status in ('delivered','sent') else '❓'} Delivered" if msg.status == "delivered" else f"{'⚠️'} {msg.status}"
            if msg.status == "delivered":
                results["sms"] = "✅ WORKING (delivered)"
            elif msg.status == "sent":
                results["sms"] = "✅ WORKING (sent - awaiting delivery report)"
            else:
                results["sms"] = f"⚠️ {msg.status}"
        except:
            results["sms"] = "⚠️ Could not fetch status"

    if wa_sid:
        try:
            msg = client.messages(wa_sid).fetch()
            if msg.status == "delivered":
                results["whatsapp"] = "✅ WORKING (delivered)"
            elif msg.status == "sent":
                results["whatsapp"] = "✅ WORKING (sent - awaiting delivery report)"
            else:
                results["whatsapp"] = f"⚠️ {msg.status}"
        except:
            results["whatsapp"] = "⚠️ Could not fetch status"
    elif wa_error and "63016" in wa_error:
        results["whatsapp"] = "❌ NOT ACTIVATED - send 'join <code>' to activate"

    # Summary
    print("\n" + "=" * 70)
    print("   RESULTS SUMMARY")
    print("=" * 70)
    print(f"\n   Twilio Account: ✅ {status if 'status' in dir() else 'OK'}")
    print(f"   SMS:            {results['sms']}")
    print(f"   WhatsApp:       {results['whatsapp']}")
    print(f"   Test Number:    {TEST_PHONE}")

    if "❌" in results["whatsapp"]:
        print(f"\n   💡 WhatsApp activation steps:")
        print(f"      1. Open WhatsApp on {TEST_PHONE}")
        print(f"      2. Send message to {TWILIO_WHATSAPP_NUMBER}")
        print(f"      3. Type: join marhaba")
        print(f"      4. Wait for confirmation, then re-run this script")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
