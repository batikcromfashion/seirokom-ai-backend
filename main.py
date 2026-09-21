import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

# Render-এর Environment Variable থেকে API Key গ্রহণ করা হচ্ছে
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_INSTRUCTION = """
আপনি SeiRokom Fashion-এর অফিশিয়াল AI অ্যাসিস্ট্যান্ট।
আপনার দায়িত্ব হলো কাস্টমারদের পোশাক পছন্দ করতে, সাইজ বেছে নিতে এবং তাদের প্রশ্নের উত্তর দিতে সাহায্য করা।
ব্যবসার প্রোগ্রামগুলো সম্পর্কে কেউ জানতে চাইলে বলবেন:
১. ড্রপশিপিং
২. ডিলারশিপ
৩. স্টক পার্টনার
৪. ডেলিভারি ম্যান
যেকোনো প্রোগ্রামে যোগ দিতে চাইলে তাদের সংশ্লিষ্ট বাটনে ক্লিক করে তথ্য দিতে বলবেন।
সবসময় বিনয়ী ও প্রফেশনাল ভাষায় বাংলায় উত্তর দেবেন।
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        response = model.generate_content(request.message)
        return {"reply": response.text}
    except Exception as e:
        return {"reply": "দুঃখিত, এই মুহূর্তে উত্তর দিতে সমস্যা হচ্ছে। অনুগ্রহ করে একটু পর চেষ্টা করুন।"}
