class LMSBaseError(Exception):
    pass


class UserNotFoundError(LMSBaseError):
    pass


class EmailAlreadyExistsError(LMSBaseError):
    pass


class InvalidEmailError(LMSBaseError):
    pass


class UserBlockedError(LMSBaseError):
    pass


class InvalidCredentialsError(LMSBaseError):
    pass


class CourseNotFoundError(LMSBaseError):
    pass


class LessonNotFoundError(LMSBaseError):
    pass


class CourseNotPublishedError(LMSBaseError):
    pass


class CourseFullError(LMSBaseError):
    pass


class AlreadyEnrolledError(LMSBaseError):
    pass


class NotEnrolledError(LMSBaseError):
    pass


class QuizNotFoundError(LMSBaseError):
    pass


class QuestionNotFoundError(LMSBaseError):
    pass


class TooManyAttemptsError(LMSBaseError):
    pass


class QuizAlreadyFinishedError(LMSBaseError):
    pass
