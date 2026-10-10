import os
import requests
import time
from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "seirokom_secret_token")

model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Gemini Error: {e}")

BASE_URL = "https://batikcromfashion.github.io/SeiRokom-Fashion-/"
WHATSAPP_URL = "https://wa.me/8801645008919"
FOOTER_TEXT = "SeiRokom Fashion সম্পর্কে জানতে\nআরও কোন প্রশ্ন থাকলে করুন, নগদ উত্তর দিচ্ছি 🫶🇧🇩❤️🤲"

# --- FIX: সব বানান যোগ করা হলো, যাতে ভুল বানানেও কাজ করে ---
SMART_MAP = [
    # পাঞ্জাবি - সব বানান
    (["পাঞ্জাবি", "পাঞ্জাবী", "পানজাবি", "পানজাবী", "panjabi", "punjabi"], "product-premium-panjabi.html?from=messenger", "পাঞ্জাবি"),
    # শার্ট
    (["শার্ট", "শাট", "shirt", "শার্টের"], "product-casual-shirt.html?from=messenger", "শার্ট"),
    # পোলো
    (["পোলো", "polo"], "product-polo-tshirt.html?from=messenger", "পোলো"),
    # প্যান্ট
    (["প্যান্ট", "পেন্ট", "pant", "ডেনিম"], "product-denim-pant.html?from=messenger", "প্যান্ট"),
    # বাচ্চাদের
    (["বাচ্চা", "বাচ্চাদের", "kids", "শিশু"], "kids.html?from=messenger", "বাচ্চাদের"),
    # থ্রি-পিস
    (["থ্রি-পিস", "থ্রি পিস", "3-piece", "3 piece"], "product-ladies-3-piece.html?from=messenger", "থ্রি-পিস"),
    # শাড়ি
    (["শাড়ি", "শারি", "saree", "শাড়ির"], "product-saree.html?from=messenger", "শাড়ি"),
    # কুর্তি
    (["কুর্তি", "kurti"], "product-kurti.html?from=messenger", "কুর্তি"),
    # শীত
    (["শীত", "winter", "জ্যাকেট"], "new-collection-winter.html?from=messenger", "শীতের"),
    # নতুন
    (["নতুন", "new collection"], "new-collection.html?from=messenger", "নতুন"),
    # ছেলেদের
    (["ছেলেদের", "mens", "ছেলে"], "mens.html?from=messenger", "ছেলেদের"),
    # মেয়েদের
    (["মেয়েদের", "womens", "মেয়ে"], "womens.html?from=messenger", "মেয়েদের"),
]

def get_smart_product(user_text):
    text = user_text.lower().strip()
    # প্রথমে প্রোডাক্ট চেক
    for keywords, file, nice_name in SMART_MAP:
        for kw in keywords:
            if kw.lower() in text:
                return BASE_URL + file, nice_name
    
    # যদি SeiRokom Fashion / Website / হোমপেজ নিয়ে প্রশ্ন করে, তখনই শুধু হোমপেজ
    home_keywords = ["seirokom", "সেইরকম", "website", "ওয়েবসাইট", "হোমপেজ", "home page", "homepage"]
    for kw in home_keywords:
        if kw in text:
            return BASE_URL + "?from=messenger", "হোমপেজ"
            
    # কিছু না মিললে হোমপেজ (Default)
    return BASE_URL + "?from=messenger", "হোমপেজ"

SYSTEM_PROMPT = """তুমি SeiRokom Fashion এর প্রফেশনাল AI।
User যে প্রোডাক্ট নিয়ে প্রশ্ন করবে, সেই প্রোডাক্ট নিয়েই উত্তর দিবে।
যেমন পাঞ্জাবি নিয়ে প্রশ্ন করলে, পাঞ্জাবির ফেব্রিক, সাইজ, দাম, কোয়ালিটি নিয়ে বলবে।
নিয়ম:
- কখনোই "আপনার প্রশ্নটি হলো" লিখবে না।
- 8-10 লাইনে, বাংলায়, প্রফেশনাল, ইমোজি সহ।
- শেষে বলবে "বিস্তারিত নিচের লিংকে দেখুন।"
"""

processed = set()

def get_fallback(product_name, user_text):
    if "পাঞ্জাবি" in product_name:
        return f"""ওয়ালাইকুম আসসালাম! 😊
আপনি {product_name}র দাম সম্পর্কে জানতে চেয়েছেন, ধন্যবাদ! ❤️
SeiRokom Fashion এ প্রিমিয়াম পাঞ্জাবি কালেকশন রয়েছে।
100% কটন/প্রিমিয়াম ফেব্রিক, সাইজ M, L, XL, XXL এভেইলেবল।
খুবই আরামদায়ক এবং স্টাইলিশ ডিজাইন, যা আপনাকে দিবে রাজকীয় লুক। 👑
দাম: ৳650 থেকে ৳1250 এর মধ্যে (ডিজাইন ভেদে)।
সারা বাংলাদেশে ক্যাশ অন ডেলিভারিতে পাবেন।
বিস্তারিত নিচের লিংকে দেখুন।"""
    else:
        return f"""আসসালামু আলাইকুম! 😊
আপনি {product_name} সম্পর্কে জানতে চেয়েছেন।
SeiRokom Fashion এ আমরা প্রিমিয়াম কোয়ালিটি {product_name} নিয়ে কাজ করি।
100% কটন/প্রিমিয়াম ফেব্রিক, সাইজ M, L, XL, XXL এভেইলেবল।
খুবই আরামদায়ক এবং স্টাইলিশ ডিজাইন।
সারা বাংলাদেশে ক্যাশ অন ডেলিভারি সুবিধা রয়েছে।
বিস্তারিত নিচের লিংকে দেখুন।"""

def send_reply(sender_id, user_text):
    try:
        if not user_text or user_text in processed: return
        processed.add(user_text)
        if len(processed) > 200: processed.clear()

        smart_url, product_name = get_smart_product(user_text)
        bot_text = ""

        try:
            if model:
                prompt = f"{SYSTEM_PROMPT}\nUser প্রশ্ন: '{user_text}'\nProduct: {product_name}\nএই প্রোডাক্ট নিয়ে 8-10 লাইনে উত্তর দাও।"
                resp = model.generate_content(prompt)
                bot_text = resp.text.strip()
        except Exception as e:
            print(f"Gemini Error: {e}")

        if not bot_text:
            bot_text = get_fallback(product_name, user_text)

        api_url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

        # বাটনে এখন ডাইনামিক লেখা আসবে - যেমন পাঞ্জাবি দেখুন
        payload1 = {
            "recipient": {"id": sender_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": bot_text[:640],
                        "buttons": [
                            {"type": "web_url", "url": smart_url, "title": f"📁 {product_name} দেখুন"},
                            {"type": "web_url", "url": WHATSAPP_URL, "title": "জরুরি WhatsApp"}
                        ]
                    }
                }
            }
        }
        requests.post(api_url, json=payload1, timeout=15)

        time.sleep(0.7)
        payload2 = {
            "recipient": {"id": sender_id},
            "message": {"text": FOOTER_TEXT}
        }
        requests.post(api_url, json=payload2, timeout=15)

    except Exception as e:
        print(f"Send Error: {e}")

@app.get("/")
def home(): return {"status": "SeiRokom V6 Smart Mapping Running"}

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
                    background_tasks.add_task(send_reply, sender_id, message["text"])
    return Response(content="EVENT_RECEIVED", status_code=200)
