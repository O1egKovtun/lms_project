import pytest
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
from src.utils.observers import EventBus


def make_app():
    """Create a fresh Flask app with isolated in-memory state."""
    from flask import Flask, jsonify, request
    from src.models.user import UserRole
    from src.models.course import DifficultyLevel
    from src.models.quiz import QuestionType
    from src.utils.exceptions import LMSBaseError

    app = Flask(__name__)

    bus = EventBus()
    u_repo = InMemoryUserRepository()
    c_repo = InMemoryCourseRepository()
    l_repo = InMemoryLessonRepository()
    q_repo = InMemoryQuizRepository()
    qq_repo = InMemoryQuestionRepository()
    a_repo = InMemoryAttemptRepository()
    p_repo = InMemoryCourseProgressRepository()
    lp_repo = InMemoryLessonProgressRepository()

    u_svc = UserService(u_repo, bus)
    c_svc = CourseService(c_repo, l_repo)
    e_svc = EnrollmentService(u_svc, c_svc, u_repo, p_repo, lp_repo, bus)
    qz_svc = QuizService(q_repo, qq_repo, a_repo)

    @app.errorhandler(LMSBaseError)
    def lms_err(e):
        return jsonify({"success": False, "error": str(e)}), 400

    @app.errorhandler(ValueError)
    def val_err(e):
        return jsonify({"success": False, "error": str(e)}), 400

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/users", methods=["POST"])
    def register():
        d = request.get_json() or {}
        role = UserRole(d.get("role", "student"))
        user = u_svc.register(d.get("name", ""), d.get("email", ""),
                              d.get("password", ""), role)
        return jsonify({"success": True, "user_id": user.id}), 201

    @app.route("/users/<int:uid>")
    def get_user(uid):
        p = u_svc.get_profile(uid)
        return jsonify({"success": True, "user": p})

    @app.route("/users/<int:uid>/block", methods=["POST"])
    def block_user(uid):
        u_svc.block_user(uid)
        return jsonify({"success": True})

    @app.route("/users/authenticate", methods=["POST"])
    def auth():
        d = request.get_json() or {}
        user = u_svc.authenticate(d.get("email", ""), d.get("password", ""))
        return jsonify({"success": True, "user_id": user.id, "role": user.role.value})

    @app.route("/courses", methods=["GET"])
    def list_courses():
        courses = c_svc.get_published_courses()
        return jsonify({"success": True, "courses": [
            {"id": c.id, "title": c.title, "category": c.category} for c in courses
        ]})

    @app.route("/courses", methods=["POST"])
    def create_course():
        d = request.get_json() or {}
        diff = DifficultyLevel(d.get("difficulty", "beginner"))
        course = c_svc.create_course(d.get("title", ""), d.get("description", ""),
                                     d.get("teacher_id", 0), d.get("category", "general"),
                                     diff, d.get("max_students"))
        return jsonify({"success": True, "course_id": course.id}), 201

    @app.route("/courses/<int:cid>/publish", methods=["POST"])
    def publish_course(cid):
        c = c_svc.publish_course(cid)
        return jsonify({"success": True, "status": c.status.value})

    @app.route("/courses/<int:cid>/lessons", methods=["POST"])
    def add_lesson(cid):
        d = request.get_json() or {}
        l = c_svc.add_lesson(cid, d.get("title", ""), d.get("content", ""),
                              d.get("order", 1), d.get("duration_minutes", 30))
        return jsonify({"success": True, "lesson_id": l.id}), 201

    @app.route("/courses/<int:cid>/lessons", methods=["GET"])
    def get_lessons(cid):
        lessons = c_svc.get_course_lessons(cid)
        return jsonify({"success": True, "lessons": [
            {"id": l.id, "title": l.title, "order": l.order} for l in lessons
        ]})

    @app.route("/enrollments", methods=["POST"])
    def enroll():
        d = request.get_json() or {}
        prog = e_svc.enroll(d.get("user_id", 0), d.get("course_id", 0))
        return jsonify({"success": True, "status": prog.status.value}), 201

    @app.route("/enrollments/<int:uid>/<int:cid>", methods=["DELETE"])
    def unenroll(uid, cid):
        e_svc.unenroll(uid, cid)
        return jsonify({"success": True})

    @app.route("/enrollments/<int:uid>/<int:cid>/progress")
    def progress(uid, cid):
        p = e_svc.get_progress(uid, cid)
        return jsonify({"success": True, "completion_percent": p.completion_percent,
                        "status": p.status.value})

    @app.route("/enrollments/<int:uid>/courses")
    def user_courses(uid):
        progs = e_svc.get_user_courses(uid)
        return jsonify({"success": True, "courses": [
            {"course_id": p.course_id, "status": p.status.value} for p in progs
        ]})

    @app.route("/lessons/<int:lid>/complete", methods=["POST"])
    def complete_lesson(lid):
        d = request.get_json() or {}
        prog = e_svc.complete_lesson(d.get("user_id", 0), lid)
        return jsonify({"success": True,
                        "completion_percent": prog.completion_percent if prog else 0,
                        "course_completed": prog.is_completed() if prog else False})

    @app.route("/quizzes", methods=["POST"])
    def create_quiz():
        d = request.get_json() or {}
        q = qz_svc.create_quiz(d.get("course_id", 0), d.get("title", ""),
                               d.get("description", ""), d.get("passing_score", 70),
                               d.get("time_limit_minutes"), d.get("max_attempts", 3))
        return jsonify({"success": True, "quiz_id": q.id}), 201

    @app.route("/quizzes/<int:qid>/questions", methods=["POST"])
    def add_question(qid):
        d = request.get_json() or {}
        qt = QuestionType(d.get("type", "single_choice"))
        q = qz_svc.add_question(qid, d.get("text", ""), qt,
                                 d.get("answers", []), d.get("points", 1), d.get("order", 0))
        return jsonify({"success": True, "question_id": q.id}), 201

    @app.route("/quizzes/<int:qid>/attempts", methods=["POST"])
    def start_attempt(qid):
        d = request.get_json() or {}
        a = qz_svc.start_attempt(d.get("user_id", 0), qid)
        return jsonify({"success": True, "attempt_id": a.id}), 201

    @app.route("/attempts/<int:aid>/submit", methods=["POST"])
    def submit(aid):
        d = request.get_json() or {}
        a = qz_svc.submit_attempt(aid, d.get("answers", {}))
        return jsonify({"success": True, "score_percent": a.score_percent, "passed": a.passed,
                        "score": a.score, "max_score": a.max_score})

    @app.route("/quizzes/<int:qid>/results/<int:uid>")
    def quiz_results(qid, uid):
        best = qz_svc.get_best_score(uid, qid)
        rem = qz_svc.get_remaining_attempts(uid, qid)
        return jsonify({"success": True, "best_score_percent": best, "remaining_attempts": rem})

    return app


