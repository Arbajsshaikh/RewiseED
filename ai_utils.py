# ai_utils.py

import os
import json
import tempfile
import requests
import google.generativeai as genai

# -------------------------
# CLIENT SETUP (COMPATIBLE)
# -------------------------
client = None

def get_client():
    global client

    if client is None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing")

        genai.configure(api_key=api_key)
        client = genai.GenerativeModel("gemini-1.5-flash")

    return client


OPENAI_MODEL = "gemini-1.5-flash"  # just to avoid breaking references


# -------------------------
# QUIZ GENERATION (SAME FUNCTION)
# -------------------------
def generate_quiz_from_text(content: str, num_questions: int = 5):

    if not content.strip():
        return []

    prompt = f"""
You are a course quiz generator for an LMS platform.

From the following content, create {num_questions} multiple-choice questions.

Rules:
- Each question MUST have 4 options: A, B, C, D.
- Exactly ONE option is correct.
- Return ONLY valid JSON.

Content:
\"\"\"{content}\"\"\"
"""

    client = get_client()

    response = client.generate_content(prompt)
    raw = response.text

    start = raw.find("[")
    end = raw.rfind("]")
    raw_json = raw[start:end+1] if start != -1 and end != -1 else "[]"

    try:
        data = json.loads(raw_json)
    except:
        data = []

    return data if isinstance(data, list) else []


# -------------------------
# 🎯 VIDEO → TRANSCRIPT (GEMINI)
# -------------------------
def transcribe_video_from_url(video_url):

    client = get_client()

    response = requests.get(video_url, stream=True)

    max_size = 10 * 1024 * 1024  # 10MB limit
    downloaded = 0

    temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")

    for chunk in response.iter_content(chunk_size=1024 * 1024):
        if chunk:
            downloaded += len(chunk)

            if downloaded > max_size:
                temp_video.close()
                raise Exception("Video too large for AI processing (>10MB)")

            temp_video.write(chunk)

    temp_video.close()

    with open(temp_video.name, "rb") as f:
        video_bytes = f.read()

    response = client.generate_content([
        {
            "mime_type": "video/mp4",
            "data": video_bytes
        },
        "Transcribe this video clearly."
    ])

    text = response.text.strip()

    if not text:
        raise ValueError("Transcription returned empty")

    return text


# -------------------------
# SUMMARY (GEMINI)
# -------------------------
def summarize_text(transcript):

    client = get_client()

    prompt = f"""
Summarize the following lecture transcript in:

1. Short summary (5 lines)
2. Key points (bullet format)

Transcript:
{transcript}
"""

    response = client.generate_content(prompt)

    return response.text.strip()
