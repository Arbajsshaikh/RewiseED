from flask import Blueprint, request, jsonify
from app import db
from models.ai_chat import AICourseChat
from services.ai_course_assistant import ask_course_ai
from models.video_lecture import VideoLecture
from models.course import Course

ai_bp = Blueprint("ai", __name__)

@ai_bp.route("/student/course/<int:course_id>/ai-chat", methods=["POST"])
def ai_course_chat(course_id):
    data = request.json
    question = data.get("question")
    student_id = data.get("student_id")

    course = Course.query.get_or_404(course_id)
    lessons = VideoLecture.query.filter_by(course_id=course_id).all()

    lesson_titles = [l.title for l in lessons]

    answer = ask_course_ai(course.title, lesson_titles, question)

    chat = AICourseChat(
        student_id=student_id,
        course_id=course_id,
        user_message=question,
        ai_response=answer
    )

    db.session.add(chat)
    db.session.commit()

    return jsonify({"answer": answer})
