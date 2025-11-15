from openai import OpenAI
import os
import json
from dotenv import load_dotenv

# Load .env variables into environment
load_dotenv()

class OpenAIClient:
    def __init__(self, model="gpt-4.1-mini"):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")
        use_real = os.getenv("USE_REAL_OPENAI", "false").lower() == "true"
        self.enabled = bool(self.api_key and use_real)

        print("DEBUG ENABLED:", self.enabled)
        print("DEBUG KEY PREFIX:", (self.api_key or "None")[:4])
        print("DEBUG USE REAL:", use_real)

    def generate(self, prompt: str) -> str:
        if not self.enabled:
            return json.dumps({"_mock": True, "text": "MOCK_RESPONSE"})

        client = OpenAI(api_key=self.api_key)
        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return resp.choices[0].message.content
        except Exception as e:
            print("🔥 OpenAI ERROR:", str(e))
            return json.dumps({"error": str(e)})
