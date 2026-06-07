import pytest
from src.models.quiz import QuestionType
from src.services.quiz_service import StrictGradingStrategy, PartialGradingStrategy
from src.utils.exceptions import (
    QuizNotFoundError, TooManyAttemptsError, QuizAlreadyFinishedError
)


class TestQuizCreation:
    def test_create_quiz_success(self, quiz_svc, published_course):
        quiz = quiz_svc.create_quiz(
            course_id=published_course.id,
            title="Вступний тест",
            description="Перевірка базових знань",
        )
        assert quiz.id > 0
        assert quiz.title == "Вступний тест"
        assert quiz.passing_score == 70

    def test_create_quiz_custom_passing_score(self, quiz_svc, published_course):
        quiz = quiz_svc.create_quiz(
            published_course.id, "Test", "Desc", passing_score=80)
        assert quiz.passing_score == 80

    def test_create_quiz_short_title_raises(self, quiz_svc, published_course):
        with pytest.raises(ValueError):
            quiz_svc.create_quiz(published_course.id, "X", "Desc")

    def test_create_quiz_invalid_passing_score_raises(self, quiz_svc, published_course):
        with pytest.raises(ValueError):
            quiz_svc.create_quiz(published_course.id, "Valid", "Desc", passing_score=110)

    def test_create_quiz_negative_passing_score_raises(self, quiz_svc, published_course):
        with pytest.raises(ValueError):
            quiz_svc.create_quiz(published_course.id, "Valid", "Desc", passing_score=-5)

    def test_create_quiz_zero_max_attempts_raises(self, quiz_svc, published_course):
        with pytest.raises(ValueError):
            quiz_svc.create_quiz(published_course.id, "Valid", "Desc", max_attempts=0)

    def test_create_quiz_with_time_limit(self, quiz_svc, published_course):
        quiz = quiz_svc.create_quiz(
            published_course.id, "Timed", "Desc", time_limit_minutes=30)
        assert quiz.time_limit_minutes == 30

    def test_get_quiz_success(self, quiz_svc, quiz_with_questions):
        quiz = quiz_svc.get_quiz(quiz_with_questions.id)
        assert quiz.id == quiz_with_questions.id

    def test_get_nonexistent_quiz_raises(self, quiz_svc):
        with pytest.raises(QuizNotFoundError):
            quiz_svc.get_quiz(9999)

    def test_create_multiple_quizzes_unique_ids(self, quiz_svc, published_course):
        q1 = quiz_svc.create_quiz(published_course.id, "Quiz1", "D1")
        q2 = quiz_svc.create_quiz(published_course.id, "Quiz2", "D2")
        assert q1.id != q2.id


class TestQuestionManagement:
    def test_add_question_success(self, quiz_svc, quiz_with_questions):
        questions = quiz_svc.get_questions(quiz_with_questions.id)
        assert len(questions) == 2

    def test_add_question_empty_text_raises(self, quiz_svc, published_course):
        quiz = quiz_svc.create_quiz(published_course.id, "QTest", "Desc")
        with pytest.raises(ValueError):
            quiz_svc.add_question(quiz.id, "", QuestionType.SINGLE_CHOICE, [])

    def test_add_question_zero_points_raises(self, quiz_svc, published_course):
        quiz = quiz_svc.create_quiz(published_course.id, "QTest", "Desc")
        with pytest.raises(ValueError):
            quiz_svc.add_question(
                quiz.id, "Text", QuestionType.SINGLE_CHOICE, [], points=0)

    def test_add_question_to_nonexistent_quiz_raises(self, quiz_svc):
        with pytest.raises(QuizNotFoundError):
            quiz_svc.add_question(9999, "Text", QuestionType.SINGLE_CHOICE, [])

    def test_questions_ordered_by_order_field(self, quiz_svc, published_course):
        quiz = quiz_svc.create_quiz(published_course.id, "Ordered", "Desc")
        quiz_svc.add_question(quiz.id, "Q3", QuestionType.TRUE_FALSE,
                               [{"text": "True", "is_correct": True}], order=3)
        quiz_svc.add_question(quiz.id, "Q1", QuestionType.TRUE_FALSE,
                               [{"text": "True", "is_correct": True}], order=1)
        quiz_svc.add_question(quiz.id, "Q2", QuestionType.TRUE_FALSE,
                               [{"text": "True", "is_correct": True}], order=2)
        questions = quiz_svc.get_questions(quiz.id)
        assert [q.order for q in questions] == [1, 2, 3]

    def test_question_correct_answer_ids(self, quiz_svc, quiz_with_questions):
        questions = quiz_svc.get_questions(quiz_with_questions.id)
        q = questions[0]
        correct = q.correct_answer_ids()
        assert len(correct) == 1

    def test_multiple_choice_correct_answers(self, quiz_svc, published_course):
        quiz = quiz_svc.create_quiz(published_course.id, "Multi", "Desc")
        q = quiz_svc.add_question(
            quiz.id, "Which are Python?", QuestionType.MULTIPLE_CHOICE,
            [
                {"text": "Python 2", "is_correct": True},
                {"text": "Python 3", "is_correct": True},
                {"text": "Java", "is_correct": False},
            ],
        )
        assert len(q.correct_answer_ids()) == 2


