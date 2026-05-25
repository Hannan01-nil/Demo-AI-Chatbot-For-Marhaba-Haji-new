# backend/app.py - Complete with Twilio SMS + Email Recovery (MongoDB)

from fastapi import FastAPI, HTTPException, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import asyncio
import re
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from twilio.twiml.messaging_response import MessagingResponse

from database.connection import db
from services.gemini_service import gemini_service

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Marhaba Haji Chatbot")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ TWILIO SMS SETUP ============
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
WHATSAPP_SANDBOX_NUMBER = "whatsapp:+14155238886"

# ============ SENDGRID EMAIL SETUP ============
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")

# ============ REQUEST MODELS ============
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str

class AddToCartRequest(BaseModel):
    package_id: str
    quantity: int
    user_phone: Optional[str] = None
    user_email: Optional[str] = None

class RecoveryRequest(BaseModel):
    cart_id: str
    channel: str  # sms, whatsapp, email, both

# ============ PHONE + SMS (TWILIO) ============
def normalize_phone(phone: str) -> str:
    """E.164 format required by Twilio (+country code)."""
    if not phone:
        return ""
    p = re.sub(r"[^\d+]", "", str(phone).strip())
    if p.lower().startswith("whatsapp:"):
        p = p[9:]
    if p and not p.startswith("+"):
        p = "+" + p.lstrip("0")
    return p


def send_sms(to_number, message, strict: bool = False):
    """Send real SMS using Twilio. strict=True returns error instead of simulating."""
    to_number = normalize_phone(to_number)
    try:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            if strict:
                return {"status": "error", "message": "Twilio not configured in .env"}
            print("Twilio not configured - simulating SMS")
            return simulate_sms(to_number, message)

        if TWILIO_PHONE_NUMBER and to_number == normalize_phone(TWILIO_PHONE_NUMBER):
            return {
                "status": "error",
                "message": "Cannot SMS your own Twilio number. Use your mobile (e.g. +919790562321).",
            }

        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        message_obj = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )

        print(f"SMS sent to {to_number} - SID: {message_obj.sid}")
        return {"status": "sent", "sid": message_obj.sid}

    except Exception as e:
        print(f"SMS failed: {e}")
        if strict:
            return {"status": "error", "message": str(e)}
        return simulate_sms(to_number, message)

def simulate_sms(to_number, message):
    """Simulate SMS (for testing without Twilio)"""
    print("\n" + "="*60)
    print("SIMULATED SMS MESSAGE")
    print("="*60)
    print(f"To: {to_number}")
    print("-"*60)
    print(message)
    print("="*60 + "\n")
    return {"status": "simulated"}

def send_whatsapp(to_number, message, strict: bool = False):
    """Send WhatsApp message using Twilio Sandbox"""
    to_number = normalize_phone(to_number)
    try:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            if strict:
                return {"status": "error", "message": "Twilio not configured in .env"}
            print("Twilio not configured - simulating WhatsApp")
            return simulate_sms(to_number, message)

        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        message_obj = client.messages.create(
            body=message,
            from_=WHATSAPP_SANDBOX_NUMBER,
            to=f"whatsapp:{to_number}"
        )

        print(f"WhatsApp sent to {to_number} - SID: {message_obj.sid}")
        return {"status": "sent", "sid": message_obj.sid}

    except Exception as e:
        print(f"WhatsApp failed: {e}")
        if strict:
            return {"status": "error", "message": str(e)}
        return simulate_sms(to_number, message)

# ============ EMAIL FUNCTIONS (SENDGRID) ============
def send_email(to_email, subject, body):
    """Send real email using SendGrid"""
    try:
        if not SENDGRID_API_KEY:
            print("SendGrid not configured - simulating email")
            return simulate_email(to_email, subject, body)

        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=EMAIL_FROM,
            to_emails=to_email,
            subject=subject,
            html_content=f"<p>{body.replace(chr(10), '<br>')}</p>"
        )

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        print(f"Email sent to {to_email} - Status: {response.status_code}")
        return {"status": "sent", "code": response.status_code}

    except Exception as e:
        print(f"Email failed: {e}")
        return simulate_email(to_email, subject, body)

