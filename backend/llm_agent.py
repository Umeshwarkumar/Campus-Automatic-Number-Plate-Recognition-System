import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = None
XAI_API_KEY = os.environ.get("XAI_API_KEY")
if XAI_API_KEY:
    client = OpenAI(
        api_key=XAI_API_KEY,
        base_url="https://api.x.ai/v1"
    )

# Define allowed intents
ALLOWED_INTENTS = ["COUNT_TODAY", "RECENT_IN", "RECENT_OUT", "COUNT_INSIDE", "UNKNOWN"]

def classify_intent(user_message: str) -> str:
    """
    Hardcoded classification of specific queries to bypass LLM.
    """
    msg = user_message.strip().lower()
    if msg == "how many vehicles are inside?":
        return "COUNT_INSIDE"
    elif msg == "vehicle count today":
        return "COUNT_TODAY"
    elif msg == "recent vehicles in":
        return "RECENT_IN"
    elif msg == "recent vehicles out":
        return "RECENT_OUT"
    return "UNKNOWN"

def generate_reply(intent: str, data: dict) -> str:
    """
    Generates a human readable reply based on the intent and data returned by Supabase.
    """
    if intent == "UNKNOWN":
        return "I'm sorry, I can only answer simple queries about recent vehicle entries, exits, and daily counts."
    if "error" in data:
        return f"An error occurred: {data['error']}"
    
    if intent == "COUNT_TODAY":
        count = data.get("count", 0)
        return f"There have been {count} vehicle visits today."
    elif intent == "COUNT_INSIDE":
        records = data.get("records", [])
        if not records:
            return "There are currently 0 vehicles inside."
        reply = f"There are currently {len(records)} vehicles inside:\n"
        for r in records:
            reply += f"- {r.get('plate_number')} (Entry: {r.get('entry_time')})\n"
        return reply.strip()
    elif intent == "RECENT_IN":
        records = data.get("records", [])
        if not records:
            return "No recent entries found."
        reply = "Here are the last 5 vehicles that entered:\n"
        for r in records:
            reply += f"- {r.get('plate_number')} (at {r.get('detected_at')})\n"
        return reply.strip()
    elif intent == "RECENT_OUT":
        records = data.get("records", [])
        if not records:
            return "No recent exits found."
        reply = "Here are the last 5 vehicles that left:\n"
        for r in records:
            reply += f"- {r.get('plate_number')} (at {r.get('detected_at')})\n"
        return reply.strip()
    
    return "Here is the information."
