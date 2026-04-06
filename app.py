from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta, date
from collections import defaultdict
from ai_utils import  generate_quiz_from_text
import json
from openai import OpenAI
from flask import request, jsonify, current_app
from itsdangerous import URLSafeSerializer

import os




from ai_utils import get_client

client = get_client()
# ---------- OpenAI client helper ----------

def get_ai_client() -> OpenAI | None:
    """
    Returns an OpenAI client or None if API key is missing.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("AI warning: OPENAI_API_KEY is not set.")
        return None
    return OpenAI(api_key=api_key)


import os
import tempfile

app = Flask(__name__, static_folder="static", template_folder="templates")
import os
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "fallback-secret")


serializer = URLSafeSerializer(app.config['SECRET_KEY'])
# Database (keep as is for now)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join('/tmp', 'academic.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ FIXED upload folder (Vercel-compatible)
app.config['VIDEO_UPLOAD_FOLDER'] = os.path.join(tempfile.gettempdir(), 'uploads', 'videos')

os.makedirs(app.config['VIDEO_UPLOAD_FOLDER'], exist_ok=True)

# Allow only some extensions for safety
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mkv", "mov", "webm", "avi"}
def allowed_video_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_VIDEO_EXTENSIONS


db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")

    # --- Profile / about ---
    headline = db.Column(db.String(120), nullable=True)      # e.g. "Senior Data Science Trainer"
    bio = db.Column(db.Text, nullable=True)                  # long about text
    years_experience = db.Column(db.Integer, nullable=True)  # e.g. 5

    # simple comma-separated values, easier than separate tables for now
    primary_domains = db.Column(db.String(255), nullable=True)   # "Data Science, Web Development"
    teaching_styles = db.Column(db.String(255), nullable=True)   # "Project-based, Beginner-friendly"
    languages = db.Column(db.String(120), nullable=True)         # "English, Hindi"
    location = db.Column(db.String(120), nullable=True)          # "Pune, India"
    timezone = db.Column(db.String(50), nullable=True)           # "Asia/Kolkata"
    accepting_new_students = db.Column(db.Boolean, nullable=False, default=True)

    # --- Social / contact links ---
    linkedin_url = db.Column(db.String(255), nullable=True)
    github_url = db.Column(db.String(255), nullable=True)
    portfolio_url = db.Column(db.String(255), nullable=True)

    # --- Notification preferences ---
    notify_on_enroll = db.Column(db.Boolean, nullable=False, default=True)
    notify_on_submission = db.Column(db.Boolean, nullable=False, default=True)
    notify_on_completion = db.Column(db.Boolean, nullable=False, default=True)
    summary_frequency = db.Column(db.String(20), nullable=False, default="weekly")  # daily/weekly/none

    # --- Payment / payout details ---
    payout_method = db.Column(db.String(20), nullable=True)  # "bank", "upi", "both"
    bank_account_name = db.Column(db.String(120), nullable=True)
    bank_account_number = db.Column(db.String(50), nullable=True)
    bank_ifsc = db.Column(db.String(20), nullable=True)
    bank_name = db.Column(db.String(120), nullable=True)
    upi_id = db.Column(db.String(120), nullable=True)

    # relationships
    courses = db.relationship("Course", backref="trainer", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)








class StudentVoiceResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    course_id = db.Column(db.Integer, nullable=False)
    response_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StudentQuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    course_id = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer)
    total = db.Column(db.Integer)
    level = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
























class Course(db.Model):
    __tablename__ = "course"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    level = db.Column(db.String(50), nullable=False)
    duration_hours = db.Column(db.Integer, nullable=False, default=6)
    color = db.Column(db.String(20), nullable=False, default="#047857")
    price = db.Column(db.Float, nullable=False, default=999.0)
    trainer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    ai_outline_json = db.Column(db.Text, nullable=True)

    enrollments = db.relationship(
        "Enrollment",
        backref="course",
        lazy=True,
        cascade="all, delete-orphan"
    )

    # ✅ SINGLE source of videos
    videos = db.relationship(
    "VideoLecture",
    backref="course",
    lazy=True,
    cascade="all, delete-orphan"

    )





class Student(db.Model):
    __tablename__ = "student"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)



# ========== NEW MODELS: QUESTION BANK, GROUPS, CERTIFICATES, TEMPLATES, AUTOMATIONS ==========

class QuestionBankItem(db.Model):
    __tablename__ = "question_bank_item"
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=True)

    topic = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, default="Medium")  # Easy/Medium/Hard
    question_type = db.Column(db.String(20), nullable=False, default="MCQ")  # MCQ/Text

    text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=True)
    option_b = db.Column(db.String(255), nullable=True)
    option_c = db.Column(db.String(255), nullable=True)
    option_d = db.Column(db.String(255), nullable=True)
    correct_option = db.Column(db.String(1), nullable=True)  # A/B/C/D
    marks = db.Column(db.Float, nullable=False, default=1.0)

    tags = db.Column(db.String(255), nullable=True)  # comma-separated tags
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to Course so templates can access q.course.title
    course = db.relationship("Course", backref="question_bank_items", lazy=True)


class StudentGroup(db.Model):
    __tablename__ = "student_group"
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    memberships = db.relationship(
        "StudentGroupMembership",
        backref="group",
        lazy=True,
        cascade="all, delete-orphan"
    )


class StudentGroupMembership(db.Model):
    __tablename__ = "student_group_membership"
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("student_group.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    joined_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    student = db.relationship("Student", lazy=True)


class CertificateTemplate(db.Model):
    __tablename__ = "certificate_template"
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False, default="Default Certificate")
    # Simple HTML fragment with placeholders: {{student_name}}, {{course_title}}, {{date}}
    body_html = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_default = db.Column(db.Boolean, nullable=False, default=False)


class TrainerTemplate(db.Model):
    """
    Generic reusable template: announcements, feedback, emails, etc.
    """
    __tablename__ = "trainer_template"
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(50), nullable=False, default="announcement")  # announcement/feedback/email/assessment
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class TrainerAutomation(db.Model):
    """
    Simple automation rules: we just store them for now (no background worker).
    """
    __tablename__ = "trainer_automation"
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    trigger_type = db.Column(db.String(50), nullable=False)  # 'enrollment', 'inactivity', 'course_completion', ...
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)
    config_json = db.Column(db.Text, nullable=True)  # store JSON as string
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Enrollment(db.Model):
    __tablename__ = "enrollment"

    id = db.Column(db.Integer, primary_key=True)

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("course.id"),
        nullable=False
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),   # ✅ FIX HERE
        nullable=False
    )

    progress = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="In Progress")
    enrolled_at = db.Column(db.DateTime, default=db.func.now())
    hours_watched = db.Column(db.Float, default=0.0)
    tests_score = db.Column(db.Float, default=0.0)

    # relationship
    student = db.relationship("User", backref="enrollments")  # ✅ FIX



class Session(db.Model):
    __tablename__ = "session"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    course = db.relationship("Course", lazy=True)
    
class VideoLecture(db.Model):
    __tablename__ = "video_lecture"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(255), nullable=False)  # saved file name
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # NEW:
    transcript = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)


class StudyLog(db.Model):
    __tablename__ = "study_log"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    hours = db.Column(db.Float, nullable=False, default=0.0)

class Assessment(db.Model):
    __tablename__ = "assessment"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    type = db.Column(db.String(50), nullable=False, default="Quiz")  # Quiz/Test/Assignment
    total_marks = db.Column(db.Float, nullable=False, default=100.0)
    passing_marks = db.Column(db.Float, nullable=False, default=40.0)
    due_date = db.Column(db.DateTime, nullable=True)
    is_published = db.Column(db.Boolean, nullable=False, default=False)

    questions = db.relationship(
        "Question",
        backref="assessment",
        lazy=True,
        cascade="all, delete-orphan"
    )

class Question(db.Model):
    __tablename__ = "question"
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessment.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    # For now: MCQ single-answer only
    option_a = db.Column(db.String(255), nullable=True)
    option_b = db.Column(db.String(255), nullable=True)
    option_c = db.Column(db.String(255), nullable=True)
    option_d = db.Column(db.String(255), nullable=True)
    correct_option = db.Column(db.String(1), nullable=True)  # "A", "B", "C", "D"
    marks = db.Column(db.Float, nullable=False, default=1.0)


from functools import wraps
from flask import session, redirect, url_for, flash

from functools import wraps
from flask import request, redirect, url_for, flash

def login_required(role=None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            print("COOKIES:", request.cookies)
            token = request.cookies.get("session_token")

            if not token:
                flash("Please log in to continue.", "error")
                return redirect(url_for("login"))

            try:
                data = serializer.loads(token)
                user_id = data.get("user_id")
            except Exception:
                flash("Session expired. Please log in again.", "error")
                return redirect(url_for("login"))

            user = User.query.get(user_id)

            if not user:
                flash("Please log in again.", "error")
                return redirect(url_for("login"))

            if role and user.role != role:
                flash("You are not authorized to access that page.", "error")
                return redirect(url_for("login"))

            kwargs["current_user"] = user
            return view_func(*args, **kwargs)

        return wrapped_view
    return decorator




def seed_data():
    if User.query.first():
        return

    trainer = User(email="trainer@example.com", name="Alesia Karapova", role="trainer")
    trainer.set_password("Password123")

    student_names = [
        "Rohit Sharma", "Sara Khan", "Vikram Patil", "Emily Clark",
        "Noah Lee", "Ananya Desai", "James Miller", "Priya Nair"
    ]
    students = [Student(name=n, email=n.replace(" ", ".").lower() + "@example.com") for n in student_names]

    courses = [
        Course(title="Design Accessibility", level="Advanced", duration_hours=5, color="#0f766e", trainer=trainer),
        Course(title="UX Research", level="Intermediate", duration_hours=6, color="#6366f1", trainer=trainer),
        Course(title="Figma for Beginner", level="Beginner", duration_hours=7, color="#111827", trainer=trainer),
        Course(title="Animation for Beginner", level="Beginner", duration_hours=6, color="#f97316", trainer=trainer),
        Course(title="Common Design Pattern", level="Intermediate", duration_hours=6, color="#0284c7", trainer=trainer),
    ]

    db.session.add(trainer)
    db.session.add_all(students)
    db.session.add_all(courses)
    db.session.commit()

    from random import random, randint

    all_students = Student.query.all()
    for course in courses:
        for student in all_students:
            if random() < 0.6:
                progress_val = randint(20, 100)
                status = "Completed" if progress_val >= 95 else "In Progress"
                enrollment = Enrollment(
                    course_id=course.id,
                    student_id=student.id,
                    progress=progress_val,
                    status=status
                )
                db.session.add(enrollment)
    db.session.commit()

    now = datetime.utcnow()
    sessions = [
        Session(course_id=courses[0].id, title="Live Q&A", start_time=now + timedelta(days=1, hours=3)),
        Session(course_id=courses[1].id, title="Project Feedback", start_time=now + timedelta(days=2, hours=2)),
        Session(course_id=courses[2].id, title="Final Review", start_time=now + timedelta(days=3, hours=1)),
    ]
    db.session.add_all(sessions)
    db.session.commit()

def ai_chat_message(system_prompt: str, messages: list[str]) -> str:
    """
    Very small wrapper around gpt-5.1-nano using Responses API.
    messages: list of strings like conversation lines.
    """
    # Build a single plain-text prompt from system + messages
    joined = system_prompt.strip() + "\n\n"
    for m in messages:
        joined += m.strip() + "\n"

    try:
        resp = client.responses.create(
            model="gpt-5.1-nano",
            input=joined,
            max_output_tokens=300  # adjust response length if you like
        )
        return resp.output[0].content[0].text.strip()
    except Exception as e:
        print("AI tutor error:", e)
        return "I'm having trouble responding right now. Please try again later."


def ai_generate(system_prompt: str, user_prompt: str) -> str:
    """
    Small helper to call OpenAI chat model.
    IMPORTANT: no temperature param so it works with gpt-5.1-nano.
    """
    model_name = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")  # or set to gpt-5.1-nano
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("AI generation error:", e)
        return ""

def run_rewiseed_for_course(course: Course):
    """
    For a given course:
    - ensure every video has transcript + summary
    - combine summaries
    - generate quiz, exam, ppt, projects, chatbot prompt, tutor script
    - save into RewiseEDPackage
    """
    from ai_utils import transcribe_audio, summarize_text  # you already have this

    # 1) Ensure transcript + summary for each video
    summaries = []
    for v in course.videos:
        if not v.summary:
            video_path = os.path.join(app.config['VIDEO_UPLOAD_FOLDER'], v.filename)
            audio_path = video_path.rsplit(".", 1)[0] + ".wav"

            # ffmpeg → WAV
            os.system(
                f'ffmpeg -i "{video_path}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{audio_path}" -y'
            )

            try:
                transcript = transcribe_audio(audio_path)
                summary = summarize_text(transcript)
            except Exception as e:
                print("RewiseED video AI error:", e)
                transcript = None
                summary = None

            v.transcript = transcript
            v.summary = summary
            db.session.add(v)

        if v.summary:
            summaries.append(f"Lecture: {v.title}\nSummary:\n{v.summary}\n")

    db.session.commit()

    if not summaries:
        raise RuntimeError("No summaries available for this course.")

    combined = "\n\n".join(summaries)

    # 2) Generate AI bundle
    course_title = course.title

    course_summary = ai_generate(
        "You are an expert course designer.",
        f"Based on these lecture summaries, write a detailed 2–3 paragraph course summary for '{course_title}'.\n\n{combined}",
    )

    quiz_content = ai_generate(
        "You are an exam setter.",
        f"Using the following course content, create 10 multiple-choice questions with 4 options each "
        f"and indicate the correct answer. Format as:\n\n"
        f'Q1. ...\nA) ...\nB) ...\nC) ...\nD) ...\nAnswer: B\n\nContent:\n{combined}',
    )

    exam_content = ai_generate(
        "You are an academic examiner.",
        f"Using this course content, create a 50-mark exam with:\n"
        f"- Section A: 5 short questions (2 marks each)\n"
        f"- Section B: 5 medium questions (4 marks each)\n"
        f"- Section C: 3 long questions (6 marks each, attempt any 2)\n\n"
        f"Only text, no markdown tables.\n\nContent:\n{combined}",
    )

    ppt_outline = ai_generate(
        "You are a presentation designer.",
        f"Generate a slide-by-slide PPT outline for a course titled '{course_title}'.\n"
        f"Include: slide title and 3–5 bullet points per slide.\n\nContent:\n{combined}",
    )

    project_ideas = ai_generate(
        "You are a mentor.",
        f"Suggest 5 project ideas for students of the course '{course_title}'. "
        f"For each project, provide:\n- Title\n- Problem statement\n- What they will learn\n- 3–5 implementation steps.\n\nContent:\n{combined}",
    )

    chatbot_prompt = ai_generate(
        "You are designing a tutoring chatbot.",
        f"Create a system prompt for an AI chatbot that will tutor students in the course '{course_title}'. "
        f"Describe its tone, what it knows, how it should answer, and how it should ask follow-up questions.\n\nContent:\n{combined}",
    )

    tutor_script = ai_generate(
        "You are an AI tutor scriptwriter.",
        f"Write a script for an AI virtual tutor to onboard a new student to '{course_title}'. "
        f"The script should:\n- Greet the student\n- Ask their background\n- Diagnose their level\n- Suggest a learning path\n"
        f"- Explain how the course is structured.\n\nUse conversational style.\n\nContent:\n{combined}",
    )

    # 3) Create or update package
    pkg = RewiseEDPackage.query.filter_by(course_id=course.id).first()
    if not pkg:
        pkg = RewiseEDPackage(course_id=course.id)

    pkg.course_summary = course_summary
    pkg.quiz_content = quiz_content
    pkg.exam_content = exam_content
    pkg.ppt_outline = ppt_outline
    pkg.project_ideas = project_ideas
    pkg.chatbot_prompt = chatbot_prompt
    pkg.tutor_script = tutor_script
    pkg.status = "ready"

    db.session.add(pkg)
    db.session.commit()
    return pkg



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "trainer")

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

        if role != user.role:
            flash(f"This account is registered as {user.role.title()}, not {role.title()}.", "error")
            return redirect(url_for("login"))

        # ✅ CREATE TOKEN INSTEAD OF SESSION
        token = serializer.dumps({
            "user_id": user.id,
            "role": user.role,
            "name": user.name
        })

        response = redirect(
            url_for("trainer_dashboard") if user.role == "trainer"
            else url_for("student_dashboard")
        )

        response.set_cookie(
            "session_token",
            token,
            httponly=True,
            samesite="Lax"   # 🔥 KEY CHANGE
        )

        return response

    return render_template("login.html")

@app.route("/trainer/courses/<int:course_id>/rewiseed")
@login_required(role="trainer")
def trainer_course_rewiseed(current_user, course_id):
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()

    # Try to get package; if missing, generate once
    pkg = RewiseEDPackage.query.filter_by(course_id=course.id).first()
    videos = VideoLecture.query.filter_by(course_id=course.id).all()

    if not pkg:
        try:
            pkg = run_rewiseed_for_course(course)
            flash("RewiseED AI package generated for this course.", "success")
        except Exception as e:
            print("RewiseED generation error:", e)
            flash("Failed to generate RewiseED package. Check logs / API quota.", "error")
            return redirect(url_for("trainer_courses"))

    return render_template(
        "trainer_course_rewiseed.html",
        user=current_user,
        course=course,
        pkg=pkg,
        videos=videos 
    )

@app.route("/trainer/courses/<int:course_id>/rewiseed/mark_paid", methods=["POST"])
@login_required(role="trainer")
def trainer_course_rewiseed_mark_paid(current_user, course_id):
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()
    pkg = RewiseEDPackage.query.filter_by(course_id=course.id).first_or_404()

    pkg.is_paid = True
    db.session.commit()
    flash("RewiseED package marked as paid. Full access unlocked.", "success")
    return redirect(url_for("trainer_course_rewiseed", course_id=course.id))


@app.route("/logout")
def logout():
    response = redirect(url_for("login"))
    response.delete_cookie("session_token")
    flash("You have been logged out.", "success")
    return response

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        role = request.form.get("role") or "student"

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("signup"))

        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for("signup"))

        # check existing
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please log in.", "error")
            return redirect(url_for("login"))

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/")
@login_required(role="trainer")
def trainer_dashboard(current_user):
    courses = Course.query.filter_by(trainer_id=current_user.id).all()
    course_ids = [c.id for c in courses]

    if course_ids:
        enrollments = Enrollment.query.filter(Enrollment.course_id.in_(course_ids)).all()
    else:
        enrollments = []

    total_courses = len(courses)
    total_students = len({e.student_id for e in enrollments})
    completed = [e for e in enrollments if e.status == "Completed"]
    in_progress = [e for e in enrollments if e.status == "In Progress"]

    # 🔹 Build per-course stats for the "Continue Teaching" section
    from collections import defaultdict
    by_course = defaultdict(list)
    for e in enrollments:
        by_course[e.course_id].append(e)

    continue_courses = []
    for c in courses:
        c_enrs = by_course.get(c.id, [])
        num_students = len(c_enrs)
        total_revenue = num_students * (c.price or 0.0)

        continue_courses.append({
            "course": c,
            "num_students": num_students,
            "total_revenue": total_revenue,
        })

    # Sort by revenue (highest first), but keep ALL courses (no slicing)
    continue_courses.sort(key=lambda x: x["total_revenue"], reverse=True)

    # Upcoming sessions (same as before)
    upcoming_sessions = Session.query.join(Course).filter(
        Course.trainer_id == current_user.id,
        Session.start_time >= datetime.utcnow()
    ).order_by(Session.start_time.asc()).limit(5).all()

    # Recommended courses (you can keep this logic as you like)
    recommended_courses = courses[:3]

    return render_template(
        "trainer_dashboard.html",
        user=current_user,
        total_courses=total_courses,
        total_students=total_students,
        completed_count=len(completed),
        in_progress_count=len(in_progress),
        continue_courses=continue_courses,
        upcoming_sessions=upcoming_sessions,
        recommended_courses=recommended_courses,
    )


@app.route("/trainer/insights")
@login_required(role="trainer")
def trainer_insights(current_user):
    # All trainer courses
    courses = Course.query.filter_by(trainer_id=current_user.id).all()
    course_ids = [c.id for c in courses]

    enrollments = []
    if course_ids:
        enrollments = Enrollment.query.filter(Enrollment.course_id.in_(course_ids)).all()

    # --- Course leaderboard (by students and revenue) ---
    stats_per_course = []
    for c in courses:
        c_enrs = [e for e in enrollments if e.course_id == c.id]
        num_students = len(c_enrs)
        avg_progress = int(sum(e.progress for e in c_enrs) / num_students) if num_students else 0
        revenue = c.price * num_students

        stats_per_course.append({
            "course": c,
            "num_students": num_students,
            "avg_progress": avg_progress,
            "revenue": revenue,
        })

    # Sort for “top 5” views
    top_by_revenue = sorted(stats_per_course, key=lambda x: x["revenue"], reverse=True)[:5]
    top_by_students = sorted(stats_per_course, key=lambda x: x["num_students"], reverse=True)[:5]

    # --- Student health: aggregate by student across trainer’s courses ---
    trainer_course_ids = course_ids
    from collections import defaultdict
    by_student = defaultdict(list)
    for e in enrollments:
        by_student[e.student_id].append(e)

    # we’ll keep this lightweight: just compute avg progress and hours
    student_health = []
    for student_id, enrs in by_student.items():
        s = Student.query.get(student_id)
        if not s:
            continue
        total_courses = len(enrs)
        avg_progress = int(sum(e.progress for e in enrs) / total_courses) if total_courses else 0
        total_hours = sum(e.hours_watched for e in enrs)
        status = "At risk" if avg_progress < 40 or total_hours < 2 else "Healthy"
        student_health.append({
            "student": s,
            "total_courses": total_courses,
            "avg_progress": avg_progress,
            "total_hours": total_hours,
            "status": status,
        })

    # --- Assessment quality overview (very simple) ---
    assessments = []
    if course_ids:
        assessments = Assessment.query.filter(Assessment.course_id.in_(course_ids)).all()

    assessment_summaries = []
    for a in assessments:
        # total marks of questions
        qs = Question.query.filter_by(assessment_id=a.id).all()
        total_q_marks = sum(q.marks for q in qs) if qs else 0

        # how many StudentAssessment attempts
        sas = StudentAssessment.query.filter_by(assessment_id=a.id).all()
        num_attempts = len(sas)
        avg_score = (sum(sa.score_obtained for sa in sas) / num_attempts) if num_attempts else 0

        assessment_summaries.append({
            "assessment": a,
            "questions_count": len(qs),
            "total_q_marks": total_q_marks,
            "num_attempts": num_attempts,
            "avg_score": round(avg_score, 1),
        })

    # --- Optional AI summary of teaching performance (not required to work) ---
    ai_summary = None
    try:
        client = get_ai_client()
        if client and stats_per_course:
            context = {
                "courses": [
                    {
                        "title": s["course"].title,
                        "students": s["num_students"],
                        "avg_progress": s["avg_progress"],
                        "revenue": s["revenue"],
                    }
                    for s in stats_per_course
                ]
            }
            resp = client.responses.create(
                model="gpt-5.1-nano",
                input=(
                    "You are an analytics coach for an online trainer platform. "
                    "Given this JSON data, write a short, friendly summary "
                    "of how the trainer is doing and 3 concrete suggestions:\n\n"
                    + json.dumps(context)
                ),
            )
            ai_summary = resp.output[0].content[0].text
    except Exception as e:
        print("AI insights error:", e)

        # --- Revenue distribution for pie chart ---
    revenue_data = [
        {
            "label": s["course"].title,
            "value": float(s["revenue"])
        }
        for s in stats_per_course
        if s["revenue"] > 0
    ]
    # --- Revenue distribution data for pie chart ---
    revenue_data = []
    for s in stats_per_course:
        if s["revenue"] > 0:
            revenue_data.append({
                "label": s["course"].title,
                "value": round(s["revenue"], 2),
                "course_id": s["course"].id,
            })

    return render_template(
        "trainer_insights.html",
        revenue_data=revenue_data,
        user=current_user,
        stats_per_course=stats_per_course,
        top_by_revenue=top_by_revenue,
        top_by_students=top_by_students,
        student_health=student_health,
        assessment_summaries=assessment_summaries,
        ai_summary=ai_summary,
    )


@app.route("/trainer/student-assessments/<int:sa_id>/ai-feedback", methods=["POST"])
@login_required(role="trainer")
def trainer_ai_feedback(current_user, sa_id):
    sa = StudentAssessment.query.get_or_404(sa_id)
    assessment = sa.assessment
    course = Course.query.get_or_404(assessment.course_id)

    # security: trainer must own this course
    if course.trainer_id != current_user.id:
        flash("You are not allowed to generate feedback for this assessment.", "error")
        return redirect(url_for("trainer_dashboard"))

    # load all questions and answers for this attempt
    questions = Question.query.filter_by(assessment_id=assessment.id).all()
    answers = StudentAnswer.query.filter_by(student_assessment_id=sa.id).all()
    answers_by_q_id = {a.question_id: a for a in answers}

    # build a compact context for AI
    q_data = []
    for q in questions:
        ans = answers_by_q_id.get(q.id)
        q_data.append({
            "question": q.text,
            "options": {
                "A": q.option_a,
                "B": q.option_b,
                "C": q.option_c,
                "D": q.option_d,
            },
            "correct": q.correct_option,
            "marks": q.marks,
            "student_answer": ans.answer_option if ans else None,
            "student_marks": ans.marks_obtained if ans else 0.0,
        })

    context = {
        "course_title": course.title,
        "assessment_title": assessment.title,
        "student_name": sa.student.name,
        "score_obtained": sa.score_obtained,
        "total_marks": sa.total_marks,
        "questions": q_data,
    }

    feedback_text = None
    try:
        client = get_ai_client()
        if not client:
            raise RuntimeError("No AI client configured")

        resp = client.responses.create(
            model="gpt-5.1-nano",
            input=(
                "You are a supportive teacher. Based on this JSON data of a student's assessment, "
                "write concise feedback to the student, with:\n"
                "- 2 bullet points: what they did well\n"
                "- 2–3 bullet points: what to improve\n"
                "- 1 short suggestion: what to study next.\n\n"
                + json.dumps(context)
            ),
        )
        feedback_text = resp.output[0].content[0].text
    except Exception as e:
        print("AI feedback error:", e)
        flash("Could not generate AI feedback. Check your API key / quota.", "error")
        return redirect(request.referrer or url_for("trainer_dashboard"))

    sa.feedback = feedback_text
    db.session.commit()
    flash("AI feedback generated and saved.", "success")
    return redirect(request.referrer or url_for("trainer_dashboard"))


@app.route("/trainer/courses/<int:course_id>/ai-plan", methods=["POST"])
@login_required(role="trainer")
def trainer_course_ai_plan(current_user, course_id):
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()

    # gather some context: title, level, duration, maybe video titles
    videos = VideoLecture.query.filter_by(course_id=course.id).order_by(VideoLecture.uploaded_at.asc()).all()
    video_titles = [v.title for v in videos]

    context = {
        "title": course.title,
        "level": course.level,
        "duration_hours": course.duration_hours,
        "video_titles": video_titles,
    }

    outline = None
    try:
        client = get_ai_client()
        if not client:
            raise RuntimeError("No AI client configured")

        resp = client.responses.create(
            model="gpt-5.1-nano",
            input=(
                "You are a course designer. Given this course info (JSON), "
                "design a structured lesson plan with modules. "
                "Return JSON only with this structure:\n"
                "{ \"modules\": [ {\"title\": str, \"outcomes\": [str], \"suggested_assessments\": [str] } ] }\n\n"
                + json.dumps(context)
            ),
        )
        raw_text = resp.output[0].content[0].text
        # try to parse JSON; if fails, just store raw text
        try:
            outline = json.loads(raw_text)
        except Exception:
            outline = {"raw": raw_text}

    except Exception as e:
        print("AI planner error:", e)
        flash("Could not generate AI lesson plan. Check your API key / quota.", "error")
        return redirect(request.referrer or url_for("trainer_course_detail", course_id=course.id))

    course.ai_outline_json = json.dumps(outline)
    db.session.commit()
    flash("AI lesson plan generated for this course.", "success")
    return redirect(url_for("trainer_course_detail", course_id=course.id))

# ========== TRAINER: COURSES PAGES ==========

@app.route("/trainer/courses")
@login_required(role="trainer")
def trainer_courses(current_user):
    courses = Course.query.filter_by(trainer_id=current_user.id).order_by(Course.id.desc()).all()
    return render_template(
        "trainer_courses.html",
        user=current_user,
        courses=courses,
    )

# ========== TRAINER: STUDENTS LIST ==========

@app.route("/trainer/students")
@login_required(role="trainer")
def trainer_students(current_user):
    # find all enrollments in trainer's courses
    trainer_course_ids = [c.id for c in Course.query.filter_by(trainer_id=current_user.id).all()]
    if not trainer_course_ids:
        students_data = []
    else:
        enrollments = Enrollment.query.filter(Enrollment.course_id.in_(trainer_course_ids)).all()
        by_student = defaultdict(list)
        for e in enrollments:
            by_student[e.student_id].append(e)

        student_ids = list(by_student.keys())
        students = Student.query.filter(Student.id.in_(student_ids)).all()

        students_data = []
        for s in students:
            s_enrs = by_student[s.id]
            total_courses = len(s_enrs)
            avg_progress = int(sum(e.progress for e in s_enrs) / total_courses) if total_courses else 0
            if not s.is_active:
                status = "Inactive"
            else:
                status = "Active" if any(e.status == "In Progress" for e in s_enrs) else "Completed"

            students_data.append({
                "student": s,
                "total_courses": total_courses,
                "avg_progress": avg_progress,
                "status": status
            })


        students_data.sort(key=lambda x: x["student"].name.lower())

    return render_template(
        "trainer_students.html",
        user=current_user,
        students_data=students_data,
    )

@app.route("/trainer/students/<int:student_id>/toggle-status", methods=["POST"])
@login_required(role="trainer")
def trainer_student_toggle_status(current_user, student_id):
    student = Student.query.get_or_404(student_id)

    # Check that student belongs to at least one of trainer's courses
    trainer_course_ids = [c.id for c in Course.query.filter_by(trainer_id=current_user.id).all()]
    if not trainer_course_ids:
        flash("You do not have any courses yet.", "error")
        return redirect(url_for("trainer_students"))

    linked_enrollment = Enrollment.query.filter(
        Enrollment.student_id == student.id,
        Enrollment.course_id.in_(trainer_course_ids)
    ).first()

    if not linked_enrollment:
        flash("You are not allowed to modify this student.", "error")
        return redirect(url_for("trainer_students"))

    student.is_active = not (student.is_active if student.is_active is not None else True)
    db.session.commit()

    flash(f"Student is now {'Active' if student.is_active else 'Inactive'}.", "success")
    return redirect(request.referrer or url_for("trainer_students"))


# ========== TRAINER: STUDENT ANALYTICS ==========

@app.route("/trainer/students/<int:student_id>")
@login_required(role="trainer")
def trainer_student_detail(current_user, student_id):
    student = Student.query.get_or_404(student_id)

    # ensure this student is in at least one of trainer's courses
    trainer_course_ids = [c.id for c in Course.query.filter_by(trainer_id=current_user.id).all()]
    if not trainer_course_ids:
        flash("You do not have any courses yet.", "error")
        return redirect(url_for("trainer_dashboard"))

    enrollments = Enrollment.query.filter(
        Enrollment.student_id == student.id,
        Enrollment.course_id.in_(trainer_course_ids)
    ).all()

    if not enrollments:
        flash("This student is not enrolled in your courses.", "error")
        return redirect(url_for("trainer_students"))





    # per-course metrics
    course_summaries = []
    for e in enrollments:
        course = e.course
        total_lectures = len(course.videos)
        watched_lectures = int(round(total_lectures * e.progress / 100)) if total_lectures else 0
        remaining_lectures = max(total_lectures - watched_lectures, 0)

        summary = {
            "course": course,
            "enrollment": e,
            "total_lectures": total_lectures,
            "watched_lectures": watched_lectures,
            "remaining_lectures": remaining_lectures,
        }

        # --- NEW: assessment stats for this student in this course ---
        # all StudentAssessment rows for (student, assessments of this course)
        sa_list = StudentAssessment.query.join(Assessment).filter(
            StudentAssessment.student_id == student.id,
            StudentAssessment.assessment_id == Assessment.id,
            Assessment.course_id == course.id
        ).all()

        if sa_list:
            sa_ids = [sa.id for sa in sa_list]
            answers = StudentAnswer.query.filter(
                StudentAnswer.student_assessment_id.in_(sa_ids)
            ).all()

            total_assessments = len(sa_list)
            attempted_assessments = sum(1 for sa in sa_list if sa.status in ("Submitted", "Graded"))

            total_marks_obtained = sum(sa.score_obtained for sa in sa_list)
            total_marks_available = sum(sa.total_marks for sa in sa_list)

            attempted_questions = len([a for a in answers if a.answer_option])
            correct_answers = len([a for a in answers if a.is_correct])

            last_dates = [sa.submitted_at or sa.assigned_at for sa in sa_list if (sa.submitted_at or sa.assigned_at)]
            last_assessment_date = max(last_dates) if last_dates else None

            assessment_stats = {
                "total_assessments": total_assessments,
                "attempted_assessments": attempted_assessments,
                "total_marks_obtained": total_marks_obtained,
                "total_marks_available": total_marks_available,
                "attempted_questions": attempted_questions,
                "correct_answers": correct_answers,
                "last_assessment_date": last_assessment_date,
            }
        else:
            assessment_stats = None

        summary["assessment_stats"] = assessment_stats
        course_summaries.append(summary)







    # analytics: daily hours (last 14 days) & monthly
    today = date.today()
    start_daily = today - timedelta(days=13)  # 14 days window
    logs = StudyLog.query.filter(
        StudyLog.student_id == student.id,
        StudyLog.course_id.in_(trainer_course_ids),
        StudyLog.date >= start_daily,
        StudyLog.date <= today
    ).all()

    # daily
    daily_map = { (start_daily + timedelta(days=i)): 0.0 for i in range(14) }
    for log in logs:
        if log.date in daily_map:
            daily_map[log.date] += log.hours

    daily_labels = [d.strftime("%d %b") for d in sorted(daily_map.keys())]
    daily_values = [round(daily_map[d], 2) for d in sorted(daily_map.keys())]

    # monthly (group all time)
    monthly = defaultdict(float)
    all_logs = StudyLog.query.filter(
        StudyLog.student_id == student.id,
        StudyLog.course_id.in_(trainer_course_ids)
    ).all()
    for log in all_logs:
        key = log.date.strftime("%Y-%m")  # e.g. 2025-12
        monthly[key] += log.hours

    monthly_labels = sorted(monthly.keys())
    monthly_values = [round(monthly[m], 2) for m in monthly_labels]

    # summary for overview
    total_hours = sum(monthly_values)
    avg_progress_all = int(sum(e.progress for e in enrollments) / len(enrollments)) if enrollments else 0

    return render_template(
        "trainer_student_detail.html",
        user=current_user,
        student=student,
        course_summaries=course_summaries,
        total_hours=total_hours,
        avg_progress_all=avg_progress_all,
        enrollments=enrollments,
        daily_labels=daily_labels,
        daily_values=daily_values,
        monthly_labels=monthly_labels,
        monthly_values=monthly_values,
    )

# ========== TRAINER: STUDENT PER-COURSE REPORT ==========

@app.route("/trainer/students/<int:student_id>/course/<int:course_id>", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_student_course_detail(current_user, student_id, course_id):
    student = Student.query.get_or_404(student_id)
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()

    enrollment = Enrollment.query.filter_by(
        student_id=student.id,
        course_id=course.id
    ).first_or_404()

    # allow trainer to update hours and test score
    if request.method == "POST":
        try:
            hours = float(request.form.get("hours_watched") or enrollment.hours_watched)
        except ValueError:
            hours = enrollment.hours_watched
        try:
            tests_score = float(request.form.get("tests_score") or enrollment.tests_score)
        except ValueError:
            tests_score = enrollment.tests_score

        enrollment.hours_watched = hours
        enrollment.tests_score = max(0.0, min(100.0, tests_score))
        db.session.commit()
        flash("Progress details updated.", "success")
        return redirect(url_for("trainer_student_course_detail",
                                student_id=student.id, course_id=course.id))

    # lectures info
    total_lectures = len(course.videos)
    watched_lectures = int(round(total_lectures * enrollment.progress / 100)) if total_lectures else 0
    remaining_lectures = max(total_lectures - watched_lectures, 0)

    # daily hours for this course (last 14 days)
    today = date.today()
    start_daily = today - timedelta(days=13)
    logs = StudyLog.query.filter(
        StudyLog.student_id == student.id,
        StudyLog.course_id == course.id,
        StudyLog.date >= start_daily,
        StudyLog.date <= today
    ).all()

    daily_map = { (start_daily + timedelta(days=i)): 0.0 for i in range(14) }
    for log in logs:
        if log.date in daily_map:
            daily_map[log.date] += log.hours

    daily_labels = [d.strftime("%d %b") for d in sorted(daily_map.keys())]
    daily_values = [round(daily_map[d], 2) for d in sorted(daily_map.keys())]

    return render_template(
        "trainer_student_course_detail.html",
        user=current_user,
        student=student,
        course=course,
        enrollment=enrollment,
        total_lectures=total_lectures,
        watched_lectures=watched_lectures,
        remaining_lectures=remaining_lectures,
        daily_labels=daily_labels,
        daily_values=daily_values,
    )


@app.route("/trainer/courses/new", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_course_new(current_user):
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        level = request.form.get("level", "").strip() or "Beginner"
        duration_hours = request.form.get("duration_hours", "6").strip()
        color = request.form.get("color", "").strip() or "#0f766e"

        if not title:
            flash("Course title is required.", "error")
            return redirect(url_for("trainer_course_new"))

        try:
            duration_hours = int(duration_hours)
        except ValueError:
            duration_hours = 6

        course = Course(
            title=title,
            level=level,
            duration_hours=duration_hours,
            color=color,
            trainer_id=current_user.id,
        )
        db.session.add(course)
        db.session.commit()
        flash("Course created successfully.", "success")
        return redirect(url_for("trainer_courses"))

    return render_template("trainer_course_form.html", user=current_user, mode="new")


@app.route("/trainer/courses/<int:course_id>/edit", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_course_edit(current_user, course_id):
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        level = request.form.get("level", "").strip() or "Beginner"
        duration_hours = request.form.get("duration_hours", "6").strip()
        color = request.form.get("color", "").strip() or "#0f766e"

        if not title:
            flash("Course title is required.", "error")
            return redirect(url_for("trainer_course_edit", course_id=course.id))

        try:
            duration_hours = int(duration_hours)
        except ValueError:
            duration_hours = course.duration_hours

        course.title = title
        course.level = level
        course.duration_hours = duration_hours
        course.color = color

        db.session.commit()
        flash("Course updated successfully.", "success")
        return redirect(url_for("trainer_courses"))

    return render_template("trainer_course_form.html", user=current_user, mode="edit", course=course)

@app.route("/trainer/courses/<int:course_id>")
@login_required(role="trainer")
def trainer_course_detail(current_user, course_id):
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()

    # Videos
    videos = VideoLecture.query.filter_by(course_id=course.id) \
                               .order_by(VideoLecture.uploaded_at.desc()).all()

    # Other resources
    assets = CourseAsset.query.filter_by(course_id=course.id) \
                              .order_by(CourseAsset.uploaded_at.desc()).all()
    pdf_assets = [a for a in assets if a.type == "pdf"]
    image_assets = [a for a in assets if a.type == "image"]
    ppt_assets = [a for a in assets if a.type == "ppt"]
    audio_assets = [a for a in assets if a.type == "audio"]
    doc_assets = [a for a in assets if a.type == "doc"]
    other_assets = [a for a in assets if a.type not in {"pdf", "image", "ppt", "audio", "doc"}]

    # 🔹 Enrollments & students for THIS course
    enrollments = (
        Enrollment.query
        .filter_by(course_id=course.id)
        .join(Student, Enrollment.student_id == Student.id)
        .order_by(Student.name.asc())
        .all()
    )

    return render_template(
        "trainer_course_detail.html",
        user=current_user,
        course=course,
        videos=videos,
        pdf_assets=pdf_assets,
        image_assets=image_assets,
        ppt_assets=ppt_assets,
        audio_assets=audio_assets,
        doc_assets=doc_assets,
        other_assets=other_assets,
        enrollments=enrollments,   # 👈 new
    )



@app.route("/trainer/courses/<int:course_id>/price", methods=["POST"])
@login_required(role="trainer")
def trainer_course_update_price(current_user, course_id):
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()
    raw_price = request.form.get("price") or ""
    try:
        price = float(raw_price)
    except ValueError:
        flash("Invalid price.", "error")
        return redirect(request.referrer or url_for("trainer_courses"))

    if price < 0:
        price = 0.0

    course.price = price
    db.session.commit()
    flash("Course price updated.", "success")
    return redirect(request.referrer or url_for("trainer_courses"))

import tempfile

BASE_UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), "uploads")
VIDEOS_UPLOAD_FOLDER = os.path.join(BASE_UPLOAD_FOLDER, "videos")
RESOURCES_UPLOAD_FOLDER = os.path.join(BASE_UPLOAD_FOLDER, "resources")

os.makedirs(VIDEOS_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESOURCES_UPLOAD_FOLDER, exist_ok=True)

class CourseAsset(db.Model):
    __tablename__ = "course_asset"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)

    # 'pdf', 'image', 'ppt', 'audio', 'doc', 'other'
    type = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False, default=0)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    course = db.relationship("Course", lazy=True)

def guess_asset_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in {".pdf"}:
        return "pdf"
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        return "image"
    if ext in {".ppt", ".pptx"}:
        return "ppt"
    if ext in {".mp3", ".wav", ".m4a", ".aac"}:
        return "audio"
    if ext in {".doc", ".docx"}:
        return "doc"
    return "other"


@app.route("/trainer/students/<int:student_id>/ai-feedback", methods=["POST"])
@login_required(role="trainer")
def trainer_student_ai_feedback(current_user, student_id):
    student = Student.query.get_or_404(student_id)

    # ensure this student belongs to at least one of trainer's courses
    trainer_course_ids = [c.id for c in Course.query.filter_by(trainer_id=current_user.id).all()]
    if not trainer_course_ids:
        flash("You do not have any courses yet.", "error")
        return redirect(url_for("trainer_students"))

    enrollments = Enrollment.query.filter(
        Enrollment.student_id == student.id,
        Enrollment.course_id.in_(trainer_course_ids)
    ).all()

    if not enrollments:
        flash("This student is not enrolled in your courses.", "error")
        return redirect(url_for("trainer_students"))

    # Build compact performance summary text
    lines = []
    for e in enrollments:
        lines.append(
            f"- Course: {e.course.title} | Progress: {e.progress}% | "
            f"Hours watched: {e.hours_watched:.1f} | Test score: {e.tests_score:.1f}%"
        )
    perf_text = "\n".join(lines)

    prompt = f"""
