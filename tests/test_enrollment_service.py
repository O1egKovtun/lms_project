import pytest
from src.models.progress import ProgressStatus
from src.utils.exceptions import (
    CourseNotPublishedError, CourseFullError,
    AlreadyEnrolledError, NotEnrolledError, CourseNotFoundError
)
from src.utils.observers import StudentEnrolledEvent, CourseCompletedEvent
from src.models.course import DifficultyLevel


class TestEnrollment:
    def test_enroll_student_success(self, enrollment_svc, student, published_course):
        progress = enrollment_svc.enroll(student.id, published_course.id)
        assert progress.user_id == student.id
        assert progress.course_id == published_course.id
        assert progress.status == ProgressStatus.NOT_STARTED

    def test_enroll_emits_event(self, enrollment_svc, student, published_course, event_bus):
        enrollment_svc.enroll(student.id, published_course.id)
        events = [e for e in event_bus.get_history() if isinstance(e, StudentEnrolledEvent)]
        assert any(e.user_id == student.id for e in events)

    def test_enroll_updates_course_enrollment_count(self, enrollment_svc, student,
                                                     published_course, course_svc):
        enrollment_svc.enroll(student.id, published_course.id)
        course = course_svc.get_course(published_course.id)
        assert course.enrolled_count == 1

    def test_enroll_adds_course_to_user(self, enrollment_svc, student,
                                         published_course, user_svc):
        enrollment_svc.enroll(student.id, published_course.id)
        user = user_svc.get_user(student.id)
        assert published_course.id in user.enrolled_course_ids

    def test_enroll_draft_course_raises(self, enrollment_svc, student,
                                         course_svc, teacher):
        draft = course_svc.create_course(
            "Draft", "Чорновий курс не доступний", teacher.id, "cat")
        with pytest.raises(CourseNotPublishedError):
            enrollment_svc.enroll(student.id, draft.id)

    def test_enroll_twice_raises(self, enrollment_svc, student, published_course):
        enrollment_svc.enroll(student.id, published_course.id)
        with pytest.raises(AlreadyEnrolledError):
            enrollment_svc.enroll(student.id, published_course.id)

    def test_enroll_full_course_raises(self, enrollment_svc, user_svc,
                                        course_svc, teacher):
        limited = course_svc.create_course(
            "Limited", "Обмежений курс лише 1 місце",
            teacher.id, "cat", max_students=1,
        )
        course_svc.publish_course(limited.id)
        limited = course_svc.get_course(limited.id)

        student1 = user_svc.register("S1", "s1@t.com", "pass123")
        student2 = user_svc.register("S2", "s2@t.com", "pass123")
        enrollment_svc.enroll(student1.id, limited.id)
        with pytest.raises(CourseFullError):
            enrollment_svc.enroll(student2.id, limited.id)

    def test_enroll_nonexistent_student_raises(self, enrollment_svc, published_course):
        from src.utils.exceptions import UserNotFoundError
        with pytest.raises(UserNotFoundError):
            enrollment_svc.enroll(9999, published_course.id)

    def test_enroll_nonexistent_course_raises(self, enrollment_svc, student):
        with pytest.raises(CourseNotFoundError):
            enrollment_svc.enroll(student.id, 9999)

    def test_enroll_sets_total_lessons(self, enrollment_svc, student, published_course):
        progress = enrollment_svc.enroll(student.id, published_course.id)
        assert progress.total_lessons == 2  # published_course fixture has 2 lessons


class TestUnenrollment:
    def test_unenroll_success(self, enrollment_svc, student, published_course, user_svc):
        enrollment_svc.enroll(student.id, published_course.id)
        result = enrollment_svc.unenroll(student.id, published_course.id)
        assert result is True
        user = user_svc.get_user(student.id)
        assert published_course.id not in user.enrolled_course_ids

    def test_unenroll_decrements_course_count(self, enrollment_svc, student,
                                               published_course, course_svc):
        enrollment_svc.enroll(student.id, published_course.id)
        enrollment_svc.unenroll(student.id, published_course.id)
        course = course_svc.get_course(published_course.id)
        assert course.enrolled_count == 0

    def test_unenroll_not_enrolled_raises(self, enrollment_svc, student, published_course):
        with pytest.raises(NotEnrolledError):
            enrollment_svc.unenroll(student.id, published_course.id)

    def test_reenroll_after_unenroll(self, enrollment_svc, student, published_course):
        enrollment_svc.enroll(student.id, published_course.id)
        enrollment_svc.unenroll(student.id, published_course.id)
        progress = enrollment_svc.enroll(student.id, published_course.id)
        assert progress is not None


