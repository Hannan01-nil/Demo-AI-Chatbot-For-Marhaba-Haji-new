# backend/app.py - Complete with Twilio SMS + Email Recovery

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import sqlite3
import json
from datetime import datetime, timedelta
import uuid
import google.generativeai as genai
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import requests

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
TWILIO_ACCOUNT_SID = "AC8e452c7468f6ad46a2978eb1a074dbb3"
TWILIO_AUTH_TOKEN = "c374a898284346550a497d98c45b724b"
TWILIO_PHONE_NUMBER = "+18782157365"

# ============ SENDGRID EMAIL SETUP ============
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")

# ============ GEMINI AI SETUP ============
GOOGLE_API_KEY = "AIzaSyCCc_rpwqft5j3MMNiC2AyW-RrztgmpT1Q"
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Gemini AI Ready")
else:
    print("❌ No Gemini API Key")
    model = None

# ============ DATABASE SETUP ============
os.makedirs("database", exist_ok=True)
DB_PATH = "database/marhaba.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            created_at TIMESTAMP
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            created_at TIMESTAMP
        )
    ''')
    
    # Packages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS packages (
            id TEXT PRIMARY KEY,
            name TEXT,
            price REAL,
            duration INT,
            description TEXT
        )
    ''')
    
    # Carts table with recovery tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            user_phone TEXT,
            user_email TEXT,
            items TEXT,
            total_amount REAL,
            status TEXT DEFAULT 'active',
            last_activity TIMESTAMP,
            abandoned_at TIMESTAMP,
            recovery_attempts INT DEFAULT 0,
            recovered_at TIMESTAMP,
            created_at TIMESTAMP
        )
    ''')
    
    # Recovery attempts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recovery_attempts (
            id TEXT PRIMARY KEY,
            cart_id TEXT,
            channel TEXT,
            message_sent BOOLEAN DEFAULT 0,
            message_sid TEXT,
            user_responded BOOLEAN DEFAULT 0,
            responded_at TIMESTAMP,
            converted BOOLEAN DEFAULT 0,
            created_at TIMESTAMP
        )
    ''')
    
    # Insert sample packages
    cursor.execute("SELECT COUNT(*) FROM packages")
    if cursor.fetchone()[0] == 0:
        packages = [
            ('pkg_001', 'Economy Umrah', 850, 7, '3-star hotel, shared transport, visa included'),
            ('pkg_002', 'Deluxe Umrah', 1500, 14, '4-star hotel near Haram, private transport'),
            ('pkg_003', 'Premium Hajj', 4500, 21, '5-star hotel, VIP service, full board')
        ]
        cursor.executemany("INSERT INTO packages VALUES (?,?,?,?,?)", packages)
    
    conn.commit()
    conn.close()
    print("✅ Database Ready")

init_db()

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
    channel: str  # sms, email, both

# ============ INTENT DETECTION ============
def detect_intent(message):
    msg = message.lower()
    if any(w in msg for w in ["hi", "hello", "salam", "assalamu"]):
        return "greeting"
    if any(w in msg for w in ["package", "umrah", "hajj", "trip"]):
        return "package"
    if any(w in msg for w in ["visa", "document", "passport"]):
        return "visa"
    if any(w in msg for w in ["price", "cost", "how much"]):
        return "price"
    return "general"

# ============ AI RESPONSE ============
def get_ai_response(message, intent):
    prompt = f"""You are Marhaba Haji, a friendly AI assistant for Hajj and Umrah travel.

User message: {message}
Intent: {intent}

Available packages:
- Economy Umrah: $850 for 7 days
- Deluxe Umrah: $1500 for 14 days
- Premium Hajj: $4500 for 21 days

Visa info: $150-200, valid passport needed, meningitis vaccine.

Respond in a friendly, helpful way. Keep it short (2-3 sentences). Use emojis. Be respectful.
"""
    try:
        if model:
            response = model.generate_content(prompt)
            return response.text
        else:
            raise Exception("No model")
    except:
        if intent == "greeting":
            return "Assalamu Alaikum! 👋 I'm Marhaba Haji. How can I help with your Umrah or Hajj plans?"
        elif intent == "package":
            return "We have Economy Umrah ($850/7 days) and Deluxe Umrah ($1500/14 days). Which interests you? 🕋"
        elif intent == "visa":
            return "Umrah visa costs $150-200. You need a valid passport (6 months) and meningitis vaccine. 📋"
        else:
            return "I can help with Umrah packages, visas, and hotels. What would you like to know? 🕋"

