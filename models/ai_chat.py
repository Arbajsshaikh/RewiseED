from datetime import datetime
from app import db

class AICourseChat(db.Model):
    __tablename__ = "ai_course_chat"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)

    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("User")
    course = db.relationship("Course")
