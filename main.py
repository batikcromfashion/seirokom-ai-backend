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

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
else:
    model = None

BASE_URL = "https://batikcromfashion.github.io/SeiRokom-Fashion-/"
WHATSAPP_URL = "https://wa.me/8801645008919"

# ফুটারে তোমার চাওয়া ২ লাইনের লেখা
FOOTER_TEXT = "SeiRokom Fashion সম্পর্কে জানতে\nআরও কোন প্রশ্ন থাকলে করুন, নগদ উত্তর দিচ্ছি 🫶🇧🇩❤️🤲"

PRODUCT_MAP = {
    "পাঞ্জাবি": "product-premium-panjabi.html?from=messenger",
    "premium panjabi": "product-premium-panjabi.html?from=messenger",
    "পাঞ্জাবি পাঞ্জাবি": "product-premium-panjabi.html?from=messenger",
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

# ১০০% মানবিক এবং প্রফেশনাল Prompt
SYSTEM_PROMPT = """তুমি SeiRokom Fashion এর সিনিয়র, ভদ্র, প্রফেশনাল AI সাপোর্ট।

কঠোর নিয়ম:
1. কখনোই "আপনার প্রশ্নটি হলো:" এই বাক্যটি লিখবে না। কখনোই না।
2. যদি User বলে "আপনি কেমন আছেন" -> উত্তর: "ওয়ালাইকুম আসসালাম! 😊 আলহামদুলিল্লাহ, আমি ভালো আছি। আপনি কেমন আছেন? SeiRokom Fashion এ আপনাকে স্বাগতম! আপনার জন্য কিভাবে সাহায্য করতে পারি?" তারপর ফ্যাশন নিয়ে 4-5 লাইন যোগ করো।
3. যদি সালাম দেয়, সুন্দরভাবে ওয়ালাইকুম আসসালাম দিয়ে শুরু করো।
4. উত্তর অবশ্যই 8 থেকে 10 লাইনে, বাংলায়, প্রফেশনাল, বন্ধুত্বপূর্ণ, ইমোজি সহ।
5. প্রতিটি উত্তরে আমাদের প্রোডাক্টের গুণগত মান - 100% কটন/প্রিমিয়াম ফেব্রিক, সাইজ M, L, XL, XXL, আরামদায়ক, স্টাইলিশ, সারা বাংলাদেশে ক্যাশ অন ডেলিভারি - এইগুলো স্মার্টভাবে যোগ করো।
6. প্রশ্নের সাথে 100% মিল রেখে উত্তর দাও, একই উত্তর বারবার দিও না।
7. শেষ লাইনে বলবে: "বিস্তারিত নিচের লিংকে দেখুন।"
"""

processed = set()

def send_reply(sender_id, user_text):
    try:
        if not user_text or user_text in processed: 
            return
        processed.add(user_text)
        if len(processed) > 200: 
            processed.clear()

        smart_url, matched_key = get_smart_product(user_text)
        bot_text = ""

        try:
            if model:
                full_prompt = f"{SYSTEM_PROMPT}\n\nUser এর বর্তমান প্রশ্ন: '{user_text}'\nএই প্রশ্নের সাথে মিল রেখে এখন 8/10 লাইনে সেরা প্রফেশনাল উত্তর দাও।"
                resp = model.generate_content(full_prompt)
                bot_text = resp.text.strip()
        except Exception as e:
            print(f"Gemini Error: {e}")

        # Fallback - যদি Gemini Fail করে, তাও রোবোটিক লেখা আসবে না
        if not bot_text:
            if "কেমন" in user_text:
                bot_text = "ওয়ালাইকুম আসসালাম! 😊\nআলহামদুলিল্লাহ, আমি ভালো আছি। আপনি কেমন আছেন?\n\nSeiRokom Fashion এ আপনাকে স্বাগতম! ❤️\nআমরা প্রিমিয়াম কোয়ালিটি পাঞ্জাবি, শার্ট, পোলো, থ্রি-পিস, শাড়ি নিয়ে কাজ করি।\nআমাদের সব প্রোডাক্ট 100% কটন/প্রিমিয়াম ফেব্রিক, সাইজ M, L, XL, XXL এভেইলেবল।\nখুবই আরামদায়ক এবং স্টাইলিশ ডিজাইন, যা আপনাকে দিবে প্রিমিয়াম লুক।\nসারা বাংলাদেশে ক্যাশ অন ডেলিভারি পাচ্ছেন।\nবিস্তারিত নিচের লিংকে দেখুন।"
            else:
                bot_text = f"আসসালামু আলাইকুম! 😊\nআপনাকে SeiRokom Fashion এ স্বাগতম!\n\nআমরা প্রিমিয়াম কোয়ালিটি পাঞ্জাবি, শার্ট, পোলো, থ্রি-পিস, শাড়ি সহ সব ফ্যাশন নিয়ে কাজ করি।\nআমাদের প্রোডাক্ট 100% কটন/প্রিমিয়াম ফেব্রিক, সাইজ M, L, XL, XXL এভেইলেবল।\nখুবই আরামদায়ক এবং স্টাইলিশ ডিজাইন।\nআপনি ঘরে বসে সারা বাংলাদেশে ক্যাশ অন ডেলিভারিতে অর্ডার করতে পারবেন।\nবিস্তারিত নিচের লিংকে দেখুন।"

        api_url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"

        # 1. 8/10 লাইনের উত্তর + 2টা বাটন (তোমার চাওয়া WhatsApp লেখা সহ)
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
                            {"type": "web_url", "url": WHATSAPP_URL, "title": "জরুরি প্রয়োজনে WhatsApp"}
                        ]
                    }
                }
            }
        }
        r1 = requests.post(api_url, json=payload1, timeout=15)
        print(f"Button Sent: {r1.status_code}")

        # 2. বাটনের নিচে 2 লাইনের ছোট ফুটার
        time.sleep(0.7)
        payload2 = {
            "recipient": {"id": sender_id},
            "message": {"text": FOOTER_TEXT}
        }
        requests.post(api_url, json=payload2, timeout=15)

    except Exception as e:
        print(f"Send Error: {e}")

@app.get("/")
def home(): return {"status": "SeiRokom Final Pro Bot Running - V4"}

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
