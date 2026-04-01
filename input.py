from typing import Callable, Optional
from stt.micro_recorder import PushToTalkRecorder
from tts.voice import Voice


class InputManager:
    def __init__(
        self,
        on_input: Callable[[str], None],
        mode: str,
        recorder: Optional[PushToTalkRecorder] = None,
        voice: Optional[Voice] = None,
    ):
        self.on_input = on_input
        self.mode = mode.lower()  # "audio" or "text"
        self.recorder = recorder
        self.voice = voice

    @classmethod
    def from_env(
        cls,
        on_input: Callable[[str], None],
        is_busy: Callable[[], bool],
        mode: str,
        voice: Optional[Voice] = None,
    ) -> "InputManager":
        recorder = None
        if mode.lower() == "audio":
            recorder = PushToTalkRecorder.from_env(
                on_transcription=on_input,
                can_record=lambda: not is_busy()
            )
        return cls(on_input=on_input, mode=mode, recorder=recorder, voice=voice)

    def run(self):
        """Starts the main input loop (text terminal or microphone)."""
        if self.mode == "text":
            print("\n💡 Type your message and press Enter (Ctrl+C to quit).")
            while True:
                try:
                    user_text = input("> ").strip()
                except EOFError:
                    return
                if not user_text:
                    continue
                self.on_input(user_text)
        else:
            try:
                self.recorder.start()
            except KeyboardInterrupt:
                if self.voice is not None:
                    self.voice.stop_playback()
