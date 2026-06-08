from flask import Flask, jsonify, request
from src.storage.repositories import (
    InMemoryUserRepository, InMemoryCourseRepository,
    InMemoryLessonRepository, InMemoryQuizRepository,
    InMemoryQuestionRepository, InMemoryAttemptRepository,
    InMemoryCourseProgressRepository, InMemoryLessonProgressRepository,
)
from src.services.user_service import UserService
from src.services.course_service import CourseService
from src.services.enrollment_service import EnrollmentService
from src.services.quiz_service import QuizService
from src.models.user import UserRole
from src.models.course import DifficultyLevel
from src.models.quiz import QuestionType
from src.utils.observers import EventBus
from src.utils.exceptions import LMSBaseError

app = Flask(__name__)

# ── Dependency wiring ───────────────────────────────────────────────────
event_bus = EventBus()
user_repo = InMemoryUserRepository()
course_repo = InMemoryCourseRepository()
lesson_repo = InMemoryLessonRepository()
quiz_repo = InMemoryQuizRepository()
question_repo = InMemoryQuestionRepository()
attempt_repo = InMemoryAttemptRepository()
progress_repo = InMemoryCourseProgressRepository()
lesson_progress_repo = InMemoryLessonProgressRepository()

user_svc = UserService(user_repo, event_bus)
course_svc = CourseService(course_repo, lesson_repo)
enrollment_svc = EnrollmentService(
    user_svc, course_svc, user_repo,
    progress_repo, lesson_progress_repo, event_bus
)
quiz_svc = QuizService(quiz_repo, question_repo, attempt_repo)


# ── Error handling ──────────────────────────────────────────────────────
@app.errorhandler(LMSBaseError)
def handle_lms_error(e):
    return jsonify({"success": False, "error": str(e)}), 400


@app.errorhandler(ValueError)
def handle_value_error(e):
    return jsonify({"success": False, "error": str(e)}), 400


# ── Root ────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return jsonify({
        "service": "LMS Platform API",
        "version": "1.0.0",
        "status": "running",
        "author": "Ковтун Олег, ФеП-32",
        "endpoints": {
            "health": "GET  /health",
            "users": [
                "POST /users",
                "GET  /users/<id>",
                "POST /users/<id>/block",
                "POST /users/authenticate",
            ],
            "courses": [
                "GET  /courses",
                "POST /courses",
                "POST /courses/<id>/publish",
                "POST /courses/<id>/lessons",
                "GET  /courses/<id>/lessons",
            ],
            "enrollment": [
                "POST   /enrollments",
                "DELETE /enrollments/<uid>/<cid>",
                "GET    /enrollments/<uid>/<cid>/progress",
                "GET    /enrollments/<uid>/courses",
                "POST   /lessons/<id>/complete",
            ],
            "quizzes": [
                "POST /quizzes",
                "POST /quizzes/<id>/questions",
                "POST /quizzes/<id>/attempts",
                "POST /attempts/<id>/submit",
                "GET  /quizzes/<id>/results/<uid>",
            ],
        }
    })


# ── Health ──────────────────────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "LMS API"})


# ── Users ───────────────────────────────────────────────────────────────
@app.route("/users", methods=["POST"])
def register_user():
    data = request.get_json() or {}
    role = UserRole(data.get("role", "student"))
    user = user_svc.register(
        name=data.get("name", ""),
        email=data.get("email", ""),
        password=data.get("password", ""),
        role=role,
    )
    return jsonify(
        {"success": True, "user_id": user.id, "name": user.name}), 201


@app.route("/users/<int:user_id>")
def get_user(user_id):
    profile = user_svc.get_profile(user_id)
    return jsonify({"success": True, "user": profile})


@app.route("/users/<int:user_id>/block", methods=["POST"])
def block_user(user_id):
    user_svc.block_user(user_id)
    return jsonify({"success": True, "message": f"User {user_id} blocked"})


@app.route("/users/authenticate", methods=["POST"])
def authenticate():
    data = request.get_json() or {}
    user = user_svc.authenticate(
        data.get(
            "email", ""), data.get(
            "password", ""))
    return jsonify(
        {"success": True, "user_id": user.id, "role": user.role.value})


# ── Courses ─────────────────────────────────────────────────────────────
@app.route("/courses", methods=["GET"])
def list_courses():
    courses = course_svc.get_published_courses()
    return jsonify({"success": True, "courses": [
        {"id": c.id, "title": c.title, "category": c.category,
         "difficulty": c.difficulty.value, "enrolled": c.enrolled_count}
        for c in courses
    ]})


@app.route("/courses", methods=["POST"])
def create_course():
    data = request.get_json() or {}
    diff = DifficultyLevel(data.get("difficulty", "beginner"))
    course = course_svc.create_course(
        title=data.get("title", ""),
        description=data.get("description", ""),
        teacher_id=data.get("teacher_id", 0),
        category=data.get("category", "general"),
        difficulty=diff,
        max_students=data.get("max_students"),
    )
    return jsonify({"success": True, "course_id": course.id}), 201


