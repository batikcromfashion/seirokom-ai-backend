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
তুমি SeiRokom Fashion এর AI অ্যাসিস্ট্যান্ট।
ওয়েবসাইট: https://batikcromfashion.github.io/SeiRokom-Fashion-/
নিয়ম: বাংলায় ছোট করে উত্তর দাও, M,L,XL,XXL সাইজ আছে বলো।
"আপনি '...' বলেছেন" বলবে না।
"""

BASE_URL = "https://batikcromfashion.github.io/SeiRokom-Fashion-/"
WHATSAPP_URL = "https://wa.me/8801645008919"

# স্মার্ট লিংক ফাংশন
def get_smart_link(user_text):
    text = user_text.lower()
    # পাঞ্জাবি চেক
    if "পাঞ্জাবি" in text or "পাঞ্জাবী" in text or "panjabi" in text or "punjabi" in text:
        return f"{BASE_URL}?search=পাঞ্জাবি"
    # শার্ট চেক
    elif "শার্ট" in text or "shirt" in text or "টি-শার্ট" in text or "t-shirt" in text or "tshirt" in text:
        return f"{BASE_URL}?search=শার্ট"
    # পোলো
    elif "পোলো" in text or "polo" in text:
        return f"{BASE_URL}?search=পোলো"
    # ডিফল্ট
    else:
        return BASE_URL

@app.get("/")
def home():
    return {"status": "SeiRokom Smart Link Bot is running!"}

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
                    
                    # স্মার্ট লিংক বের করা
                    smart_website_url = get_smart_link(user_text)
                    
                    bot_text = ""
                    try:
                        if model:
                            resp = model.generate_content(f"{SYSTEM_INSTRUCTION}\n\nUser: {user_text}")
                            bot_text = resp.text.strip()
                    except Exception as e:
                        print(f"GEMINI ERROR: {e}")
                    
                    if not bot_text:
                        bot_text = f"আপনার প্রশ্নের জন্য ধন্যবাদ! আমাদের প্রিমিয়াম কালেকশন আছে M,L,XL,XXL সাইজে।"

                    url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
                    payload1 = {"recipient": {"id": sender_id}, "message": {"text": bot_text[:1800]}}
                    requests.post(url, json=payload1)
                    
                    # স্মার্ট বাটন
                    if "পাঞ্জাবি" in smart_website_url:
                        button_title = "🟢 পাঞ্জাবি দেখুন"
                    elif "শার্ট" in smart_website_url:
                        button_title = "👕 শার্ট দেখুন"
                    else:
                        button_title = "🛍️ বিস্তারিত দেখুন"

                    payload2 = {
                        "recipient": {"id": sender_id},
                        "message": {
                            "attachment": {
                                "type": "template",
                                "payload": {
                                    "template_type": "button",
                                    "text": "নিচে থেকে সিলেক্ট করুন:",
                                    "buttons": [
                                        {"type": "web_url", "url": smart_website_url, "title": button_title},
                                        {"type": "web_url", "url": WHATSAPP_URL, "title": "💬 WhatsApp করুন"}
                                    ]
                                }
                            }
                        }
                    }
                    requests.post(url, json=payload2)
    return Response(content="ok", status_code=200)
