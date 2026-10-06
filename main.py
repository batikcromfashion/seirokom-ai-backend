import os
import requests
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# CORS সেটআপ
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Render Environment Variables থেকে টোকেন গ্রহণ
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
PAGE_ID = os.getenv("PAGE_ID", "1252524921281306")
AD_ACCOUNT_ID = os.getenv("AD_ACCOUNT_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "seirokom_secret_token")

# Gemini AI কনফিগারেশন
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
আপনি SeiRokom Fashion (সেইরকম ফ্যাশন)-এর অফিশিয়াল AI অ্যাসিস্ট্যান্ট।
গ্রাহকের সাথে সবসময় অমায়িক, বন্ধুত্বপূর্ণ, আনন্দময় ও স্পষ্ট বাংলায় কথা বলুন।
আমাদের এখানে ছেলেদের শার্ট, পাঞ্জাবি, পলো টি-শার্ট, মেয়েদের শাড়ি, থ্রি-পিস এবং শিশুদের জামাকাপড় পাওয়া যায়।
গ্রাহক পণ্য দেখতে চাইলে আমাদের ওয়েবসাইট ভিজিট করতে বলুন বা কি টাইপের পোশাক খুঁজছেন তা জানতে চান।
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

# Request Models
class ChatRequest(BaseModel):
    message: str

class PostRequest(BaseModel):
    message: str

class AdRequest(BaseModel):
    name: str
    objective: str = "OUTCOME_TRAFFIC"

# ১. হোম এন্ডপয়েন্ট
@app.get("/")
def home():
    return {"status": "SeiRokom AI Backend is running fully!"}

# ২. Meta Webhook ভেরিফিকেশন (GET Request)
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return Response(content=challenge, status_code=200)
        return Response(status_code=403)
    return Response(status_code=400)

# ৩. Meta Webhook মেসেজ রিসিভ (POST Request)
@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event.get("sender", {}).get("id")
                
                # নিজের পেজের পাঠানো মেসেজ বা Echo স্কিপ করার ফিল্টার
                message_data = messaging_event.get("message", {})
                if message_data.get("is_echo") or sender_id == PAGE_ID:
                    continue
                
                if "text" in message_data:
                    user_text = message_data["text"]
                    
                    # Gemini AI দিয়ে রেসপন্স তৈরি
                    try:
                        response = model.generate_content(user_text)
                        ai_response = response.text if response and response.text else "ধন্যবাদ! আমি SeiRokom Fashion AI। কিভাবে সাহায্য করতে পারি?"
                    except Exception as e:
                        print(f"Gemini API Error: {e}")
                        ai_response = "জি বলুন, SeiRokom Fashion-এ আপনাকে কীভাবে সাহায্য করতে পারি?"
                    
                    # ফেসবুক পেজ থেকে ইউজারকে মেসেজ পাঠানো
                    if PAGE_ACCESS_TOKEN and sender_id:
                        send_url = f"https://graph.facebook.com/v26.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
                        payload = {
                            "recipient": {"id": sender_id},
                            "message": {"text": ai_response}
                        }
                        requests.post(send_url, json=payload)
                        
    return Response(content="EVENT_RECEIVED", status_code=200)

# ৪. AI Chatbot এন্ডপয়েন্ট (ওয়েবসাইটের জন্য)
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        response = model.generate_content(request.message)
        return {"reply": response.text}
    except Exception as e:
        return {"reply": "দুঃখিত, এই মুহূর্তে উত্তর দিতে সমস্যা হচ্ছে। অনুগ্রহ করে একটু পর চেষ্টা করুন।"}

# ৫. ফেসবুক পেজে পোস্ট করার এন্ডপয়েন্ট
@app.post("/facebook/post")
def create_facebook_post(data: PostRequest):
    if not PAGE_ACCESS_TOKEN:
        raise HTTPException(status_code=500, detail="PAGE_ACCESS_TOKEN পাওয়া যায়নি")
    
    url = f"https://graph.facebook.com/v26.0/{PAGE_ID}/feed"
    payload = {
        "message": data.message,
        "access_token": PAGE_ACCESS_TOKEN
    }
    response = requests.post(url, data=payload)
    return response.json()

# ৬. ফেসবুক এড ক্যাম্পেইন তৈরি করার এন্ডপয়েন্ট
@app.post("/facebook/ad")
def create_ad_campaign(data: AdRequest):
    if not PAGE_ACCESS_TOKEN or not AD_ACCOUNT_ID:
        raise HTTPException(status_code=500, detail="Token অথবা Ad Account ID সেট করা নেই")
    
    url = f"https://graph.facebook.com/v26.0/{AD_ACCOUNT_ID}/campaigns"
    payload = {
        "name": data.name,
        "objective": data.objective,
        "status": "PAUSED",
        "special_ad_categories": [],
        "access_token": PAGE_ACCESS_TOKEN
    }
    response = requests.post(url, data=payload)
    return response.json()
