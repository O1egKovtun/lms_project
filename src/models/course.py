from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import List, Optional


class CourseStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DifficultyLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class Lesson:
    id: int
    course_id: int
    title: str
    content: str
    order: int
    duration_minutes: int = 30
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Course:
    id: int
    title: str
    description: str
    teacher_id: int
    category: str
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    status: CourseStatus = CourseStatus.DRAFT
    lesson_ids: List[int] = field(default_factory=list)
    quiz_ids: List[int] = field(default_factory=list)
    max_students: Optional[int] = None
    enrolled_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def publish(self) -> None:
        if self.status == CourseStatus.DRAFT:
            self.status = CourseStatus.PUBLISHED
            self.updated_at = datetime.now()

    def archive(self) -> None:
        self.status = CourseStatus.ARCHIVED
        self.updated_at = datetime.now()

    def is_published(self) -> bool:
        return self.status == CourseStatus.PUBLISHED

    def has_capacity(self) -> bool:
        if self.max_students is None:
            return True
        return self.enrolled_count < self.max_students

    def increment_enrollment(self) -> None:
        self.enrolled_count += 1

    def decrement_enrollment(self) -> None:
        if self.enrolled_count > 0:
            self.enrolled_count -= 1
