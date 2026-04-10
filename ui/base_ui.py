from abc import ABC, abstractmethod

class BaseUI(ABC):
    """Abstract base class for all UI adapters."""
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def start(self):
        """Start the UI (e.g. launch the thread or async task)."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the UI safely."""
        pass

    @abstractmethod
    def set_state(self, state: str):
        """
        Update the visual state of the assistant.
        Typical states: 'idle', 'listening', 'thinking', 'speaking', 'booting', 'error'
        """
        pass
