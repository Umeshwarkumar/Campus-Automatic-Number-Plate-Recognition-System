import os
import json
import requests
from dotenv import load_dotenv

load_dotenv("backend/.env")

headers = {
    "Authorization": f"Bearer {os.environ.get('XAI_API_KEY')}"
}
r = requests.get("https://api.x.ai/v1/models", headers=headers)
print(json.dumps(r.json(), indent=2))
