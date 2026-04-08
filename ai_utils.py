# ai_utils.py

import os
import json
from google.genai import Client


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

        client = Client(api_key=api_key)

    return client


MODEL = "gemini-1.5-flash"


# -------------------------
# QUIZ GENERATION
# -------------------------
def generate_quiz_from_text(content: str, num_questions: int = 5):

    if not content or not content.strip():
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

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        raw = response.text or ""

        start = raw.find("[")
        end = raw.rfind("]")

        raw_json = raw[start:end+1] if start != -1 and end != -1 else "[]"

        return json.loads(raw_json)

    except Exception as e:
        print("QUIZ ERROR:", str(e))
        return []


# -------------------------
# 🎯 VIDEO TRANSCRIPTION (FIXED)
# -------------------------
def transcribe_video_from_url(video_url):

    client = get_client()

    if not video_url:
        raise ValueError("Video URL is empty")

    try:
        # ✅ FIX: DO NOT download video
        # ✅ Directly pass URL to Gemini

        response = client.models.generate_content(
            model=MODEL,
            contents=[
                video_url,
                "Transcribe this video clearly. Provide clean readable text."
            ]
        )

        text = (response.text or "").strip()

        if not text:
            raise ValueError("Empty transcription")

        return text

    except Exception as e:
        print("TRANSCRIPTION ERROR:", str(e))
        raise


# -------------------------
# SUMMARY
# -------------------------
def summarize_text(transcript):

    client = get_client()

    if not transcript or not transcript.strip():
        return "No transcript available."

    prompt = f"""
Summarize the following lecture:

1. Short summary (5 lines)
2. Key points (bullet points)

Transcript:
{transcript}
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        return (response.text or "").strip()

    except Exception as e:
        print("SUMMARY ERROR:", str(e))
        return "Summary generation failed."
