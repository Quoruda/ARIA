# main.py
import queue
import threading
import sys
import numpy as np
import sounddevice as sd
from pynput import keyboard

import os
from dotenv import load_dotenv

from stt.transcriber import BaseTranscriber
from stt.whisper_faster import FasterWhisperTranscriber

class PushToTalkRecorder:
    @classmethod
    def from_env(cls, on_transcription=None, can_record=None) -> "PushToTalkRecorder":
        """Reads STT configuration from environment variables and returns a ready PushToTalkRecorder."""
        import os
        model_name = os.getenv("STT_MODEL", "small")
        language = os.getenv("STT_LANG", "fr")
        transcriber = FasterWhisperTranscriber(model_name=model_name, language=language)
        return cls(transcriber=transcriber, on_transcription=on_transcription, can_record=can_record)

    def __init__(self, transcriber: BaseTranscriber, sample_rate=16000, chunk_seconds=3, on_transcription=None, can_record=None):
        self.transcriber = transcriber
        self.sample_rate = sample_rate
        self.chunk_size = sample_rate * chunk_seconds
        
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.hotkey = {keyboard.Key.ctrl_l, keyboard.Key.alt_l}
        self.pressed_keys = set()
        self.running = True
        
        self.on_transcription = on_transcription
        self.can_record = can_record

    def _audio_callback(self, indata, frames, time_info, status):
        """Non-blocking audio callback."""
        if status:
            print(f"⚠️ {status}", file=sys.stderr)
        if self.is_recording:
            self.audio_queue.put(indata.copy())

    def _on_press(self, key):
        self.pressed_keys.add(key)
        if self.hotkey.issubset(self.pressed_keys) and not self.is_recording:
            if self.can_record and not self.can_record():
                return
            self.is_recording = True
            print("\n🎙  Recording in progress...", flush=True)

    def _on_release(self, key):
        self.pressed_keys.discard(key)
        if self.is_recording and not self.hotkey.issubset(self.pressed_keys):
            self.is_recording = False
            self.audio_queue.put(None) 

    def _process_queue(self):
        """Worker thread for asynchronous transcription."""
        buffer = []
        full_session_text = []
        current_frames = 0

        while self.running:
            item = self.audio_queue.get() 

            if item is None:
                if buffer:
                    audio_data = np.concatenate(buffer, axis=0).flatten()
                    text = self.transcriber.transcribe(audio_data)
                    if text:
                        print(f"  {text}", flush=True)
                        full_session_text.append(text)
                
                final_text = " ".join(full_session_text).strip()
                if final_text and self.on_transcription:
                    self.on_transcription(final_text)

                buffer.clear()
                full_session_text.clear()
                current_frames = 0
                print("⏸️  Recording stopped.", flush=True)

            else:
                buffer.append(item)
                current_frames += len(item)

                if current_frames >= self.chunk_size:
                    audio_data = np.concatenate(buffer, axis=0).flatten()
                    buffer.clear()
                    current_frames = 0
                    
                    text = self.transcriber.transcribe(audio_data)
                    if text:
                        print(f"  {text}", flush=True)
                        full_session_text.append(text)

    def start(self):
        """Starts the processing thread and microphone/keyboard listening."""
        worker = threading.Thread(target=self._process_queue, daemon=True)
        worker.start()

        print("\n💡 Hold Ctrl+Alt to dictate — Ctrl+C in console to quit\n")

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                callback=self._audio_callback,
                blocksize=1024
            ):
                with keyboard.Listener(on_press=self._on_press, on_release=self._on_release) as listener:
                    listener.join()
        except KeyboardInterrupt:
            print("\n👋 Program stopped.")
        finally:
            self.running = False


if __name__ == "__main__":
    load_dotenv()
    
    model_name = os.getenv("ARIA_STT_MODEL", "small")
    language = os.getenv("ARIA_STT_LANG", "fr")
    
    engine = FasterWhisperTranscriber(model_name=model_name, language=language)
    app = PushToTalkRecorder(transcriber=engine)
    app.start()