class TestQuizAttempts:
    def test_start_attempt_success(self, quiz_svc, student, quiz_with_questions):
        attempt = quiz_svc.start_attempt(student.id, quiz_with_questions.id)
        assert attempt.id > 0
        assert attempt.user_id == student.id
        assert attempt.quiz_id == quiz_with_questions.id

    def test_start_too_many_attempts_raises(self, quiz_svc, student, published_course):
        quiz = quiz_svc.create_quiz(
            published_course.id, "LimitedAttempts", "Desc", max_attempts=2)
        quiz_svc.add_question(
            quiz.id, "Q?", QuestionType.TRUE_FALSE,
            [{"text": "True", "is_correct": True}],
        )
        a1 = quiz_svc.start_attempt(student.id, quiz.id)
        quiz_svc.submit_attempt(a1.id, {str(q.id): q.answers[0].id
                                         for q in quiz_svc.get_questions(quiz.id)})
        a2 = quiz_svc.start_attempt(student.id, quiz.id)
        quiz_svc.submit_attempt(a2.id, {str(q.id): q.answers[0].id
                                         for q in quiz_svc.get_questions(quiz.id)})
        with pytest.raises(TooManyAttemptsError):
            quiz_svc.start_attempt(student.id, quiz.id)

    def test_submit_attempt_success(self, quiz_svc, student, quiz_with_questions):
        attempt = quiz_svc.start_attempt(student.id, quiz_with_questions.id)
        questions = quiz_svc.get_questions(quiz_with_questions.id)
        answers = {str(q.id): q.correct_answer_ids()[0] for q in questions}
        result = quiz_svc.submit_attempt(attempt.id, answers)
        assert result.finished_at is not None

    def test_submit_all_correct_passes(self, quiz_svc, student, quiz_with_questions):
        attempt = quiz_svc.start_attempt(student.id, quiz_with_questions.id)
        questions = quiz_svc.get_questions(quiz_with_questions.id)
        answers = {str(q.id): q.correct_answer_ids()[0] for q in questions}
        result = quiz_svc.submit_attempt(attempt.id, answers)
        assert result.passed is True

    def test_submit_all_wrong_fails(self, quiz_svc, student, quiz_with_questions):
        attempt = quiz_svc.start_attempt(student.id, quiz_with_questions.id)
        questions = quiz_svc.get_questions(quiz_with_questions.id)
        answers = {str(q.id): 9999 for q in questions}
        result = quiz_svc.submit_attempt(attempt.id, answers)
        assert result.passed is False

    def test_submit_twice_raises(self, quiz_svc, student, quiz_with_questions):
        attempt = quiz_svc.start_attempt(student.id, quiz_with_questions.id)
        questions = quiz_svc.get_questions(quiz_with_questions.id)
        answers = {str(q.id): q.correct_answer_ids()[0] for q in questions}
        quiz_svc.submit_attempt(attempt.id, answers)
        with pytest.raises(QuizAlreadyFinishedError):
            quiz_svc.submit_attempt(attempt.id, answers)

    def test_submit_nonexistent_attempt_raises(self, quiz_svc):
        with pytest.raises(QuizNotFoundError):
            quiz_svc.submit_attempt(9999, {})

    def test_score_percent_all_correct(self, quiz_svc, student, quiz_with_questions):
        attempt = quiz_svc.start_attempt(student.id, quiz_with_questions.id)
        questions = quiz_svc.get_questions(quiz_with_questions.id)
        answers = {str(q.id): q.correct_answer_ids()[0] for q in questions}
        result = quiz_svc.submit_attempt(attempt.id, answers)
        assert result.score_percent == 100.0

    def test_score_percent_zero_wrong(self, quiz_svc, student, quiz_with_questions):
        attempt = quiz_svc.start_attempt(student.id, quiz_with_questions.id)
        result = quiz_svc.submit_attempt(attempt.id, {})
        assert result.score_percent == 0.0

    def test_get_remaining_attempts_initial(self, quiz_svc, student, quiz_with_questions):
        remaining = quiz_svc.get_remaining_attempts(student.id, quiz_with_questions.id)
        assert remaining == quiz_with_questions.max_attempts

    def test_get_remaining_attempts_decreases(self, quiz_svc, student, quiz_with_questions):
        quiz_svc.start_attempt(student.id, quiz_with_questions.id)
        remaining = quiz_svc.get_remaining_attempts(student.id, quiz_with_questions.id)
        assert remaining == quiz_with_questions.max_attempts - 1

    def test_get_best_score_none_initially(self, quiz_svc, student, quiz_with_questions):
        best = quiz_svc.get_best_score(student.id, quiz_with_questions.id)
        assert best is None

    def test_get_best_score_after_attempt(self, quiz_svc, student, quiz_with_questions):
        attempt = quiz_svc.start_attempt(student.id, quiz_with_questions.id)
        questions = quiz_svc.get_questions(quiz_with_questions.id)
        answers = {str(q.id): q.correct_answer_ids()[0] for q in questions}
        quiz_svc.submit_attempt(attempt.id, answers)
        best = quiz_svc.get_best_score(student.id, quiz_with_questions.id)
        assert best == 100.0

    def test_get_attempt_results_dict(self, quiz_svc, student, quiz_with_questions):
        attempt = quiz_svc.start_attempt(student.id, quiz_with_questions.id)
        questions = quiz_svc.get_questions(quiz_with_questions.id)
        answers = {str(q.id): q.correct_answer_ids()[0] for q in questions}
        quiz_svc.submit_attempt(attempt.id, answers)
        results = quiz_svc.get_attempt_results(attempt.id)
        assert "score_percent" in results
        assert "passed" in results

    def test_get_user_attempts(self, quiz_svc, student, quiz_with_questions):
        quiz_svc.start_attempt(student.id, quiz_with_questions.id)
        attempts = quiz_svc.get_user_attempts(student.id, quiz_with_questions.id)
        assert len(attempts) == 1


