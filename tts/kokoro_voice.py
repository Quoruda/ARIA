import os
from kokoro import KPipeline
from tts.voice import Voice

class KokoroVoice(Voice):
    def __init__(self, lang_code='f', voice_name='ff_siwis', speed=1.0):
        super().__init__() # Initializes the parent queue
        self.lang_code = lang_code
        self.voice_name = voice_name
        self.speed = speed
        self.pipeline = None

    def load_model(self):
        """
        Loads the Kokoro model, explicitly forcing CPU device.
        """
        print(f"Loading Kokoro model (lang={self.lang_code}) on CPU...")
        
        # device='cpu' ensures it runs on CPU
        self.pipeline = KPipeline(lang_code=self.lang_code, device='cpu')
        
        print("Kokoro model loaded!")

    def unload_model(self):
        self.pipeline = None

    def generate_audio(self, text: str):
        """
        Génère l'audio avec Kokoro et le délègue au système de lecture du parent.
        """
        if self.pipeline is None:
            self.load_model()

        # Kokoro découpe déjà nativement les phrases longues en générateurs
        generator = self.pipeline(text, voice=self.voice_name, speed=self.speed)
        
        for _, _, audio_chunk in generator:
            # On envoie le morceau au parent. Kokoro sort toujours du 24000 Hz.
            self.add_to_queue(audio_chunk, 24000)