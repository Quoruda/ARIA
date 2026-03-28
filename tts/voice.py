import threading
import queue
import sounddevice as sd

class Voice:
    def __init__(self):
        # --- SYSTÈME DE LECTURE STREAMING (Commun à toutes les voix) ---
        self.audio_queue = queue.Queue()
        self.is_playing = False
        self.playback_thread = None

    def start_playback(self):
        """Lance le Thread de lecture audio en arrière-plan."""
        if not self.is_playing:
            self.is_playing = True
            self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
            self.playback_thread.start()

    def stop_playback(self):
        """Arrête la lecture et vide le buffer."""
        self.is_playing = False
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def _playback_loop(self):
        """Boucle de consommation de la file d'attente (exécutée dans le Thread)."""
        while self.is_playing:
            try:
                # On attend un tuple contenant (données_audio, frequence_echantillonnage)
                audio_data, sample_rate = self.audio_queue.get(timeout=0.1)
                
                if audio_data is not None:
                    sd.play(audio_data, samplerate=sample_rate)
                    sd.wait() # Bloque jusqu'à la fin de ce son précis
                
                self.audio_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Erreur de lecture audio : {e}")

    def add_to_queue(self, audio_data, sample_rate: int):
        """Méthode à appeler par les classes enfants pour jouer un son."""
        self.audio_queue.put((audio_data, sample_rate))

    # --- MÉTHODES ABSTRAITES (À implémenter par les enfants) ---
    def load_model(self):
        raise NotImplementedError

    def unload_model(self):
        raise NotImplementedError
    
    def generate_audio(self, text: str):
        """Génère l'audio et appelle self.add_to_queue(audio, sr)"""
        raise NotImplementedError