from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    @abstractmethod
    def save(self, entity: T) -> T:
        pass

    @abstractmethod
    def find_by_id(self, entity_id: int) -> Optional[T]:
        pass

    @abstractmethod
    def find_all(self) -> List[T]:
        pass

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        pass

    @abstractmethod
    def exists(self, entity_id: int) -> bool:
        pass
