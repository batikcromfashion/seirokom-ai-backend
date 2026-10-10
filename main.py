import os
import requests
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

# ফুটারে তোমার চাওয়া লেখা
FOOTER_TEXT = "SeiRokom Fashion সম্পর্কে জানতে\nআরও কোন প্রশ্ন থাকলে করুন, নগদ উত্তর দিচ্ছি 🫶🇧🇩❤️🤲"

PRODUCT_MAP = {
    "পাঞ্জাবি": "product-premium-panjabi.html?from=messenger",
    "premium panjabi": "product-premium-panjabi.html?from=messenger",
    "শার্ট": "product-casual-shirt.html?from=messenger",
    "casual shirt": "product-casual-shirt.html?from=messenger",
    "পোলো": "product-polo-tshirt.html?from=messenger",
    "polo": "product-polo-tshirt.html?from=messenger",
    "প্যান্ট": "product-denim-pant.html?from=messenger",
    "বাচ্চা": "kids.html?from=messenger",
    "কুর্তি": "product-kurti.html?from=messenger",
    "থ্রি-পিস": "product-ladies-3-piece.html?from=messenger",
    "শাড়ি": "product-saree.html?from=messenger",
    "শীত": "new-collection-winter.html?from=messenger",
    "নতুন": "new-collection.html?from=messenger",
    "ছেলেদের": "mens.html?from=messenger",
    "মেয়েদের": "womens.html?from=messenger",
    "যোগাযোগ": "contact.html?from=messenger",
    "হোম": "index.html?from=messenger",
}

def get_smart_product(user_text):
    text = user_text.lower()
    for key, file in PRODUCT_MAP.items():
        if key.lower() in text:
            return BASE_URL + file, key
    return BASE_URL + "?from=messenger", "হোম পেজ"

SYSTEM_PROMPT = """তুমি SeiRokom Fashion এর সিনিয়র প্রফেশনাল কাস্টমার সাপোর্ট AI।
তোমার কাজ:
1. User যা প্রশ্ন করবে, তার সাথে 100% মিল রেখে উত্তর দিবে। যদি সালাম দেয়, সালামের উত্তর দিবে। যদি দাম জিজ্ঞেস করে, দাম নিয়ে বলবে। যদি কেমন আছো বলে, তার উত্তর দিবে।
2. উত্তর অবশ্যই 8 থেকে 10 লাইনের মধ্যে, প্রফেশনাল, বন্ধুত্বপূর্ণ, ইমোজি সহ, বাংলায়।
3. উত্তরে প্রোডাক্টের ফেব্রিক, সাইজ M,L,XL,XXL, আরামদায়ক, স্টাইলিশ এইগুলো উল্লেখ করবে।
4. কখনোই "হোম পেজ নিয়ে বিস্তারিত" এই একই কথা বারবার বলবে না। প্রশ্ন অনুযায়ী উত্তর বদলাবে।
5. শেষ লাইনে বলবে: বিস্তারিত নিচের লিংকে দেখুন।
"""

processed = set()

def send_reply(sender_id, user_text):
    try:
        if user_text in processed: return
        processed.add(user_text)
        if len(processed) > 200: processed.clear()

        smart_url, matched_key = get_smart_product(user_text)
        
        # সালাম চেক
        is_greeting_only = user_text.strip().lower() in ["আসসালামু আলাইকুম", "assalamu alaikum", "সালাম", "হ্যালো", "hello", "hi"]
        
        bot_text = ""
        try:
            if model:
                full_prompt = f"{SYSTEM_PROMPT}\n\nUser এর প্রশ্ন: '{user_text}'\nMatched Product: {matched_key}\n\nএখন 8/10 লাইনে প্রফেশনাল উত্তর দাও বাংলায়।"
                resp = model.generate_content(full_prompt)
                bot_text = resp.text.strip()
        except Exception as e:
            print(f"Gemini Error: {e}")

        if not bot_text:
            bot_text = f"ওয়ালাইকুম আসসালাম! 😊\nআপনার প্রশ্নটি হলো: {user_text}\n\nSeiRokom Fashion এ আমরা প্রিমিয়াম কোয়ালিটি পাঞ্জাবি, শার্ট, পোলো, থ্রি-পিস, শাড়ি সহ সব ধরনের ফ্যাশন নিয়ে কাজ করি।\nআমাদের সব প্রোডাক্ট 100% কটন/প্রিমিয়াম ফেব্রিক, সাইজ M, L, XL, XXL এভেইলেবল।\nখুবই আরামদায়ক এবং স্টাইলিশ ডিজাইন।\nআপনি অনলাইনে অর্ডার করতে পারবেন সারা বাংলাদেশে ক্যাশ অন ডেলিভারি।\nবিস্তারিত নিচের লিংকে দেখুন।"

        api_url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

        # 1. প্রথমে 8/10 লাইনের প্রফেশনাল উত্তর + 2টা বাটন
        payload1 = {
            "recipient": {"id": sender_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": bot_text[:640],
                        "buttons": [
                            {"type": "web_url", "url": smart_url, "title": f"📁 {matched_key} দেখুন"},
                            {"type": "web_url", "url": WHATSAPP_URL, "title": "💬 WhatsApp"}
                        ]
                    }
                }
            }
        }
        requests.post(api_url, json=payload1, timeout=15)

        # 2. বাটনের নিচে তোমার চাওয়া ছোট 2 লাইনের লেখা - যাতে বিভ্রান্ত না হয়
        import time
        time.sleep(0.5)
        payload2 = {
            "recipient": {"id": sender_id},
            "message": {"text": FOOTER_TEXT}
        }
        requests.post(api_url, json=payload2, timeout=15)

    except Exception as e:
        print(f"Send Error: {e}")

@app.get("/")
def home(): return {"status": "SeiRokom Final Pro Bot Running"}

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
