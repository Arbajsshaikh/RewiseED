# ai_utils.py
import os
import json
from openai import OpenAI
import os


client = None

def get_client():
    global client

    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing")

        client = OpenAI(api_key=api_key)

    return client

# You can change this to the model you have access to
OPENAI_MODEL = "gpt-5-nano"


def generate_quiz_from_text(content: str, num_questions: int = 5):
    """
    Generate MCQ quiz questions from given content.

    Returns a list of dicts:
    [
      {
        "text": "question text",
        "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
        "correct": "A",
        "marks": 1.0
      },
      ...
    ]
    """
    if not content.strip():
        return []

    prompt = f"""
You are a course quiz generator for an LMS platform.

From the following content, create {num_questions} multiple-choice questions.

Rules:
- Each question MUST have 4 options: A, B, C, D.
- Exactly ONE option is correct.
- Difficulty: mixed but suitable for the given content.
- Language: same as the input text (mostly English).

Return ONLY valid JSON in this format:

[
  {{
    "text": "Question text here",
    "options": {{
      "A": "Option A text",
      "B": "Option B text",
      "C": "Option C text",
      "D": "Option D text"
    }},
    "correct": "A",
    "marks": 1.0
  }}
]

Content:
\"\"\"{content}\"\"\"
"""

    resp = client.chat.completions.create(
    model=OPENAI_MODEL,
    messages=[
        {"role": "system", "content": "You are a strict JSON API. Respond with ONLY JSON."},
        {"role": "user", "content": prompt},
    ]
)


    raw = resp.choices[0].message.content

    # robust JSON extraction
    start = raw.find("[")
    end = raw.rfind("]")
    if start != -1 and end != -1:
        raw_json = raw[start:end+1]
    else:
        raw_json = "[]"

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        data = []

    # Ensure we always return a list
    if not isinstance(data, list):
        return []

    return data


import os
from openai import OpenAI

from ai_utils import get_client

client = get_client()

def transcribe_audio(audio_path):
    """
    Converts audio to text using OpenAI API (NO heavy dependencies)
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError("Audio file not found")

    with open(audio_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=f
        )

    text = transcript.text.strip()

    if not text:
        raise ValueError("Transcription returned empty text")

    return text


def summarize_text(transcript):
    """
    SAME simple rule-based summary (unchanged)
    """
    lines = transcript.split(".")
    summary = ". ".join(lines[:5]).strip()

    if not summary:
        raise ValueError("Summary generation failed")

    return summary
