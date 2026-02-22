from utils.gemini_helper import get_gemini_response

prompt = "Explain Operating System in simple words"

reply = get_gemini_response(prompt)
print(reply)