You are an expert mentor for online courses.

Student name: {student.name}
Data from trainer's courses:
{perf_text}

Write a concise feedback report for the trainer, with sections:
1) Overall summary of the student's learning behaviour
2) Strengths (bullet points)
3) Areas to improve (bullet points)
4) Concrete next steps the trainer can take (bullet points)

Keep it under 350 words.
"""

    ai_feedback = "AI feedback is not available (no API client configured)."

    try:
        # Reuse the same OpenAI client you already use for AI quiz, WITHOUT temperature param
        from openai import OpenAI  # if not already imported at top
        from ai_utils import get_client

        client = get_client()

        resp = client.responses.create(
            model="gpt-5.1-nano",   # same model you used for quizzes
            input=prompt
        )

        # Adjust this extraction exactly like you did in your AI quiz code
        try:
            ai_feedback = resp.output[0].content[0].text
        except Exception:
            ai_feedback = str(resp)

    except Exception as e:
        print("AI student feedback error:", e)
        flash("Could not generate AI feedback (check API key / quota).", "error")
        return redirect(url_for("trainer_students"))

    # Render a simple page showing the feedback
    return render_template(
        "trainer_student_ai_feedback.html",
        user=current_user,
        student=student,
        enrollments=enrollments,
        ai_feedback=ai_feedback,
    )



@app.route("/trainer/courses/<int:course_id>/assets/upload", methods=["POST"])
@login_required(role="trainer")
def trainer_asset_upload(current_user, course_id):
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()

    file = request.files.get("asset_file")
    if not file or file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("trainer_course_detail", course_id=course.id))

    original_name = file.filename
    safe_name = secure_filename(original_name)
    if not safe_name:
        flash("Invalid file name.", "error")
        return redirect(url_for("trainer_course_detail", course_id=course.id))

    file_path = os.path.join(RESOURCES_UPLOAD_FOLDER, safe_name)

    # avoid overwriting
    base, ext = os.path.splitext(safe_name)
    counter = 1
    while os.path.exists(file_path):
        safe_name = f"{base}_{counter}{ext}"
        file_path = os.path.join(RESOURCES_UPLOAD_FOLDER, safe_name)
        counter += 1

    file.save(file_path)
    size_bytes = os.path.getsize(file_path)

    asset_type = guess_asset_type(safe_name)
    asset = CourseAsset(
        course_id=course.id,
        type=asset_type,
        title=original_name,
        filename=safe_name,
        size_bytes=size_bytes,
    )
    db.session.add(asset)
    db.session.commit()
    flash("File uploaded.", "success")
    return redirect(url_for("trainer_course_detail", course_id=course.id))

@app.route("/trainer/courses/<int:course_id>/revenue")
@login_required(role="trainer")
def trainer_course_revenue(current_user, course_id):
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()
    enrollments = Enrollment.query.filter_by(course_id=course.id).all()

    course_price = course.price or 0.0
    total_revenue = len(enrollments) * course_price

    month_labels = []
    month_values = []

    if enrollments:
        # find earliest enrollment date
        valid_dates = [e.enrolled_at.date() for e in enrollments if e.enrolled_at]
        if valid_dates:
            from datetime import date

            first_date = min(valid_dates)
            today = date.today()

            # start at first day of first month, end at first day of current month
            start_month = date(first_date.year, first_date.month, 1)
            end_month = date(today.year, today.month, 1)

            # helper: add one month
            def add_month(d: date) -> date:
                if d.month == 12:
                    return date(d.year + 1, 1, 1)
                else:
                    return date(d.year, d.month + 1, 1)

            # pre-group enrollments by (year, month)
            from collections import defaultdict
            monthly_counts = defaultdict(int)
            for e in enrollments:
                if not e.enrolled_at:
                    continue
                y = e.enrolled_at.year
                m = e.enrolled_at.month
                monthly_counts[(y, m)] += 1

            cur = start_month
            while cur <= end_month:
                y, m = cur.year, cur.month
                count = monthly_counts.get((y, m), 0)
                revenue = count * course_price

                month_labels.append(cur.strftime("%b %Y"))  # e.g. "Dec 2025"
                month_values.append(round(revenue, 2))

                cur = add_month(cur)

    return render_template(
        "trainer_course_revenue.html",
        user=current_user,
        course=course,
        total_revenue=total_revenue,
        month_labels=month_labels,
        month_values=month_values,
    )


@app.route("/trainer/assets/<int:asset_id>/rename", methods=["POST"])
@login_required(role="trainer")
def trainer_asset_rename(current_user, asset_id):
    asset = CourseAsset.query.get_or_404(asset_id)
    course = asset.course
    if course.trainer_id != current_user.id:
        flash("Not allowed.", "error")
        return redirect(url_for("trainer_dashboard"))

    title = (request.form.get("title") or "").strip()
    if not title:
        flash("Title cannot be empty.", "error")
        return redirect(url_for("trainer_course_detail", course_id=course.id))

    asset.title = title
    db.session.commit()
    flash("Resource renamed.", "success")
    return redirect(url_for("trainer_course_detail", course_id=course.id))


@app.route("/trainer/assets/<int:asset_id>/delete", methods=["POST"])
@login_required(role="trainer")
def trainer_asset_delete(current_user, asset_id):
    asset = CourseAsset.query.get_or_404(asset_id)
    course = asset.course
    if course.trainer_id != current_user.id:
        flash("Not allowed.", "error")
        return redirect(url_for("trainer_dashboard"))

    file_path = os.path.join(RESOURCES_UPLOAD_FOLDER, asset.filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass

    db.session.delete(asset)
    db.session.commit()
    flash("Resource deleted.", "success")
    return redirect(url_for("trainer_course_detail", course_id=course.id))



@app.route("/trainer/courses/<int:course_id>/videos/upload", methods=["POST"])
@login_required(role="trainer")
def trainer_video_upload(current_user, course_id):

    course = Course.query.filter_by(
        id=course_id,
        trainer_id=current_user.id
    ).first_or_404()

    file = request.files.get("video_file")
    title = (request.form.get("title") or "").strip()

    if not file or file.filename == "":
        flash("Please select a video file.", "error")
        return redirect(url_for("trainer_course_detail", course_id=course.id))

    filename = secure_filename(file.filename)
    unique_name = f"{course.id}_{int(datetime.utcnow().timestamp())}_{filename}"
    save_path = os.path.join(app.config["VIDEO_UPLOAD_FOLDER"], unique_name)
    file.save(save_path)

    if not title:
        title = os.path.splitext(filename)[0]

    transcript = None
    summary = None

    try:
        # 1️⃣ Extract audio
        audio_path = save_path.replace(".mp4", ".wav")
        os.system(
            f'ffmpeg -i "{save_path}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{audio_path}" -y'
        )

        # 2️⃣ Transcribe + summarize
        from ai_utils import transcribe_audio, summarize_text
        transcript = transcribe_audio(audio_path)
        summary = summarize_text(transcript)

        if not summary:
            raise ValueError("Summary generation returned empty text")

        # 3️⃣ CREATE SUMMARY FILE (THIS IS THE KEY PART)
        base_dir = os.getcwd()
        summary_dir = os.path.join(tempfile.gettempdir(), "summaries")
        os.makedirs(summary_dir, exist_ok=True)

        # ⚠️ video_id not available yet, so use filename timestamp
        summary_file_path = os.path.join(
            summary_dir,
            f"video_{unique_name}.txt"
        )

        with open(summary_file_path, "w", encoding="utf-8") as f:
            f.write(summary)

        flash("Video uploaded and summary generated successfully!", "success")

    except Exception as e:
        print("AI processing error:", e)
        flash("Video uploaded, but summary generation failed.", "warning")

    # 4️⃣ Save to DB
    video = VideoLecture(
        course_id=course.id,
        title=title,
        filename=unique_name,
        transcript=transcript,
        summary=summary
    )

    db.session.add(video)
    db.session.commit()

    return redirect(url_for("trainer_course_detail", course_id=course.id))

@app.route("/trainer/videos/<int:video_id>/rename", methods=["POST"])
@login_required(role="trainer")
def trainer_video_rename(current_user, video_id):
    video = VideoLecture.query.get_or_404(video_id)

    # ensure trainer owns this course
    if video.course.trainer_id != current_user.id:
        flash("You are not allowed to modify this video.", "error")
        return redirect(url_for("trainer_dashboard"))

    new_title = (request.form.get("title") or "").strip()
    if not new_title:
        flash("Title cannot be empty.", "error")
        return redirect(url_for("trainer_course_detail", course_id=video.course_id))

    video.title = new_title
    db.session.commit()
    flash("Video title updated.", "success")
    return redirect(url_for("trainer_course_detail", course_id=video.course_id))

@app.route("/trainer/videos/<int:video_id>/delete", methods=["POST"])
@login_required(role="trainer")
def trainer_video_delete(current_user, video_id):
    video = VideoLecture.query.get_or_404(video_id)

    if video.course.trainer_id != current_user.id:
        flash("You are not allowed to delete this video.", "error")
        return redirect(url_for("trainer_dashboard"))

    # try to delete the file from disk
    file_path = os.path.join(app.config['VIDEO_UPLOAD_FOLDER'], video.filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        # don't crash if file deletion fails
        pass

    course_id = video.course_id
    db.session.delete(video)
    db.session.commit()

    flash("Video deleted.", "success")
    return redirect(url_for("trainer_course_detail", course_id=course_id))

@app.route("/trainer/videos/<int:video_id>/generate_summary", methods=["POST"])
@login_required(role="trainer")
def trainer_video_generate_summary(current_user, video_id):

    video = VideoLecture.query.get_or_404(video_id)
    course = video.course

    if course.trainer_id != current_user.id:
        flash("Not allowed.", "error")
        return redirect(url_for("trainer_dashboard"))

    video_path = os.path.join(app.config['VIDEO_UPLOAD_FOLDER'], video.filename)
    audio_path = video_path.replace(".mp4", ".wav")

    try:
        # 1️⃣ Extract audio
        os.system(
            f'ffmpeg -i "{video_path}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{audio_path}" -y'
        )

        from ai_utils import transcribe_audio, summarize_text

        # 2️⃣ Transcription
        transcript = transcribe_audio(audio_path)

        # 3️⃣ Summary
        summary = summarize_text(transcript)

        # 4️⃣ Save to DB
        video.transcript = transcript
        video.summary = summary
        db.session.commit()

        # 5️⃣ SAVE TO FILE (IMPORTANT FOR DEBUG)
        summary_dir = os.path.join(os.getcwd(), "summaries")
        os.makedirs(summary_dir, exist_ok=True)

        summary_file = os.path.join(summary_dir, f"video_{video.id}.txt")

        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(summary)

        flash("AI transcription & summary generated successfully!", "success")

    except Exception as e:
        print("AI video processing error:", e)
        flash(f"AI summary generation failed: {str(e)}", "error")

    return redirect(url_for("trainer_course_detail", course_id=course.id))





@app.route("/trainer/courses/<int:course_id>/delete", methods=["POST"])
@login_required(role="trainer")
def trainer_course_delete(current_user, course_id):
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted.", "success")
    return redirect(url_for("trainer_courses"))


# ========== TRAINER: ASSESSMENTS FOR A COURSE ==========

@app.route("/trainer/courses/<int:course_id>/assessments")
@login_required(role="trainer")
def trainer_course_assessments(current_user, course_id):
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()
    assessments = Assessment.query.filter_by(course_id=course.id).order_by(Assessment.id.desc()).all()

    return render_template(
        "trainer_course_assessments.html",
        user=current_user,
        course=course,
        assessments=assessments,
    )

@app.route("/trainer/courses/<int:course_id>/assessments/new", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_assessment_new(current_user, course_id):
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        type_ = (request.form.get("type") or "Quiz").strip()
        total_marks = request.form.get("total_marks") or "100"
        passing_marks = request.form.get("passing_marks") or "40"
        due_date_str = request.form.get("due_date") or ""

        if not title:
            flash("Title is required.", "error")
            return redirect(url_for("trainer_assessment_new", course_id=course.id))

        try:
            total_marks = float(total_marks)
        except ValueError:
            total_marks = 100.0
        try:
            passing_marks = float(passing_marks)
        except ValueError:
            passing_marks = 40.0

        due_date = None
        if due_date_str:
            try:
                # Expect format: YYYY-MM-DDTHH:MM from <input type="datetime-local">
                due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                due_date = None

        assessment = Assessment(
            course_id=course.id,
            title=title,
            description=description,
            type=type_,
            total_marks=total_marks,
            passing_marks=passing_marks,
            due_date=due_date,
            is_published=("is_published" in request.form),
        )
        db.session.add(assessment)
        db.session.commit()
        flash("Assessment created. Now add questions.", "success")
        return redirect(url_for("trainer_assessment_edit", course_id=course.id, assessment_id=assessment.id))

    return render_template(
        "trainer_assessment_form.html",
        user=current_user,
        course=course,
        mode="new",
    )

@app.route("/trainer/courses/<int:course_id>/assessments/<int:assessment_id>/edit", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_assessment_edit(current_user, course_id, assessment_id):
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()
    assessment = Assessment.query.filter_by(id=assessment_id, course_id=course.id).first_or_404()

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        type_ = (request.form.get("type") or "Quiz").strip()
        total_marks = request.form.get("total_marks") or "100"
        passing_marks = request.form.get("passing_marks") or "40"
        due_date_str = request.form.get("due_date") or ""

        if not title:
            flash("Title is required.", "error")
            return redirect(url_for("trainer_assessment_edit", course_id=course.id, assessment_id=assessment.id))

        try:
            total_marks = float(total_marks)
        except ValueError:
            total_marks = assessment.total_marks
        try:
            passing_marks = float(passing_marks)
        except ValueError:
            passing_marks = assessment.passing_marks

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                due_date = assessment.due_date

        assessment.title = title
        assessment.description = description
        assessment.type = type_
        assessment.total_marks = total_marks
        assessment.passing_marks = passing_marks
        assessment.due_date = due_date
        assessment.is_published = ("is_published" in request.form)

        db.session.commit()
        flash("Assessment updated.", "success")
        return redirect(url_for("trainer_assessment_edit", course_id=course.id, assessment_id=assessment.id))

    questions = Question.query.filter_by(assessment_id=assessment.id).all()

    # Format due_date for datetime-local input
    due_date_value = assessment.due_date.strftime("%Y-%m-%dT%H:%M") if assessment.due_date else ""

    return render_template(
        "trainer_assessment_form.html",
        user=current_user,
        course=course,
        assessment=assessment,
        questions=questions,
        due_date_value=due_date_value,
        mode="edit",
    )




@app.route("/trainer/courses/<int:course_id>/assessments/<int:assessment_id>/questions/new", methods=["POST"])
@login_required(role="trainer")
def trainer_question_new(current_user, course_id, assessment_id):
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()
    assessment = Assessment.query.filter_by(id=assessment_id, course_id=course.id).first_or_404()

    text = (request.form.get("text") or "").strip()
    option_a = (request.form.get("option_a") or "").strip()
    option_b = (request.form.get("option_b") or "").strip()
    option_c = (request.form.get("option_c") or "").strip()
    option_d = (request.form.get("option_d") or "").strip()
    correct_option = (request.form.get("correct_option") or "").strip().upper() or None
    marks = request.form.get("marks") or "1"

    if not text:
        flash("Question text is required.", "error")
        return redirect(url_for("trainer_assessment_edit", course_id=course.id, assessment_id=assessment.id))

    try:
        marks = float(marks)
    except ValueError:
        marks = 1.0

    question = Question(
        assessment_id=assessment.id,
        text=text,
        option_a=option_a or None,
        option_b=option_b or None,
        option_c=option_c or None,
        option_d=option_d or None,
        correct_option=correct_option if correct_option in {"A", "B", "C", "D"} else None,
        marks=marks,
    )
    db.session.add(question)
    db.session.commit()
    flash("Question added.", "success")
    return redirect(url_for("trainer_assessment_edit", course_id=course.id, assessment_id=assessment.id))


@app.route("/trainer/questions/<int:question_id>/delete", methods=["POST"])
@login_required(role="trainer")
def trainer_question_delete(current_user, question_id):
    question = Question.query.get_or_404(question_id)
    assessment = question.assessment

    # get course via course_id
    course = Course.query.get_or_404(assessment.course_id)

    # security: ensure trainer owns this course
    if course.trainer_id != current_user.id:
        flash("Not allowed.", "error")
        return redirect(url_for("trainer_dashboard"))

    course_id = course.id
    assessment_id = assessment.id

    db.session.delete(question)
    db.session.commit()
    flash("Question deleted.", "success")
    return redirect(url_for("trainer_assessment_edit", course_id=course_id, assessment_id=assessment_id))



@app.route("/trainer/courses/<int:course_id>/assessments/<int:assessment_id>/ai-quiz", methods=["POST"])
@login_required(role="trainer")
def trainer_assessment_ai_quiz(current_user, course_id, assessment_id):
    """
    Use OpenAI to generate MCQs for an existing assessment and save them as Question rows.
    """
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()
    assessment = Assessment.query.filter_by(id=assessment_id, course_id=course.id).first_or_404()

    source = (request.form.get("source_text") or "").strip()
    num_q_raw = request.form.get("num_questions") or "5"

    try:
        num_questions = max(1, min(20, int(num_q_raw)))
    except ValueError:
        num_questions = 5

    if not source:
        flash("Provide some text or notes for AI to generate questions from.", "error")
        return redirect(url_for("trainer_assessment_edit", course_id=course.id, assessment_id=assessment.id))

    try:
        quiz_items = generate_quiz_from_text(source, num_questions=num_questions)
    except Exception as e:
        print("AI quiz error:", e)
        flash("AI quiz generation failed. Check your API key or try again later.", "error")
        return redirect(url_for("trainer_assessment_edit", course_id=course.id, assessment_id=assessment.id))

    created = 0
    for q in quiz_items:
        text = (q.get("text") or "").strip()
        options = q.get("options") or {}
        correct = (q.get("correct") or "").strip().upper()
        marks = q.get("marks", 1.0)

        if not text:
            continue

        # Normalize marks
        try:
            marks_val = float(marks)
        except (ValueError, TypeError):
            marks_val = 1.0

        question = Question(
            assessment_id=assessment.id,
            text=text,
            option_a=options.get("A"),
            option_b=options.get("B"),
            option_c=options.get("C"),
            option_d=options.get("D"),
            correct_option=correct if correct in {"A", "B", "C", "D"} else None,
            marks=marks_val,
        )
        db.session.add(question)
        created += 1

    db.session.commit()
    if created:
        flash(f"AI generated {created} questions and added them to this assessment.", "success")
    else:
        flash("AI did not produce any valid questions. Try with more detailed content.", "error")

    return redirect(url_for("trainer_assessment_edit", course_id=course.id, assessment_id=assessment.id))


class StudentAssessment(db.Model):
    __tablename__ = "student_assessment"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey("assessment.id"), nullable=False)
    assigned_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Not Started")
    score_obtained = db.Column(db.Float, nullable=False, default=0.0)
    total_marks = db.Column(db.Float, nullable=False, default=0.0)

    # NEW: AI feedback for this student’s attempt
    feedback = db.Column(db.Text, nullable=True)

    student = db.relationship("Student", lazy=True)
    assessment = db.relationship("Assessment", lazy=True)



class StudentAnswer(db.Model):
    __tablename__ = "student_answer"
    id = db.Column(db.Integer, primary_key=True)
    student_assessment_id = db.Column(db.Integer, db.ForeignKey("student_assessment.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    answer_option = db.Column(db.String(1), nullable=True)  # "A"/"B"/"C"/"D"
    is_correct = db.Column(db.Boolean, nullable=True)
    marks_obtained = db.Column(db.Float, nullable=False, default=0.0)

    student_assessment = db.relationship("StudentAssessment", lazy=True)
    question = db.relationship("Question", lazy=True)




@app.route("/trainer/courses/<int:course_id>/assessments/<int:assessment_id>/delete", methods=["POST"])
@login_required(role="trainer")
def trainer_assessment_delete(current_user, course_id, assessment_id):
    course = Course.query.filter_by(id=course_id, trainer_id=current_user.id).first_or_404()
    assessment = Assessment.query.filter_by(id=assessment_id, course_id=course.id).first_or_404()

    db.session.delete(assessment)
    db.session.commit()
    flash("Assessment deleted.", "success")
    return redirect(url_for("trainer_course_assessments", course_id=course.id))

@app.route("/trainer/assessments")
@login_required(role="trainer")
def trainer_assessments_overview(current_user):
    courses = Course.query.filter_by(trainer_id=current_user.id).all()
    course_ids = [c.id for c in courses]

    if not course_ids:
        assessments = []
    else:
        assessments = Assessment.query.filter(Assessment.course_id.in_(course_ids)) \
                                      .order_by(Assessment.id.desc()).all()

    courses_by_id = {c.id: c for c in courses}

    return render_template(
        "trainer_assessments_overview.html",
        user=current_user,
        assessments=assessments,
        courses_by_id=courses_by_id,
    )

# ========== TRAINER: SIMPLE UTILITY PAGES ==========


class Event(db.Model):
    __tablename__ = "event"
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    type = db.Column(db.String(50), nullable=False, default="Live Class")  # Live, Q&A, Deadline, Exam etc.
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)

    meeting_link = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    is_online = db.Column(db.Boolean, nullable=False, default=True)
    color = db.Column(db.String(20), nullable=True, default="#0f766e")

    trainer = db.relationship("User", lazy=True)
    course = db.relationship("Course", lazy=True)


class Announcement(db.Model):
    __tablename__ = "announcement"
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_pinned = db.Column(db.Boolean, nullable=False, default=False)

    trainer = db.relationship("User", lazy=True)
    course = db.relationship("Course", lazy=True)


class DiscussionThread(db.Model):
    __tablename__ = "discussion_thread"
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_pinned = db.Column(db.Boolean, nullable=False, default=False)
    is_locked = db.Column(db.Boolean, nullable=False, default=False)

    trainer = db.relationship("User", lazy=True)
    course = db.relationship("Course", lazy=True)
    replies = db.relationship(
        "DiscussionReply",
        backref="thread",
        lazy=True,
        cascade="all, delete-orphan"
    )


class DiscussionReply(db.Model):
    __tablename__ = "discussion_reply"
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("discussion_thread.id"), nullable=False)

    author_name = db.Column(db.String(120), nullable=False)   # for now trainer name; later extend for students
    author_role = db.Column(db.String(20), nullable=False, default="trainer")  # trainer / student
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)



@app.route("/trainer/resources")
@login_required(role="trainer")
def trainer_resources(current_user):
    # All courses of this trainer
    courses = Course.query.filter_by(trainer_id=current_user.id).all()
    course_ids = [c.id for c in courses]

    # Read filters
    q_type = request.args.get("type") or ""
    q_course = request.args.get("course_id") or ""
    q_search = (request.args.get("q") or "").strip().lower()

    # Base query: only assets from trainer's courses
    query = CourseAsset.query.join(Course, CourseAsset.course_id == Course.id) \
                             .filter(Course.trainer_id == current_user.id)

    if q_type:
        query = query.filter(CourseAsset.type == q_type)

    if q_course and q_course.isdigit():
        query = query.filter(CourseAsset.course_id == int(q_course))

    assets = query.order_by(CourseAsset.uploaded_at.desc()).all()

    # Simple search in title/filename
    if q_search:
        assets = [
            a for a in assets
            if q_search in (a.title or "").lower()
            or q_search in (a.filename or "").lower()
        ]

    courses_by_id = {c.id: c for c in courses}

    return render_template(
        "trainer_resources.html",
        user=current_user,
        assets=assets,
        courses=courses,
        courses_by_id=courses_by_id,
        q_type=q_type,
        q_course=q_course,
        q_search=q_search,
    )



@app.route("/trainer/events", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_events(current_user):
    # Trainer's courses (for dropdown)
    courses = Course.query.filter_by(trainer_id=current_user.id).all()

    # Handle create form
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        course_id = request.form.get("course_id") or ""
        start_time_str = request.form.get("start_time") or ""

        if not title or not course_id or not start_time_str:
            flash("Title, course and date/time are required.", "error")
            return redirect(url_for("trainer_events"))

        # Ensure course belongs to this trainer
        course = Course.query.filter_by(
            id=course_id,
            trainer_id=current_user.id
        ).first()

        if not course:
            flash("Invalid course selected.", "error")
            return redirect(url_for("trainer_events"))

        try:
            # from <input type="datetime-local">
            start_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Invalid date/time format.", "error")
            return redirect(url_for("trainer_events"))

        s = Session(
            course_id=course.id,
            title=title,
            start_time=start_time,
        )
        db.session.add(s)
        db.session.commit()
        flash("Session created.", "success")
        return redirect(url_for("trainer_events"))

    # GET: list upcoming + past
    now = datetime.utcnow()
    upcoming_sessions = (
        Session.query
        .join(Course)
        .filter(
            Course.trainer_id == current_user.id,
            Session.start_time >= now,
        )
        .order_by(Session.start_time.asc())
        .all()
    )

    past_sessions = (
        Session.query
        .join(Course)
        .filter(
            Course.trainer_id == current_user.id,
            Session.start_time < now,
        )
        .order_by(Session.start_time.desc())
        .limit(20)
        .all()
    )

    return render_template(
        "trainer_events.html",
        user=current_user,
        courses=courses,
        upcoming_sessions=upcoming_sessions,
        past_sessions=past_sessions,
    )


@app.route("/trainer/events/new", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_event_new(current_user):
    courses = Course.query.filter_by(trainer_id=current_user.id).all()

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        type_ = (request.form.get("type") or "Live Class").strip()
        start_str = request.form.get("start_time") or ""
        end_str = request.form.get("end_time") or ""
        meeting_link = (request.form.get("meeting_link") or "").strip()
        location = (request.form.get("location") or "").strip()
        is_online = (request.form.get("is_online") == "on")
        color = (request.form.get("color") or "#0f766e").strip()

        if not title or not start_str:
            flash("Title and start time are required.", "error")
            return redirect(url_for("trainer_event_new"))

        try:
            start_time = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Invalid start time.", "error")
            return redirect(url_for("trainer_event_new"))

        end_time = None
        if end_str:
            try:
                end_time = datetime.strptime(end_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                end_time = None

        course_id = request.form.get("course_id") or ""
        course_id_int = None
        if course_id.isdigit():
            course_id_int = int(course_id)

        ev = Event(
            trainer_id=current_user.id,
            course_id=course_id_int,
            title=title,
            description=description,
            type=type_,
            start_time=start_time,
            end_time=end_time,
            meeting_link=meeting_link or None,
            location=location or None,
            is_online=is_online,
            color=color or "#0f766e",
        )
        db.session.add(ev)
        db.session.commit()
        flash("Event created.", "success")
        return redirect(url_for("trainer_events"))

    return render_template(
        "trainer_event_form.html",
        user=current_user,
        mode="new",
        event=None,
        courses=courses,
    )


@app.route("/trainer/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_event_edit(current_user, event_id):
    ev = Event.query.get_or_404(event_id)
    if ev.trainer_id != current_user.id:
        flash("Not allowed.", "error")
        return redirect(url_for("trainer_events"))

    courses = Course.query.filter_by(trainer_id=current_user.id).all()

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        type_ = (request.form.get("type") or "Live Class").strip()
        start_str = request.form.get("start_time") or ""
        end_str = request.form.get("end_time") or ""
        meeting_link = (request.form.get("meeting_link") or "").strip()
        location = (request.form.get("location") or "").strip()
        is_online = (request.form.get("is_online") == "on")
        color = (request.form.get("color") or "#0f766e").strip()

        if not title or not start_str:
            flash("Title and start time are required.", "error")
            return redirect(url_for("trainer_event_edit", event_id=ev.id))

        try:
            start_time = datetime.strptime(start_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Invalid start time.", "error")
            return redirect(url_for("trainer_event_edit", event_id=ev.id))

        end_time = None
        if end_str:
            try:
                end_time = datetime.strptime(end_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                end_time = ev.end_time

        course_id = request.form.get("course_id") or ""
        course_id_int = None
        if course_id.isdigit():
            course_id_int = int(course_id)

        ev.title = title
        ev.description = description
        ev.type = type_
        ev.start_time = start_time
        ev.end_time = end_time
        ev.meeting_link = meeting_link or None
        ev.location = location or None
        ev.is_online = is_online
        ev.color = color or "#0f766e"
        ev.course_id = course_id_int

        db.session.commit()
        flash("Event updated.", "success")
        return redirect(url_for("trainer_events"))

    # for datetime-local
    start_value = ev.start_time.strftime("%Y-%m-%dT%H:%M")
    end_value = ev.end_time.strftime("%Y-%m-%dT%H:%M") if ev.end_time else ""

    return render_template(
        "trainer_event_form.html",
        user=current_user,
        mode="edit",
        event=ev,
        start_value=start_value,
        end_value=end_value,
        courses=courses,
    )

@app.route("/trainer/events/<int:session_id>/delete", methods=["POST"])
@login_required(role="trainer")
def trainer_event_delete(current_user, session_id):
    s = Session.query.get_or_404(session_id)

    if not s.course or s.course.trainer_id != current_user.id:
        flash("You are not allowed to delete this session.", "error")
        return redirect(url_for("trainer_events"))

    db.session.delete(s)
    db.session.commit()
    flash("Session deleted.", "success")
    return redirect(url_for("trainer_events"))




@app.route("/trainer/community", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_community(current_user):
    courses = Course.query.filter_by(trainer_id=current_user.id).all()
    course_ids = [c.id for c in courses]

    # create announcement inline
    if request.method == "POST" and request.form.get("form_type") == "announcement":
        title = (request.form.get("title") or "").strip()
        body = (request.form.get("body") or "").strip()
        course_id = (request.form.get("course_id") or "").strip()
        is_pinned = ("is_pinned" in request.form)

        if not title or not body:
            flash("Title and body required for announcement.", "error")
        else:
            cid = int(course_id) if course_id.isdigit() else None
            ann = Announcement(
                trainer_id=current_user.id,
                course_id=cid,
                title=title,
                body=body,
                is_pinned=is_pinned,
            )
            db.session.add(ann)
            db.session.commit()
            flash("Announcement posted.", "success")
        return redirect(url_for("trainer_community"))

    # create thread inline
    if request.method == "POST" and request.form.get("form_type") == "thread":
        title = (request.form.get("title") or "").strip()
        body = (request.form.get("body") or "").strip()
        course_id = (request.form.get("course_id") or "").strip()

        if not title or not body:
            flash("Title and body required for discussion thread.", "error")
        else:
            cid = int(course_id) if course_id.isdigit() else None
            th = DiscussionThread(
                trainer_id=current_user.id,
                course_id=cid,
                title=title,
                body=body,
            )
            db.session.add(th)
            db.session.commit()
            flash("Thread created.", "success")
        return redirect(url_for("trainer_community"))

    announcements = Announcement.query.filter_by(trainer_id=current_user.id) \
                                      .order_by(Announcement.is_pinned.desc(),
                                                Announcement.created_at.desc()) \
                                      .limit(10).all()

    threads = DiscussionThread.query.filter_by(trainer_id=current_user.id) \
                                    .order_by(DiscussionThread.is_pinned.desc(),
                                              DiscussionThread.created_at.desc()) \
                                    .limit(15).all()

    courses_by_id = {c.id: c for c in courses}

    return render_template(
        "trainer_community.html",
        user=current_user,
        announcements=announcements,
        threads=threads,
        courses=courses,
        courses_by_id=courses_by_id,
    )


@app.route("/trainer/community/threads/<int:thread_id>", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_thread_detail(current_user, thread_id):
    thread = DiscussionThread.query.get_or_404(thread_id)
    if thread.trainer_id != current_user.id:
        flash("Not allowed.", "error")
        return redirect(url_for("trainer_community"))

    if request.method == "POST":
        body = (request.form.get("body") or "").strip()
        if not body:
            flash("Reply cannot be empty.", "error")
            return redirect(url_for("trainer_thread_detail", thread_id=thread.id))

        reply = DiscussionReply(
            thread_id=thread.id,
            author_name=current_user.name,
            author_role="trainer",
            body=body,
        )
        db.session.add(reply)
        db.session.commit()
        flash("Reply posted.", "success")
        return redirect(url_for("trainer_thread_detail", thread_id=thread.id))

    replies = DiscussionReply.query.filter_by(thread_id=thread.id) \
                                   .order_by(DiscussionReply.created_at.asc()).all()

    return render_template(
        "trainer_thread_detail.html",
        user=current_user,
        thread=thread,
        replies=replies,
    )

# ========== TRAINER: QUESTION BANK ==========

@app.route("/trainer/question-bank")
@login_required(role="trainer")
def trainer_question_bank(current_user):
    topic = request.args.get("topic", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    course_id = request.args.get("course_id", "").strip()

    query = QuestionBankItem.query.filter_by(trainer_id=current_user.id)

    if topic:
        like = f"%{topic.lower()}%"
        query = query.filter(db.func.lower(QuestionBankItem.topic).like(like))
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if course_id.isdigit():
        query = query.filter_by(course_id=int(course_id))

    items = query.order_by(QuestionBankItem.created_at.desc()).all()
    courses = Course.query.filter_by(trainer_id=current_user.id).all()

    return render_template(
        "trainer_question_bank.html",
        user=current_user,
        items=items,
        courses=courses,
        topic=topic,
        difficulty=difficulty,
        selected_course_id=int(course_id) if course_id.isdigit() else None,
    )


@app.route("/trainer/question-bank/new", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_question_bank_new(current_user):
    courses = Course.query.filter_by(trainer_id=current_user.id).all()

    if request.method == "POST":
        topic = (request.form.get("topic") or "").strip()
        difficulty = (request.form.get("difficulty") or "Medium").strip()
        qtype = (request.form.get("question_type") or "MCQ").strip()
        text = (request.form.get("text") or "").strip()
        course_id_raw = request.form.get("course_id") or ""
        tags = (request.form.get("tags") or "").strip()
        marks_raw = request.form.get("marks") or "1"

        if not topic or not text:
            flash("Topic and question text are required.", "error")
            return redirect(url_for("trainer_question_bank_new"))

        try:
            marks = float(marks_raw)
        except ValueError:
            marks = 1.0

        course_id = int(course_id_raw) if course_id_raw.isdigit() else None

        item = QuestionBankItem(
            trainer_id=current_user.id,
            course_id=course_id,
            topic=topic,
            difficulty=difficulty,
            question_type=qtype,
            text=text,
            option_a=(request.form.get("option_a") or "").strip() or None,
            option_b=(request.form.get("option_b") or "").strip() or None,
            option_c=(request.form.get("option_c") or "").strip() or None,
            option_d=(request.form.get("option_d") or "").strip() or None,
            correct_option=((request.form.get("correct_option") or "").strip().upper() or None),
            marks=marks,
            tags=tags or None,
        )
        db.session.add(item)
        db.session.commit()
        flash("Question added to bank.", "success")
        return redirect(url_for("trainer_question_bank"))

    return render_template(
        "trainer_question_bank_form.html",
        user=current_user,
        mode="new",
        courses=courses,
        item=None,
    )


@app.route("/trainer/question-bank/<int:item_id>/edit", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_question_bank_edit(current_user, item_id):
    item = QuestionBankItem.query.get_or_404(item_id)
    if item.trainer_id != current_user.id:
        flash("Not allowed.", "error")
        return redirect(url_for("trainer_question_bank"))

    courses = Course.query.filter_by(trainer_id=current_user.id).all()

    if request.method == "POST":
        topic = (request.form.get("topic") or "").strip()
        difficulty = (request.form.get("difficulty") or "Medium").strip()
        qtype = (request.form.get("question_type") or "MCQ").strip()
        text = (request.form.get("text") or "").strip()
        course_id_raw = request.form.get("course_id") or ""
        tags = (request.form.get("tags") or "").strip()
        marks_raw = request.form.get("marks") or "1"

        if not topic or not text:
            flash("Topic and question text are required.", "error")
            return redirect(url_for("trainer_question_bank_edit", item_id=item.id))

        try:
            marks = float(marks_raw)
        except ValueError:
            marks = item.marks

        course_id = int(course_id_raw) if course_id_raw.isdigit() else None

        item.topic = topic
        item.difficulty = difficulty
        item.question_type = qtype
        item.text = text
        item.course_id = course_id
        item.option_a = (request.form.get("option_a") or "").strip() or None
        item.option_b = (request.form.get("option_b") or "").strip() or None
        item.option_c = (request.form.get("option_c") or "").strip() or None
        item.option_d = (request.form.get("option_d") or "").strip() or None
        item.correct_option = ((request.form.get("correct_option") or "").strip().upper() or None)
        item.marks = marks
        item.tags = tags or None

        db.session.commit()
        flash("Question updated.", "success")
        return redirect(url_for("trainer_question_bank"))

    return render_template(
        "trainer_question_bank_form.html",
        user=current_user,
        mode="edit",
        courses=courses,
        item=item,
    )


@app.route("/trainer/question-bank/<int:item_id>/delete", methods=["POST"])
@login_required(role="trainer")
def trainer_question_bank_delete(current_user, item_id):
    item = QuestionBankItem.query.get_or_404(item_id)
    if item.trainer_id != current_user.id:
        flash("Not allowed.", "error")
        return redirect(url_for("trainer_question_bank"))

    db.session.delete(item)
    db.session.commit()
    flash("Question removed from bank.", "success")
    return redirect(url_for("trainer_question_bank"))


# ========== TRAINER: STUDENT GROUPS / COHORTS ==========

@app.route("/trainer/groups")
@login_required(role="trainer")
def trainer_groups(current_user):
    groups = StudentGroup.query.filter_by(trainer_id=current_user.id)\
                               .order_by(StudentGroup.created_at.desc()).all()
    return render_template("trainer_groups.html", user=current_user, groups=groups)


@app.route("/trainer/groups/new", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_groups_new(current_user):
    students = Student.query.all()

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        description = (request.form.get("description") or "").strip()
        selected_ids = request.form.getlist("students")

        if not name:
            flash("Group name is required.", "error")
            return redirect(url_for("trainer_groups_new"))

        group = StudentGroup(trainer_id=current_user.id, name=name, description=description)
        db.session.add(group)
        db.session.flush()  # get group.id

        for sid in selected_ids:
            if sid.isdigit():
                membership = StudentGroupMembership(group_id=group.id, student_id=int(sid))
                db.session.add(membership)

        db.session.commit()
        flash("Group created.", "success")
        return redirect(url_for("trainer_groups"))

    return render_template("trainer_groups_form.html", user=current_user, mode="new", students=students, group=None)


@app.route("/trainer/groups/<int:group_id>", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_groups_detail(current_user, group_id):
    group = StudentGroup.query.get_or_404(group_id)
    if group.trainer_id != current_user.id:
        flash("Not allowed.", "error")
        return redirect(url_for("trainer_groups"))

    students = Student.query.all()
    member_ids = {m.student_id for m in group.memberships}

    if request.method == "POST":
        # update members
        selected_ids = request.form.getlist("students")
        new_ids = {int(s) for s in selected_ids if s.isdigit()}

        # remove old
        for m in group.memberships:
            if m.student_id not in new_ids:
                db.session.delete(m)

        # add new
        for sid in new_ids:
            if sid not in member_ids:
                db.session.add(StudentGroupMembership(group_id=group.id, student_id=sid))

        group.name = (request.form.get("name") or group.name).strip()
        group.description = (request.form.get("description") or group.description or "").strip()

        db.session.commit()
        flash("Group updated.", "success")
        return redirect(url_for("trainer_groups_detail", group_id=group.id))

    return render_template(
        "trainer_groups_form.html",
        user=current_user,
        mode="edit",
        group=group,
        students=students,
        member_ids=member_ids,
    )


@app.route("/trainer/groups/<int:group_id>/delete", methods=["POST"])
@login_required(role="trainer")
def trainer_groups_delete(current_user, group_id):
    group = StudentGroup.query.get_or_404(group_id)
    if group.trainer_id != current_user.id:
        flash("Not allowed.", "error")
        return redirect(url_for("trainer_groups"))

    db.session.delete(group)
    db.session.commit()
    flash("Group deleted.", "success")
    return redirect(url_for("trainer_groups"))


# ========== TRAINER: CERTIFICATES ==========

def ensure_default_certificate_template(trainer_id: int) -> CertificateTemplate:
    tmpl = CertificateTemplate.query.filter_by(trainer_id=trainer_id, is_default=True).first()
    if tmpl:
        return tmpl

    default_body = """
    <div class="cert-card">
      <h1>Certificate of Completion</h1>
      <p>This is to certify that</p>
      <h2>{{ student_name }}</h2>
      <p>has successfully completed the course</p>
      <h3>{{ course_title }}</h3>
      <p>on {{ date }}.</p>
    </div>
    """
    tmpl = CertificateTemplate(
        trainer_id=trainer_id,
        name="Default Certificate",
        body_html=default_body.strip(),
        is_default=True,
    )
    db.session.add(tmpl)
    db.session.commit()
    return tmpl


@app.route("/trainer/certificates")
@login_required(role="trainer")
def trainer_certificates(current_user):
    templates = CertificateTemplate.query.filter_by(trainer_id=current_user.id)\
                                         .order_by(CertificateTemplate.created_at.desc()).all()
    if not templates:
        ensure_default_certificate_template(current_user.id)
        templates = CertificateTemplate.query.filter_by(trainer_id=current_user.id)\
                                             .order_by(CertificateTemplate.created_at.desc()).all()

    return render_template("trainer_certificates.html", user=current_user, templates=templates)


@app.route("/trainer/certificates/new", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_certificate_new(current_user):
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        body_html = (request.form.get("body_html") or "").strip()

        if not name or not body_html:
            flash("Name and body are required.", "error")
            return redirect(url_for("trainer_certificate_new"))

        tmpl = CertificateTemplate(
            trainer_id=current_user.id,
            name=name,
            body_html=body_html,
            is_default=("is_default" in request.form),
        )

        if tmpl.is_default:
            CertificateTemplate.query.filter_by(trainer_id=current_user.id, is_default=True)\
                                     .update({"is_default": False})

        db.session.add(tmpl)
        db.session.commit()
        flash("Certificate template created.", "success")
        return redirect(url_for("trainer_certificates"))

    return render_template("trainer_certificate_form.html", user=current_user, mode="new", template=None)


@app.route("/trainer/certificates/<int:template_id>/edit", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_certificate_edit(current_user, template_id):
    tmpl = CertificateTemplate.query.get_or_404(template_id)
    if tmpl.trainer_id != current_user.id:
        flash("Not allowed.", "error")
        return redirect(url_for("trainer_certificates"))

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        body_html = (request.form.get("body_html") or "").strip()
        is_default = ("is_default" in request.form)

        if not name or not body_html:
            flash("Name and body are required.", "error")
            return redirect(url_for("trainer_certificate_edit", template_id=tmpl.id))

        tmpl.name = name
        tmpl.body_html = body_html
        tmpl.is_default = is_default

        if is_default:
            CertificateTemplate.query.filter(
                CertificateTemplate.trainer_id == current_user.id,
                CertificateTemplate.id != tmpl.id,
            ).update({"is_default": False})

        db.session.commit()
        flash("Certificate template updated.", "success")
        return redirect(url_for("trainer_certificates"))

    return render_template("trainer_certificate_form.html", user=current_user, mode="edit", template=tmpl)


@app.route("/trainer/certificates/<int:template_id>/delete", methods=["POST"])
@login_required(role="trainer")
def trainer_certificate_delete(current_user, template_id):
    tmpl = CertificateTemplate.query.get_or_404(template_id)
    if tmpl.trainer_id != current_user.id:
        flash("Not allowed.", "error")
        return redirect(url_for("trainer_certificates"))

    if tmpl.is_default:
        flash("You cannot delete the default template.", "error")
        return redirect(url_for("trainer_certificates"))

    db.session.delete(tmpl)
    db.session.commit()
    flash("Certificate template deleted.", "success")
    return redirect(url_for("trainer_certificates"))





# ========== TRAINER: SIMPLE AUTOMATIONS (MVP) ==========

@app.route("/trainer/automations")
@login_required(role="trainer")
def trainer_automations(current_user):
    automations = TrainerAutomation.query.filter_by(trainer_id=current_user.id)\
                                         .order_by(TrainerAutomation.created_at.desc()).all()
    return render_template("trainer_automations.html", user=current_user, automations=automations)


@app.route("/trainer/automations/new", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_automations_new(current_user):
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        trigger_type = (request.form.get("trigger_type") or "enrollment").strip()
        config = (request.form.get("config_json") or "").strip()

        if not name:
            flash("Name is required.", "error")
            return redirect(url_for("trainer_automations_new"))

        auto = TrainerAutomation(
            trainer_id=current_user.id,
            name=name,
            trigger_type=trigger_type,
            config_json=config or None,
            is_enabled=("is_enabled" in request.form),
        )
        db.session.add(auto)
        db.session.commit()
        flash("Automation saved.", "success")
        return redirect(url_for("trainer_automations"))

    return render_template("trainer_automations_form.html", user=current_user, mode="new", automation=None)


@app.route("/trainer/automations/<int:auto_id>/edit", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_automations_edit(current_user, auto_id):
    auto = TrainerAutomation.query.get_or_404(auto_id)
    if auto.trainer_id != current_user.id:
        flash("Not allowed.", "error")
        return redirect(url_for("trainer_automations"))

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        trigger_type = (request.form.get("trigger_type") or "enrollment").strip()
        config = (request.form.get("config_json") or "").strip()
        is_enabled = ("is_enabled" in request.form)

        if not name:
            flash("Name is required.", "error")
            return redirect(url_for("trainer_automations_edit", auto_id=auto.id))

        auto.name = name
        auto.trigger_type = trigger_type
        auto.config_json = config or None
        auto.is_enabled = is_enabled
        db.session.commit()
        flash("Automation updated.", "success")
        return redirect(url_for("trainer_automations"))

    return render_template("trainer_automations_form.html", user=current_user, mode="edit", automation=auto)


@app.route("/trainer/automations/<int:auto_id>/toggle", methods=["POST"])
@login_required(role="trainer")
def trainer_automations_toggle(current_user, auto_id):
    auto = TrainerAutomation.query.get_or_404(auto_id)
    if auto.trainer_id != current_user.id:
        flash("Not allowed.", "error")
        return redirect(url_for("trainer_automations"))

    auto.is_enabled = not auto.is_enabled
    db.session.commit()
    flash(f"Automation {'enabled' if auto.is_enabled else 'disabled'}.", "success")
    return redirect(url_for("trainer_automations"))


@app.route("/trainer/automations/<int:auto_id>/delete", methods=["POST"])
@login_required(role="trainer")
def trainer_automations_delete(current_user, auto_id):
    auto = TrainerAutomation.query.get_or_404(auto_id)
    if auto.trainer_id != current_user.id:
        flash("Not allowed.", "error")
        return redirect(url_for("trainer_automations"))

    db.session.delete(auto)
    db.session.commit()
    flash("Automation deleted.", "success")
    return redirect(url_for("trainer_automations"))


class Template(db.Model):
    __tablename__ = "template"
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    # ... rest of fields ...
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    trainer = db.relationship("User", lazy=True)



@app.route("/trainer/settings")
@login_required(role="trainer")
def trainer_settings(current_user):
    return render_template("trainer_settings.html", user=current_user)

@app.route("/trainer/help")
@login_required(role="trainer")
def trainer_help(current_user):
    return render_template("trainer_help.html", user=current_user)


@app.route("/trainer/profile", methods=["GET", "POST"])
@login_required(role="trainer")
def trainer_profile(current_user):
    # --------- SAVE ON POST ---------
    if request.method == "POST":
        # basic info
        name = (request.form.get("name") or "").strip()
        if name:
            current_user.name = name

        current_user.headline = (request.form.get("headline") or "").strip() or None
        current_user.bio = (request.form.get("bio") or "").strip() or None

        years = (request.form.get("years_experience") or "").strip()
        try:
            current_user.years_experience = int(years) if years else None
        except ValueError:
            pass  # ignore bad input

        current_user.primary_domains = (request.form.get("primary_domains") or "").strip() or None
        current_user.teaching_styles = (request.form.get("teaching_styles") or "").strip() or None
        current_user.languages = (request.form.get("languages") or "").strip() or None
        current_user.location = (request.form.get("location") or "").strip() or None
        current_user.timezone = (request.form.get("timezone") or "").strip() or None

        # availability
        accepting = request.form.get("accepting_new_students", "off")
        current_user.accepting_new_students = (accepting == "on")

        # socials
        current_user.linkedin_url = (request.form.get("linkedin_url") or "").strip() or None
        current_user.github_url = (request.form.get("github_url") or "").strip() or None
        current_user.portfolio_url = (request.form.get("portfolio_url") or "").strip() or None

        # notifications
        current_user.notify_on_enroll = ("notify_on_enroll" in request.form)
        current_user.notify_on_submission = ("notify_on_submission" in request.form)
        current_user.notify_on_completion = ("notify_on_completion" in request.form)
        current_user.summary_frequency = (request.form.get("summary_frequency") or "weekly").strip()

        # payout / payment details
        payout_method = request.form.get("payout_method") or None
        current_user.payout_method = payout_method

        current_user.bank_account_name = (request.form.get("bank_account_name") or "").strip() or None
        current_user.bank_account_number = (request.form.get("bank_account_number") or "").strip() or None
        current_user.bank_ifsc = (request.form.get("bank_ifsc") or "").strip().upper() or None
        current_user.bank_name = (request.form.get("bank_name") or "").strip() or None
        current_user.upi_id = (request.form.get("upi_id") or "").strip() or None

        db.session.commit()
        flash("Profile, preferences and payment details updated.", "success")
        return redirect(url_for("trainer_profile"))

    # --------- PORTFOLIO STATS FOR DISPLAY ---------
    # courses & enrollments for this trainer
    courses = Course.query.filter_by(trainer_id=current_user.id).all()
    course_ids = [c.id for c in courses]

    enrollments = []
    if course_ids:
        enrollments = Enrollment.query.filter(Enrollment.course_id.in_(course_ids)).all()

    total_courses = len(courses)
    total_students = len({e.student_id for e in enrollments}) if enrollments else 0
    total_learning_hours = sum(e.hours_watched for e in enrollments) if enrollments else 0.0
    avg_progress = int(
        sum(e.progress for e in enrollments) / len(enrollments)
    ) if enrollments else 0

    # achievements idea (simple badges flags)
    badges = []
    if total_students >= 50:
        badges.append("Taught 50+ students")
    if total_learning_hours >= 200:
        badges.append("200+ learning hours delivered")
    if total_courses >= 5:
        badges.append("Created 5+ courses")

    # sort courses by enrollments count for "top" view
    enroll_by_course = {}
    for e in enrollments:
        enroll_by_course.setdefault(e.course_id, []).append(e)

    course_summaries = []
    for c in courses:
        c_enrs = enroll_by_course.get(c.id, [])
        c_students = len(c_enrs)
        c_avg_progress = int(sum(e.progress for e in c_enrs) / c_students) if c_students else 0
        course_summaries.append({
            "course": c,
            "students": c_students,
            "avg_progress": c_avg_progress,
        })

    # order by students desc
    course_summaries.sort(key=lambda x: -x["students"])

    return render_template(
        "trainer_profile.html",
        user=current_user,
        total_courses=total_courses,
        total_students=total_students,
        total_learning_hours=total_learning_hours,
        avg_progress=avg_progress,
        badges=badges,
        course_summaries=course_summaries,
    )

class RewiseEDPackage(db.Model):
    __tablename__ = "rewiseed_package"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False, unique=True)

    summary = db.Column(db.Text, nullable=True)
    quiz_content = db.Column(db.Text, nullable=True)
    exam_content = db.Column(db.Text, nullable=True)
    ppt_outline = db.Column(db.Text, nullable=True)
    project_ideas = db.Column(db.Text, nullable=True)
    chatbot_prompt = db.Column(db.Text, nullable=True)
    tutor_script = db.Column(db.Text, nullable=True)

    price = db.Column(db.Float, nullable=False, default=499.0)
    is_paid = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    course = db.relationship("Course", lazy=True)



@app.route("/student/courses/<int:course_id>/tutor")
@login_required(role="student")
def student_course_tutor(current_user, course_id):
    # Make sure the course exists
    course = Course.query.get_or_404(course_id)

    # (Optional but better) – ensure this student is enrolled in the course
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,  # if you use a separate Student table, adapt this
        course_id=course.id
    ).first()

    # If your "students" are separate from User, you may want to skip this check
    # or adapt it to your mapping.

    pkg = RewiseEDPackage.query.filter_by(course_id=course.id).first()

    # Fallback prompt if we don't have a RewiseED chatbot prompt
    if pkg and pkg.chatbot_prompt:
        base_prompt = pkg.chatbot_prompt
    else:
        base_prompt = f"""
