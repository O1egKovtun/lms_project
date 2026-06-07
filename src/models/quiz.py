from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import List, Optional


class QuestionType(Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    TEXT = "text"


@dataclass
class Answer:
    id: int
    text: str
    is_correct: bool


@dataclass
class Question:
    id: int
    quiz_id: int
    text: str
    question_type: QuestionType
    answers: List[Answer] = field(default_factory=list)
    points: int = 1
    order: int = 0

    def correct_answer_ids(self) -> List[int]:
        return [a.id for a in self.answers if a.is_correct]

    def is_correct_single(self, answer_id: int) -> bool:
        return answer_id in self.correct_answer_ids()

    def is_correct_multiple(self, answer_ids: List[int]) -> bool:
        return set(answer_ids) == set(self.correct_answer_ids())


@dataclass
class Quiz:
    id: int
    course_id: int
    title: str
    description: str
    time_limit_minutes: Optional[int] = None
    passing_score: int = 70  # percent
    max_attempts: int = 3
    question_ids: List[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def is_passed(self, score_percent: float) -> bool:
        return score_percent >= self.passing_score


@dataclass
class QuizAttempt:
    id: int
    quiz_id: int
    user_id: int
    answers: dict  # {question_id: answer_id or list[answer_id]}
    score: float = 0.0
    max_score: float = 0.0
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    passed: bool = False

    @property
    def score_percent(self) -> float:
        if self.max_score == 0:
            return 0.0
        return round((self.score / self.max_score) * 100, 2)

    def finish(self, score: float, max_score: float, passed: bool) -> None:
        self.score = score
        self.max_score = max_score
        self.passed = passed
        self.finished_at = datetime.now()
