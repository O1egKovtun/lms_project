from abc import ABC, abstractmethod
from typing import List, Dict, Optional

from src.models.quiz import Quiz, Question, QuizAttempt, QuestionType, Answer
from src.storage.repositories import (
    InMemoryQuizRepository, InMemoryQuestionRepository, InMemoryAttemptRepository
)
from src.utils.exceptions import (
    QuizNotFoundError, QuestionNotFoundError,
    TooManyAttemptsError, QuizAlreadyFinishedError
)


# ── Strategy Pattern: Grading ───────────────────────────────────────────

class IGradingStrategy(ABC):
    @abstractmethod
    def grade(self, question: Question, user_answer) -> float:
        pass


class StrictGradingStrategy(IGradingStrategy):
    """Full points only if ALL correct answers selected and nothing wrong."""

    def grade(self, question: Question, user_answer) -> float:
        correct = set(question.correct_answer_ids())
        if isinstance(user_answer, list):
            selected = set(user_answer)
        else:
            selected = {user_answer}
        return float(question.points) if selected == correct else 0.0


class PartialGradingStrategy(IGradingStrategy):
    """Partial points for partially correct multiple-choice."""

    def grade(self, question: Question, user_answer) -> float:
        correct = set(question.correct_answer_ids())
        if isinstance(user_answer, list):
            selected = set(user_answer)
        else:
            selected = {user_answer}
        if not correct:
            return 0.0
        true_positives = len(selected & correct)
        false_positives = len(selected - correct)
        score = (true_positives - false_positives) / \
            len(correct) * question.points
        return max(0.0, score)


# ── Observer notifications (placeholder) ─────────────────────────────────────

class QuizService:
    def __init__(self,
                 quiz_repo: InMemoryQuizRepository,
                 question_repo: InMemoryQuestionRepository,
                 attempt_repo: InMemoryAttemptRepository,
                 grading_strategy: IGradingStrategy = None):
        self._quiz_repo = quiz_repo
        self._question_repo = question_repo
        self._attempt_repo = attempt_repo
        self._grading = grading_strategy or StrictGradingStrategy()

    def set_grading_strategy(self, strategy: IGradingStrategy) -> None:
        self._grading = strategy

    # ── Quiz management ─────────────────────────────────────────────────────

    def create_quiz(self, course_id: int, title: str, description: str,
                    passing_score: int = 70, time_limit_minutes: Optional[int] = None,
                    max_attempts: int = 3) -> Quiz:
        if not title or len(title.strip()) < 2:
            raise ValueError("Quiz title must be at least 2 characters")
        if not 0 <= passing_score <= 100:
            raise ValueError("Passing score must be between 0 and 100")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        quiz = Quiz(
            id=0,
            course_id=course_id,
            title=title.strip(),
            description=description,
            passing_score=passing_score,
            time_limit_minutes=time_limit_minutes,
            max_attempts=max_attempts,
        )
        return self._quiz_repo.save(quiz)

    def get_quiz(self, quiz_id: int) -> Quiz:
        quiz = self._quiz_repo.find_by_id(quiz_id)
        if not quiz:
            raise QuizNotFoundError(f"Quiz {quiz_id} not found")
        return quiz

    def add_question(self, quiz_id: int, text: str,
                     question_type: QuestionType,
                     answers: List[Dict], points: int = 1, order: int = 0) -> Question:
        quiz = self.get_quiz(quiz_id)
        if not text:
            raise ValueError("Question text cannot be empty")
        if points < 1:
            raise ValueError("Points must be at least 1")

        answer_objs = [
            Answer(
                id=i + 1,
                text=a["text"],
                is_correct=a.get(
                    "is_correct",
                    False))
            for i, a in enumerate(answers)
        ]
        q = Question(
            id=0,
            quiz_id=quiz_id,
            text=text,
            question_type=question_type,
            answers=answer_objs,
            points=points,
            order=order,
        )
        saved = self._question_repo.save(q)
        quiz.question_ids.append(saved.id)
        self._quiz_repo.save(quiz)
        return saved

    def get_questions(self, quiz_id: int) -> List[Question]:
        self.get_quiz(quiz_id)
        return self._question_repo.find_by_quiz(quiz_id)

    # ── Attempt flow ────────────────────────────────────────────────────────

    def start_attempt(self, user_id: int, quiz_id: int) -> QuizAttempt:
        quiz = self.get_quiz(quiz_id)
        past = self._attempt_repo.find_by_user_and_quiz(user_id, quiz_id)
        if len(past) >= quiz.max_attempts:
            raise TooManyAttemptsError(
                f"Max {quiz.max_attempts} attempts allowed for quiz {quiz_id}"
            )
        attempt = QuizAttempt(
            id=0,
            quiz_id=quiz_id,
            user_id=user_id,
            answers={})
        return self._attempt_repo.save(attempt)

    def submit_attempt(self, attempt_id: int, answers: Dict) -> QuizAttempt:
        attempt = self._attempt_repo.find_by_id(attempt_id)
        if not attempt:
            raise QuizNotFoundError(f"Attempt {attempt_id} not found")
        if attempt.finished_at is not None:
            raise QuizAlreadyFinishedError(
                f"Attempt {attempt_id} already submitted")

        attempt.answers = answers
        quiz = self.get_quiz(attempt.quiz_id)
        questions = self.get_questions(
            quiz.quiz_id if hasattr(
                quiz, 'quiz_id') else attempt.quiz_id)

        total_score = 0.0
        max_score = 0.0
        for q in questions:
            max_score += q.points
            user_ans = answers.get(str(q.id)) or answers.get(q.id)
            if user_ans is not None:
                total_score += self._grading.grade(q, user_ans)

        passed = quiz.is_passed(
            (total_score / max_score * 100) if max_score > 0 else 0)
        attempt.finish(total_score, max_score, passed)
        return self._attempt_repo.save(attempt)

    def get_attempt_results(self, attempt_id: int) -> dict:
        attempt = self._attempt_repo.find_by_id(attempt_id)
        if not attempt:
            raise QuizNotFoundError(f"Attempt {attempt_id} not found")
        return {
            "attempt_id": attempt.id,
            "quiz_id": attempt.quiz_id,
            "user_id": attempt.user_id,
            "score": attempt.score,
            "max_score": attempt.max_score,
            "score_percent": attempt.score_percent,
            "passed": attempt.passed,
            "started_at": attempt.started_at.isoformat(),
            "finished_at": attempt.finished_at.isoformat() if attempt.finished_at else None,
        }

    def get_user_attempts(self, user_id: int,
                          quiz_id: int) -> List[QuizAttempt]:
        return self._attempt_repo.find_by_user_and_quiz(user_id, quiz_id)

    def get_remaining_attempts(self, user_id: int, quiz_id: int) -> int:
        quiz = self.get_quiz(quiz_id)
        used = len(self._attempt_repo.find_by_user_and_quiz(user_id, quiz_id))
        return max(0, quiz.max_attempts - used)

    def get_best_score(self, user_id: int, quiz_id: int) -> Optional[float]:
        attempts = self._attempt_repo.find_by_user_and_quiz(user_id, quiz_id)
        finished = [a for a in attempts if a.finished_at]
        if not finished:
            return None
        return max(a.score_percent for a in finished)
