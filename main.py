import os
import requests
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from google import genai

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

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

SYSTEM_INSTRUCTION = """
তুমি SeiRokom Fashion এর AI অ্যাসিস্ট্যান্ট।
তোমার তথ্যের মূল উৎস: https://batikcromfashion.github.io/SeiRokom-Fashion-/
তোমার কাজ:
1. কাস্টমারের প্রশ্ন বুঝে ওই ওয়েবসাইটের প্রোডাক্ট (শার্ট, পাঞ্জাবি) অনুযায়ী সুন্দর বাংলায় উত্তর দাও।
2. যদি বাচ্চাদের প্রোডাক্ট চায়, বলো: আপাতত আমাদের বড়দের M,L,XL,XXL আছে, বাচ্চাদের কালেকশন খুব শিগ্রই আসবে।
3. একই বাক্য বারবার বলবে না। "আপনি '...' বলেছেন" এই লাইনটা বলবে না।
4. সালাম দিলে ভদ্রভাবে সালামের উত্তর দাও।
5. উত্তর ছোট, সুন্দর ও বন্ধুসুলভ রাখো।
"""

WEBSITE_URL = "https://batikcromfashion.github.io/SeiRokom-Fashion-/"
WHATSAPP_URL = "https://wa.me/8801645008919"

@app.get("/")
def home():
    return {"status": "SeiRokom AI Backend is running fully!"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return Response(content=params.get("hub.challenge"), status_code=200)
    return Response(status_code=403)

@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    print(f"Webhook: {data}")
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event.get("sender", {}).get("id")
                message = event.get("message", {})
                if sender_id and "text" in message:
                    user_text = message["text"]
                    try:
                        resp = client.models.generate_content(
                            model="gemini-1.5-flash",
                            contents=f"{SYSTEM_INSTRUCTION}\n\nUser: {user_text}"
                        )
                        bot_text = resp.text.strip()
                    except Exception as e:
                        print(f"GEMINI ERROR: {e}")
                        bot_text = f"আসসালামু আলাইকুম! আমাদের প্রিমিয়াম শার্ট ও পাঞ্জাবি কালেকশন আছে M,L,XL,XXL সাইজে। আপনি কোনটা দেখতে চান?"

                    # 1st message - AI reply
                    url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
                    payload1 = {
                        "recipient": {"id": sender_id},
                        "message": {"text": bot_text[:1800]}
                    }
                    requests.post(url, json=payload1)
                    
                    # 2nd message - Buttons
                    payload2 = {
                        "recipient": {"id": sender_id},
                        "message": {
                            "attachment": {
                                "type": "template",
                                "payload": {
                                    "template_type": "button",
                                    "text": "আরো কালেকশন দেখতে বা অর্ডার করতে নিচের বাটনে ক্লিক করুন:",
                                    "buttons": [
                                        {
                                            "type": "web_url",
                                            "url": WEBSITE_URL,
                                            "title": "🛍️ বিস্তারিত দেখুন"
                                        },
                                        {
                                            "type": "web_url",
                                            "url": WHATSAPP_URL,
                                            "title": "💬 হোয়াটসঅ্যাপে যোগাযোগ"
                                        }
                                    ]
                                }
                            }
                        }
                    }
                    r = requests.post(url, json=payload2)
                    print(f"FB Send: {r.status_code}")

    return Response(content="ok", status_code=200)