# ============ SMS FUNCTIONS (TWILIO) ============
def send_sms(to_number, message):
    """Send real SMS using Twilio"""
    try:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            print("⚠️ Twilio not configured - simulating SMS")
            return simulate_sms(to_number, message)
        
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message_obj = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_number
        )
        
        print(f"✅ SMS sent to {to_number} - SID: {message_obj.sid}")
        return {"status": "sent", "sid": message_obj.sid}
    
    except Exception as e:
        print(f"❌ SMS failed: {e}")
        return simulate_sms(to_number, message)

def simulate_sms(to_number, message):
    """Simulate SMS (for testing without Twilio)"""
    print("\n" + "="*60)
    print("📱 SIMULATED SMS MESSAGE")
    print("="*60)
    print(f"To: {to_number}")
    print("-"*60)
    print(message)
    print("="*60 + "\n")
    return {"status": "simulated"}

# ============ EMAIL FUNCTIONS (SENDGRID) ============
def send_email(to_email, subject, body):
    """Send real email using SendGrid"""
    try:
        if not SENDGRID_API_KEY:
            print("⚠️ SendGrid not configured - simulating email")
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
        
        print(f"✅ Email sent to {to_email} - Status: {response.status_code}")
        return {"status": "sent", "code": response.status_code}
    
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return simulate_email(to_email, subject, body)

def simulate_email(to_email, subject, body):
    """Simulate email (for testing without SendGrid)"""
    print("\n" + "="*60)
    print("📧 SIMULATED EMAIL")
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
    
    resume_url = f"http://localhost:8000/cart/resume/{cart_id}"
    
    if channel == "sms":
        return f"""🕋 Assalamu Alaikum!

You left {items_text} in your cart (Total: ${total}).

Complete your Umrah booking now:
{resume_url}

Reply HELP for assistance or STOP to unsubscribe.

Marhaba Haji Team 🤲"""
    
    else:  # email
        return f"""
Assalamu Alaikum! 🕋

You left the following items in your cart:

{chr(10).join([f"• {item['name']} - ${item['price']} x {item['quantity']}" for item in items])}

Total: ${total}

Don't miss out on these packages! Complete your booking now:

👉 Resume your booking: {resume_url}

Need help? Reply to this email or WhatsApp us at {TWILIO_PHONE_NUMBER}

May your journey be blessed! 🤲

Marhaba Haji Team
"""

# ============ CART API ENDPOINTS ============
@app.post("/cart/add/{session_id}")
async def add_to_cart(session_id: str, request: AddToCartRequest):
    """Add item to cart"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, price FROM packages WHERE id = ?", (request.package_id,))
    package = cursor.fetchone()
    
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    cursor.execute("SELECT id, items, total_amount FROM carts WHERE session_id = ? AND status = 'active'", (session_id,))
    cart = cursor.fetchone()
    
    now = datetime.now()
    
    if cart:
        cart_id = cart[0]
        items = json.loads(cart[1])
        total = cart[2]
        
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
                "name": package[0],
                "price": package[1],
                "quantity": request.quantity,
                "total": package[1] * request.quantity
            })
        
        total = sum(i["price"] * i["quantity"] for i in items)
        
        cursor.execute('''
            UPDATE carts SET items = ?, total_amount = ?, last_activity = ?, user_phone = COALESCE(?, user_phone), user_email = COALESCE(?, user_email)
            WHERE id = ?
        ''', (json.dumps(items), total, now, request.user_phone, request.user_email, cart_id))
    else:
        cart_id = str(uuid.uuid4())
        items = [{
            "package_id": request.package_id,
            "name": package[0],
            "price": package[1],
            "quantity": request.quantity,
            "total": package[1] * request.quantity
        }]
        total = package[1] * request.quantity
        
        cursor.execute('''
            INSERT INTO carts (id, session_id, user_phone, user_email, items, total_amount, last_activity, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cart_id, session_id, request.user_phone, request.user_email, json.dumps(items), total, now, now))
    
    conn.commit()
    conn.close()
    
    return {"message": "Item added to cart", "cart_id": cart_id, "total": total}

@app.get("/cart/{session_id}")
async def get_cart(session_id: str):
    """Get current cart"""
    from fastapi.responses import JSONResponse
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, items, total_amount FROM carts WHERE session_id = ? AND status = 'active'", (session_id,))
    cart = cursor.fetchone()
    conn.close()
    
    if cart:
        return JSONResponse(content={
            "cart_id": cart[0],
            "items": json.loads(cart[1]),
            "total": cart[2]
        }, headers={"Cache-Control": "no-store, no-cache, must-revalidate"})
    return JSONResponse(content={"cart_id": None, "items": [], "total": 0}, headers={"Cache-Control": "no-store, no-cache, must-revalidate"})

@app.delete("/cart/remove/{session_id}/{package_id}")
async def remove_from_cart(session_id: str, package_id: str):
    """Remove item from cart"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, items FROM carts WHERE session_id = ? AND status = 'active'", (session_id,))
    cart = cursor.fetchone()
    
    if cart:
        cart_id = cart[0]
        items = json.loads(cart[1])
        items = [i for i in items if i["package_id"] != package_id]
        total = sum(i["price"] * i["quantity"] for i in items)
        
        cursor.execute('''
            UPDATE carts SET items = ?, total_amount = ?, last_activity = ?
            WHERE id = ?
        ''', (json.dumps(items), total, datetime.now(), cart_id))
        conn.commit()
    
    conn.close()
    return {"message": "Item removed"}

