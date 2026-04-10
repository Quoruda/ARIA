from abc import ABC, abstractmethod
from threading import Lock
import logging
import uuid

logger = logging.getLogger(__name__)


class BaseTrigger(ABC):
    """
    Abstract base class for all trigger types.
    Each trigger type (time-based, event-based, etc.) inherits from this.
    """

    def __init__(self, prompt: str, context: str = None):
        from triggers.scheduler import scheduler
        self.id = str(uuid.uuid4())
        self.prompt = prompt
        self.context = context
        self.executed = False
        self._lock = Lock()
        self._claimed = False  # Prevents a trigger from being fetched multiple times before execution
        self.target_channel = getattr(scheduler, 'current_channel', None)
        self.user_id = getattr(scheduler, 'current_user_id', None)

    @abstractmethod
    def is_due(self) -> bool:
        """
        Check if this trigger should be executed now.
        Returns True if the trigger's condition is met.
        """
        pass

    def try_claim(self) -> bool:
        """Returns True if the trigger is reserved for execution."""
        with self._lock:
            if self.executed or self._claimed:
                return False
            self._claimed = True
            return True

    def mark_executed(self):
        """Mark this trigger as executed."""
        with self._lock:
            self.executed = True
            self._claimed = False

    def __repr__(self):
        return f"<{self.__class__.__name__}(prompt='{self.prompt[:20]}...', executed={self.executed})>"
