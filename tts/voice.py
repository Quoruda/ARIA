import threading
import queue
import sounddevice as sd

class Voice:
    def __init__(self):
        # --- STREAMING PLAYBACK SYSTEM (Common to all voices) ---
        self.audio_queue = queue.Queue()
        self.is_playing = False
        self.playback_thread = None

    def start_playback(self):
        """Starts the background audio playback thread."""
        if not self.is_playing:
            self.is_playing = True
            self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
            self.playback_thread.start()

    def stop_playback(self):
        """Stops playback and clears the buffer."""
        self.is_playing = False
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def _playback_loop(self):
        """Queue consumer loop (executed within the Thread)."""
        while self.is_playing:
            try:
                # We expect a tuple containing (audio_data, sample_rate)
                audio_data, sample_rate = self.audio_queue.get(timeout=0.1)
                
                if audio_data is not None:
                    sd.play(audio_data, samplerate=sample_rate)
                    sd.wait() # Blocks until this specific sound is finished
                
                self.audio_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Audio playback error: {e}")

    def add_to_queue(self, audio_data, sample_rate: int):
        """Method to be called by child classes to play sound."""
        self.audio_queue.put((audio_data, sample_rate))

    # --- ABSTRACT METHODS (To be implemented by children) ---
    def load_model(self):
        raise NotImplementedError

    def unload_model(self):
        raise NotImplementedError
    
    def generate_audio(self, text: str):
        """Generates audio and calls self.add_to_queue(audio, sr)"""
        raise NotImplementedError