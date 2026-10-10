import os
import requests
import asyncio
from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "seirokom_secret_token")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
else:
    model = None

BASE_URL = "https://batikcromfashion.github.io/SeiRokom-Fashion-/"
WHATSAPP_URL = "https://wa.me/8801645008919"

# তোমার ম্যাপ আগের মতই থাকবে
PRODUCT_MAP = {
    "পাঞ্জাবি": "product-premium-panjabi.html?from=messenger",
    "premium panjabi": "product-premium-panjabi.html?from=messenger",
    "শার্ট": "product-casual-shirt.html?from=messenger",
    "casual shirt": "product-casual-shirt.html?from=messenger",
    "পোলো": "product-polo-tshirt.html?from=messenger",
    "polo tshirt": "product-polo-tshirt.html?from=messenger",
    "প্যান্ট": "product-denim-pant.html?from=messenger",
    "denim pant": "product-denim-pant.html?from=messenger",
    "বাচ্চা": "kids.html?from=messenger",
    "kids": "kids.html?from=messenger",
    "বয়েজ টি-শার্ট": "product-boys-tshirt.html?from=messenger",
    "boys tshirt": "product-boys-tshirt.html?from=messenger",
    "গার্লস ফ্রক": "product-girls-frock.html?from=messenger",
    "girls frock": "product-girls-frock.html?from=messenger",
    "কিডস সেট": "product-kids-set.html?from=messenger",
    "কুর্তি": "product-kurti.html?from=messenger",
    "kurti": "product-kurti.html?from=messenger",
    "থ্রি-পিস": "product-ladies-3-piece.html?from=messenger",
    "3 piece": "product-ladies-3-piece.html?from=messenger",
    "শাড়ি": "product-saree.html?from=messenger",
    "saree": "product-saree.html?from=messenger",
    "শীতের": "mens-winter.html?from=messenger",
    "winter": "new-collection-winter.html?from=messenger",
    "ছেলেদের": "mens.html?from=messenger",
    "mens": "mens.html?from=messenger",
    "মেয়েদের": "womens.html?from=messenger",
    "womens": "womens.html?from=messenger",
    "নতুন কালেকশন": "new-collection.html?from=messenger",
    "new collection": "new-collection.html?from=messenger",
    "হোম": "index.html?from=messenger",
    "home": "index.html?from=messenger",
    "কার্ট": "cart.html?from=messenger",
    "cart": "cart.html?from=messenger",
    "চেকআউট": "checkout.html?from=messenger",
    "checkout": "checkout.html?from=messenger",
    "উইশলিস্ট": "wishlist.html?from=messenger",
    "wishlist": "wishlist.html?from=messenger",
    "সাইজ": "size-guide.html?from=messenger",
    "size guide": "size-guide.html?from=messenger",
    "শিপিং": "shipping-info.html?from=messenger",
    "shipping": "shipping-info.html?from=messenger",
    "অর্ডার ট্র্যাক": "order-tracking.html?from=messenger",
    "order tracking": "order-tracking.html?from=messenger",
    "রিটার্ন": "return-policy.html?from=messenger",
    "return policy": "return-policy.html?from=messenger",
    "প্রাইভেসি": "privacy-policy.html?from=messenger",
    "privacy": "privacy-policy.html?from=messenger",
    "শর্ত": "terms-and-conditions.html?from=messenger",
    "terms": "terms-and-conditions.html?from=messenger",
    "জিজ্ঞাসা": "faq.html?from=messenger",
    "faq": "faq.html?from=messenger",
    "যোগাযোগ": "contact.html?from=messenger",
    "contact": "contact.html?from=messenger",
    "আমাদের সম্পর্কে": "about.html?from=messenger",
    "about": "about.html?from=messenger",
    "ডিলার": "stock-partner.html?from=messenger",
    "ড্রপশিপ": "dropship.html?from=messenger",
}

def get_smart_product(user_text):
    text = user_text.lower()
    for key, file in PRODUCT_MAP.items():
        if key.lower() in text:
            return BASE_URL + file, key
    return BASE_URL + "?from=messenger", "হোম পেজ"

# *** এইখানে আসল পরিবর্তন - প্রফেশনাল এবং বিস্তারিত ***
SYSTEM_INSTRUCTION = """তুমি SeiRokom Fashion এর প্রফেশনাল AI সহকারী।
তুমি বাংলায় সুন্দর, ভদ্র, এবং বিস্তারিত উত্তর দিবে। কখনোই ছোট বা শর্টকাট উত্তর দিবে না।
প্রতিটি উত্তরে প্রোডাক্টের ফেব্রিক, সাইজ M,L,XL,XXL, দাম, এবং কেন কিনবে তা বুঝিয়ে বলবে।
ইমোজি ব্যবহার করবে এবং শেষে সবসময় বলবে বিস্তারিত তথ্য নিচের লিংকে পাবেন।"""

# ডাবল মেসেজ আটকানোর জন্য
processed_messages = set()

def send_reply(sender_id, user_text):
    try:
        if user_text in processed_messages:
            return
        processed_messages.add(user_text)
        if len(processed_messages) > 100:
            processed_messages.clear()

        smart_url, matched_key = get_smart_product(user_text)
        bot_text = ""
        try:
            if model:
                resp = model.generate_content(f"{SYSTEM_INSTRUCTION}\nUser asked about {matched_key}: {user_text}\nAnswer in Bengali professionally in 3-4 lines.")
                bot_text = resp.text.strip()
        except:
            pass
        
        if not bot_text:
            bot_text = f"জ্বি, {matched_key} নিয়ে বিস্তারিত তথ্য নিচের লিংকে পাবেন।"

        api_url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
        
        # শুধু ১টা মেসেজ পাঠাবো - বাটন সহ, ডাবল না
        payload = {
            "recipient": {"id": sender_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": bot_text[:640],
                        "buttons": [
                            {"type": "web_url", "url": smart_url, "title": f"📁 {matched_key}"},
                            {"type": "web_url", "url": WHATSAPP_URL, "title": "💬 WhatsApp"}
                        ]
                    }
                }
            }
        }
        requests.post(api_url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error: {e}")

@app.get("/")
def home(): return {"status": "SeiRokom Full Map Bot Running - Fixed"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return Response(content=params.get("hub.challenge"), status_code=200)
    return Response(status_code=403)

@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event.get("sender", {}).get("id")
                message = event.get("message", {})
                if sender_id and "text" in message and not message.get("is_echo"):
                    user_text = message["text"]
                    # Background এ পাঠাবো, তাই Facebook সাথে সাথে 200 পাবে এবং Retry করবে না - ডাবল বন্ধ
                    background_tasks.add_task(send_reply, sender_id, user_text)
    # সাথে সাথে OK বলে দাও
    return Response(content="EVENT_RECEIVED", status_code=200)
