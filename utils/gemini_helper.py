import os
from google import genai

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in Streamlit Secrets")

# Create Gemini client
client = genai.Client(api_key=API_KEY)


def get_gemini_response(prompt: str) -> str:
    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ Gemini Error: {e}"
