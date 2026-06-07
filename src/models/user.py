from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import List


class UserRole(Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class UserStatus(Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    PENDING = "pending"


@dataclass
class User:
    id: int
    name: str
    email: str
    password_hash: str
    role: UserRole = UserRole.STUDENT
    status: UserStatus = UserStatus.ACTIVE
    enrolled_course_ids: List[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    def is_student(self) -> bool:
        return self.role == UserRole.STUDENT

    def is_teacher(self) -> bool:
        return self.role == UserRole.TEACHER

    def enroll(self, course_id: int) -> None:
        if course_id not in self.enrolled_course_ids:
            self.enrolled_course_ids.append(course_id)

    def unenroll(self, course_id: int) -> None:
        if course_id in self.enrolled_course_ids:
            self.enrolled_course_ids.remove(course_id)

    def block(self) -> None:
        self.status = UserStatus.BLOCKED

    def activate(self) -> None:
        self.status = UserStatus.ACTIVE
