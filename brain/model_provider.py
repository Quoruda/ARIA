from abc import ABC, abstractmethod

class ModelProvider(ABC):
    @abstractmethod
    def get_model(self):
        """Returns a configured LangChain-compatible model instance."""
        ...