@pytest.fixture
def client():
    app = make_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def student_id(client):
    r = client.post("/users", json={
        "name": "Тест Студент", "email": "student@t.com",
        "password": "pass123", "role": "student",
    })
    return r.get_json()["user_id"]


@pytest.fixture
def teacher_id(client):
    r = client.post("/users", json={
        "name": "Тест Вчитель", "email": "teacher@t.com",
        "password": "pass123", "role": "teacher",
    })
    return r.get_json()["user_id"]


@pytest.fixture
def course_id(client, teacher_id):
    r = client.post("/courses", json={
        "title": "Інтеграційний Курс",
        "description": "Курс для інтеграційних тестів API",
        "teacher_id": teacher_id, "category": "testing",
    })
    cid = r.get_json()["course_id"]
    client.post(f"/courses/{cid}/publish")
    client.post(f"/courses/{cid}/lessons",
                json={"title": "Урок А", "content": "Зміст уроку А", "order": 1})
    client.post(f"/courses/{cid}/lessons",
                json={"title": "Урок Б", "content": "Зміст уроку Б", "order": 2})
    return cid


# ── Health ────────────────────────────────────────────────────────────────────
class TestHealthEndpoint:
    def test_health_200(self, client):
        assert client.get("/health").status_code == 200

    def test_health_ok(self, client):
        assert client.get("/health").get_json()["status"] == "ok"


