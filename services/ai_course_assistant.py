import google.generativeai as genai

# 🔐 Set your Gemini API Key
genai.configure(api_key="AIzaSyDnbE7Ba6BDAoLAah9t9UZrLyRM7U1_cRg")

# Use Gemini Pro model
model = genai.GenerativeModel("gemini-pro")


def ask_course_ai(course_title, lesson_titles, user_question):
    """
    Context-aware AI tutor using Gemini
    """

    context = f"""
You are an expert course instructor.

Course Title:
{course_title}

Lessons:
{", ".join(lesson_titles)}

Student Question:
{user_question}

Instructions:
- Explain in simple language
- Use examples
- Be friendly and clear
- Avoid unnecessary theory
"""

    response = model.generate_content(context)

    return response.text
