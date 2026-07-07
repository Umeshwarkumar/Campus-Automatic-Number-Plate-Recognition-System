import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("backend/.env")

client = OpenAI(
    api_key=os.environ.get("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

try:
    response = client.chat.completions.create(
        model="grok-2-latest",
        messages=[{"role": "system", "content": "You are a helpful assistant. Respond with JSON: {\"intent\": \"COUNT_TODAY\"}"}],
        response_format={ "type": "json_object" },
        temperature=0.0,
    )
    print(response.choices[0].message.content)
except Exception as e:
    import traceback
    traceback.print_exc()