# ── Users ─────────────────────────────────────────────────────────────────────
class TestUserEndpoints:
    def test_register_201(self, client):
        r = client.post("/users", json={"name": "Новий", "email": "new@t.com",
                                         "password": "pass123"})
        assert r.status_code == 201

    def test_register_returns_id(self, client):
        r = client.post("/users", json={"name": "ID Test", "email": "id@t.com",
                                         "password": "pass123"})
        assert r.get_json()["user_id"] > 0

    def test_duplicate_email_400(self, client, student_id):
        r = client.post("/users", json={"name": "Dup", "email": "student@t.com",
                                         "password": "pass123"})
        assert r.status_code == 400

    def test_invalid_email_400(self, client):
        r = client.post("/users", json={"name": "Bad", "email": "bad", "password": "pass123"})
        assert r.status_code == 400

    def test_get_user_200(self, client, student_id):
        assert client.get(f"/users/{student_id}").status_code == 200

    def test_get_user_profile(self, client, student_id):
        data = client.get(f"/users/{student_id}").get_json()
        assert data["user"]["email"] == "student@t.com"

    def test_get_nonexistent_400(self, client):
        assert client.get("/users/99999").status_code == 400

    def test_block_user(self, client, student_id):
        r = client.post(f"/users/{student_id}/block")
        assert r.get_json()["success"] is True

    def test_authenticate_success(self, client, student_id):
        r = client.post("/users/authenticate",
                        json={"email": "student@t.com", "password": "pass123"})
        assert r.get_json()["success"] is True

    def test_authenticate_wrong_pass_400(self, client, student_id):
        r = client.post("/users/authenticate",
                        json={"email": "student@t.com", "password": "wrong"})
        assert r.status_code == 400


# ── Courses ───────────────────────────────────────────────────────────────────
class TestCourseEndpoints:
    def test_create_course_201(self, client, teacher_id):
        r = client.post("/courses", json={
            "title": "Новий Курс", "description": "Опис нового курсу для тесту",
            "teacher_id": teacher_id, "category": "math",
        })
        assert r.status_code == 201

    def test_list_published_courses(self, client, course_id):
        data = client.get("/courses").get_json()
        assert any(c["id"] == course_id for c in data["courses"])

    def test_publish_course(self, client, teacher_id):
        cid = client.post("/courses", json={
            "title": "Pub Test", "description": "Курс для публікації тесту",
            "teacher_id": teacher_id, "category": "cat",
        }).get_json()["course_id"]
        r = client.post(f"/courses/{cid}/publish")
        assert r.get_json()["status"] == "published"

    def test_add_lesson(self, client, course_id):
        r = client.post(f"/courses/{course_id}/lessons",
                        json={"title": "Новий Урок", "content": "Зміст", "order": 3})
        assert r.status_code == 201

    def test_get_lessons(self, client, course_id):
        lessons = client.get(f"/courses/{course_id}/lessons").get_json()["lessons"]
        assert len(lessons) >= 2


