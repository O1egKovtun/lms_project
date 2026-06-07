import pytest
from src.models.user import UserRole, UserStatus
from src.utils.exceptions import (
    EmailAlreadyExistsError, InvalidEmailError,
    UserNotFoundError, UserBlockedError, InvalidCredentialsError
)
from src.utils.observers import UserRegisteredEvent, UserBlockedEvent


class TestUserRegistration:
    def test_register_student_success(self, user_svc):
        user = user_svc.register("Іван Франко", "ivan@test.com", "pass123")
        assert user.id > 0
        assert user.name == "Іван Франко"
        assert user.email == "ivan@test.com"
        assert user.role == UserRole.STUDENT

    def test_register_teacher_success(self, user_svc):
        user = user_svc.register("Проф. Шевченко", "prof@test.com", "pass123", UserRole.TEACHER)
        assert user.role == UserRole.TEACHER

    def test_register_trims_name(self, user_svc):
        user = user_svc.register("  Олег  ", "oleg@test.com", "pass123")
        assert user.name == "Олег"

    def test_register_lowercases_email(self, user_svc):
        user = user_svc.register("Test", "TEST@MAIL.COM", "pass123")
        assert user.email == "test@mail.com"

    def test_register_duplicate_email_raises(self, user_svc):
        user_svc.register("First", "same@mail.com", "pass123")
        with pytest.raises(EmailAlreadyExistsError):
            user_svc.register("Second", "same@mail.com", "pass123")

    def test_register_invalid_email_raises(self, user_svc):
        with pytest.raises(InvalidEmailError):
            user_svc.register("Test", "not-an-email", "pass123")

    def test_register_invalid_email_no_dot(self, user_svc):
        with pytest.raises(InvalidEmailError):
            user_svc.register("Test", "user@nodot", "pass123")

    def test_register_short_name_raises(self, user_svc):
        with pytest.raises(ValueError):
            user_svc.register("A", "valid@mail.com", "pass123")

    def test_register_empty_name_raises(self, user_svc):
        with pytest.raises(ValueError):
            user_svc.register("", "valid@mail.com", "pass123")

    def test_register_short_password_raises(self, user_svc):
        with pytest.raises(ValueError):
            user_svc.register("Valid Name", "valid@mail.com", "123")

    def test_register_empty_password_raises(self, user_svc):
        with pytest.raises(ValueError):
            user_svc.register("Valid Name", "valid@mail.com", "")

    def test_register_password_not_stored_plaintext(self, user_svc):
        user = user_svc.register("Test", "t@t.com", "mypassword")
        assert user.password_hash != "mypassword"

    def test_register_emits_event(self, user_svc, event_bus):
        user_svc.register("Test", "event@t.com", "pass123")
        events = [e for e in event_bus.get_history() if isinstance(e, UserRegisteredEvent)]
        assert len(events) == 1
        assert events[0].email == "event@t.com"

    def test_register_multiple_users_unique_ids(self, user_svc):
        u1 = user_svc.register("User One", "u1@t.com", "pass123")
        u2 = user_svc.register("User Two", "u2@t.com", "pass123")
        assert u1.id != u2.id

    def test_register_status_is_active(self, user_svc):
        user = user_svc.register("Active", "active@t.com", "pass123")
        assert user.status == UserStatus.ACTIVE


class TestUserAuthentication:
    def test_authenticate_success(self, user_svc):
        user_svc.register("Auth Test", "auth@t.com", "mypassword")
        user = user_svc.authenticate("auth@t.com", "mypassword")
        assert user.email == "auth@t.com"

    def test_authenticate_wrong_password_raises(self, user_svc):
        user_svc.register("Auth Test", "auth2@t.com", "correctpass")
        with pytest.raises(InvalidCredentialsError):
            user_svc.authenticate("auth2@t.com", "wrongpass")

    def test_authenticate_nonexistent_email_raises(self, user_svc):
        with pytest.raises(InvalidCredentialsError):
            user_svc.authenticate("nobody@t.com", "pass123")

    def test_authenticate_blocked_user_raises(self, user_svc):
        user = user_svc.register("Blocked", "blocked@t.com", "pass123")
        user_svc.block_user(user.id)
        with pytest.raises(UserBlockedError):
            user_svc.authenticate("blocked@t.com", "pass123")

    def test_authenticate_case_insensitive_email(self, user_svc):
        user_svc.register("Case", "Case@T.COM", "pass123")
        user = user_svc.authenticate("case@t.com", "pass123")
        assert user is not None