You are an AI teaching assistant for the course "{course.title}".
Explain concepts clearly for beginners, using simple examples.
Answer only course-related questions. If something is not covered, say so gently.
Keep answers short and focused unless the student asks for more detail.
"""

    # Retrieve chat history from session (list of dicts)
    history_key = f"tutor_history_{course.id}"
    history = session.get(history_key, [])

    return render_template(
        "student_ai_tutor.html",
        user=current_user,
        course=course,
        base_prompt=base_prompt,
        history=history,
        pkg=pkg,
    )

@app.route("/student/courses/<int:course_id>/tutor/chat", methods=["POST"])
@login_required(role="student")
def student_course_tutor_chat(current_user, course_id):
    course = Course.query.get_or_404(course_id)
    pkg = RewiseEDPackage.query.filter_by(course_id=course.id).first()

    if pkg and pkg.chatbot_prompt:
        base_prompt = pkg.chatbot_prompt
    else:
        base_prompt = f"""
You are an AI tutor for the course "{course.title}".
Be friendly, concise and practical. When relevant, refer to typical course topics.
If the student asks something unrelated, gently bring them back to the course.
"""

    data = request.get_json() or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"error": "Empty message"}), 400

    # Get existing history from session
    history_key = f"tutor_history_{course.id}"
    history = session.get(history_key, [])

    # Build a simple text-based conversation log
    # e.g. "Student: ...", "Tutor: ..."
    text_messages = []
    for turn in history[-6:]:  # last 6 turns max
        role = turn.get("role", "user")
        content = turn.get("content", "")
        label = "Student" if role == "user" else "Tutor"
        text_messages.append(f"{label}: {content}")

    # Add the new student message
    text_messages.append(f"Student: {message}")

    ai_reply = ai_chat_message(base_prompt, text_messages)

    # Update history and persist to session
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": ai_reply})
    session[history_key] = history
    session.modified = True

    return jsonify({
        "reply": ai_reply
    })







@app.route("/trainer/certificates")
@login_required(role="trainer")
def trainer_certificate_builder(user):
    courses = Course.query.filter_by(trainer_id=user.id).all()
    return render_template(
        "trainer_certificate_builder.html",
        user=user,
        courses=courses
    )


@app.route("/trainer/certificates/preview-ui")
@login_required(role="trainer")
def trainer_certificate_preview_ui(user):
    data = {
        "student": request.args.get("student", ""),
        "course": request.args.get("course", ""),
        "date": request.args.get("date", ""),
        "trainer": request.args.get("trainer", ""),
        "designation": request.args.get("designation", ""),
        "signature": request.args.get("signature", "")
    }
    return render_template("trainer_certificate_preview.html", **data)




from datetime import date

@app.route("/trainer/certificates/issue")
@login_required(role="trainer")
def trainer_certificate_issue(current_user):
    courses = Course.query.filter_by(trainer_id=current_user.id).all()

    return render_template(
        "trainer_certificate_issue.html",
        user=current_user,
        courses=courses,
        today=date.today().isoformat()  # ✅ REQUIRED
    )



@app.route("/trainer/certificates/courses")
@login_required("trainer")
def trainer_certificate_courses(current_user):
    courses = Course.query.filter_by(trainer_id=current_user.id).all()
    return jsonify([
        {"id": c.id, "title": c.title}
        for c in courses
    ])






import json
from flask import request, jsonify, render_template
from openai import OpenAI

# ===============================
# PAGE
# ===============================
@app.route("/trainer/detailed-modules")
@login_required(role="trainer")
def trainer_detailed_modules(user):
    courses = Course.query.filter_by(trainer_id=user.id).all()
    return render_template(
        "trainer_detailed_modules.html",
        user=user,
        courses=courses
    )

@app.post("/trainer/detailed-modules/process")
@login_required(role="trainer")
def process_detailed_modules(user):
    try:
        content = request.json.get("content", "").strip()
        if not content:
            return jsonify({"error": "No content provided"}), 400

        prompt = f"""
