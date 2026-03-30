# main.py
import queue
import threading
import sys
import numpy as np
import sounddevice as sd
from pynput import keyboard

import os
from dotenv import load_dotenv

from transcriber import BaseTranscriber
from whisper_faster import FasterWhisperTranscriber

class PushToTalkRecorder:
    def __init__(self, transcriber: BaseTranscriber, sample_rate=16000, chunk_seconds=3):
        self.transcriber = transcriber
        self.sample_rate = sample_rate
        self.chunk_size = sample_rate * chunk_seconds
        
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.hotkey = {keyboard.Key.ctrl_l, keyboard.Key.alt_l}
        self.pressed_keys = set()
        self.running = True

    def _audio_callback(self, indata, frames, time_info, status):
        """Met l'audio en file d'attente (callback très léger = pas de blocage)."""
        if status:
            print(f"⚠️ {status}", file=sys.stderr)
        if self.is_recording:
            self.audio_queue.put(indata.copy())

    def _on_press(self, key):
        self.pressed_keys.add(key)
        if self.hotkey.issubset(self.pressed_keys) and not self.is_recording:
            self.is_recording = True
            print("\n🎙  Enregistrement en cours...", flush=True)

    def _on_release(self, key):
        self.pressed_keys.discard(key)
        if self.is_recording and not self.hotkey.issubset(self.pressed_keys):
            self.is_recording = False
            # None agit comme un "signal de fin de phrase" pour le thread
            self.audio_queue.put(None) 

    def _process_queue(self):
        """Worker Thread unique : lit la queue et transcrit de manière asynchrone."""
        buffer = []
        current_frames = 0

        while self.running:
            item = self.audio_queue.get() # Bloque jusqu'à recevoir de l'audio

            if item is None:
                # Touche relâchée : On transcrit tout ce qu'il reste dans le buffer
                if buffer:
                    audio_data = np.concatenate(buffer, axis=0).flatten()
                    text = self.transcriber.transcribe(audio_data)
                    if text:
                        print(f"  {text}", flush=True)
                buffer.clear()
                current_frames = 0
                print("⏸️  Pause.", flush=True)

            else:
                # Accumulation ultra rapide dans une liste
                buffer.append(item)
                current_frames += len(item)

                # Si le buffer atteint la taille d'un "chunk" (ex: 3 secondes), on transcrit en direct
                if current_frames >= self.chunk_size:
                    audio_data = np.concatenate(buffer, axis=0).flatten()
                    buffer.clear()
                    current_frames = 0
                    
                    text = self.transcriber.transcribe(audio_data)
                    if text:
                        print(f"  {text}", flush=True)

    def start(self):
        """Démarre le thread de traitement et l'écoute du micro/clavier."""
        worker = threading.Thread(target=self._process_queue, daemon=True)
        worker.start()

        print("\n💡 Maintenez Ctrl+Alt pour dicter — Ctrl+C dans la console pour quitter\n")

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
            print("\n👋 Arrêt du programme.")
        finally:
            self.running = False


if __name__ == "__main__":
    load_dotenv()
    
    model_name = os.getenv("ARIA_STT_MODEL", "small")
    language = os.getenv("ARIA_STT_LANG", "fr")
    
    # Injection de dépendance : On initialise le moteur et on le donne à l'enregistreur
    engine = FasterWhisperTranscriber(model_name=model_name, language=language)
    app = PushToTalkRecorder(transcriber=engine)
    app.start()