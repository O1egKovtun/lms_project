from typing import Optional, List, Dict
from src.storage.interfaces import IRepository
from src.models.user import User
from src.models.course import Course, Lesson
from src.models.quiz import Quiz, Question, QuizAttempt
from src.models.progress import CourseProgress, LessonProgress


class InMemoryUserRepository(IRepository[User]):
    def __init__(self):
        self._store: Dict[int, User] = {}
        self._next_id: int = 1

    def save(self, user: User) -> User:
        if user.id == 0 or user.id is None:
            user.id = self._next_id
            self._next_id += 1
        self._store[user.id] = user
        return user

    def find_by_id(self, entity_id: int) -> Optional[User]:
        return self._store.get(entity_id)

    def find_all(self) -> List[User]:
        return list(self._store.values())

    def delete(self, entity_id: int) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def exists(self, entity_id: int) -> bool:
        return entity_id in self._store

    def find_by_email(self, email: str) -> Optional[User]:
        for user in self._store.values():
            if user.email.lower() == email.lower():
                return user
        return None

    def find_by_role(self, role) -> List[User]:
        return [u for u in self._store.values() if u.role == role]


class InMemoryCourseRepository(IRepository[Course]):
    def __init__(self):
        self._store: Dict[int, Course] = {}
        self._next_id: int = 1

    def save(self, course: Course) -> Course:
        if course.id == 0 or course.id is None:
            course.id = self._next_id
            self._next_id += 1
        self._store[course.id] = course
        return course

    def find_by_id(self, entity_id: int) -> Optional[Course]:
        return self._store.get(entity_id)

    def find_all(self) -> List[Course]:
        return list(self._store.values())

    def delete(self, entity_id: int) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def exists(self, entity_id: int) -> bool:
        return entity_id in self._store

    def find_published(self) -> List[Course]:
        from src.models.course import CourseStatus
        return [c for c in self._store.values() if c.status ==
                CourseStatus.PUBLISHED]

    def find_by_teacher(self, teacher_id: int) -> List[Course]:
        return [c for c in self._store.values() if c.teacher_id == teacher_id]

    def find_by_category(self, category: str) -> List[Course]:
        return [c for c in self._store.values() if c.category.lower()
                == category.lower()]


class InMemoryLessonRepository(IRepository[Lesson]):
    def __init__(self):
        self._store: Dict[int, Lesson] = {}
        self._next_id: int = 1

    def save(self, lesson: Lesson) -> Lesson:
        if lesson.id == 0 or lesson.id is None:
            lesson.id = self._next_id
            self._next_id += 1
        self._store[lesson.id] = lesson
        return lesson

    def find_by_id(self, entity_id: int) -> Optional[Lesson]:
        return self._store.get(entity_id)

    def find_all(self) -> List[Lesson]:
        return list(self._store.values())

    def delete(self, entity_id: int) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def exists(self, entity_id: int) -> bool:
        return entity_id in self._store

    def find_by_course(self, course_id: int) -> List[Lesson]:
        lessons = [l for l in self._store.values() if l.course_id == course_id]
        return sorted(lessons, key=lambda l: l.order)


class InMemoryQuizRepository(IRepository[Quiz]):
    def __init__(self):
        self._store: Dict[int, Quiz] = {}
        self._next_id: int = 1

    def save(self, quiz: Quiz) -> Quiz:
        if quiz.id == 0 or quiz.id is None:
            quiz.id = self._next_id
            self._next_id += 1
        self._store[quiz.id] = quiz
        return quiz

    def find_by_id(self, entity_id: int) -> Optional[Quiz]:
        return self._store.get(entity_id)

    def find_all(self) -> List[Quiz]:
        return list(self._store.values())

    def delete(self, entity_id: int) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def exists(self, entity_id: int) -> bool:
        return entity_id in self._store

    def find_by_course(self, course_id: int) -> List[Quiz]:
        return [q for q in self._store.values() if q.course_id == course_id]


class InMemoryQuestionRepository(IRepository[Question]):
    def __init__(self):
        self._store: Dict[int, Question] = {}
        self._next_id: int = 1

    def save(self, question: Question) -> Question:
        if question.id == 0 or question.id is None:
            question.id = self._next_id
            self._next_id += 1
        self._store[question.id] = question
        return question

    def find_by_id(self, entity_id: int) -> Optional[Question]:
        return self._store.get(entity_id)

    def find_all(self) -> List[Question]:
        return list(self._store.values())

    def delete(self, entity_id: int) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def exists(self, entity_id: int) -> bool:
        return entity_id in self._store

    def find_by_quiz(self, quiz_id: int) -> List[Question]:
        questions = [q for q in self._store.values() if q.quiz_id == quiz_id]
        return sorted(questions, key=lambda q: q.order)


class InMemoryAttemptRepository(IRepository[QuizAttempt]):
    def __init__(self):
        self._store: Dict[int, QuizAttempt] = {}
        self._next_id: int = 1

    def save(self, attempt: QuizAttempt) -> QuizAttempt:
        if attempt.id == 0 or attempt.id is None:
            attempt.id = self._next_id
            self._next_id += 1
        self._store[attempt.id] = attempt
        return attempt

    def find_by_id(self, entity_id: int) -> Optional[QuizAttempt]:
        return self._store.get(entity_id)

    def find_all(self) -> List[QuizAttempt]:
        return list(self._store.values())

    def delete(self, entity_id: int) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def exists(self, entity_id: int) -> bool:
        return entity_id in self._store

    def find_by_user_and_quiz(self, user_id: int,
                              quiz_id: int) -> List[QuizAttempt]:
        return [a for a in self._store.values()
                if a.user_id == user_id and a.quiz_id == quiz_id]

    def find_by_user(self, user_id: int) -> List[QuizAttempt]:
        return [a for a in self._store.values() if a.user_id == user_id]


class InMemoryCourseProgressRepository:
    def __init__(self):
        self._store: Dict[tuple, CourseProgress] = {}

    def save(self, progress: CourseProgress) -> CourseProgress:
        self._store[(progress.user_id, progress.course_id)] = progress
        return progress

    def find(self, user_id: int, course_id: int) -> Optional[CourseProgress]:
        return self._store.get((user_id, course_id))

    def find_by_user(self, user_id: int) -> List[CourseProgress]:
        return [p for p in self._store.values() if p.user_id == user_id]

    def find_by_course(self, course_id: int) -> List[CourseProgress]:
        return [p for p in self._store.values() if p.course_id == course_id]

    def delete(self, user_id: int, course_id: int) -> bool:
        key = (user_id, course_id)
        if key in self._store:
            del self._store[key]
            return True
        return False


class InMemoryLessonProgressRepository:
    def __init__(self):
        self._store: Dict[tuple, LessonProgress] = {}

    def save(self, progress: LessonProgress) -> LessonProgress:
        self._store[(progress.user_id, progress.lesson_id)] = progress
        return progress

    def find(self, user_id: int, lesson_id: int) -> Optional[LessonProgress]:
        return self._store.get((user_id, lesson_id))

    def find_by_user_and_course(self, user_id: int,
                                course_id: int) -> List[LessonProgress]:
        return [p for p in self._store.values()
                if p.user_id == user_id and p.course_id == course_id]