You are an expert curriculum designer.

From the content below, extract a clean hierarchy.

Return ONLY valid JSON in this format (NO markdown):

{{
  "modules": [
    {{
      "title": "Main Topic",
      "subtopics": ["Subtopic 1", "Subtopic 2"]
    }}
  ]
}}

CONTENT:
{content}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        raw = response.choices[0].message.content.strip()

        # 🔥 HARD CLEAN (THIS FIXES 90% FAILURES)
        raw = raw.replace("```json", "").replace("```", "").strip()

        data = json.loads(raw)

        # ✅ GUARANTEE STRUCTURE
        if "modules" not in data or not isinstance(data["modules"], list):
            raise ValueError("Invalid AI structure")

        return jsonify(data)

    except Exception as e:
        print("❌ MODULE GENERATION ERROR:", str(e))
        return jsonify({
            "error": "AI processing failed",
            "details": str(e)
        }), 500

@app.post("/trainer/detailed-modules/explain")
@login_required(role="trainer")
def explain_topic(user):
    topic = request.json.get("topic")

    prompt = f"""
You are an expert teacher.

Explain the topic below and DESIGN learning playgrounds.

Return ONLY valid JSON.

FORMAT:
{{
  "topic": "...",
  "explanation": "...",
  "steps": [],
  "formulas": [],
  "playgrounds": [
    {{
      "type": "slider|scatter|sequence|chart",
      "label": "...",
      "details": {{ }}
    }}
  ]
}}

TOPIC:
{topic}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    raw = response.choices[0].message.content
    raw = raw.replace("```json", "").replace("```", "").strip()

    return jsonify(json.loads(raw))




@app.route("/trainer/course/<int:course_id>/summary")
@login_required(role="trainer")
def trainer_course_summary(user, course_id):
    course = Course.query.filter_by(
        id=course_id,
        trainer_id=user.id
    ).first()

    if not course:
        return jsonify({"summary": ""})

    return jsonify({
        "summary": course.ai_outline_json or ""
    })



# insights
from collections import defaultdict











# student dashboard



@app.route("/student/dashboard")
@login_required(role="student")
def student_dashboard(current_user):

    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()

    courses = []
    total_progress = 0

    for e in enrollments:
        course = e.course
        courses.append({
            "id": course.id,
            "title": course.title,
            "trainer": course.trainer.name,
            "progress": e.progress,
            "hours": round(e.hours_watched, 1)
        })
        total_progress += e.progress

    avg_progress = int(total_progress / len(courses)) if courses else 0

    return render_template(
        "student_dashboard.html",
        user=current_user,
        courses=courses,
        total_courses=len(courses),
        avg_progress=avg_progress
    )



# ================================
# STUDENT: VIEW TRAINERS
# ================================
@app.route("/student/trainers")
@login_required(role="student")
def student_trainers(current_user):
    trainers = User.query.filter_by(role="trainer").all()
    return render_template("student_trainers.html", trainers=trainers)


# ================================
# STUDENT: VIEW COURSES BY TRAINER
# ================================
@app.route("/student/trainer/<int:trainer_id>/courses")
@login_required(role="student")
def student_trainer_courses(current_user, trainer_id):
    trainer = User.query.get_or_404(trainer_id)
    courses = Course.query.filter_by(trainer_id=trainer.id).all()
    return render_template(
        "student_trainer_courses.html",
        trainer=trainer,
        courses=courses
    )


# ================================
# STUDENT: COURSE ACCESS GATE
# ================================
@app.route("/student/course/<int:course_id>")
@login_required(role="student")
def student_course_gate(current_user, course_id):

    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=course_id
    ).first()

    if enrollment:
        return redirect(url_for("student_course_player", course_id=course_id))

    return redirect(url_for("student_course_checkout", course_id=course_id))


# ================================
# STUDENT: COURSE CHECKOUT
# ================================
@app.route("/student/course/<int:course_id>/checkout", methods=["GET", "POST"])
@login_required(role="student")
def student_course_checkout(current_user, course_id):
    course = Course.query.get_or_404(course_id)

    if request.method == "POST":
        enrollment = Enrollment(
            course_id=course.id,
            student_id=current_user.id
        )
        db.session.add(enrollment)
        db.session.commit()

        return redirect(url_for("student_course_player", course_id=course.id))

    return render_template("course_checkout.html", course=course)


# ================================
# STUDENT: MY COURSES
# ================================
@app.route("/student/courses")
@login_required(role="student")
def student_courses(current_user):
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    return render_template("student_courses.html", enrollments=enrollments)


# ================================
# STUDENT: COURSE PLAYER
# ================================
@app.route("/student/course/<int:course_id>/player")
@login_required(role="student")
def student_course_player(user, course_id):

    enrollment = Enrollment.query.filter_by(
        student_id=user.id,
        course_id=course_id
    ).first_or_404()

    course = Course.query.get_or_404(course_id)
    videos = VideoLecture.query.filter_by(course_id=course.id).all()
    pkg = RewiseEDPackage.query.filter_by(course_id=course.id).first()

    # ✅ ADD THIS
    assessment = Assessment.query.filter_by(
        course_id=course.id
    ).first()

    has_questions = False
    if assessment:
        has_questions = Question.query.filter_by(
            assessment_id=assessment.id
        ).count() > 0

    return render_template(
        "student_course_player.html",
        user=user,
        course=course,
        videos=videos,
        assessment=assessment,
        has_questions=has_questions,
        pkg=pkg
    )

@app.route(
    "/student/courses/<int:course_id>/assessments/<int:assessment_id>",
    methods=["GET"]
)
@login_required(role="student")
def student_view_assessment(user, course_id, assessment_id):

    # ensure student is enrolled
    Enrollment.query.filter_by(
        student_id=user.id,
        course_id=course_id
    ).first_or_404()

    assessment = Assessment.query.filter_by(
        id=assessment_id,
        course_id=course_id
    ).first_or_404()

    questions = Question.query.filter_by(
        assessment_id=assessment.id
    ).all()

    return render_template(
        "student/assessment_quiz.html",
        course_id=course_id,
        assessment=assessment,
        questions=questions
    )


@app.route(
    "/student/courses/<int:course_id>/assessments/<int:assessment_id>/submit",
    methods=["POST"]
)
@login_required(role="student")
def submit_student_assessment(user, course_id, assessment_id):

    Enrollment.query.filter_by(
        student_id=user.id,
        course_id=course_id
    ).first_or_404()

    questions = Question.query.filter_by(
        assessment_id=assessment_id
    ).all()

    score = 0
    total = 0

    for q in questions:
        selected = request.form.get(f"q_{q.id}")
        total += q.marks

        if selected == q.correct_option:
            score += q.marks

    return render_template(
        "student/assessment_result.html",
        score=score,
        total=total
    )


from openai import OpenAI

from ai_utils import get_client

client = get_client()


# 🔥 ADD ONLY THIS
@app.route("/entrepreneured")
@app.route("/entrepreneured/<path:path>")
def entrepreneured(path=None):
    return render_template("index.html")



@app.route("/student/course/<int:course_id>/ai-chat", methods=["POST"])
@login_required(role="student")
def ai_course_chat(user, course_id):

    data = request.get_json()
    question = data.get("question", "").strip()
    video_id = data.get("video_id")

    if not question or not video_id:
        return jsonify({"answer": "Please ask a valid question."})

    video = VideoLecture.query.get_or_404(video_id)

    if not video.summary:
        return jsonify({
            "answer": "This lesson does not have an AI summary yet."
        })

    SYSTEM_PROMPT = f"""
