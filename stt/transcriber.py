from abc import ABC, abstractmethod

class BaseTranscriber(ABC):
    
    @abstractmethod
    def transcribe(self, audio_data) -> str:
        pass