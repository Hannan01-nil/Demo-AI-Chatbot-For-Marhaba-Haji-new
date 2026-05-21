import os
import google.genai as genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

SYSTEM_PROMPT = """You are Marhaba Haji, a friendly and knowledgeable AI assistant for Hajj and Umrah travel planning. You work for a travel agency based in Saudi Arabia.

## Your Knowledge Base

### Available Packages:
1. **Economy Umrah** — $850 for 7 days
   - 3-star hotel, shared transport, visa included
2. **Deluxe Umrah** — $1,500 for 14 days
   - 4-star hotel near Haram, private transport
3. **Premium Hajj** — $4,500 for 21 days
   - 5-star hotel, VIP service, full board

### Visa Requirements:
- Umrah visa: $150–$200
- Valid passport (6+ months validity)
- Meningitis vaccine required
- Processing time: 5–7 business days

### Additional Services:
- Hotel bookings near Haram
- Transport arrangements
- Group discounts available for 10+ people

## Guidelines:
1. Be warm, respectful, and concise — use 2–4 sentences
2. Use Islamic greetings and appropriate emojis (🕋 🤲 ✈️ 🏕️)
3. NEVER make up prices or packages — only use the listed information above
4. If asked something outside your knowledge, politely redirect to Umrah/Hajj topics
5. Always end your response with a helpful question or clear next step
6. Encourage users to add packages to their cart when they show interest
7. If user seems unsure, offer to help compare packages
8. Maintain a supportive, patient tone — many users may be first-time travelers"""


class GeminiService:
    """Service for interacting with Google Gemini AI (google.genai)"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model_name = "gemini-2.5-flash"
        self.client = None
        self._setup()

    def _setup(self):
        if self.api_key:
            key = self.api_key.strip()
            self.client = genai.Client(api_key=key)

    def is_available(self) -> bool:
        return self.client is not None and bool(self.api_key)

    def generate_response(self, message: str, conversation_history: list = None) -> str:
        if not self.is_available():
            raise RuntimeError("Gemini AI is not configured. Set GOOGLE_API_KEY in .env")

        try:
            if conversation_history and len(conversation_history) > 0:
                chat = self.client.chats.create(
                    model=self.model_name,
                    history=conversation_history,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
                )
                response = chat.send_message(message)
            else:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=message,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
                )

            return response.text.strip()

        except Exception as e:
            error_msg = str(e)
            if "API_KEY" in error_msg or "API key" in error_msg or "PERMISSION_DENIED" in error_msg:
                raise RuntimeError("Invalid Gemini API key. Check GOOGLE_API_KEY in .env")
            if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
                raise RuntimeError("Gemini API free quota exhausted. Enable billing at https://aistudio.google.com or use a new API key.")
            if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                raise RuntimeError("Gemini API rate limit reached. Please wait and try again.")
            if "NOT_FOUND" in error_msg or "not found" in error_msg:
                raise RuntimeError(f"Gemini model '{self.model_name}' not found. Check model availability.")
            raise RuntimeError(f"Gemini AI error: {error_msg}")

    @staticmethod
    def format_history_for_gemini(messages: list) -> list:
        formatted = []
        for msg in messages[-20:]:
            role = "user" if msg["role"] == "user" else "model"
            formatted.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])]
            ))
        return formatted


gemini_service = GeminiService()
