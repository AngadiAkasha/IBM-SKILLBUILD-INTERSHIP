from dotenv import load_dotenv
import os

load_dotenv()

key = os.getenv("GEMINI_API_KEY")

if key:
    print("✅ Gemini API key loaded successfully")
else:
    print("❌ API key NOT loaded")