class TestUserBlockUnblock:
    def test_block_user_success(self, user_svc, student):
        blocked = user_svc.block_user(student.id)
        assert blocked.status == UserStatus.BLOCKED

    def test_block_nonexistent_user_raises(self, user_svc):
        with pytest.raises(UserNotFoundError):
            user_svc.block_user(9999)

    def test_activate_user_success(self, user_svc, student):
        user_svc.block_user(student.id)
        activated = user_svc.activate_user(student.id)
        assert activated.status == UserStatus.ACTIVE

    def test_block_emits_event(self, user_svc, student, event_bus):
        user_svc.block_user(student.id)
        events = [e for e in event_bus.get_history() if isinstance(e, UserBlockedEvent)]
        assert any(e.user_id == student.id for e in events)

    def test_blocked_user_is_not_active(self, user_svc, student):
        user_svc.block_user(student.id)
        user = user_svc.get_user(student.id)
        assert not user.is_active()


class TestUserProfile:
    def test_get_profile_returns_dict(self, user_svc, student):
        profile = user_svc.get_profile(student.id)
        assert isinstance(profile, dict)
        assert profile["email"] == student.email

    def test_get_profile_nonexistent_raises(self, user_svc):
        with pytest.raises(UserNotFoundError):
            user_svc.get_profile(9999)

    def test_update_name_success(self, user_svc, student):
        updated = user_svc.update_name(student.id, "Нове Ім'я")
        assert updated.name == "Нове Ім'я"

    def test_update_name_too_short_raises(self, user_svc, student):
        with pytest.raises(ValueError):
            user_svc.update_name(student.id, "X")

    def test_change_password_success(self, user_svc, student):
        updated = user_svc.change_password(student.id, "pass123", "newpass456")
        assert updated.password_hash != ""

    def test_change_password_wrong_old_raises(self, user_svc, student):
        with pytest.raises(InvalidCredentialsError):
            user_svc.change_password(student.id, "wrongold", "newpass456")

    def test_change_password_too_short_raises(self, user_svc, student):
        with pytest.raises(ValueError):
            user_svc.change_password(student.id, "pass123", "abc")

    def test_get_all_students(self, user_svc, student, teacher):
        students = user_svc.get_all_students()
        assert any(u.id == student.id for u in students)
        assert not any(u.id == teacher.id for u in students)

    def test_get_all_teachers(self, user_svc, student, teacher):
        teachers = user_svc.get_all_teachers()
        assert any(u.id == teacher.id for u in teachers)
        assert not any(u.id == student.id for u in teachers)

    def test_profile_contains_enrolled_courses_count(self, user_svc, student):
        profile = user_svc.get_profile(student.id)
        assert "enrolled_courses" in profile
        assert profile["enrolled_courses"] == 0


class TestUserModel:
    def test_user_enroll_adds_course(self, student):
        student.enroll(42)
        assert 42 in student.enrolled_course_ids

    def test_user_enroll_idempotent(self, student):
        student.enroll(42)
        student.enroll(42)
        assert student.enrolled_course_ids.count(42) == 1

    def test_user_unenroll_removes_course(self, student):
        student.enroll(42)
        student.unenroll(42)
        assert 42 not in student.enrolled_course_ids

    def test_user_unenroll_not_enrolled_safe(self, student):
        student.unenroll(999)  # should not raise

    def test_is_student_true(self, student):
        assert student.is_student()

    def test_is_teacher_false_for_student(self, student):
        assert not student.is_teacher()

    def test_is_teacher_true(self, teacher):
        assert teacher.is_teacher()
