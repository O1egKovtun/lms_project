from typing import List

from src.models.progress import CourseProgress, LessonProgress, ProgressStatus
from src.storage.repositories import (
    InMemoryUserRepository, InMemoryCourseProgressRepository,
    InMemoryLessonProgressRepository
)
from src.services.course_service import CourseService
from src.services.user_service import UserService
from src.utils.exceptions import (
    CourseNotPublishedError, CourseFullError,
    AlreadyEnrolledError, NotEnrolledError
)
from src.utils.observers import EventBus, StudentEnrolledEvent, CourseCompletedEvent


class EnrollmentService:
    def __init__(self,
                 user_service: UserService,
                 course_service: CourseService,
                 user_repo: InMemoryUserRepository,
                 progress_repo: InMemoryCourseProgressRepository,
                 lesson_progress_repo: InMemoryLessonProgressRepository,
                 event_bus: EventBus = None):
        self._user_service = user_service
        self._course_service = course_service
        self._user_repo = user_repo
        self._progress_repo = progress_repo
        self._lesson_progress_repo = lesson_progress_repo
        self._event_bus = event_bus or EventBus()

    def enroll(self, user_id: int, course_id: int) -> CourseProgress:
        user = self._user_service.get_user(user_id)
        course = self._course_service.get_course(course_id)

        if not course.is_published():
            raise CourseNotPublishedError(
                f"Course {course_id} is not published")
        if not course.has_capacity():
            raise CourseFullError(f"Course {course_id} is full")
        if course_id in user.enrolled_course_ids:
            raise AlreadyEnrolledError(
                f"User {user_id} already enrolled in course {course_id}")

        user.enroll(course_id)
        course.increment_enrollment()
        self._user_repo.save(user)
        self._course_service._course_repo.save(course)

        lessons = self._course_service.get_course_lessons(course_id)
        progress = CourseProgress(
            user_id=user_id,
            course_id=course_id,
            total_lessons=len(lessons),
        )
        saved = self._progress_repo.save(progress)
        self._event_bus.publish(
            StudentEnrolledEvent(
                user_id=user_id,
                course_id=course_id))
        return saved

    def unenroll(self, user_id: int, course_id: int) -> bool:
        user = self._user_service.get_user(user_id)
        if course_id not in user.enrolled_course_ids:
            raise NotEnrolledError(
                f"User {user_id} not enrolled in course {course_id}")

        course = self._course_service.get_course(course_id)
        user.unenroll(course_id)
        course.decrement_enrollment()
        self._user_repo.save(user)
        self._course_service._course_repo.save(course)
        self._progress_repo.delete(user_id, course_id)
        return True

    def complete_lesson(self, user_id: int, lesson_id: int) -> CourseProgress:
        lesson = self._course_service.get_lesson(lesson_id)
        user = self._user_service.get_user(user_id)

        if lesson.course_id not in user.enrolled_course_ids:
            raise NotEnrolledError(
                f"User {user_id} not enrolled in course {lesson.course_id}")

        lesson_prog = self._lesson_progress_repo.find(user_id, lesson_id)
        if not lesson_prog:
            lesson_prog = LessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                course_id=lesson.course_id,
            )
        lesson_prog.mark_completed()
        self._lesson_progress_repo.save(lesson_prog)

        progress = self._progress_repo.find(user_id, lesson.course_id)
        if progress:
            progress.complete_lesson(lesson_id)
            self._progress_repo.save(progress)
            if progress.is_completed():
                self._event_bus.publish(
                    CourseCompletedEvent(
                        user_id=user_id, course_id=lesson.course_id)
                )
        return progress

    def get_progress(self, user_id: int, course_id: int) -> CourseProgress:
        progress = self._progress_repo.find(user_id, course_id)
        if not progress:
            self._user_service.get_user(user_id)
            self._course_service.get_course(course_id)
            return CourseProgress(user_id=user_id, course_id=course_id)
        return progress

    def get_user_courses(self, user_id: int) -> List[CourseProgress]:
        self._user_service.get_user(user_id)
        return self._progress_repo.find_by_user(user_id)

    def get_course_students_count(self, course_id: int) -> int:
        self._course_service.get_course(course_id)
        return len(self._progress_repo.find_by_course(course_id))

    def get_lesson_progress(self, user_id: int,
                            course_id: int) -> List[LessonProgress]:
        return self._lesson_progress_repo.find_by_user_and_course(
            user_id, course_id)