@app.route("/courses/<int:course_id>/publish", methods=["POST"])
def publish_course(course_id):
    course = course_svc.publish_course(course_id)
    return jsonify({"success": True, "status": course.status.value})


@app.route("/courses/<int:course_id>/lessons", methods=["POST"])
def add_lesson(course_id):
    data = request.get_json() or {}
    lesson = course_svc.add_lesson(
        course_id=course_id,
        title=data.get("title", ""),
        content=data.get("content", ""),
        order=data.get("order", 1),
        duration_minutes=data.get("duration_minutes", 30),
    )
    return jsonify({"success": True, "lesson_id": lesson.id}), 201


@app.route("/courses/<int:course_id>/lessons", methods=["GET"])
def get_lessons(course_id):
    lessons = course_svc.get_course_lessons(course_id)
    return jsonify({"success": True, "lessons": [
        {"id": l.id, "title": l.title, "order": l.order,
            "duration": l.duration_minutes}
        for item in lessons
    ]})


# ── Enrollment ──────────────────────────────────────────────────────────
@app.route("/enrollments", methods=["POST"])
def enroll():
    data = request.get_json() or {}
    progress = enrollment_svc.enroll(
        data.get(
            "user_id", 0), data.get(
            "course_id", 0))
    return jsonify({"success": True, "status": progress.status.value}), 201


@app.route("/enrollments/<int:user_id>/<int:course_id>", methods=["DELETE"])
def unenroll(user_id, course_id):
    enrollment_svc.unenroll(user_id, course_id)
    return jsonify({"success": True, "message": "Unenrolled"})


@app.route("/enrollments/<int:user_id>/<int:course_id>/progress")
def get_progress(user_id, course_id):
    prog = enrollment_svc.get_progress(user_id, course_id)
    return jsonify({
        "success": True,
        "completion_percent": prog.completion_percent,
        "status": prog.status.value,
        "completed_lessons": len(prog.completed_lesson_ids),
        "total_lessons": prog.total_lessons,
    })


@app.route("/enrollments/<int:user_id>/courses")
def user_courses(user_id):
    progs = enrollment_svc.get_user_courses(user_id)
    return jsonify({"success": True, "courses": [
        {"course_id": p.course_id, "status": p.status.value,
         "completion_percent": p.completion_percent}
        for p in progs
    ]})


@app.route("/lessons/<int:lesson_id>/complete", methods=["POST"])
def complete_lesson(lesson_id):
    data = request.get_json() or {}
    prog = enrollment_svc.complete_lesson(data.get("user_id", 0), lesson_id)
    return jsonify({
        "success": True,
        "completion_percent": prog.completion_percent if prog else 0,
        "course_completed": prog.is_completed() if prog else False,
    })


# ── Quizzes ─────────────────────────────────────────────────────────────
@app.route("/quizzes", methods=["POST"])
def create_quiz():
    data = request.get_json() or {}
    quiz = quiz_svc.create_quiz(
        course_id=data.get("course_id", 0),
        title=data.get("title", ""),
        description=data.get("description", ""),
        passing_score=data.get("passing_score", 70),
        time_limit_minutes=data.get("time_limit_minutes"),
        max_attempts=data.get("max_attempts", 3),
    )
    return jsonify({"success": True, "quiz_id": quiz.id}), 201


@app.route("/quizzes/<int:quiz_id>/questions", methods=["POST"])
def add_question(quiz_id):
    data = request.get_json() or {}
    qtype = QuestionType(data.get("type", "single_choice"))
    question = quiz_svc.add_question(
        quiz_id=quiz_id,
        text=data.get("text", ""),
        question_type=qtype,
        answers=data.get("answers", []),
        points=data.get("points", 1),
        order=data.get("order", 0),
    )
    return jsonify({"success": True, "question_id": question.id}), 201


@app.route("/quizzes/<int:quiz_id>/attempts", methods=["POST"])
def start_attempt(quiz_id):
    data = request.get_json() or {}
    attempt = quiz_svc.start_attempt(data.get("user_id", 0), quiz_id)
    return jsonify({"success": True, "attempt_id": attempt.id}), 201


@app.route("/attempts/<int:attempt_id>/submit", methods=["POST"])
def submit_attempt(attempt_id):
    data = request.get_json() or {}
    attempt = quiz_svc.submit_attempt(attempt_id, data.get("answers", {}))
    return jsonify({
        "success": True,
        "score_percent": attempt.score_percent,
        "passed": attempt.passed,
        "score": attempt.score,
        "max_score": attempt.max_score,
    })


@app.route("/quizzes/<int:quiz_id>/results/<int:user_id>")
def quiz_results(quiz_id, user_id):
    best = quiz_svc.get_best_score(user_id, quiz_id)
    remaining = quiz_svc.get_remaining_attempts(user_id, quiz_id)
    return jsonify({
        "success": True,
        "best_score_percent": best,
        "remaining_attempts": remaining,
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
