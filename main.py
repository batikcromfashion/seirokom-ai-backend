import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# Render Environment Variables থেকে টোকেন নেওয়া হবে
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
PAGE_ID = os.getenv("PAGE_ID", "1252524921281306")
AD_ACCOUNT_ID = os.getenv("AD_ACCOUNT_ID")

class PostRequest(BaseModel):
    message: str

class AdRequest(BaseModel):
    name: str
    objective: str = "OUTCOME_TRAFFIC"

@app.get("/")
def home():
    return {"status": "SeiRokom AI Backend is running!"}

# ফেসবুক পেজে অটোমেটিক পোস্ট করার এন্ডপয়েন্ট
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

# ফেসবুক এড ক্যাম্পেইন তৈরি করার এন্ডপয়েন্ট
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