def simulate_email(to_email, subject, body):
    """Simulate email (for testing without SendGrid)"""
    print("\n" + "="*60)
    print("SIMULATED EMAIL")
    print("="*60)
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print("-"*60)
    print(body)
    print("="*60 + "\n")
    return {"status": "simulated"}

# ============ RECOVERY MESSAGE GENERATION ============
def generate_recovery_message(items, total, cart_id, channel):
    """Generate personalized recovery message"""
    item_names = [item['name'] for item in items]
    items_text = ", ".join(item_names[:2])
    if len(items) > 2:
        items_text += f" and {len(items)-2} more"

    app_url = os.getenv("APP_URL", "http://localhost:8000").rstrip("/")
    resume_url = f"{app_url}/cart/resume/{cart_id}"

    if channel in ("sms", "whatsapp"):
        return f"""Assalamu Alaikum!

You left {items_text} in your cart (Total: ${total}).

Complete your Umrah booking now:
{resume_url}

Reply HELP for assistance or STOP to unsubscribe.

Marhaba Haji Team"""

    else:  # email
        return f"""
Assalamu Alaikum!

You left the following items in your cart:

{chr(10).join([f"• {item['name']} - ${item['price']} x {item['quantity']}" for item in items])}

Total: ${total}

Don't miss out on these packages! Complete your booking now:

Resume your booking: {resume_url}

Need help? Reply to this email or WhatsApp us at {TWILIO_PHONE_NUMBER}

May your journey be blessed!

Marhaba Haji Team
"""

# ============ CART API ENDPOINTS ============
@app.post("/cart/add/{session_id}")
async def add_to_cart(session_id: str, request: AddToCartRequest):
    """Add item to cart"""
    package = db.packages.find_one({"_id": request.package_id})
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    cart = db.carts.find_one({"session_id": session_id, "status": "active"})
    now = datetime.now()

    if cart:
        cart_id = cart["_id"]
        items = cart["items"]
        total = cart["total_amount"]

        found = False
        for item in items:
            if item["package_id"] == request.package_id:
                item["quantity"] += request.quantity
                item["total"] = item["price"] * item["quantity"]
                found = True
                break

        if not found:
            items.append({
                "package_id": request.package_id,
                "name": package["name"],
                "price": package["price"],
                "quantity": request.quantity,
                "total": package["price"] * request.quantity
            })

        total = sum(i["price"] * i["quantity"] for i in items)

        update_fields = {
            "items": items,
            "total_amount": total,
            "last_activity": now
        }
        if request.user_phone:
            update_fields["user_phone"] = request.user_phone
        if request.user_email:
            update_fields["user_email"] = request.user_email

        db.carts.update_one({"_id": cart_id}, {"$set": update_fields})
    else:
        cart_id = str(uuid.uuid4())
        items = [{
            "package_id": request.package_id,
            "name": package["name"],
            "price": package["price"],
            "quantity": request.quantity,
            "total": package["price"] * request.quantity
        }]
        total = package["price"] * request.quantity

        db.carts.insert_one({
            "_id": cart_id,
            "session_id": session_id,
            "user_phone": request.user_phone,
            "user_email": request.user_email,
            "items": items,
            "total_amount": total,
            "status": "active",
            "last_activity": now,
            "abandoned_at": None,
            "recovery_attempts": 0,
            "recovered_at": None,
            "created_at": now
        })

    return {"message": "Item added to cart", "cart_id": cart_id, "total": total}

@app.get("/cart/{session_id}")
async def get_cart(session_id: str):
    """Get current cart"""
    from fastapi.responses import JSONResponse

    cart = db.carts.find_one({"session_id": session_id, "status": "active"})

    if cart:
        return JSONResponse(content={
            "cart_id": cart["_id"],
            "items": cart["items"],
            "total": cart["total_amount"]
        }, headers={"Cache-Control": "no-store, no-cache, must-revalidate"})
    return JSONResponse(content={"cart_id": None, "items": [], "total": 0}, headers={"Cache-Control": "no-store, no-cache, must-revalidate"})

