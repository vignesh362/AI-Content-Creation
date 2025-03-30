import requests
import textwrap
from utils import format_json
API_URL = "http://localhost:1234/v1/chat/completions"

def generate_dialogue_script(transcript: str, topic: str = "Video Topic") -> str:
    prompt = f"""
You are a scriptwriter creating YouTube video content.
Write a dialogue-based script between a Human and their AI Sidekick.

FORMAT:
- Output as a JSON array of exchanges:
  [{{"Human": "...", "Bot": "..."}}, ...]

SCRIPT CONTROLS:
- Topic: "{topic}"
- Use this reference transcript:
{textwrap.shorten(transcript, width=3000, placeholder="...")}
- Tone: Human = formal, AI = witty and informative
- Dialogue ratio: Human ~80%, Bot ~20%
- Total token budget: ~500
- Ensure the script flows naturally and ends clearly.
"""

    payload = {
        "model": "mythomax-l2-13b",
        "messages": [
            {"role": "system", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.8,
        "top_p": 0.95
    }

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        return format_json(response.json()["choices"][0]["message"]["content"].strip())
    except Exception as e:
        print(f"LLM error: {e}")
        return "Script generation failed."
