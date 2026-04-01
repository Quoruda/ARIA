import re
from typing import Callable, Iterator, Optional
from tts.voice import Voice


class OutputManager:
    def __init__(self, voice: Optional[Voice], mode: str):
        self.voice = voice
        self.mode = mode.lower()  # "audio" or "text"
        self.is_generating = False
        self._sentence_end_pattern = re.compile(r'([.!?]+(?:\s+|$))')

    @classmethod
    def from_env(cls, voice: Optional[Voice], mode: str) -> "OutputManager":
        return cls(voice=voice, mode=mode)

    def stream_async(self, generator: Iterator[str]):
        """Runs stream() in a background thread."""
        import threading
        threading.Thread(target=self.stream, args=(generator,), daemon=True).start()

    def stream(self, generator: Iterator[str]):
        """Consumes a word stream, prints it, and sends phrases to the voice engine."""
        self.is_generating = True
        try:
            sentence_buffer = ""
            print("🔊 ARIA: ", end="", flush=True)

            for word in generator:
                print(word, end="", flush=True)
                sentence_buffer += word

                match = self._sentence_end_pattern.search(sentence_buffer)
                if match:
                    end_index = match.end()
                    phrase = sentence_buffer[:end_index].strip()

                    if len(phrase) > 1 and self.mode == "audio" and self.voice is not None:
                        self.voice.generate_audio(phrase)

                    sentence_buffer = sentence_buffer[end_index:]

            if sentence_buffer.strip():
                phrase = sentence_buffer.strip()
                if len(phrase) > 1 and self.mode == "audio" and self.voice is not None:
                    self.voice.generate_audio(phrase)
        finally:
            self.is_generating = False
            if self.mode == "text":
                print("\n💡 Type your message and press Enter (Ctrl+C to quit).", flush=True)
            else:
                print("\n💡 Press Ctrl+Alt to speak.", flush=True)
