from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional, List


class ProgressStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class LessonProgress:
    user_id: int
    lesson_id: int
    course_id: int
    completed: bool = False
    completed_at: Optional[datetime] = None

    def mark_completed(self) -> None:
        self.completed = True
        self.completed_at = datetime.now()


@dataclass
class CourseProgress:
    user_id: int
    course_id: int
    status: ProgressStatus = ProgressStatus.NOT_STARTED
    completed_lesson_ids: List[int] = field(default_factory=list)
    total_lessons: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    certificate_issued: bool = False

    @property
    def completion_percent(self) -> float:
        if self.total_lessons == 0:
            return 0.0
        return round(len(self.completed_lesson_ids) /
                     self.total_lessons * 100, 2)

    def start(self) -> None:
        if self.status == ProgressStatus.NOT_STARTED:
            self.status = ProgressStatus.IN_PROGRESS
            self.started_at = datetime.now()

    def complete_lesson(self, lesson_id: int) -> None:
        if lesson_id not in self.completed_lesson_ids:
            self.completed_lesson_ids.append(lesson_id)
        if self.status == ProgressStatus.NOT_STARTED:
            self.start()
        if self.total_lessons > 0 and len(
                self.completed_lesson_ids) >= self.total_lessons:
            self.status = ProgressStatus.COMPLETED
            self.completed_at = datetime.now()

    def is_completed(self) -> bool:
        return self.status == ProgressStatus.COMPLETED