class TestLessonCompletion:
    def test_complete_lesson_success(self, enrollment_svc, student, published_course, course_svc):
        enrollment_svc.enroll(student.id, published_course.id)
        lessons = course_svc.get_course_lessons(published_course.id)
        progress = enrollment_svc.complete_lesson(student.id, lessons[0].id)
        assert lessons[0].id in progress.completed_lesson_ids

    def test_complete_lesson_updates_percent(self, enrollment_svc, student,
                                              published_course, course_svc):
        enrollment_svc.enroll(student.id, published_course.id)
        lessons = course_svc.get_course_lessons(published_course.id)
        progress = enrollment_svc.complete_lesson(student.id, lessons[0].id)
        assert progress.completion_percent == 50.0

    def test_complete_all_lessons_marks_completed(self, enrollment_svc, student,
                                                    published_course, course_svc):
        enrollment_svc.enroll(student.id, published_course.id)
        lessons = course_svc.get_course_lessons(published_course.id)
        for lesson in lessons:
            enrollment_svc.complete_lesson(student.id, lesson.id)
        progress = enrollment_svc.get_progress(student.id, published_course.id)
        assert progress.is_completed()

    def test_complete_all_emits_course_completed_event(self, enrollment_svc, student,
                                                         published_course, course_svc, event_bus):
        enrollment_svc.enroll(student.id, published_course.id)
        lessons = course_svc.get_course_lessons(published_course.id)
        for lesson in lessons:
            enrollment_svc.complete_lesson(student.id, lesson.id)
        events = [e for e in event_bus.get_history() if isinstance(e, CourseCompletedEvent)]
        assert any(e.user_id == student.id for e in events)

    def test_complete_lesson_idempotent(self, enrollment_svc, student,
                                         published_course, course_svc):
        enrollment_svc.enroll(student.id, published_course.id)
        lessons = course_svc.get_course_lessons(published_course.id)
        enrollment_svc.complete_lesson(student.id, lessons[0].id)
        progress = enrollment_svc.complete_lesson(student.id, lessons[0].id)
        assert progress.completed_lesson_ids.count(lessons[0].id) == 1

    def test_complete_lesson_not_enrolled_raises(self, enrollment_svc, student,
                                                   published_course, course_svc):
        lessons = course_svc.get_course_lessons(published_course.id)
        with pytest.raises(NotEnrolledError):
            enrollment_svc.complete_lesson(student.id, lessons[0].id)


class TestProgressTracking:
    def test_get_progress_not_started(self, enrollment_svc, student, published_course):
        enrollment_svc.enroll(student.id, published_course.id)
        progress = enrollment_svc.get_progress(student.id, published_course.id)
        assert progress.status == ProgressStatus.NOT_STARTED

    def test_get_progress_in_progress_after_lesson(self, enrollment_svc, student,
                                                     published_course, course_svc):
        enrollment_svc.enroll(student.id, published_course.id)
        lessons = course_svc.get_course_lessons(published_course.id)
        enrollment_svc.complete_lesson(student.id, lessons[0].id)
        progress = enrollment_svc.get_progress(student.id, published_course.id)
        assert progress.status == ProgressStatus.IN_PROGRESS

    def test_get_user_courses_returns_enrolled(self, enrollment_svc, student, published_course):
        enrollment_svc.enroll(student.id, published_course.id)
        courses = enrollment_svc.get_user_courses(student.id)
        assert any(p.course_id == published_course.id for p in courses)

    def test_get_course_students_count(self, enrollment_svc, student,
                                        published_course, user_svc):
        enrollment_svc.enroll(student.id, published_course.id)
        s2 = user_svc.register("Student2", "s2@t.com", "pass123")
        enrollment_svc.enroll(s2.id, published_course.id)
        count = enrollment_svc.get_course_students_count(published_course.id)
        assert count == 2

    def test_get_lesson_progress_empty_initially(self, enrollment_svc, student, published_course):
        enrollment_svc.enroll(student.id, published_course.id)
        lp = enrollment_svc.get_lesson_progress(student.id, published_course.id)
        assert lp == []

    def test_get_lesson_progress_after_completion(self, enrollment_svc, student,
                                                    published_course, course_svc):
        enrollment_svc.enroll(student.id, published_course.id)
        lessons = course_svc.get_course_lessons(published_course.id)
        enrollment_svc.complete_lesson(student.id, lessons[0].id)
        lp = enrollment_svc.get_lesson_progress(student.id, published_course.id)
        assert len(lp) == 1
        assert lp[0].completed is True

    def test_completion_percent_zero_initially(self, enrollment_svc, student, published_course):
        enrollment_svc.enroll(student.id, published_course.id)
        progress = enrollment_svc.get_progress(student.id, published_course.id)
        assert progress.completion_percent == 0.0

    def test_completion_percent_100_when_done(self, enrollment_svc, student,
                                               published_course, course_svc):
        enrollment_svc.enroll(student.id, published_course.id)
        lessons = course_svc.get_course_lessons(published_course.id)
        for lesson in lessons:
            enrollment_svc.complete_lesson(student.id, lesson.id)
        progress = enrollment_svc.get_progress(student.id, published_course.id)
        assert progress.completion_percent == 100.0

    def test_multiple_students_independent_progress(self, enrollment_svc, user_svc,
                                                     published_course, course_svc):
        s1 = user_svc.register("Stud1", "st1@t.com", "pass123")
        s2 = user_svc.register("Stud2", "st2@t.com", "pass123")
        enrollment_svc.enroll(s1.id, published_course.id)
        enrollment_svc.enroll(s2.id, published_course.id)
        lessons = course_svc.get_course_lessons(published_course.id)
        enrollment_svc.complete_lesson(s1.id, lessons[0].id)
        p1 = enrollment_svc.get_progress(s1.id, published_course.id)
        p2 = enrollment_svc.get_progress(s2.id, published_course.id)
        assert p1.completion_percent > p2.completion_percent
