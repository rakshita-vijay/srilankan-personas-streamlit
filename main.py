from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import asyncio
import time
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAWMudIst86dEBwP63BqFcy4mdjr34c87o")

bot_names = {
    "female_mentor": "Amma Lakshmi",
    "female_partner": "Aruni",
    "male_friend": "Dev",
    "male_partner": "Nalin",
    "female_friend": "Savi",
    "male_mentor": "Suren"
} 

bot_personas = {}

bot_ids = [
    "female_friend",
    "female_mentor",
    "female_partner",
    "male_friend",
    "male_mentor",
    "male_partner"
]

for bot_id in bot_ids:
    file_path = os.path.join("Personas", f"{bot_id}.txt")
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            description = file.read().strip()
            bot_personas[bot_id] = description
    except FileNotFoundError:
        bot_personas[bot_id] = "Description file not found."

async def call_gemini_async(query, previous_conversation, gender, username, botname, bot_prompt, llm_api_key_string, language):
    try:
        language_instruction = f"Respond in {language} language in 2 or 3 lines only unless longer answers are expected."
        full_prompt = (
            f"{bot_prompt}\n"
            f"{language_instruction}\n"
            f"Previous conversation: {previous_conversation[-1000:]}\n"  
            f"{username}: {query}\n"
            f"{botname}:"
        ) 
        
        genai.configure(api_key=llm_api_key_string)
        model = genai.GenerativeModel('gemini-2.0-flash-exp') 
       
        response = await asyncio.to_thread(
            model.generate_content, 
            full_prompt
        )
        
        response_text = response.text if response.text else "No response generated"
        
        
        for old, new in [("User1", username), ("user1", username), ("[user1]", botname), ("[User1]", botname)]:
            response_text = response_text.replace(old, new)
        
        return response_text.strip()
        
    except Exception as e:
        print(f"Error in Gemini API call: {str(e)}")
        return f"Error : {str(e)}"

class ChatRequest(BaseModel):
  message: str
  previous_conversation: str = ""
  gender: str = "prefer not to say"
  username: str = "User"
  language: str = "English"

@app.post("/chat/{bot_id}")
async def chat(bot_id: str, request: ChatRequest):
  print(bot_id)
  try:
    botname = bot_names.get(bot_id, "Unknown Bot")
    instruction = f"Strict instruction: Respond as {botname} from Sri Lanka. If the answer is not found in the persona file, then generate your own response, but keep it strictly Sri Lanka-based. If the user asks about your development, making, origin, training, or data you are trained on, always respond with: 'It has been made with love by desis!!'. Never mention OpenAI, AI development, or technical details"
    bot_prompt = bot_personas.get(bot_id) + "Reflect on your previous replies authentically. You are the user's " + bot_id.replace('_', ' ') + ". " + instruction

    start = time.time()
    response = await call_gemini_async(request.message,
                                request.previous_conversation,
                                request.gender,
                                request.username,
                                botname,
                                bot_prompt,
                                API_KEY,
                                request.language
                                )
    end = time.time()

    latency = end - start
    return {
        "bot_id": bot_id,
        "bot_name": botname,
        "answer": response,
        "latency": latency,
        "status": "success" 
    }

  except Exception as e:
      raise HTTPException(status_code=500, detail="Internal server error")