@app.delete("/cart/remove/{session_id}/{package_id}")
async def remove_from_cart(session_id: str, package_id: str):
    """Remove item from cart"""
    cart = db.carts.find_one({"session_id": session_id, "status": "active"})

    if cart:
        items = [i for i in cart["items"] if i["package_id"] != package_id]
        total = sum(i["price"] * i["quantity"] for i in items)

        db.carts.update_one(
            {"_id": cart["_id"]},
            {"$set": {"items": items, "total_amount": total, "last_activity": datetime.now()}}
        )

    return {"message": "Item removed"}

@app.get("/cart/resume/{cart_id}")
async def resume_cart(cart_id: str):
    """Resume abandoned cart"""
    cart = db.carts.find_one({"_id": cart_id})

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    now = datetime.now()
    db.carts.update_one(
        {"_id": cart_id},
        {"$set": {"status": "recovered", "recovered_at": now, "last_activity": now}}
    )

    # Mark latest recovery attempt as converted
    latest_attempt = db.recovery_attempts.find_one(
        {"cart_id": cart_id, "converted": False},
        sort=[("created_at", -1)]
    )
    if latest_attempt:
        db.recovery_attempts.update_one(
            {"_id": latest_attempt["_id"]},
            {"$set": {"user_responded": True, "responded_at": now, "converted": True}}
        )

    return {
        "message": "Cart recovered! You can continue booking.",
        "cart_id": cart_id,
        "items": cart["items"],
        "total": cart["total_amount"]
    }

@app.post("/cart/recovery/manual/{cart_id}")
async def manual_recovery(cart_id: str, request: RecoveryRequest):
    """Manually trigger recovery for a cart"""
    cart = db.carts.find_one({"_id": cart_id})

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    user_phone = cart.get("user_phone")
    user_email = cart.get("user_email")
    items = cart["items"]
    total = cart["total_amount"]

    recovery_id = str(uuid.uuid4())
    db.recovery_attempts.insert_one({
        "_id": recovery_id,
        "cart_id": cart_id,
        "channel": request.channel,
        "message_sent": False,
        "message_sid": None,
        "user_responded": False,
        "responded_at": None,
        "converted": False,
        "created_at": datetime.now()
    })

    results = {}

    if request.channel in ["sms", "both"] and user_phone:
        message = generate_recovery_message(items, total, cart_id, "sms")
        results["sms"] = send_sms(user_phone, message)
        db.recovery_attempts.update_one(
            {"_id": recovery_id},
            {"$set": {"message_sent": True}}
        )

    if request.channel in ["whatsapp", "both"] and user_phone:
        message = generate_recovery_message(items, total, cart_id, "whatsapp")
        results["whatsapp"] = send_whatsapp(user_phone, message)
        db.recovery_attempts.update_one(
            {"_id": recovery_id},
            {"$set": {"message_sent": True}}
        )

    if request.channel in ["email", "both"] and user_email:
        message = generate_recovery_message(items, total, cart_id, "email")
        results["email"] = send_email(user_email, "Complete Your Umrah Booking - Cart Recovery", message)
        db.recovery_attempts.update_one(
            {"_id": recovery_id},
            {"$set": {"message_sent": True}}
        )

    return {"status": "recovery triggered", "results": results}

