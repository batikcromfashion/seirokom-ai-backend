import os
import requests
import google.generativeai as genai
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

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

SYSTEM_INSTRUCTION = """
আপনি SeiRokom Fashion (সেইরকম ফ্যাশন)-এর অফিশিয়াল AI অ্যাসিস্ট্যান্ট।
গ্রাহকের সাথে সবসময় অমায়িক, বন্ধুত্বপূর্ণ, আনন্দময় ও স্পষ্ট বাংলায় কথা বলুন।
আমাদের এখানে ছেলেদের শার্ট, পাঞ্জাবি, পলো টি-শার্ট, টি-শার্ট এবং শীতের কালেকশন পাওয়া যায়।
সাইজ: M, L, XL, XXL। ডেলিভারি 2-3 দিন। 
যদি কেউ বলে 'কেমন আছেন' তাহলে সুন্দর করে উত্তর দাও, একই কথা বারবার বলবে না।
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

@app.get("/")
def home():
    return {"status": "SeiRokom AI Backend is running fully!"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, status_code=200)
    return Response(status_code=403)

@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    print(f"Webhook data: {data}")
    
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event.get("sender", {}).get("id")
                message = event.get("message", {})
                
                if sender_id and "text" in message:
                    user_text = message["text"]
                    print(f"User {sender_id}: {user_text}")

                    try:
                        # এখানেই আসল AI কল
                        response = model.generate_content(user_text)
                        bot_text = response.text.strip()
                        print(f"Gemini Reply: {bot_text}")
                    except Exception as e:
                        print(f"GEMINI ERROR: {e}")
                        bot_text = "আপনার মেসেজের জন্য ধন্যবাদ! আমাদের শার্ট, পাঞ্জাবি M, L, XL, XXL সাইজে available আছে। আপনি কোন প্রোডাক্ট সম্পর্কে জানতে চান?"

                    # Facebook এ পাঠানো
                    send_url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
                    payload = {
                        "recipient": {"id": sender_id},
                        "message": {"text": bot_text[:1900]} # 2000 char limit
                    }
                    r = requests.post(send_url, json=payload)
                    print(f"FB Send: {r.status_code} - {r.text}")

    return Response(content="ok", status_code=200)

def send_message(recipient_id, text):
    url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    requests.post(url, json={"recipient": {"id": recipient_id}, "message": {"text": text}})
