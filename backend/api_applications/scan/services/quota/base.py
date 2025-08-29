from abc import ABC, abstractmethod

class QuotaStrategy(ABC):
    @abstractmethod
    def consume(self, user, count=1) -> bool:
        """Attempt to consume quota for a given resource type."""
        pass