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

    def stream_async(self, generator_func):
        """Runs stream() in a background thread.

        Args:
            generator_func: A callable that returns a generator (not a generator itself)
        """
        import threading
        def run():
            # Call the function to get the generator INSIDE the thread
            generator = generator_func() if callable(generator_func) else generator_func
            self.stream(generator)
        threading.Thread(target=run, daemon=True).start()

    def stream(self, generator: Iterator[str]):
        """Consumes a word stream, prints it, and sends phrases to the voice engine."""
        self.is_generating = True
        try:
            sentence_buffer = ""
            sent_to_tts = set()  # Track which phrases we've already sent to TTS
            print("🔊 ARIA: ", end="", flush=True)

            for word in generator:
                print(word, end="", flush=True)
                sentence_buffer += word

                match = self._sentence_end_pattern.search(sentence_buffer)
                if match:
                    end_index = match.end()
                    phrase = sentence_buffer[:end_index].strip()

                    if len(phrase) > 1 and self.mode == "audio" and self.voice is not None:
                        if phrase not in sent_to_tts:  # Only send if not already sent
                            self.voice.generate_audio(phrase)
                            sent_to_tts.add(phrase)

                    sentence_buffer = sentence_buffer[end_index:]

            if sentence_buffer.strip():
                phrase = sentence_buffer.strip()
                if len(phrase) > 1 and self.mode == "audio" and self.voice is not None:
                    if phrase not in sent_to_tts:  # Only send if not already sent
                        self.voice.generate_audio(phrase)
                        sent_to_tts.add(phrase)
        finally:
            self.is_generating = False
            if self.mode == "text":
                print("\n💡 Type your message and press Enter (Ctrl+C to quit).", flush=True)
            else:
                print("\n💡 Press Ctrl+Alt to speak.", flush=True)
