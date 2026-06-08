from typing import List, Optional
from datetime import datetime

from src.models.course import Course, Lesson, CourseStatus, DifficultyLevel
from src.storage.repositories import InMemoryCourseRepository, InMemoryLessonRepository
from src.utils.exceptions import (
    CourseNotFoundError, LessonNotFoundError,
    CourseNotPublishedError, CourseFullError
)


class CourseService:
    def __init__(self,
                 course_repo: InMemoryCourseRepository,
                 lesson_repo: InMemoryLessonRepository):
        self._course_repo = course_repo
        self._lesson_repo = lesson_repo

    def create_course(self, title: str, description: str, teacher_id: int,
                      category: str, difficulty: DifficultyLevel = DifficultyLevel.BEGINNER,
                      max_students: Optional[int] = None) -> Course:
        if not title or len(title.strip()) < 3:
            raise ValueError("Title must be at least 3 characters")
        if not description or len(description.strip()) < 10:
            raise ValueError("Description must be at least 10 characters")
        if max_students is not None and max_students <= 0:
            raise ValueError("max_students must be positive")

        course = Course(
            id=0,
            title=title.strip(),
            description=description.strip(),
            teacher_id=teacher_id,
            category=category,
            difficulty=difficulty,
            max_students=max_students,
        )
        return self._course_repo.save(course)

    def get_course(self, course_id: int) -> Course:
        course = self._course_repo.find_by_id(course_id)
        if not course:
            raise CourseNotFoundError(f"Course {course_id} not found")
        return course

    def publish_course(self, course_id: int) -> Course:
        course = self.get_course(course_id)
        course.publish()
        return self._course_repo.save(course)

    def archive_course(self, course_id: int) -> Course:
        course = self.get_course(course_id)
        course.archive()
        return self._course_repo.save(course)

    def add_lesson(self, course_id: int, title: str, content: str,
                   order: int, duration_minutes: int = 30) -> Lesson:
        course = self.get_course(course_id)
        if not title or len(title.strip()) < 2:
            raise ValueError("Lesson title must be at least 2 characters")
        if not content:
            raise ValueError("Lesson content cannot be empty")

        lesson = Lesson(
            id=0,
            course_id=course_id,
            title=title.strip(),
            content=content,
            order=order,
            duration_minutes=duration_minutes,
        )
        saved = self._lesson_repo.save(lesson)
        course.lesson_ids.append(saved.id)
        self._course_repo.save(course)
        return saved

    def get_lesson(self, lesson_id: int) -> Lesson:
        lesson = self._lesson_repo.find_by_id(lesson_id)
        if not lesson:
            raise LessonNotFoundError(f"Lesson {lesson_id} not found")
        return lesson

    def get_course_lessons(self, course_id: int) -> List[Lesson]:
        self.get_course(course_id)  # validates existence
        return self._lesson_repo.find_by_course(course_id)

    def get_published_courses(self) -> List[Course]:
        return self._course_repo.find_published()

    def get_courses_by_teacher(self, teacher_id: int) -> List[Course]:
        return self._course_repo.find_by_teacher(teacher_id)

    def get_courses_by_category(self, category: str) -> List[Course]:
        return self._course_repo.find_by_category(category)

    def search_courses(self, query: str) -> List[Course]:
        q = query.lower()
        return [c for c in self._course_repo.find_all()
                if q in c.title.lower() or q in c.description.lower()]

    def update_course(self, course_id: int, **kwargs) -> Course:
        course = self.get_course(course_id)
        allowed = {
            "title",
            "description",
            "category",
            "difficulty",
            "max_students"}
        for key, val in kwargs.items():
            if key in allowed:
                setattr(course, key, val)
        course.updated_at = datetime.now()
        return self._course_repo.save(course)

    def delete_lesson(self, lesson_id: int) -> bool:
        lesson = self.get_lesson(lesson_id)
        course = self.get_course(lesson.course_id)
        if lesson_id in course.lesson_ids:
            course.lesson_ids.remove(lesson_id)
            self._course_repo.save(course)
        return self._lesson_repo.delete(lesson_id)
