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
from src.models.user import UserRole
from src.models.course import DifficultyLevel
from src.models.quiz import QuestionType


@pytest.fixture
def event_bus():
    return EventBus()

@pytest.fixture
def user_repo():
    return InMemoryUserRepository()

@pytest.fixture
def course_repo():
    return InMemoryCourseRepository()

@pytest.fixture
def lesson_repo():
    return InMemoryLessonRepository()

@pytest.fixture
def quiz_repo():
    return InMemoryQuizRepository()

@pytest.fixture
def question_repo():
    return InMemoryQuestionRepository()

@pytest.fixture
def attempt_repo():
    return InMemoryAttemptRepository()

@pytest.fixture
def progress_repo():
    return InMemoryCourseProgressRepository()

@pytest.fixture
def lesson_progress_repo():
    return InMemoryLessonProgressRepository()

@pytest.fixture
def user_svc(user_repo, event_bus):
    return UserService(user_repo, event_bus)

@pytest.fixture
def course_svc(course_repo, lesson_repo):
    return CourseService(course_repo, lesson_repo)

@pytest.fixture
def enrollment_svc(user_svc, course_svc, user_repo, progress_repo, lesson_progress_repo, event_bus):
    return EnrollmentService(user_svc, course_svc, user_repo, progress_repo, lesson_progress_repo, event_bus)

@pytest.fixture
def quiz_svc(quiz_repo, question_repo, attempt_repo):
    return QuizService(quiz_repo, question_repo, attempt_repo)

@pytest.fixture
def student(user_svc):
    return user_svc.register("Олег Ковтун", "oleg@test.com", "pass123", UserRole.STUDENT)

@pytest.fixture
def teacher(user_svc):
    return user_svc.register("Проф. Швелеба", "teacher@test.com", "pass123", UserRole.TEACHER)

@pytest.fixture
def published_course(course_svc, teacher):
    course = course_svc.create_course(
        title="Python для початківців",
        description="Базовий курс Python з нуля до джуна",
        teacher_id=teacher.id,
        category="programming",
        difficulty=DifficultyLevel.BEGINNER,
    )
    course_svc.add_lesson(course.id, "Вступ до Python", "Контент уроку 1", order=1)
    course_svc.add_lesson(course.id, "Змінні та типи", "Контент уроку 2", order=2)
    course_svc.publish_course(course.id)
    return course_svc.get_course(course.id)

@pytest.fixture
def quiz_with_questions(quiz_svc, published_course):
    quiz = quiz_svc.create_quiz(
        course_id=published_course.id,
        title="Тест з Python",
        description="Базовий тест",
        passing_score=60,
        max_attempts=3,
    )
    quiz_svc.add_question(
        quiz_id=quiz.id,
        text="Що таке Python?",
        question_type=QuestionType.SINGLE_CHOICE,
        answers=[
            {"text": "Мова програмування", "is_correct": True},
            {"text": "База даних", "is_correct": False},
            {"text": "Операційна система", "is_correct": False},
        ],
        points=2,
        order=1,
    )
    quiz_svc.add_question(
        quiz_id=quiz.id,
        text="Python є інтерпретованою мовою?",
        question_type=QuestionType.TRUE_FALSE,
        answers=[
            {"text": "True", "is_correct": True},
            {"text": "False", "is_correct": False},
        ],
        points=1,
        order=2,
    )
    return quiz_svc.get_quiz(quiz.id)
