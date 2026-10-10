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

# --- FIX 1: Model Name ঠিক করা ---
model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash') # latest বাদ দিলাম, এটা stable
        print("Gemini Model Ready")
    except Exception as e:
        print(f"Gemini Config Error: {e}")

BASE_URL = "https://batikcromfashion.github.io/SeiRokom-Fashion-/"
WHATSAPP_URL = "https://wa.me/8801645008919"

FOOTER_TEXT = "SeiRokom Fashion সম্পর্কে জানতে\nআরও কোন প্রশ্ন থাকলে করুন, নগদ উত্তর দিচ্ছি 🫶🇧🇩❤️🤲"

PRODUCT_MAP = {
    "পাঞ্জাবি": "product-premium-panjabi.html?from=messenger",
    "শার্ট": "product-casual-shirt.html?from=messenger",
    "পোলো": "product-polo-tshirt.html?from=messenger",
    "প্যান্ট": "product-denim-pant.html?from=messenger",
    "বাচ্চা": "kids.html?from=messenger",
    "থ্রি-পিস": "product-ladies-3-piece.html?from=messenger",
    "শাড়ি": "product-saree.html?from=messenger",
    "শীত": "new-collection-winter.html?from=messenger",
    "নতুন": "new-collection.html?from=messenger",
}

def get_smart_product(user_text):
    text = user_text.lower()
    for key, file in PRODUCT_MAP.items():
        if key.lower() in text:
            return BASE_URL + file, key
    return BASE_URL + "?from=messenger", "কালেকশন"

SYSTEM_PROMPT = """তুমি SeiRokom Fashion এর প্রফেশনাল AI।
নিয়ম: 
- কখনোই "আপনার প্রশ্নটি হলো" লিখবে না।
- User "আপনি কেমন আছেন" বললে: "ওয়ালাইকুম আসসালাম! 😊 আলহামদুলিল্লাহ আমি ভালো আছি, আপনি কেমন আছেন? SeiRokom Fashion এ আপনাকে স্বাগতম!" দিয়ে শুরু করবে।
- উত্তর 8-10 লাইনে, বাংলায়, ইমোজি সহ, প্রফেশনাল।
- শেষে বলবে "বিস্তারিত নিচের লিংকে দেখুন।"
"""

processed = set()

def get_professional_fallback(user_text):
    # এই Fallback এ কখনোই "আপনার প্রশ্নটি হলো" থাকবে না - 100% প্রফেশনাল
    if "কেমন" in user_text:
        return """ওয়ালাইকুম আসসালাম! 😊
আলহামদুলিল্লাহ, আমি ভালো আছি, আপনি কেমন আছেন?
SeiRokom Fashion এ আপনাকে স্বাগতম! ❤️
আমরা প্রিমিয়াম কোয়ালিটি পাঞ্জাবি, শার্ট, পোলো, থ্রি-পিস, শাড়ি নিয়ে কাজ করি।
আমাদের সব প্রোডাক্ট 100% কটন/প্রিমিয়াম ফেব্রিক, সাইজ M, L, XL, XXL এভেইলেবল।
খুবই আরামদায়ক এবং স্টাইলিশ ডিজাইন, যা আপনাকে দিবে আত্মবিশ্বাসী লুক।
সারা বাংলাদেশে ক্যাশ অন ডেলিভারিতে অর্ডার করতে পারবেন।
বিস্তারিত নিচের লিংকে দেখুন।"""
    else:
        return f"""আসসালামু আলাইকুম! 😊
SeiRokom Fashion এ আপনাকে স্বাগতম!
আপনার প্রশ্নের জন্য ধন্যবাদ। ❤️
আমরা প্রিমিয়াম কোয়ালিটি পাঞ্জাবি, শার্ট, পোলো, থ্রি-পিস, শাড়ি নিয়ে কাজ করি।
আমাদের সব প্রোডাক্ট 100% কটন/প্রিমিয়াম ফেব্রিক, সাইজ M, L, XL, XXL এভেইলেবল।
খুবই আরামদায়ক এবং স্টাইলিশ ডিজাইন।
সারা বাংলাদেশে ক্যাশ অন ডেলিভারি সুবিধা রয়েছে।
বিস্তারিত নিচের লিংকে দেখুন।"""

def send_reply(sender_id, user_text):
    try:
        if not user_text or user_text in processed: return
        processed.add(user_text)
        if len(processed) > 200: processed.clear()

        smart_url, matched_key = get_smart_product(user_text)
        bot_text = ""

        try:
            if model:
                prompt = f"{SYSTEM_PROMPT}\nUser প্রশ্ন: '{user_text}'\nProduct: {matched_key}\nএখন 8-10 লাইনে উত্তর দাও।"
                resp = model.generate_content(prompt)
                bot_text = resp.text.strip()
                print(f"Gemini Success: {bot_text[:50]}")
            else:
                print("Model is None, using fallback")
        except Exception as e:
            print(f"Gemini API Error: {e} - Using fallback")
            bot_text = ""

        if not bot_text:
            bot_text = get_professional_fallback(user_text)

        api_url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

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
                            {"type": "web_url", "url": WHATSAPP_URL, "title": "জরুরি WhatsApp"}
                        ]
                    }
                }
            }
        }
        r1 = requests.post(api_url, json=payload1, timeout=15)
        print(f"FB Response: {r1.status_code} {r1.text}")

        time.sleep(0.7)
        payload2 = {
            "recipient": {"id": sender_id},
            "message": {"text": FOOTER_TEXT}
        }
        requests.post(api_url, json=payload2, timeout=15)

    except Exception as e:
        print(f"Send Error: {e}")

@app.get("/")
def home(): return {"status": "SeiRokom Bot V5 - No Robotic Text"}

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