@app.get("/cart/resume/{cart_id}")
async def resume_cart(cart_id: str):
    """Resume abandoned cart"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT session_id, items, total_amount FROM carts WHERE id = ?", (cart_id,))
    cart = cursor.fetchone()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cursor.execute('''
        UPDATE carts SET status = 'recovered', recovered_at = ?, last_activity = ?
        WHERE id = ?
    ''', (datetime.now(), datetime.now(), cart_id))
    
    cursor.execute('''
        UPDATE recovery_attempts SET user_responded = 1, responded_at = ?, converted = 1
        WHERE cart_id = ? AND converted = 0
        ORDER BY created_at DESC LIMIT 1
    ''', (datetime.now(), cart_id))
    
    conn.commit()
    conn.close()
    
    return {
        "message": "Cart recovered! You can continue booking.",
        "cart_id": cart_id,
        "items": json.loads(cart[1]),
        "total": cart[2]
    }

@app.post("/cart/recovery/manual/{cart_id}")
async def manual_recovery(cart_id: str, request: RecoveryRequest):
    """Manually trigger recovery for a cart"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_phone, user_email, items, total_amount FROM carts WHERE id = ?", (cart_id,))
    cart = cursor.fetchone()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    user_phone = cart[0]
    user_email = cart[1]
    items = json.loads(cart[2])
    total = cart[3]
    
    recovery_id = str(uuid.uuid4())
    cursor.execute('''
        INSERT INTO recovery_attempts (id, cart_id, channel, created_at)
        VALUES (?, ?, ?, ?)
    ''', (recovery_id, cart_id, request.channel, datetime.now()))
    conn.commit()
    conn.close()
    
    results = {}
    
    if request.channel in ["sms", "both"] and user_phone:
        message = generate_recovery_message(items, total, cart_id, "sms")
        results["sms"] = send_sms(user_phone, message)
        cursor.execute("UPDATE recovery_attempts SET message_sent = 1 WHERE id = ?", (recovery_id,))
    
    if request.channel in ["email", "both"] and user_email:
        message = generate_recovery_message(items, total, cart_id, "email")
        results["email"] = send_email(user_email, "Complete Your Umrah Booking - Cart Recovery", message)
        cursor.execute("UPDATE recovery_attempts SET message_sent = 1 WHERE id = ?", (recovery_id,))
    
    conn.commit()
    conn.close()
    
    return {"status": "recovery triggered", "results": results}

