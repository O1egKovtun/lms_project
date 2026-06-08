import hashlib
import re
from typing import Optional, List

from src.models.user import User, UserRole, UserStatus
from src.storage.repositories import InMemoryUserRepository
from src.utils.exceptions import (
    UserNotFoundError, EmailAlreadyExistsError,
    InvalidEmailError, UserBlockedError, InvalidCredentialsError
)
from src.utils.observers import EventBus, UserRegisteredEvent, UserBlockedEvent


class UserService:
    EMAIL_REGEX = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$')

    def __init__(self, user_repo: InMemoryUserRepository,
                 event_bus: EventBus = None):
        self._repo = user_repo
        self._event_bus = event_bus or EventBus()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _validate_email(self, email: str) -> None:
        if not self.EMAIL_REGEX.match(email):
            raise InvalidEmailError(f"Invalid email format: {email}")

    def register(self, name: str, email: str, password: str,
                 role: UserRole = UserRole.STUDENT) -> User:
        self._validate_email(email)
        if not name or len(name.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        if self._repo.find_by_email(email):
            raise EmailAlreadyExistsError(f"Email already registered: {email}")

        user = User(
            id=0,
            name=name.strip(),
            email=email.lower().strip(),
            password_hash=self._hash_password(password),
            role=role,
        )
        saved = self._repo.save(user)
        self._event_bus.publish(
            UserRegisteredEvent(
                user_id=saved.id,
                email=saved.email))
        return saved

    def authenticate(self, email: str, password: str) -> User:
        user = self._repo.find_by_email(email)
        if not user:
            raise InvalidCredentialsError("Invalid email or password")
        if user.password_hash != self._hash_password(password):
            raise InvalidCredentialsError("Invalid email or password")
        if not user.is_active():
            raise UserBlockedError(f"User {user.email} is blocked")
        return user

    def get_user(self, user_id: int) -> User:
        user = self._repo.find_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        return user

    def block_user(self, user_id: int) -> User:
        user = self.get_user(user_id)
        user.block()
        self._repo.save(user)
        self._event_bus.publish(UserBlockedEvent(user_id=user.id))
        return user

    def activate_user(self, user_id: int) -> User:
        user = self.get_user(user_id)
        user.activate()
        return self._repo.save(user)

    def get_all_students(self) -> List[User]:
        return self._repo.find_by_role(UserRole.STUDENT)

    def get_all_teachers(self) -> List[User]:
        return self._repo.find_by_role(UserRole.TEACHER)

    def get_profile(self, user_id: int) -> dict:
        user = self.get_user(user_id)
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role.value,
            "status": user.status.value,
            "enrolled_courses": len(user.enrolled_course_ids),
        }

    def update_name(self, user_id: int, new_name: str) -> User:
        if not new_name or len(new_name.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        user = self.get_user(user_id)
        user.name = new_name.strip()
        return self._repo.save(user)

    def change_password(self, user_id: int, old_password: str,
                        new_password: str) -> User:
        user = self.get_user(user_id)
        if user.password_hash != self._hash_password(old_password):
            raise InvalidCredentialsError("Old password is incorrect")
        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters")
        user.password_hash = self._hash_password(new_password)
        return self._repo.save(user)
