# ai_utils.py

import os
import json
import tempfile
import requests
from google import genai

# -------------------------
# CLIENT SETUP
# -------------------------
client = None

def get_client():
    global client

    if client is None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing")

        client = genai.Client(api_key=api_key)

    return client


OPENAI_MODEL = "gemini-1.5-flash"  # keep name for compatibility


# -------------------------
# QUIZ GENERATION
# -------------------------
def generate_quiz_from_text(content: str, num_questions: int = 5):

    if not content.strip():
        return []

    prompt = f"""
Create {num_questions} MCQ questions.

Rules:
- 4 options (A,B,C,D)
- One correct answer
- Return ONLY JSON array

Content:
{content}
"""

    client = get_client()

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    raw = response.text

    start = raw.find("[")
    end = raw.rfind("]")

    raw_json = raw[start:end+1] if start != -1 and end != -1 else "[]"

    try:
        return json.loads(raw_json)
    except:
        return []


# -------------------------
# 🎯 VIDEO TRANSCRIPTION
# -------------------------
def transcribe_video_from_url(video_url):

    client = get_client()

    response = requests.get(video_url, stream=True)

    max_size = 10 * 1024 * 1024
    downloaded = 0

    temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")

    for chunk in response.iter_content(1024 * 1024):
        if chunk:
            downloaded += len(chunk)

            if downloaded > max_size:
                temp_video.close()
                raise Exception("Video too large (>10MB)")

            temp_video.write(chunk)

    temp_video.close()

    with open(temp_video.name, "rb") as f:
        video_bytes = f.read()

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[
            {"mime_type": "video/mp4", "data": video_bytes},
            "Transcribe this video clearly."
        ]
    )

    text = response.text.strip()

    if not text:
        raise ValueError("Transcription returned empty")

    return text


# -------------------------
# SUMMARY
# -------------------------
def summarize_text(transcript):

    client = get_client()

    prompt = f"""
Summarize the following lecture:

1. Short summary (5 lines)
2. Key points

{transcript}
"""

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )

    return response.text.strip()