# ── Enrollment ────────────────────────────────────────────────────────────────
class TestEnrollmentEndpoints:
    def test_enroll_201(self, client, student_id, course_id):
        r = client.post("/enrollments", json={"user_id": student_id, "course_id": course_id})
        assert r.status_code == 201

    def test_enroll_twice_400(self, client, student_id, course_id):
        client.post("/enrollments", json={"user_id": student_id, "course_id": course_id})
        r = client.post("/enrollments", json={"user_id": student_id, "course_id": course_id})
        assert r.status_code == 400

    def test_progress_after_enroll(self, client, student_id, course_id):
        client.post("/enrollments", json={"user_id": student_id, "course_id": course_id})
        data = client.get(f"/enrollments/{student_id}/{course_id}/progress").get_json()
        assert data["completion_percent"] == 0.0

    def test_complete_lesson_updates_progress(self, client, student_id, course_id):
        client.post("/enrollments", json={"user_id": student_id, "course_id": course_id})
        lessons = client.get(f"/courses/{course_id}/lessons").get_json()["lessons"]
        r = client.post(f"/lessons/{lessons[0]['id']}/complete",
                        json={"user_id": student_id})
        assert r.get_json()["completion_percent"] > 0

    def test_user_courses(self, client, student_id, course_id):
        client.post("/enrollments", json={"user_id": student_id, "course_id": course_id})
        data = client.get(f"/enrollments/{student_id}/courses").get_json()
        assert any(c["course_id"] == course_id for c in data["courses"])

    def test_unenroll(self, client, student_id, course_id):
        client.post("/enrollments", json={"user_id": student_id, "course_id": course_id})
        r = client.delete(f"/enrollments/{student_id}/{course_id}")
        assert r.status_code == 200


# ── Quizzes ───────────────────────────────────────────────────────────────────
class TestQuizEndpoints:
    def test_create_quiz_201(self, client, course_id):
        r = client.post("/quizzes", json={
            "course_id": course_id, "title": "Тест", "description": "Опис",
        })
        assert r.status_code == 201

    def test_add_question(self, client, course_id):
        qid = client.post("/quizzes", json={
            "course_id": course_id, "title": "Q Test", "description": "desc",
        }).get_json()["quiz_id"]
        r = client.post(f"/quizzes/{qid}/questions", json={
            "text": "Що таке Flask?", "type": "single_choice",
            "answers": [{"text": "Веб-фреймворк", "is_correct": True},
                        {"text": "БД", "is_correct": False}],
        })
        assert r.status_code == 201

    def test_full_quiz_workflow(self, client, student_id, course_id):
        qid = client.post("/quizzes", json={
            "course_id": course_id, "title": "Full", "description": "d",
            "passing_score": 50,
        }).get_json()["quiz_id"]
        q_id = client.post(f"/quizzes/{qid}/questions", json={
            "text": "2+2=?", "type": "single_choice",
            "answers": [{"text": "4", "is_correct": True}, {"text": "5", "is_correct": False}],
        }).get_json()["question_id"]
        aid = client.post(f"/quizzes/{qid}/attempts",
                          json={"user_id": student_id}).get_json()["attempt_id"]
        result = client.post(f"/attempts/{aid}/submit",
                             json={"answers": {str(q_id): 1}}).get_json()
        assert "score_percent" in result and "passed" in result

    def test_quiz_results(self, client, student_id, course_id):
        qid = client.post("/quizzes", json={
            "course_id": course_id, "title": "Res", "description": "d",
        }).get_json()["quiz_id"]
        r = client.get(f"/quizzes/{qid}/results/{student_id}")
        assert "remaining_attempts" in r.get_json()

    def test_too_many_attempts_400(self, client, student_id, course_id):
        qid = client.post("/quizzes", json={
            "course_id": course_id, "title": "Lim", "description": "d",
            "max_attempts": 1,
        }).get_json()["quiz_id"]
        client.post(f"/quizzes/{qid}/questions", json={
            "text": "Q?", "type": "true_false",
            "answers": [{"text": "True", "is_correct": True}],
        })
        aid = client.post(f"/quizzes/{qid}/attempts",
                          json={"user_id": student_id}).get_json()["attempt_id"]
        client.post(f"/attempts/{aid}/submit", json={"answers": {}})
        r = client.post(f"/quizzes/{qid}/attempts", json={"user_id": student_id})
        assert r.status_code == 400