# ============ ABANDONED CART DETECTION ============
def detect_abandoned_carts():
    """Detect and process abandoned carts"""
    threshold = datetime.now() - timedelta(minutes=30)

    abandoned_carts = db.carts.find({
        "status": "active",
        "last_activity": {"$lt": threshold},
        "abandoned_at": None,
        "recovery_attempts": {"$lt": 3}
    })

    count = 0
    for cart in abandoned_carts:
        cart_id = cart["_id"]
        user_phone = cart.get("user_phone")
        user_email = cart.get("user_email")
        items = cart["items"]
        total = cart["total_amount"]
        attempts = cart.get("recovery_attempts", 0)

        # Mark as abandoned
        db.carts.update_one(
            {"_id": cart_id},
            {"$set": {"status": "abandoned", "abandoned_at": datetime.now(), "recovery_attempts": attempts + 1}}
        )

        # Determine recovery channel based on attempt number
        if attempts == 0:
            channel = "whatsapp" if user_phone else "email" if user_email else None
        elif attempts == 1:
            channel = "sms" if user_phone else "email" if user_email else None
        elif attempts == 2:
            channel = "email" if user_email else "sms" if user_phone else None
        else:
            channel = "both" if (user_phone and user_email) else "whatsapp" if user_phone else "email" if user_email else None

        if channel:
            recovery_id = str(uuid.uuid4())
            db.recovery_attempts.insert_one({
                "_id": recovery_id,
                "cart_id": cart_id,
                "channel": channel,
                "message_sent": False,
                "message_sid": None,
                "user_responded": False,
                "responded_at": None,
                "converted": False,
                "created_at": datetime.now()
            })

            message = generate_recovery_message(items, total, cart_id, "sms" if "sms" in channel else "email" if "email" in channel else "whatsapp")

            if "whatsapp" == channel and user_phone:
                send_whatsapp(user_phone, message)
            elif "sms" == channel and user_phone:
                send_sms(user_phone, message)
            elif "email" == channel and user_email:
                send_email(user_email, "Complete Your Umrah Booking - Special Offer", message)
            elif "both" == channel and user_phone and user_email:
                send_sms(user_phone, message)
                email_body = generate_recovery_message(items, total, cart_id, "email")
                send_email(user_email, "Complete Your Umrah Booking - Special Offer", email_body)

            db.recovery_attempts.update_one(
                {"_id": recovery_id},
                {"$set": {"message_sent": True}}
            )

        print(f"Recovery sent for cart {cart_id} (Attempt {attempts + 1})")
        count += 1

    return count

