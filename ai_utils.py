# ai_utils.py

import os
import json
import tempfile
import requests
from openai import OpenAI

# -------------------------
# CLIENT SETUP
# -------------------------
client = None

def get_client():
    global client

    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing")

        client = OpenAI(api_key=api_key)

    return client


OPENAI_MODEL = "gpt-5-nano"


# -------------------------
# QUIZ GENERATION (UNCHANGED)
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
- Difficulty: mixed but suitable for the given content.

Return ONLY valid JSON.

Content:
\"\"\"{content}\"\"\"
"""

    client = get_client()

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a strict JSON API. Respond with ONLY JSON."},
            {"role": "user", "content": prompt},
        ]
    )

    raw = resp.choices[0].message.content

    start = raw.find("[")
    end = raw.rfind("]")
    raw_json = raw[start:end+1] if start != -1 and end != -1 else "[]"

    try:
        data = json.loads(raw_json)
    except:
        data = []

    return data if isinstance(data, list) else []


# -------------------------
# 🎯 NEW: VIDEO → AUDIO → TRANSCRIPT (VERCEL SAFE)
# -------------------------
def transcribe_video_from_url(video_url):
    """
    Vercel-safe transcription:
    - Downloads small video
    - Extracts limited audio
    - Sends to OpenAI
    """

    client = get_client()

    # 📥 Download video (LIMIT SIZE)
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

    # ⚠️ IMPORTANT: Instead of ffmpeg, send raw file (OpenAI handles audio extraction internally)
    with open(temp_video.name, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=f
        )

    text = transcript.text.strip()

    if not text:
        raise ValueError("Transcription returned empty")

    return text


# -------------------------
# SUMMARY (IMPROVED USING AI)
# -------------------------
def summarize_text(transcript):
    """
    Better AI-based summary
    """

    client = get_client()

    prompt = f"""
Summarize the following lecture transcript in:

1. Short summary (5 lines)
2. Key points (bullet format)

Transcript:
{transcript}
"""

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful summarizer."},
            {"role": "user", "content": prompt},
        ]
    )

    return resp.choices[0].message.content.strip()