You are a STRICT video lesson assistant.

RULES:
- Answer ONLY from the lesson summary
- If answer is not present, say:
  "This is not covered in the current video."

LESSON TITLE:
{video.title}

LESSON SUMMARY:
{video.summary}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ],
            temperature=0.2,
            max_tokens=300
        )

        return jsonify({
            "answer": response.choices[0].message.content
        })

    except Exception as e:
        print("AI ERROR:", e)
        return jsonify({"answer": "AI is temporarily unavailable."}), 500





























@app.route("/student/voice-response", methods=["POST"])
@login_required(role="student")
def save_voice_response(user):
    data = request.json

    resp = StudentVoiceResponse(
        student_id=user.id,
        course_id=data.get("course_id"),
        response_text=data.get("response")
    )

    db.session.add(resp)
    db.session.commit()

    return jsonify({"status": "saved"})




@app.route("/student/voice-response", methods=["POST"])
@login_required(role="student")
def save_student_voice_response(user):
    data = request.get_json()

    response_text = data.get("response")
    course_id = data.get("course_id")

    if not response_text or not course_id:
        return jsonify({"error": "Invalid data"}), 400

    resp = StudentVoiceResponse(
        student_id=user.id,
        course_id=course_id,
        response_text=response_text
    )

    db.session.add(resp)
    db.session.commit()

    return jsonify({"status": "saved"})


@app.route("/student/quiz-result", methods=["POST"])
@login_required(role="student")
def save_quiz_result(user):
    data = request.get_json()
    print("QUIZ DATA RECEIVED:", data)  # 👈 ADD THIS
    course_id = data.get("course_id")
    score = data.get("score")
    total = data.get("total")

    if course_id is None or score is None or total is None:
        return jsonify({"error": "Invalid data"}), 400

    result = StudentQuizResult(
        student_id=user.id,
        course_id=course_id,
        score=score,
        total=total
    )

    db.session.add(result)
    db.session.commit()

    return jsonify({"status": "saved"})











with app.app_context():
    db.create_all()
    seed_data()


if __name__ == "__main__":
    app.run(debug=True)