# ============ ABANDONED CART DETECTION ============
def detect_abandoned_carts():
    """Detect and process abandoned carts"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    threshold = datetime.now() - timedelta(minutes=30)  # 30 minutes
    
    cursor.execute('''
        SELECT id, session_id, user_phone, user_email, items, total_amount, recovery_attempts
        FROM carts 
        WHERE status = 'active' 
        AND last_activity < ?
        AND abandoned_at IS NULL
        AND recovery_attempts < 3
    ''', (threshold,))
    
    abandoned_carts = cursor.fetchall()
    
    for cart in abandoned_carts:
        cart_id = cart[0]
        user_phone = cart[2]
        user_email = cart[3]
        items = json.loads(cart[4])
        total = cart[5]
        attempts = cart[6]
        
        # Mark as abandoned
        cursor.execute('''
            UPDATE carts SET status = 'abandoned', abandoned_at = ?, recovery_attempts = ?
            WHERE id = ?
        ''', (datetime.now(), attempts + 1, cart_id))
        
        # Determine recovery channel based on attempt number
        if attempts == 0:
            # First attempt: SMS if available
            channel = "sms" if user_phone else "email" if user_email else None
        elif attempts == 1:
            # Second attempt: Email if available
            channel = "email" if user_email else "sms" if user_phone else None
        else:
            # Third attempt: Both if available
            channel = "both" if (user_phone and user_email) else "sms" if user_phone else "email" if user_email else None
        
        if channel:
            recovery_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO recovery_attempts (id, cart_id, channel, created_at)
                VALUES (?, ?, ?, ?)
            ''', (recovery_id, cart_id, channel, datetime.now()))
            conn.commit()
            
            message = generate_recovery_message(items, total, cart_id, "sms" if "sms" in channel else "email")
            
            if "sms" in channel and user_phone:
                send_sms(user_phone, message)
            
            if "email" in channel and user_email:
                email_body = generate_recovery_message(items, total, cart_id, "email")
                send_email(user_email, "Complete Your Umrah Booking - Special Offer", email_body)
            
            cursor.execute("UPDATE recovery_attempts SET message_sent = 1 WHERE id = ?", (recovery_id,))
        
        print(f"🔄 Recovery sent for cart {cart_id} (Attempt {attempts + 1})")
    
    conn.commit()
    conn.close()
    return len(abandoned_carts)

# ============ CHAT ENDPOINT ============
@app.post("/chat/send", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """Main chat endpoint"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM conversations WHERE session_id = ?", (chat_request.session_id,))
    conv = cursor.fetchone()
    
    if not conv:
        conv_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO conversations VALUES (?, ?, ?)", (conv_id, chat_request.session_id, datetime.now()))
    else:
        conv_id = conv[0]
    
    cursor.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", 
                   (str(uuid.uuid4()), conv_id, "user", chat_request.message, datetime.now()))
    
    intent = detect_intent(chat_request.message)
    reply = get_ai_response(chat_request.message, intent)
    
    cursor.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?)", 
                   (str(uuid.uuid4()), conv_id, "assistant", reply, datetime.now()))
    
    conn.commit()
    conn.close()
    
    return ChatResponse(reply=reply)

@app.get("/")
def root():
    return {"status": "running", "message": "Marhaba Haji Chatbot with Recovery"}

@app.get("/packages")
def get_packages():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, duration, description FROM packages")
    packages = cursor.fetchall()
    conn.close()
    return {"packages": [{"id": p[0], "name": p[1], "price": p[2], "duration": p[3], "description": p[4]} for p in packages]}

@app.get("/analytics/abandoned")
def get_abandoned_stats():
    """Get abandoned cart analytics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM carts WHERE status = 'abandoned'")
    abandoned_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM recovery_attempts WHERE converted = 1")
    recovered_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM recovery_attempts WHERE message_sent = 1")
    messages_sent = cursor.fetchone()[0]
    
    conn.close()
    
    recovery_rate = (recovered_count / abandoned_count * 100) if abandoned_count > 0 else 0
    
    return {
        "abandoned_carts": abandoned_count,
        "recovered_carts": recovered_count,
        "recovery_rate": round(recovery_rate, 2),
        "messages_sent": messages_sent
    }

# ============ DEMO ENDPOINTS ============
@app.post("/demo/abandon/{session_id}")
async def demo_abandon(session_id: str):
    """Demo: mark cart as abandoned and return items info"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, items, total_amount FROM carts WHERE session_id = ? AND status = 'active'", (session_id,))
    cart = cursor.fetchone()

    if cart:
        cart_id = cart[0]
        items = json.loads(cart[1])
        total = cart[2]

        cursor.execute('''
            UPDATE carts SET status = 'abandoned', abandoned_at = ?
            WHERE id = ?
        ''', (datetime.now(), cart_id))

        conn.commit()
        conn.close()
        return {"status": "abandoned", "cart_id": cart_id, "items": items, "total": total}

    conn.close()
    return {"status": "empty", "cart_id": None, "items": [], "total": 0}

class DemoSmsRequest(BaseModel):
    phone: str
    message: Optional[str] = None

@app.post("/api/demo-sms")
async def demo_sms(request: DemoSmsRequest):
    """Simple demo endpoint to send SMS to any number"""
    msg = request.message or "🕋 Assalamu Alaikum! This is a test SMS from Marhaba Haji Chatbot. Your booking is ready! Reply HELP for assistance."
    result = send_sms(request.phone, msg)
    return {"status": result["status"], "to": request.phone, "result": result}

# ============ SCHEDULER ============
scheduler = BackgroundScheduler()
scheduler.add_job(func=detect_abandoned_carts, trigger="interval", minutes=15, id="abandoned_cart_check")
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# ============ START SERVER ============
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("🚀 Marhaba Haji Chatbot with Recovery")
    print("📍 http://localhost:8000")
    print("📚 http://localhost:8000/docs")
    print("📱 SMS via Twilio | 📧 Email via SendGrid")
    print("🔄 Abandoned cart detection every 15 min")
    print("="*50 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)