# ============ CHAT ENDPOINT ============
@app.post("/chat/send", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """Main chat endpoint with real Gemini AI responses"""
    conv = db.conversations.find_one({"session_id": chat_request.session_id})

    if not conv:
        conv_id = str(uuid.uuid4())
        db.conversations.insert_one({
            "_id": conv_id,
            "session_id": chat_request.session_id,
            "created_at": datetime.now()
        })
    else:
        conv_id = conv["_id"]

    now = datetime.now()

    # Save user message
    db.messages.insert_one({
        "_id": str(uuid.uuid4()),
        "conversation_id": conv_id,
        "role": "user",
        "content": chat_request.message,
        "created_at": now
    })

    # Load previous messages for context. The current user message is sent separately below.
    raw_history = db.messages.find(
        {"conversation_id": conv_id, "created_at": {"$lt": now}}
    ).sort("created_at", 1).limit(20)

    raw_messages = [{"role": m["role"], "content": m["content"]} for m in raw_history]
    gemini_history = gemini_service.format_history_for_gemini(raw_messages)

    try:
        if gemini_service.is_available():
            reply = gemini_service.generate_response(chat_request.message, gemini_history)
        else:
            reply = (
                "Assalamu Alaikum! I can help with Economy Umrah, Deluxe Umrah, "
                "Premium Hajj, visa requirements, hotels, and transport. Gemini is "
                "not configured yet, so add GOOGLE_API_KEY to enable full AI replies. "
                "Would you like to see the packages?"
            )
    except Exception as e:
        reply = str(e)

    # Save bot response
    db.messages.insert_one({
        "_id": str(uuid.uuid4()),
        "conversation_id": conv_id,
        "role": "assistant",
        "content": reply,
        "created_at": now
    })

    return ChatResponse(reply=reply)

@app.get("/")
def root():
    return {"status": "running", "message": "Marhaba Haji Chatbot with Recovery"}

@app.get("/packages")
def get_packages():
    packages = db.packages.find({}).sort("_id", 1)
    return {"packages": [{"id": p["_id"], "name": p["name"], "price": p["price"], "duration": p["duration"], "description": p["description"]} for p in packages]}

@app.get("/analytics/abandoned")
def get_abandoned_stats():
    """Get abandoned cart analytics"""
    abandoned_count = db.carts.count_documents({"status": "abandoned"})
    recovered_count = db.recovery_attempts.count_documents({"converted": True})
    messages_sent = db.recovery_attempts.count_documents({"message_sent": True})

    recovery_rate = (recovered_count / abandoned_count * 100) if abandoned_count > 0 else 0

    return {
        "abandoned_carts": abandoned_count,
        "recovered_carts": recovered_count,
        "recovery_rate": round(recovery_rate, 2),
        "messages_sent": messages_sent
    }

# ============ DEMO ENDPOINTS ============
@app.get("/demo/cart/{session_id}")
async def demo_get_cart(session_id: str):
    """Demo: get current cart info without modifying it"""
    cart = db.carts.find_one({"session_id": session_id, "status": "active"})

    if cart:
        return {"status": "active", "cart_id": cart["_id"], "items": cart["items"], "total": cart["total_amount"]}

    return {"status": "empty", "cart_id": None, "items": [], "total": 0}

class DemoSmsRequest(BaseModel):
    phone: str
    message: Optional[str] = None

@app.post("/demo-sms")
@app.post("/api/demo-sms", include_in_schema=False)
async def demo_sms(request: DemoSmsRequest):
    """Simple demo endpoint to send SMS to any number"""
    msg = request.message or "Assalamu Alaikum! This is a test SMS from Marhaba Haji Chatbot. Your booking is ready! Reply HELP for assistance."
    result = send_sms(request.phone, msg)
    return {"status": result["status"], "to": request.phone, "result": result}

class DemoAbandonRequest(BaseModel):
    phone: str
    cart_total: Optional[float] = 1500.0
    package_name: Optional[str] = None

@app.post("/demo-abandon")
@app.post("/api/demo-abandon", include_in_schema=False)
async def demo_abandon(request: DemoAbandonRequest):
    """Send BOTH WhatsApp AND SMS abandoned cart reminder (parallel, real Twilio only)."""
    phone = normalize_phone(request.phone)
    if not phone or len(phone) < 10:
        raise HTTPException(
            status_code=400,
            detail="Invalid phone. Save number with country code, e.g. +919790562321",
        )

    package_name = request.package_name or "Deluxe Umrah Package"
    cart_total = request.cart_total

    message_body = f"""Marhaba Haji!

You left {package_name} in your cart (Total: ${cart_total:,.2f}).

Complete your booking now:
{os.getenv("APP_URL", "http://localhost:8000").rstrip("/")}/cart/resume

Reply HELP for assistance.

Marhaba Haji Team"""

    app_url = os.getenv("APP_URL", "http://localhost:8000").rstrip("/")
    sms_body = f"Marhaba Haji! You left {package_name} (${cart_total:,.2f}) in your cart. Complete booking: {app_url}/cart/resume - Reply HELP for assistance."

    loop = asyncio.get_event_loop()
    sms_result, whatsapp_result = await asyncio.gather(
        loop.run_in_executor(None, lambda: send_sms(phone, sms_body, strict=True)),
        loop.run_in_executor(None, lambda: send_whatsapp(phone, message_body, strict=True)),
    )

    return {
        "sms": sms_result,
        "whatsapp": whatsapp_result,
        "to": phone,
    }

# ============ WHATSAPP WEBHOOK (TWILIO SANDBOX) ============
@app.post("/webhook")
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    """Receive WhatsApp messages from Twilio Sandbox and auto-reply"""
    try:
        print(f"\n[WhatsApp] message from {From}: {Body}")
    except UnicodeEncodeError:
        print(f"\n[WhatsApp] message from {From!r}")
    twilio_response = MessagingResponse()
    twilio_response.message("Assalamu Alaikum! Welcome to Marhaba Haji AI")
    return Response(content=str(twilio_response), media_type="application/xml")

# ============ SCHEDULER ============
scheduler = None
if os.getenv("VERCEL") != "1" or os.getenv("ENABLE_SCHEDULER") == "true":
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=detect_abandoned_carts, trigger="interval", minutes=15, id="abandoned_cart_check")
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

# ============ START SERVER ============
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("Marhaba Haji Chatbot with Recovery")
    print("http://localhost:8000")
    print("http://localhost:8000/docs")
    print("SMS via Twilio | Email via SendGrid")
    print("Abandoned cart detection every 15 min")
    print("="*50 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
