import os
import requests
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# CORS সেটআপ (যাতে অ্যাপ ও ওয়েবসাইট ব্যাকএন্ডের সাথে যোগাযোগ করতে পারে)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Render Environment Variables থেকে কী ও টোকেনগুলো গ্রহণ করা
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
PAGE_ID = os.getenv("PAGE_ID", "1252524921281306")
AD_ACCOUNT_ID = os.getenv("AD_ACCOUNT_ID")

# Gemini AI কনফিগারেশন
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
আপনি SeiRokom Fashion-এর অফিশিয়াল AI অ্যাসিস্ট্যান্ট।
গ্রাহকের সাথে মাস্কট স্টাইলে সবসময় বন্ধুত্বপূর্ণ, আনন্দময় ও প্রাঞ্জল ভাষায় কথা বলুন।
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

# ২. AI Chatbot এন্ডপয়েন্ট
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        response = model.generate_content(request.message)
        return {"reply": response.text}
    except Exception as e:
        return {"reply": "দুঃখিত, এই মুহূর্তে উত্তর দিতে সমস্যা হচ্ছে। অনুগ্রহ করে একটু পর চেষ্টা করুন।"}

# ৩. ফেসবুক পেজে পোস্ট করার এন্ডপয়েন্ট
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

# ৪. ফেসবুক এড ক্যাম্পেইন তৈরি করার এন্ডপয়েন্ট
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