class TestGradingStrategies:
    def test_strict_single_correct(self, quiz_svc, quiz_with_questions):
        questions = quiz_svc.get_questions(quiz_with_questions.id)
        q = questions[0]
        strategy = StrictGradingStrategy()
        correct_id = q.correct_answer_ids()[0]
        score = strategy.grade(q, correct_id)
        assert score == q.points

    def test_strict_single_wrong(self, quiz_svc, quiz_with_questions):
        questions = quiz_svc.get_questions(quiz_with_questions.id)
        q = questions[0]
        strategy = StrictGradingStrategy()
        score = strategy.grade(q, 9999)
        assert score == 0.0

    def test_strict_multiple_all_correct(self, quiz_svc, published_course):
        quiz = quiz_svc.create_quiz(published_course.id, "Multi", "Desc")
        q = quiz_svc.add_question(
            quiz.id, "Choose all", QuestionType.MULTIPLE_CHOICE,
            [{"text": "A", "is_correct": True}, {"text": "B", "is_correct": True},
             {"text": "C", "is_correct": False}],
            points=3,
        )
        strategy = StrictGradingStrategy()
        correct = q.correct_answer_ids()
        score = strategy.grade(q, correct)
        assert score == 3.0

    def test_strict_multiple_partial_gives_zero(self, quiz_svc, published_course):
        quiz = quiz_svc.create_quiz(published_course.id, "Multi2", "Desc")
        q = quiz_svc.add_question(
            quiz.id, "Choose all", QuestionType.MULTIPLE_CHOICE,
            [{"text": "A", "is_correct": True}, {"text": "B", "is_correct": True}],
            points=2,
        )
        strategy = StrictGradingStrategy()
        score = strategy.grade(q, [q.answers[0].id])  # only one of two
        assert score == 0.0

    def test_partial_strategy_gives_half_points(self, quiz_svc, published_course):
        quiz = quiz_svc.create_quiz(published_course.id, "Partial", "Desc")
        q = quiz_svc.add_question(
            quiz.id, "Choose all", QuestionType.MULTIPLE_CHOICE,
            [{"text": "A", "is_correct": True}, {"text": "B", "is_correct": True},
             {"text": "C", "is_correct": False}],
            points=2,
        )
        strategy = PartialGradingStrategy()
        score = strategy.grade(q, [q.answers[0].id])  # one of two correct
        assert score == 1.0

    def test_partial_strategy_wrong_answer_penalizes(self, quiz_svc, published_course):
        quiz = quiz_svc.create_quiz(published_course.id, "Penalty", "Desc")
        q = quiz_svc.add_question(
            quiz.id, "Choose", QuestionType.MULTIPLE_CHOICE,
            [{"text": "A", "is_correct": True}, {"text": "B", "is_correct": False}],
            points=2,
        )
        strategy = PartialGradingStrategy()
        score = strategy.grade(q, [q.answers[1].id])  # wrong answer only
        assert score == 0.0

    def test_switch_grading_strategy(self, quiz_svc, published_course):
        quiz_svc.set_grading_strategy(PartialGradingStrategy())
        assert isinstance(quiz_svc._grading, PartialGradingStrategy)

    def test_quiz_is_passed_above_threshold(self, quiz_svc, published_course):
        quiz = quiz_svc.create_quiz(
            published_course.id, "PassTest", "Desc", passing_score=70)
        assert quiz.is_passed(70.0) is True
        assert quiz.is_passed(100.0) is True

    def test_quiz_is_not_passed_below_threshold(self, quiz_svc, published_course):
        quiz = quiz_svc.create_quiz(
            published_course.id, "FailTest", "Desc", passing_score=70)
        assert quiz.is_passed(69.9) is False
        assert quiz.is_passed(0.0) is False
