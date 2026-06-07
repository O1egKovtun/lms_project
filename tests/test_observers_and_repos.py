import pytest
from src.utils.observers import (
    EventBus, UserRegisteredEvent, UserBlockedEvent,
    StudentEnrolledEvent, CourseCompletedEvent, QuizPassedEvent
)
from src.models.progress import CourseProgress, LessonProgress, ProgressStatus
from src.storage.repositories import (
    InMemoryUserRepository, InMemoryCourseRepository,
    InMemoryCourseProgressRepository, InMemoryLessonProgressRepository,
)
from src.models.user import User, UserRole, UserStatus
from src.models.course import Course, CourseStatus, DifficultyLevel


class TestEventBus:
    def test_subscribe_and_receive_event(self):
        bus = EventBus()
        received = []
        bus.subscribe(UserRegisteredEvent, lambda e: received.append(e))
        event = UserRegisteredEvent(user_id=1, email="t@t.com")
        bus.publish(event)
        assert len(received) == 1
        assert received[0].user_id == 1

    def test_multiple_subscribers(self):
        bus = EventBus()
        log1, log2 = [], []
        bus.subscribe(StudentEnrolledEvent, lambda e: log1.append(e))
        bus.subscribe(StudentEnrolledEvent, lambda e: log2.append(e))
        bus.publish(StudentEnrolledEvent(user_id=1, course_id=2))
        assert len(log1) == 1
        assert len(log2) == 1

    def test_unsubscribe_stops_receiving(self):
        bus = EventBus()
        received = []
        handler = lambda e: received.append(e)
        bus.subscribe(UserBlockedEvent, handler)
        bus.unsubscribe(UserBlockedEvent, handler)
        bus.publish(UserBlockedEvent(user_id=1))
        assert received == []

    def test_history_records_all_events(self):
        bus = EventBus()
        bus.publish(UserRegisteredEvent(user_id=1, email="a@b.com"))
        bus.publish(UserBlockedEvent(user_id=1))
        history = bus.get_history()
        assert len(history) == 2

    def test_clear_history(self):
        bus = EventBus()
        bus.publish(UserRegisteredEvent(user_id=1, email="a@b.com"))
        bus.clear_history()
        assert bus.get_history() == []

    def test_wrong_event_type_not_delivered(self):
        bus = EventBus()
        received = []
        bus.subscribe(UserRegisteredEvent, lambda e: received.append(e))
        bus.publish(UserBlockedEvent(user_id=1))
        assert received == []

    def test_multiple_event_types(self):
        bus = EventBus()
        reg_log, block_log = [], []
        bus.subscribe(UserRegisteredEvent, lambda e: reg_log.append(e))
        bus.subscribe(UserBlockedEvent, lambda e: block_log.append(e))
        bus.publish(UserRegisteredEvent(user_id=1, email="x@y.com"))
        bus.publish(UserBlockedEvent(user_id=2))
        assert len(reg_log) == 1
        assert len(block_log) == 1


class TestInMemoryUserRepository:
    def test_save_assigns_id(self, user_repo):
        user = User(id=0, name="Test", email="t@t.com",
                    password_hash="hash", role=UserRole.STUDENT)
        saved = user_repo.save(user)
        assert saved.id > 0

    def test_save_and_find_by_id(self, user_repo):
        user = User(id=0, name="Find", email="f@t.com",
                    password_hash="hash", role=UserRole.STUDENT)
        saved = user_repo.save(user)
        found = user_repo.find_by_id(saved.id)
        assert found is not None
        assert found.email == "f@t.com"

    def test_find_nonexistent_returns_none(self, user_repo):
        assert user_repo.find_by_id(9999) is None

    def test_find_by_email(self, user_repo):
        user = User(id=0, name="Email", email="email@t.com",
                    password_hash="hash", role=UserRole.STUDENT)
        user_repo.save(user)
        found = user_repo.find_by_email("email@t.com")
        assert found is not None

    def test_find_by_email_not_found(self, user_repo):
        assert user_repo.find_by_email("nobody@t.com") is None

    def test_delete_existing(self, user_repo):
        user = User(id=0, name="Del", email="del@t.com",
                    password_hash="hash", role=UserRole.STUDENT)
        saved = user_repo.save(user)
        result = user_repo.delete(saved.id)
        assert result is True
        assert user_repo.find_by_id(saved.id) is None

    def test_delete_nonexistent_returns_false(self, user_repo):
        assert user_repo.delete(9999) is False

    def test_find_all_returns_all(self, user_repo):
        for i in range(3):
            user_repo.save(User(id=0, name=f"U{i}", email=f"u{i}@t.com",
                                password_hash="h", role=UserRole.STUDENT))
        assert len(user_repo.find_all()) == 3

    def test_exists_true(self, user_repo):
        user = User(id=0, name="Ex", email="ex@t.com",
                    password_hash="h", role=UserRole.STUDENT)
        saved = user_repo.save(user)
        assert user_repo.exists(saved.id) is True

    def test_exists_false(self, user_repo):
        assert user_repo.exists(9999) is False


class TestCourseProgressModel:
    def test_initial_status_not_started(self):
        p = CourseProgress(user_id=1, course_id=1)
        assert p.status == ProgressStatus.NOT_STARTED

    def test_start_changes_status(self):
        p = CourseProgress(user_id=1, course_id=1)
        p.start()
        assert p.status == ProgressStatus.IN_PROGRESS

    def test_start_idempotent(self):
        p = CourseProgress(user_id=1, course_id=1)
        p.start()
        p.start()
        assert p.status == ProgressStatus.IN_PROGRESS

    def test_complete_lesson_updates_list(self):
        p = CourseProgress(user_id=1, course_id=1, total_lessons=3)
        p.complete_lesson(10)
        assert 10 in p.completed_lesson_ids

    def test_complete_all_lessons_marks_completed(self):
        p = CourseProgress(user_id=1, course_id=1, total_lessons=2)
        p.complete_lesson(1)
        p.complete_lesson(2)
        assert p.is_completed()

    def test_completion_percent_calculation(self):
        p = CourseProgress(user_id=1, course_id=1, total_lessons=4)
        p.complete_lesson(1)
        p.complete_lesson(2)
        assert p.completion_percent == 50.0

    def test_completion_percent_zero_lessons(self):
        p = CourseProgress(user_id=1, course_id=1, total_lessons=0)
        assert p.completion_percent == 0.0


class TestLessonProgressModel:
    def test_initial_not_completed(self):
        lp = LessonProgress(user_id=1, lesson_id=1, course_id=1)
        assert lp.completed is False

    def test_mark_completed(self):
        lp = LessonProgress(user_id=1, lesson_id=1, course_id=1)
        lp.mark_completed()
        assert lp.completed is True
        assert lp.completed_at is not None

    def test_mark_completed_sets_timestamp(self):
        from datetime import datetime
        lp = LessonProgress(user_id=1, lesson_id=1, course_id=1)
        before = datetime.now()
        lp.mark_completed()
        assert lp.completed_at >= before
