import os
import requests
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "seirokom_secret_token")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

BASE_URL = "https://batikcromfashion.github.io/SeiRokom-Fashion-/"
WHATSAPP_URL = "https://wa.me/8801645008919"

# তোমার সব ফাইলের ফুল ম্যাপ - যত প্রশ্ন তত লিংক
PRODUCT_MAP = {
    # প্রোডাক্ট ফাইল
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
    "ছেলেদের টি-শার্ট": "product-boys-tshirt.html?from=messenger",
    "boys tshirt": "product-boys-tshirt.html?from=messenger",
    "মেয়েদের ফ্রক": "product-girls-frock.html?from=messenger",
    "girls frock": "product-girls-frock.html?from=messenger",
    "কিডস সেট": "product-kids-set.html?from=messenger",
    "কুর্তি": "product-kurti.html?from=messenger",
    "kurti": "product-kurti.html?from=messenger",
    "থ্রি-পিস": "product-ladies-3-piece.html?from=messenger",
    "3 piece": "product-ladies-3-piece.html?from=messenger",
    "শাড়ি": "product-saree.html?from=messenger",
    "saree": "product-saree.html?from=messenger",
    "শীতের": "mens-winter.html?from=messenger",
    "winter": "new-collection-winter.html?from=messenger",
    
    # ক্যাটাগরি ফাইল
    "মেনস": "mens.html?from=messenger",
    "mens": "mens.html?from=messenger",
    "ওমেনস": "womens.html?from=messenger",
    "womens": "womens.html?from=messenger",
    "নতুন কালেকশন": "new-collection.html?from=messenger",
    "new collection": "new-collection.html?from=messenger",
    
    # ইনফো ফাইল
    "কার্ট": "cart.html?from=messenger",
    "cart": "cart.html?from=messenger",
    "চেকআউট": "checkout.html?from=messenger",
    "checkout": "checkout.html?from=messenger",
    "উইশলিস্ট": "wishlist.html?from=messenger",
    "wishlist": "wishlist.html?from=messenger",
    "সাইজ": "size-guide.html?from=messenger",
    "size guide": "size-guide.html?from=messenger",
    "ডেলিভারি": "shipping-info.html?from=messenger",
    "shipping": "shipping-info.html?from=messenger",
    "অর্ডার ট্র্যাক": "order-tracking.html?from=messenger",
    "order tracking": "order-tracking.html?from=messenger",
    "রিটার্ন": "return-policy.html?from=messenger",
    "return policy": "return-policy.html?from=messenger",
    "প্রাইভেসি": "privacy-policy.html?from=messenger",
    "privacy": "privacy-policy.html?from=messenger",
    "শর্ত": "terms-and-conditions.html?from=messenger",
    "terms": "terms-and-conditions.html?from=messenger",
    "এফএকিউ": "faq.html?from=messenger",
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

SYSTEM_INSTRUCTION = """তুমি SeiRokom Fashion এর AI। M,L,XL,XXL আছে। বাংলায় ছোট উত্তর দাও।"""

@app.get("/")
def home(): return {"status": "SeiRokom Full Map Bot Running"}

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
                    smart_url, matched_key = get_smart_product(user_text)
                    bot_text = ""
                    try:
                        if model:
                            resp = model.generate_content(f"{SYSTEM_INSTRUCTION}\nUser asked about {matched_key}: {user_text}")
                            bot_text = resp.text.strip()
                    except: pass
                    if not bot_text:
                        bot_text = f"জ্বি, {matched_key} নিয়ে বিস্তারিত তথ্য নিচের লিংকে পাবেন।"
                    
                    api_url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
                    requests.post(api_url, json={"recipient": {"id": sender_id}, "message": {"text": bot_text[:1800]}})
                    requests.post(api_url, json={
                        "recipient": {"id": sender_id},
                        "message": {
                            "attachment": {
                                "type": "template",
                                "payload": {
                                    "template_type": "button",
                                    "text": f"🔗 {matched_key} এর ফাইল খুলুন:",
                                    "buttons": [
                                        {"type": "web_url", "url": smart_url, "title": f"📂 {matched_key}"},
                                        {"type": "web_url", "url": WHATSAPP_URL, "title": "💬 WhatsApp"}
                                    ]
                                }
                            }
                        }
                    })
    return Response(content="ok", status_code=200)
