import os
from dotenv import load_dotenv

import requests
import json

load_dotenv()

required_env_vars = {
    "GEMINI_KEY": os.getenv("GEMINI_API_KEY")
}

missing_vars = [var for var, value in required_env_vars.items() if not value]

if missing_vars:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing_vars)}")

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + \
    required_env_vars["GEMINI_KEY"]


def askAI(msg):
    payload = json.dumps({
        "contents": [
            {
                "parts": [
                    {
                        "text": msg
                    }
                ]
            }
        ]
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response = json.loads(response.text)

    return response["candidates"][0]["content"]["parts"][0]["text"]
