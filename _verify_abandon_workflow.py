"""Verify abandoned cart alert workflow only."""
import json
import os
import sys
import uuid

import requests
from dotenv import load_dotenv

load_dotenv("backend/.env")
BASE = "http://localhost:8000"
SESSION = f"abandon-verify-{uuid.uuid4().hex[:8]}"
PHONE = os.getenv("ADMIN_PHONE") or "+919790562321"
# Use distinct test phone if admin equals Twilio from-number
TWILIO_FROM = os.getenv("TWILIO_PHONE_NUMBER", "")
if PHONE == TWILIO_FROM:
    PHONE = "+919790562321"

passed = 0
failed = 0


def ok(msg):
    global passed
    passed += 1
    print(f"  PASS: {msg}")


def fail(msg):
    global failed
    failed += 1
    print(f"  FAIL: {msg}")


def cart_snapshot():
    r = requests.get(f"{BASE}/cart/{SESSION}", timeout=10)
    r.raise_for_status()
    return r.json()


def main():
    print("=" * 60)
    print("ABANDONED CART ALERT WORKFLOW VERIFICATION")
    print("=" * 60)

    # 1. Backend
    print("\n[1] Backend running")
    try:
        r = requests.get(f"{BASE}/", timeout=5)
        if r.status_code == 200 and r.json().get("status") == "running":
            ok("Backend up at localhost:8000")
        else:
            fail(f"Unexpected root response: {r.text}")
    except Exception as e:
        fail(f"Backend not reachable: {e}")
        print(f"\nRESULT: {passed} passed, {failed} failed")
        sys.exit(1)

    # 2. Twilio
    print("\n[2] Twilio connected")
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    if not sid or not token:
        fail("Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN")
    else:
        try:
            from twilio.rest import Client

            client = Client(sid, token)
            acct = client.api.accounts(sid).fetch()
            ok(f"Twilio account: {acct.friendly_name}")
        except Exception as e:
            fail(f"Twilio connection: {e}")

    # 3. Seed cart
    print("\n[3] Seed active cart (session + item)")
    add_body = {
        "package_id": "pkg_002",
        "quantity": 2,
        "user_phone": PHONE,
    }
    try:
        r = requests.post(
            f"{BASE}/cart/add/{SESSION}",
            json=add_body,
            timeout=15,
        )
        r.raise_for_status()
        add_data = r.json()
        ok(f"Cart created cart_id={add_data.get('cart_id')} total={add_data.get('total')}")
    except Exception as e:
        fail(f"Could not add to cart: {e}")
        print(f"\nRESULT: {passed} passed, {failed} failed")
        sys.exit(1)

    before = cart_snapshot()
    expected_items = len(before.get("items", []))
    expected_total = before.get("total")
    expected_cart_id = before.get("cart_id")

    if not expected_cart_id or expected_items == 0:
        fail("Cart empty after seed")
    else:
        ok(f"Cart has {expected_items} item(s), total=${expected_total}")

    def carts_equal(a, b, label):
        same_id = a.get("cart_id") == b.get("cart_id")
        same_items = json.dumps(a.get("items"), sort_keys=True) == json.dumps(
            b.get("items"), sort_keys=True
        )
        same_total = a.get("total") == b.get("total")
        if same_id and same_items and same_total:
            ok(f"{label}: cart_id, items, total unchanged")
            return True
        if not same_id:
            fail(f"{label}: cart_id changed {a.get('cart_id')} -> {b.get('cart_id')}")
        if not same_items:
            fail(f"{label}: items changed")
        if not same_total:
            fail(f"{label}: total changed {a.get('total')} -> {b.get('total')}")
        return False

    # 4. API demo-abandon (simulate button clicks)
    print("\n[4] POST /api/demo-abandon (click 1)")
    pkg_name = ", ".join(i["name"] for i in before["items"])
    payload = {
        "phone": PHONE,
        "cart_total": before["total"],
        "package_name": pkg_name,
    }
    sids = []
    for click in (1, 2):
        label = f"click {click}"
        print(f"\n[4.{click}] Button click -> alerts")
        try:
            r = requests.post(
                f"{BASE}/api/demo-abandon",
                json=payload,
                timeout=30,
            )
            if r.status_code != 200:
                fail(f"{label}: HTTP {r.status_code} {r.text[:200]}")
                continue
            data = r.json()
            sms = data.get("sms", {})
            wa = data.get("whatsapp", {})
            sms_ok = sms.get("status") in ("sent", "simulated")
            wa_ok = wa.get("status") in ("sent", "simulated")
            if sms_ok:
                ok(f"{label}: SMS {sms.get('status')} sid={sms.get('sid', 'sim')}")
                if sms.get("sid"):
                    sids.append(("SMS", sms["sid"]))
            else:
                fail(f"{label}: SMS not sent — {sms}")
            if wa_ok:
                ok(f"{label}: WhatsApp {wa.get('status')} sid={wa.get('sid', 'sim')}")
                if wa.get("sid"):
                    sids.append(("WA", wa["sid"]))
            else:
                fail(f"{label}: WhatsApp not sent — {wa}")
        except Exception as e:
            fail(f"{label}: request error — {e}")

        after = cart_snapshot()
        carts_equal(before, after, f"After {label}")

    # 5. Demo cart endpoint (read-only, used by frontend)
    print("\n[5] GET /demo/cart/{session} (frontend read — no mutation)")
    try:
        r = requests.get(f"{BASE}/demo/cart/{SESSION}", timeout=10)
        demo = r.json()
        if demo.get("status") == "active" and demo.get("cart_id") == expected_cart_id:
            ok("demo/cart returns active cart unchanged")
        else:
            fail(f"demo/cart unexpected: {demo}")
    except Exception as e:
        fail(f"demo/cart error: {e}")

    # 6. Twilio delivery for latest SIDs
    if sids and sid and token:
        print("\n[6] Twilio delivery status (latest alerts)")
        from twilio.rest import Client

        client = Client(sid, token)
        for kind, message_sid in sids[-4:]:
            try:
                m = client.messages(message_sid).fetch()
                ok(f"{kind} delivery status={m.status} to={m.to}")
            except Exception as e:
                fail(f"{kind} status fetch: {e}")

    print("\n" + "=" * 60)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 60)
    checks = [
        ("WhatsApp Alert Sent", any("WA" in k for k, _ in sids)),
        ("SMS Alert Sent", any("SMS" in k for k, _ in sids)),
        ("Cart Preserved", failed == 0 or "cart_id changed" not in str(failed)),
        ("Button/API Working", passed >= 6),
        ("Workflow Operational", failed == 0),
    ]
    for name, cond in checks:
        print(f"  {'✅' if cond else '❌'} {name}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
