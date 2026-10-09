import os
import requests
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "seirokom_secret_token")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

SYSTEM_INSTRUCTION = """
তুমি SeiRokom Fashion এর AI সেলস অ্যাসিস্ট্যান্ট।
তোমার তথ্যের মূল উৎস হলো: https://batikcromfashion.github.io/SeiRokom-Fashion-/

নিয়ম:
1. কাস্টমারের প্রশ্ন বুঝে ওই ওয়েবসাইট অনুযায়ী সুন্দর বাংলায় উত্তর দাও।
2. যদি ওয়েবসাইটের বাইরে প্রশ্ন করে (যেমন আবহাওয়া, গল্প), তাহলেও সুন্দর করে উত্তর দিবে।
3. বাচ্চাদের সাইজ চাইলে বলবে: আমাদের আপাতত বড়দের M,L,XL,XXL আছে, বাচ্চাদের কালেকশন শীঘ্রই আসবে।
4. কখনো "আপনি '...' বলেছেন" এই লাইনটা বলবে না।
5. উত্তর ছোট, 2-3 লাইনে রাখবে।
"""

WEBSITE_URL = "https://batikcromfashion.github.io/SeiRokom-Fashion-/"
WHATSAPP_URL = "https://wa.me/8801645008919"

@app.get("/")
def home():
    return {"status": "SeiRokom AI Backend is running OK!"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return Response(content=params.get("hub.challenge"), status_code=200)
    return Response(status_code=403)

@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event.get("sender", {}).get("id")
                message = event.get("message", {})
                if sender_id and "text" in message and not message.get("is_echo"):
                    user_text = message["text"]
                    bot_text = ""
                    try:
                        if model:
                            resp = model.generate_content(f"{SYSTEM_INSTRUCTION}\n\nUser: {user_text}")
                            bot_text = resp.text.strip()
                    except Exception as e:
                        print(f"GEMINI ERROR: {e}")
                    
                    if not bot_text:
                        bot_text = f"আসসালামু আলাইকুম! '{user_text}' এর জন্য ধন্যবাদ। আমাদের প্রিমিয়াম শার্ট ও পাঞ্জাবি আছে।"

                    url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
                    payload1 = {"recipient": {"id": sender_id}, "message": {"text": bot_text[:1800]}}
                    requests.post(url, json=payload1)
                    
                    payload2 = {
                        "recipient": {"id": sender_id},
                        "message": {
                            "attachment": {
                                "type": "template",
                                "payload": {
                                    "template_type": "button",
                                    "text": "নিচে থেকে অপশন সিলেক্ট করুন:",
                                    "buttons": [
                                        {"type": "web_url", "url": WEBSITE_URL, "title": "🛍️ বিস্তারিত দেখুন"},
                                        {"type": "web_url", "url": WHATSAPP_URL, "title": "💬 হোয়াটসঅ্যাপে যোগাযোগ"}
                                    ]
                                }
                            }
                        }
                    }
                    requests.post(url, json=payload2)
    return Response(content="ok", status_code=200)
